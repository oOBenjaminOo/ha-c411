"""Download and Freeleech conditions for automations."""

from homeassistant.components.binary_sensor import BinarySensorEntity

from .entity import C411Entity, value_at


async def async_setup_entry(hass, entry, async_add_entities):
    """Register the profile conditions."""
    async_add_entities(
        [
            C411BinarySensor(entry.runtime_data, "freeleech", "freeleech", ("freeleech", "active")),
            C411BinarySensor(
                entry.runtime_data, "download_allowed", "telechargement_autorise", ("download", "allowed")
            ),
            C411BinarySensor(entry.runtime_data, "silverleech", "silverleech", ("silverLeech",)),
        ]
    )


class C411BinarySensor(C411Entity, BinarySensorEntity):
    """Expose a boolean without guessing absent data."""

    def __init__(self, coordinator, key, object_id, path):
        super().__init__(coordinator, key, object_id)
        self._path = path

    @property
    def is_on(self):
        value = value_at(self.coordinator.data, *self._path)
        return value if isinstance(value, bool) else None
