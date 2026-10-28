"""Admin import staging; no arbitrary paths and no production data defaults."""

from pathlib import Path
import re
import shutil
import uuid

from ._core.collector import drain_on_cancel
from ._core.history_import import inspect_legacy, import_history
from .const import DOMAIN


def stage_upload(hass, file_id):
    from homeassistant.components.file_upload import process_uploaded_file

    root = Path(hass.config.path(".storage", "energy_cost_monitor_imports"))
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if len(list(root.glob("*/source.sqlite3"))) >= 3:
        raise ValueError("discard_previous_import_first")
    ident = uuid.uuid4().hex
    directory = root / ident
    directory.mkdir(mode=0o700)
    try:
        with process_uploaded_file(hass, file_id) as uploaded:
            if uploaded.stat().st_size > 100 * 1024 * 1024:
                raise ValueError("import_too_large")
            target = directory / "source.sqlite3"
            shutil.copyfile(uploaded, target)
            target.chmod(0o600)
        return {"id": ident, **inspect_legacy(target)}
    except BaseException:
        shutil.rmtree(directory)
        raise


def staged_path(hass, ident):
    if not isinstance(ident, str) or not re.fullmatch(r"[0-9a-f]{32}", ident):
        raise ValueError("invalid_import_id")
    root = Path(hass.config.path(".storage", "energy_cost_monitor_imports")).resolve()
    directory = root / ident
    if directory.is_symlink() or directory.resolve().parent != root:
        raise ValueError("invalid_import_path")
    source = directory / "source.sqlite3"
    if source.is_symlink() or not source.is_file():
        raise ValueError("missing_import")
    return source


def discard_upload(hass, ident):
    source = staged_path(hass, ident)
    source.unlink()
    source.parent.rmdir()
    return {"discarded": True}


def list_uploads(hass):
    root = Path(hass.config.path(".storage", "energy_cost_monitor_imports"))
    return [{"id": path.parent.name, "created": path.stat().st_mtime}
            for path in root.glob("*/source.sqlite3")
            if re.fullmatch(r"[0-9a-f]{32}", path.parent.name)]


def resume_upload(hass, ident):
    return {"id": ident, **inspect_legacy(staged_path(hass, ident))}


async def apply_import(runtime, data):
    app, hass = runtime.application, runtime.hass
    if data.get("confirm") is not True:
        raise ValueError("review_and_confirm_import")
    async with app.lock:
        if app.stopped or hass.data.get(f"{DOMAIN}_backup_in_progress"):
            raise ValueError("application_temporarily_unavailable")
        await runtime.collector.pause()
        try:
            def run():
                source = staged_path(hass, data["id"])
                backup = Path(hass.config.path(".storage", "energy_cost_monitor_import_backups", uuid.uuid4().hex))
                return import_history(source, runtime.collector.engine, app.store, backup,
                                      expected_sha256=data["sha256"], role_mapping=data["mapping"],
                                      horizon=data["horizon"], active_profile=data["profile"],
                                      activate=data.get("activate", False))
            return await drain_on_cancel(hass.async_add_executor_job(run))
        finally:
            # A HA backup may have paused collection while waiting for app.lock.
            # It owns the pause until its post-backup hook, so do not undo it.
            if not hass.data.get(f"{DOMAIN}_backup_in_progress"):
                runtime.collector.resume()
