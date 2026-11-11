"""Generate Lovelace YAML using the entity registry."""

from pathlib import Path
import re

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry

DOMAIN = "c411"
TEMPLATE = Path(__file__).with_name("mushroom-card.yaml")
CARD_ENTITIES = {
    "utilisateur": "profile",
    "niveau": "level",
    "rang": "rank",
    "zen": "zen",
    "ratio": "ratio",
    "marge_de_telechargement": "margin",
    "envoye": "uploaded",
    "telecharge": "downloaded",
    "freeleech": "freeleech",
    "silverleech": "silverleech",
    "telechargement_autorise": "download_allowed",
}
PLACEHOLDER = re.compile(r"\b(?:binary_)?sensor\.c411_([a-z_]+)\b")


def async_register_dashboard_action(hass: HomeAssistant) -> None:
    """Register the read-only YAML generator."""

    async def generate_card(call: ServiceCall) -> dict[str, str]:
        registry = entity_registry.async_get(hass)
        entries = entity_registry.async_entries_for_device(registry, call.data["device_id"])
        ids = {
            entry.unique_id.partition("_")[2]: entry.entity_id
            for entry in entries
            if entry.platform == DOMAIN and entry.domain in {"sensor", "binary_sensor"} and not entry.disabled
        }
        missing = sorted(set(CARD_ENTITIES.values()) - ids.keys())
        if missing:
            raise HomeAssistantError(f"C411 card sensors missing or disabled: {', '.join(missing)}")
        template = await hass.async_add_executor_job(TEMPLATE.read_text, "utf-8")
        yaml = PLACEHOLDER.sub(lambda match: ids[CARD_ENTITIES[match[1]]], template)
        return {"yaml": yaml}

    hass.services.async_register(
        DOMAIN,
        "generate_card",
        generate_card,
        schema=vol.Schema({vol.Required("device_id"): str}),
        supports_response=SupportsResponse.ONLY,
    )
