"""Quiesce the single SQLite writer during Home Assistant backup."""

from .const import DOMAIN

BACKUP_LOCK = f"{DOMAIN}_backup_in_progress"


async def async_pre_backup(hass):
    """No writer remains once this hook returns; connections close per operation."""
    hass.data[BACKUP_LOCK] = True
    try:
        runtime = hass.data.get(DOMAIN)
        if runtime is not None and runtime.collector is None:
            raise RuntimeError("Energy Cost Monitor setup in progress; retry backup")
        if runtime is not None and runtime.collector is not None:
            await runtime.collector.pause()
        if runtime is not None and runtime.application is not None:
            await runtime.application.pause()
    except BaseException:
        hass.data.pop(BACKUP_LOCK, None)
        if runtime is not None and runtime.collector is not None:
            runtime.collector.resume()
        raise


async def async_post_backup(hass):
    """Resume if still loaded, preserving the backup gap as incomplete evidence."""
    hass.data.pop(BACKUP_LOCK, None)
    runtime = hass.data.get(DOMAIN)
    if runtime is not None and runtime.collector is not None:
        runtime.collector.resume()
