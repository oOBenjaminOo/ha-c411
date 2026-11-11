"""Expose integration health without account or profile data."""

from homeassistant.loader import async_get_integration


async def async_get_config_entry_diagnostics(hass, entry):
    """Return only sync health for the selected entry."""
    integration = await async_get_integration(hass, "c411")
    coordinator = getattr(entry, "runtime_data", None)
    data = coordinator.data if coordinator is not None else None
    last_sync = data.get("_last_success") if data else None
    error = getattr(coordinator, "last_exception", None)
    if error is not None and error.__cause__ is not None:
        error = error.__cause__
    return {
        "version": str(integration.version),
        "last_successful_sync": last_sync.isoformat() if last_sync else None,
        "last_update_success": coordinator.last_update_success if coordinator else None,
        "last_error_type": type(error).__name__ if error else None,
    }
