"""Shared profile entity."""

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN


class C411Entity(CoordinatorEntity):
    """Identify entities by account and metric."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, key, object_id):
        super().__init__(coordinator)
        profile = coordinator.data
        self._attr_unique_id = f"{profile['id']}_{key}"
        self._attr_translation_key = key
        self._attr_suggested_object_id = f"c411_{object_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(profile["id"]))},
            name=f"C411 {profile['username']}",
            manufacturer="C411",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://c411.org/",
        )


def value_at(profile, *path):
    """Read a documented nested field that may be absent."""
    value = profile
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value
