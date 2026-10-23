"""Run inside the pinned HA container; only synthetic states, no HA doubles."""

import asyncio
import json
from pathlib import Path
import sqlite3
import sys

from homeassistant import bootstrap, loader
from homeassistant.core import HomeAssistant

DOMAIN = "energy_cost_monitor"
CONFIG = Path("/config")


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
        await runtime.collector.request()
        await hass.async_block_till_done()
        sensor = hass.states.get("sensor.energy_cost_monitor_collection")
        assert sensor and sensor.state == "collecting", sensor
        before = await hass.async_add_executor_job(rows)
        if phase == "restart":
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
        print(json.dumps({"phase": phase, "samples": count, "result": "PASS"}), flush=True)
    finally:
        await hass.async_stop()


asyncio.run(main())
