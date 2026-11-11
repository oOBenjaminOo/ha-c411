"""Profile and numeric statistics."""

from urllib.parse import urljoin, urlsplit

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfInformation

from .entity import C411Entity, value_at

METRICS = {
    "profile": ("utilisateur", ("username",)),
    "level": ("niveau", ("level", "level")),
    "rank": ("rang", ("class", "slug")),
    "zen": ("zen", ("zen", "balance")),
    "uploaded": ("envoye", ("transfer", "uploaded", "total")),
    "downloaded": ("telecharge", ("transfer", "downloaded", "total")),
    "ratio": ("ratio", ()),
    "margin": ("marge_de_telechargement", ()),
}


async def async_setup_entry(hass, entry, async_add_entities):
    """Register profile sensors."""
    async_add_entities(
        C411Sensor(entry.runtime_data, key, object_id, path)
        for key, (object_id, path) in METRICS.items()
    )


class C411Sensor(C411Entity, SensorEntity):
    """Expose a metric from the shared profile."""

    def __init__(self, coordinator, key, object_id, path):
        super().__init__(coordinator, key, object_id)
        self._key = key
        self._path = path
        if key in {"uploaded", "downloaded", "margin"}:
            self._attr_device_class = SensorDeviceClass.DATA_SIZE
            self._attr_native_unit_of_measurement = UnitOfInformation.BYTES
            self._attr_suggested_unit_of_measurement = UnitOfInformation.GIBIBYTES
        if key not in {"profile", "rank"}:
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        profile = self.coordinator.data
        if self._key == "rank":
            slug = value_at(profile, "class", "effectiveSlug") or value_at(profile, *self._path)
            if not isinstance(slug, str) or not slug:
                return None
            tier = value_at(profile, "class", "progress", "grade", "tier")
            grade = value_at(profile, "class", "progress", "grade", "level")
            name = slug.replace("_", " ").replace("-", " ").title()
            if isinstance(tier, str) and type(grade) is int and 1 <= grade <= 4:
                return f"{name} {tier.title()} {('I', 'II', 'III', 'IV')[grade - 1]}"
            return name
        if self._key in {"ratio", "margin"}:
            sent = value_at(profile, "transfer", "uploaded", "total")
            received = value_at(profile, "transfer", "downloaded", "total")
            if type(sent) is not int or type(received) is not int:
                return None
            if self._key == "ratio":
                return sent / received if received > 0 else None
            # C411's minimum ratio is 0.8. Keep negative margin visible.
            return sent * 5 // 4 - received
        return value_at(profile, *self._path)

    @property
    def entity_picture(self):
        if self._key == "profile":
            avatar = self.coordinator.data.get("avatarUrl")
            if isinstance(avatar, str) and avatar:
                url = urljoin("https://c411.org/", avatar)
                parts = urlsplit(url)
                if parts.scheme == "https" and parts.netloc == "c411.org":
                    return url
        return None

    @property
    def extra_state_attributes(self):
        if self._key in {"uploaded", "downloaded", "margin"}:
            return {"bytes": self.native_value}
        if self._key != "profile":
            return None
        profile = self.coordinator.data
        return {
            key: profile[key]
            for key in ("level", "transfer", "freeleech", "download")
            if isinstance(profile.get(key), dict)
        }
