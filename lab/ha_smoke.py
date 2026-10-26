"""Run inside the pinned HA container; only synthetic states, no HA doubles."""

import asyncio
import json
import os
from pathlib import Path
import sqlite3
import sys
import time

from homeassistant import bootstrap, loader
from homeassistant.core import HomeAssistant, HassJob

DOMAIN = "energy_cost_monitor"
CONFIG = Path("/config")


def prepare_migration():
    """Invent one closed interval; never load any operator data into this lab."""
    from custom_components.energy_cost_monitor._core.migration import TABLES, migrate_legacy
    from custom_components.energy_cost_monitor._core.sources import parse_config
    from custom_components.energy_cost_monitor._core.application_migration import migrate_application
    config = parse_config(json.loads(Path("/repo/examples/minimal.json").read_text()))
    start = int(time.time() // 900) * 900 - 3600
    with sqlite3.connect(CONFIG / "synthetic-legacy.sqlite3") as old:
        for table, definition in TABLES.items():
            old.execute(f'CREATE TABLE "{table}"({definition})')
        old.execute("INSERT INTO samples VALUES(?, '{}')", (start + 800,))
        old.execute("INSERT INTO intervals VALUES(?,?)", (start, json.dumps({
            "energy": {"invented": 0.5}, "seconds": {"invented": 900}})))
        profile = {"schema_version": 1, "timezone": "UTC", "market": {"basis": "quarter_hour"},
                   "suppliers": {"invented": [{"from": "2020-01-01", "until": "2030-01-01",
                       "import_net": .2, "export_net": .05, "monthly_net": 3, "discount_net": 0,
                       "source": "Synthetic laboratory"}]}}
        old.execute("INSERT INTO profiles VALUES('synthetic',?,?)", (start, json.dumps(profile)))
        old.execute("INSERT INTO reports VALUES('synthetic',?,?,?,?)",
                    (start, start+900, start+900, json.dumps({"csv": "a,b\n1,2", "note": "<script>invented</script>"})))
    migrate_legacy(CONFIG / "synthetic-legacy.sqlite3", CONFIG / ".storage/energy_cost_monitor.sqlite3",
                   config, role_mapping={"house": "invented", "import": "invented"}, cutover=start + 900)
    (CONFIG / "historical-start").write_text(str(start))
    evidence = migrate_application(CONFIG / "synthetic-legacy.sqlite3",
                                   CONFIG / ".storage/energy_cost_monitor_application.sqlite3",
                                   horizon="2030-01-01", active_profile="synthetic")
    (CONFIG / "legacy-report-id").write_text(evidence["reports"]["synthetic"])


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
        {"http": {"server_host": "127.0.0.1", "server_port": 8123},
         "homeassistant": {"name": "Synthetic lab", "time_zone": "Europe/Ljubljana",
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
        from custom_components.energy_cost_monitor.api import ApplicationView
        from types import SimpleNamespace
        app_view = ApplicationView(hass)
        class Request(dict):
            method = "GET"
        admin_request = Request(hass_user=SimpleNamespace(is_admin=True))
        app = runtime.application
        # The real HA scheduler must keep this callback on the event loop.
        # A plain sync function is sent to an executor, where create_task fails.
        scheduled = hass.async_run_hass_job(HassJob(app.tick))
        if scheduled is not None:
            await scheduled
        assert app.market_task is not None
        await app.market_task
        assert app.price_error is None
        profile = json.loads(Path("/repo/examples/application-profile.json").read_text())
        if phase == "create":
            await app.call(app.store.save_profile, profile)
            end = int(time.time() // 900) * 900
            report_id = await app.call(app.store.freeze, runtime.collector.engine, end-900, end)
            await hass.async_add_executor_job((CONFIG / "report-id").write_text, report_id)
        report_id = (CONFIG / "report-id").read_text()
        response = await app_view.dispatch(admin_request, "report", {"id": report_id, "format": "html"})
        assert response.status == 200 and "sandbox" in response.headers["Content-Security-Policy"]
        if os.environ.get("ECM_LAB_MIGRATE") == "1":
            archived_id = (CONFIG / "legacy-report-id").read_text()
            archived = await app_view.dispatch(admin_request, "report", {"id": archived_id, "format": "csv"})
            assert archived.status == 200 and archived.text == "a,b\n1,2"
            archived = await app_view.dispatch(admin_request, "report", {"id": archived_id, "format": "html"})
            assert "&lt;script&gt;invented" in archived.text and "<script>invented" not in archived.text
        assert (await app.call(app.store.profiles))["active"]
        from aiohttp import ClientSession
        from homeassistant.auth.const import GROUP_ID_ADMIN
        admin = await hass.auth.async_create_system_user("Synthetic admin", group_ids=[GROUP_ID_ADMIN])
        member = await hass.auth.async_create_system_user("Synthetic member")
        admin_refresh = await hass.auth.async_create_refresh_token(admin)
        member_refresh = await hass.auth.async_create_refresh_token(member)
        headers = {"Authorization": "Bearer " + hass.auth.async_create_access_token(admin_refresh)}
        member_headers = {"Authorization": "Bearer " + hass.auth.async_create_access_token(member_refresh)}
        base = "http://127.0.0.1:8123"
        async with ClientSession() as client:
            async with client.get(base + "/api/energy_cost_monitor/profiles") as response:
                assert response.status == 401, response.status
            async with client.get(base + "/api/energy_cost_monitor/profiles", headers=member_headers) as response:
                assert response.status == 403, response.status
            async with client.post(base + "/api/energy_cost_monitor/profiles", json=profile, headers=headers) as response:
                assert response.status == 200, await response.text()
            async with client.get(base + "/api/energy_cost_monitor/view", headers=headers) as response:
                assert response.status == 200, await response.text()
            async with client.get(base + "/energy_cost_monitor/energy-cost-monitor-card.js") as response:
                assert response.status == 200 and "EnergyCostMonitorCard" in await response.text()
        hass.auth.async_remove_refresh_token(admin_refresh)
        hass.auth.async_remove_refresh_token(member_refresh)
        await hass.auth.async_remove_user(admin)
        await hass.auth.async_remove_user(member)
        from custom_components.energy_cost_monitor.backup import async_post_backup, async_pre_backup
        from custom_components.energy_cost_monitor._core.migration import snapshot
        await async_pre_backup(hass)
        assert runtime.collector.paused and runtime.collector.request() is None
        await hass.async_add_executor_job(
            snapshot, CONFIG / ".storage/energy_cost_monitor.sqlite3", CONFIG / f"backup-{phase}.sqlite3"
        )
        def application_snapshot():
            with sqlite3.connect(CONFIG / ".storage/energy_cost_monitor_application.sqlite3") as source:
                with sqlite3.connect(CONFIG / f"application-backup-{phase}.sqlite3") as target:
                    source.backup(target)
        await hass.async_add_executor_job(application_snapshot)
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
    application = CONFIG / ".storage/energy_cost_monitor_application.sqlite3"
    application.rename(CONFIG / "application-pre-restore.sqlite3")
    import shutil
    shutil.copyfile(CONFIG / "application-backup-restart.sqlite3", application)

asyncio.run(main())
