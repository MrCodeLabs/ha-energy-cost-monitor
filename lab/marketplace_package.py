"""Install an exact ECM commit through the real Marketplace archive installer."""

import asyncio
import os
from pathlib import Path
import sys

from homeassistant import bootstrap, loader
from homeassistant.components.marketplace.base import MarketplaceManager
from homeassistant.components.marketplace.enums import RepositoryCategory
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TOKEN
from homeassistant.core import HomeAssistant

DOMAIN = "energy_cost_monitor"
REPOSITORY = "MrCodeLabs/ha-energy-cost-monitor"


async def install(ref: str, expected_tree: Path | None) -> None:
    """Register the custom repository and install from a fixture catalog pointer."""
    hass = HomeAssistant("/config")
    hass.config.skip_pip = True
    loader.async_setup(hass)
    assert await bootstrap.async_from_config_dict(
        {"http": {"server_host": "127.0.0.1"}, "lovelace": {}}, hass
    )
    try:
        entry = ConfigEntry(
            data={CONF_TOKEN: os.environ["ECM_LAB_GITHUB_TOKEN"]},
            domain="marketplace",
            minor_version=1,
            options={},
            source="system",
            subentries_data=None,
            title="Marketplace lab",
            unique_id=None,
            version=1,
        )
        manager = MarketplaceManager(hass, entry)
        manager.set_active_categories()
        errors = await manager.async_register_repository(
            REPOSITORY, RepositoryCategory.INTEGRATION
        )
        assert not errors, errors
        repo = manager.repositories.get_by_full_name(REPOSITORY)
        assert repo is not None and repo.data.domain == DOMAIN
        installed = Path(hass.config.path("custom_components", DOMAIN))
        repo.data.installed = installed.is_dir()

        # No published tag is needed to rehearse the production archive path.
        manager.repositories.mark_default(repo)
        repo.data.last_version = None
        repo.data.last_commit = ref
        await repo.async_install_repository(ref=ref)
        assert repo.data.installed and repo.data.installed_commit == ref
        assert (installed / "manifest.json").is_file()
        if expected_tree is not None:
            expected = {
                path.relative_to(expected_tree): path.read_bytes()
                for path in expected_tree.rglob("*")
                if path.is_file()
            }
            actual = {
                path.relative_to(installed): path.read_bytes()
                for path in installed.rglob("*")
                if path.is_file()
            }
            assert actual.keys() == expected.keys()
            assert actual == expected
        print(f"Marketplace installed {ref} into the disposable HA configuration")
    finally:
        await hass.async_stop(force=True)


if __name__ == "__main__":
    asyncio.run(install(sys.argv[1], Path(sys.argv[2]) if len(sys.argv) == 3 else None))
