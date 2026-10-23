"""Normalize detached state observations, preserving explicit quality reasons."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType

from .sources import ENERGY_KINDS, ENERGY_UNITS, POWER_UNITS, Source, SourceConfig


@dataclass(frozen=True)
class Observation:
    """Adapter input; reported_at is a UTC Unix timestamp, not last_changed."""

    value: object
    unit: str | None
    reported_at: float | None


@dataclass(frozen=True)
class Reading:
    value: float | bool | None
    unit: str | None
    quality: str

    @property
    def usable(self) -> bool:
        return self.quality in {"valid", "estimated"}


@dataclass(frozen=True)
class Snapshot:
    readings: Mapping[str, Reading]
    required_roles: frozenset[str]

    @property
    def ready(self) -> bool:
        """Instantaneous meter readiness, not interval coverage or study approval."""
        return all(self.readings[role].usable for role in self.required_roles)


def _finite(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        return None
    try:
        number = float(value)
    except (ValueError, OverflowError):
        return None
    return number if isfinite(number) else None


def _read(role: str, source: Source, observation: Observation | None, now: float) -> Reading:
    unit = "kWh" if source.kind in ENERGY_KINDS else "kW" if source.kind == "power" else source.unit

    def invalid(reason: str) -> Reading:
        return Reading(None, unit, reason)

    if observation is None:
        return invalid("missing")
    value = observation.value
    if value is None or (isinstance(value, str) and value.strip().lower() in {"unknown", "unavailable", ""}):
        return invalid("unavailable")
    timestamp = observation.reported_at
    if type(timestamp) not in (int, float) or (timestamp := _finite(timestamp)) is None:
        return invalid("invalid_timestamp")
    age = now - timestamp
    if age < 0:
        return invalid("future_timestamp")
    if age > source.max_age_seconds:
        return invalid("stale")
    if observation.unit != source.unit:
        return invalid("unit_mismatch")
    if source.kind == "binary":
        if value == "on" or value is True:
            return Reading(True, None, "valid")
        if value == "off" or value is False:
            return Reading(False, None, "valid")
        return invalid("invalid_value")
    number = _finite(value)
    if number is None:
        return invalid("invalid_value")
    factor = (ENERGY_UNITS[source.unit] if source.kind in ENERGY_KINDS
              else POWER_UNITS[source.unit] if source.kind == "power" else 1.0)
    number *= factor
    if not isfinite(number):
        return invalid("invalid_value")
    signed_power = role in {"grid_power", "battery_power"}
    if (number < 0 and not signed_power) or (source.kind == "percentage" and number > 100):
        return invalid("out_of_range")
    quality = "estimated" if source.kind == "daily_energy_estimate" else "valid"
    return Reading(number, unit, quality)


def normalize_snapshot(config: SourceConfig, observations: Mapping[str, Observation], *, now: float) -> Snapshot:
    """Read only mapped entities; dependencies invalidate only their owning meter."""
    if type(now) not in (int, float) or (now := _finite(now)) is None:
        raise ValueError("invalid_observation_time")
    readings = {role: _read(role, source, observations.get(source.entity_id), now)
                for role, source in config.sources.items()}
    for role, source in config.sources.items():
        if readings[role].usable and any(not readings[dependency].usable for dependency in source.freshness_sources):
            readings[role] = Reading(None, readings[role].unit, "dependency_unavailable")
    return Snapshot(MappingProxyType(readings), config.required_roles)
