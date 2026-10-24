"""Run inside the pinned HA container; only synthetic states, no HA doubles."""

import asyncio
import json
import os
from pathlib import Path
import sqlite3
import sys
import time

from homeassistant import bootstrap, loader
from homeassistant.core import HomeAssistant

DOMAIN = "energy_cost_monitor"
CONFIG = Path("/config")


def prepare_migration():
    """Invent one closed interval; never load any operator data into this lab."""
    from custom_components.energy_cost_monitor._core.migration import TABLES, migrate_legacy
    from custom_components.energy_cost_monitor._core.sources import parse_config
    config = parse_config(json.loads(Path("/repo/examples/minimal.json").read_text()))
    start = int(time.time() // 900) * 900 - 3600
    with sqlite3.connect(CONFIG / "synthetic-legacy.sqlite3") as old:
        for table, definition in TABLES.items():
            old.execute(f'CREATE TABLE "{table}"({definition})')
        old.execute("INSERT INTO samples VALUES(?, '{}')", (start + 800,))
        old.execute("INSERT INTO intervals VALUES(?,?)", (start, json.dumps({
            "energy": {"invented": 0.5}, "seconds": {"invented": 900}})))
    migrate_legacy(CONFIG / "synthetic-legacy.sqlite3", CONFIG / ".storage/energy_cost_monitor.sqlite3",
                   config, role_mapping={"house": "invented", "import": "invented"}, cutover=start + 900)
    (CONFIG / "historical-start").write_text(str(start))


def rows():
    with sqlite3.connect(CONFIG / ".storage/energy_cost_monitor.sqlite3") as db:
        assert db.execute("PRAGMA quick_check").fetchone()[0] == "ok"
        return db.execute("SELECT count(*) FROM samples").fetchone()[0]


async def main():
    phase = sys.argv[1]
    hass = HomeAssistant(str(CONFIG))
    hass.config.skip_pip = True
    loader.async_setup(hass)
    assert await bootstrap.async_from_config_dict(
        {"homeassistant": {"name": "Synthetic lab", "time_zone": "Europe/Ljubljana",
                           "latitude": 0, "longitude": 0, "elevation": 0,
                           "unit_system": "metric"}}, hass
    ) is hass
    await hass.async_start()
    try:
        if phase == "create" and os.environ.get("ECM_LAB_MIGRATE") == "1":
            # Bootstrap has registered the custom package; migration stays offline
            # before creating the config entry/starting its writer.
            sys.path.insert(0, str(CONFIG))
            await hass.async_add_executor_job(prepare_migration)
        hass.states.async_set("sensor.example_import_energy", "10", {"unit_of_measurement": "kWh"})
        if phase == "create":
            sources = json.loads(Path("/repo/examples/minimal.json").read_text())
            result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
            assert result["type"] == "form", result
            result = await hass.config_entries.flow.async_configure(result["flow_id"], {
                "source_config": json.dumps(sources), "max_gap_seconds": 300,
            })
            assert result["type"] == "create_entry", result
        await hass.async_block_till_done()
        entries = hass.config_entries.async_entries(DOMAIN)
        assert len(entries) == 1
        entry = entries[0]
        assert entry.state.value == "loaded", entry.state
        runtime = hass.data[DOMAIN]
        if os.environ.get("ECM_LAB_MIGRATE") == "1":
            start = int((CONFIG / "historical-start").read_text())
            historical = await hass.async_add_executor_job(runtime.collector.engine.summary, start, start + 900)
            assert historical.energy_kwh["import"] == 0.5
        await runtime.collector.request()
        await hass.async_block_till_done()
        sensor = hass.states.get("sensor.energy_cost_monitor_collection")
        assert sensor and sensor.state == "collecting", sensor
        from custom_components.energy_cost_monitor.backup import async_post_backup, async_pre_backup
        from custom_components.energy_cost_monitor._core.migration import snapshot
        await async_pre_backup(hass)
        assert runtime.collector.paused and runtime.collector.request() is None
        await hass.async_add_executor_job(
            snapshot, CONFIG / ".storage/energy_cost_monitor.sqlite3", CONFIG / f"backup-{phase}.sqlite3"
        )
        await async_post_backup(hass)
        await runtime.collector.task
        before = await hass.async_add_executor_job(rows)
        if phase != "create":
            previous = int((CONFIG / "previous-count").read_text())
            assert before > previous, (before, previous)
        hass.states.async_set("sensor.example_import_energy", "unavailable", {"unit_of_measurement": "kWh"})
        await runtime.collector.request()
        await hass.async_block_till_done()
        assert hass.states.get(sensor.entity_id).state == "incomplete"
        hass.states.async_set("sensor.example_import_energy", "10.001", {"unit_of_measurement": "kWh"})
        await runtime.collector.request()
        assert await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        assert hass.data[DOMAIN] is not runtime
        count = await hass.async_add_executor_job(rows)
        assert count > before
        await hass.async_add_executor_job((CONFIG / "previous-count").write_text, str(count))
        print(json.dumps({"phase": phase, "migrated": os.environ.get("ECM_LAB_MIGRATE") == "1",
                          "samples": count, "result": "PASS"}), flush=True)
    finally:
        await hass.async_stop()


if sys.argv[1] == "restore":
    # The previous HA process has stopped. Keep its synthetic database and
    # recover into the now-vacant lab path before booting a third HA process.
    sys.path.insert(0, "/repo")
    from energy_cost_monitor.migration import recovery_bundle, restore_bundle
    from energy_cost_monitor.sources import parse_config
    source_config = parse_config(json.loads(Path("/repo/examples/minimal.json").read_text()))
    ledger = CONFIG / ".storage/energy_cost_monitor.sqlite3"
    bundle = CONFIG / "recovery.zip"
    recovery_bundle(ledger, bundle, source_config)
    ledger.rename(CONFIG / "pre-restore.sqlite3")
    restore_bundle(bundle, ledger, source_config)

asyncio.run(main())
