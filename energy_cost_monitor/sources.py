"""Validated source mapping, independent of Home Assistant and storage."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from math import isfinite
import re
from types import MappingProxyType


ENERGY_UNITS = {"Wh": 0.001, "kWh": 1.0, "MWh": 1000.0}
POWER_UNITS = {"W": 0.001, "kW": 1.0, "MW": 1000.0}
ENERGY_KINDS = frozenset({"cumulative_energy", "daily_energy_estimate"})
CAPABILITIES = frozenset({"solar", "battery", "ev", "heat_pump"})
# role: (owning capability, allowed input kinds)
ROLE_RULES = {
    "house": (None, {"cumulative_energy"}),
    "import": (None, {"cumulative_energy"}),
    "export": (None, {"cumulative_energy"}),
    "pv": ("solar", {"cumulative_energy"}),
    "charge": ("battery", {"cumulative_energy"}),
    "discharge": ("battery", {"cumulative_energy"}),
    "ev": ("ev", {"cumulative_energy"}),
    "heating": ("heat_pump", ENERGY_KINDS),
    "water": ("heat_pump", ENERGY_KINDS),
    "house_power": (None, {"power"}),
    "grid_power": (None, {"power"}),
    "pv_power": ("solar", {"power"}),
    "battery_power": ("battery", {"power"}),
    "battery_soc": ("battery", {"percentage"}),
    "ev_power": ("ev", {"power"}),
    "ev_connected": ("ev", {"binary"}),
}


class ConfigurationError(ValueError):
    """A safe field location and code, without echoing configuration values."""

    def __init__(self, path: str, code: str) -> None:
        self.path, self.code = path, code
        super().__init__(f"{path}: {code}")


def _object(value: object, path: str, allowed: set[str]) -> Mapping:
    if not isinstance(value, Mapping):
        raise ConfigurationError(path, "expected_object")
    if any(key not in allowed for key in value):
        raise ConfigurationError(path, "unknown_field")
    return value


def _positive(value: object, path: str) -> float:
    if type(value) not in (int, float):
        raise ConfigurationError(path, "expected_positive_number")
    try:
        result = float(value)
    except OverflowError:
        raise ConfigurationError(path, "expected_positive_number") from None
    if not isfinite(result) or result <= 0:
        raise ConfigurationError(path, "expected_positive_number")
    return result


@dataclass(frozen=True)
class Source:
    entity_id: str = field(repr=False)
    kind: str
    unit: str | None
    max_age_seconds: float
    max_power_kw: float | None
    freshness_sources: tuple[str, ...]


@dataclass(frozen=True)
class SourceConfig:
    capabilities: frozenset[str]
    sources: Mapping[str, Source]

    @property
    def required_roles(self) -> frozenset[str]:
        """Configured cumulative meters, excluding daily estimates and signals."""
        return frozenset(role for role, source in self.sources.items()
                         if source.kind == "cumulative_energy")


def parse_config(value: object) -> SourceConfig:
    """Validate the development schema; never look up entities or write files."""
    config = _object(value, "config", {"schema_version", "capabilities", "sources"})
    if type(config.get("schema_version")) is not int or config["schema_version"] != 1:
        raise ConfigurationError("schema_version", "unsupported_version")
    caps = config.get("capabilities", [])
    if not isinstance(caps, list) or any(not isinstance(c, str) or c not in CAPABILITIES for c in caps):
        raise ConfigurationError("capabilities", "invalid_capability")
    if len(set(caps)) != len(caps):
        raise ConfigurationError("capabilities", "duplicate_capability")
    raw_sources = _object(config.get("sources"), "sources", set(ROLE_RULES))
    sources = {}
    for role, raw in raw_sources.items():
        path = f"sources.{role}"
        raw = _object(raw, path, {"entity_id", "kind", "unit", "max_age_seconds",
                                  "max_power_kw", "freshness_sources"})
        capability, kinds = ROLE_RULES[role]
        if capability is not None and capability not in caps:
            raise ConfigurationError(path, "capability_disabled")
        kind = raw.get("kind")
        if not isinstance(kind, str) or kind not in kinds:
            raise ConfigurationError(path + ".kind", "invalid_kind")
        entity = raw.get("entity_id")
        domain = "binary_sensor" if kind == "binary" else "sensor"
        if not isinstance(entity, str) or not re.fullmatch(domain + r"\.[a-z0-9_]+", entity):
            raise ConfigurationError(path + ".entity_id", "invalid_entity_id")
        unit = raw.get("unit")
        units = ENERGY_UNITS if kind in ENERGY_KINDS else POWER_UNITS if kind == "power" else {"%": 1}
        if kind == "binary":
            unit_ok = unit is None
        else:
            unit_ok = isinstance(unit, str) and unit in units
        if not unit_ok:
            raise ConfigurationError(path + ".unit", "unsupported_unit")
        age = _positive(raw.get("max_age_seconds"), path + ".max_age_seconds")
        power = None
        if kind in ENERGY_KINDS:
            power = _positive(raw.get("max_power_kw"), path + ".max_power_kw")
        elif "max_power_kw" in raw:
            raise ConfigurationError(path + ".max_power_kw", "energy_only")
        dependencies = raw.get("freshness_sources", [])
        if (not isinstance(dependencies, list)
                or any(not isinstance(d, str) or d not in ROLE_RULES for d in dependencies)
                or len(set(dependencies)) != len(dependencies)):
            raise ConfigurationError(path + ".freshness_sources", "invalid_dependencies")
        if dependencies and kind not in ENERGY_KINDS:
            raise ConfigurationError(path + ".freshness_sources", "energy_only")
        sources[role] = Source(entity, kind, unit, age, power, tuple(dependencies))

    required = {"house", "import"}
    for capability, roles in (("solar", {"pv"}), ("battery", {"charge", "discharge"}), ("ev", {"ev"})):
        if capability in caps:
            required.update(roles)
    if not required <= sources.keys():
        raise ConfigurationError("sources", "missing_required_meter")
    if "heat_pump" in caps and not {"heating", "water"} & sources.keys():
        raise ConfigurationError("sources", "missing_heat_pump_source")

    for role, source in sources.items():
        for dependency in source.freshness_sources:
            if dependency not in sources or sources[dependency].kind in ENERGY_KINDS:
                raise ConfigurationError(f"sources.{role}.freshness_sources", "expected_configured_signal")
    # Aliasing house/import is useful for a minimal import-only household.
    entities: dict[str, set[str]] = {}
    for role, source in sources.items():
        entities.setdefault(source.entity_id, set()).add(role)
    for roles in entities.values():
        if len(roles) < 2:
            continue
        alias_ok = (roles == {"house", "import"} and not ({"solar", "battery"} & set(caps))
                    and "export" not in sources and sources["house"] == sources["import"])
        if not alias_ok:
            raise ConfigurationError("sources", "conflicting_entity_mapping")
    return SourceConfig(frozenset(caps), MappingProxyType(sources))
