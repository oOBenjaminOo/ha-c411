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
DETAIL_ENTITIES = {
    "zen_gagnes": "zen_earned",
    "zen_depenses": "zen_spent",
    "envoye_reel": "uploaded_actual",
    "telecharge_reel": "downloaded_actual",
    "equipe": "team",
    "quetes_terminees": "quests_completed",
    "derniere_synchronisation_reussie": "last_sync",
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
            if entry.platform == DOMAIN and entry.domain in {"sensor", "binary_sensor"}
        }
        enabled = {entry.entity_id for entry in entries if not entry.disabled}
        missing = sorted(key for key in CARD_ENTITIES.values() if ids.get(key) not in enabled)
        if missing:
            raise HomeAssistantError(f"C411 card sensors missing or disabled: {', '.join(missing)}")
        template = await hass.async_add_executor_job(TEMPLATE.read_text, "utf-8")
        card_entities = CARD_ENTITIES | DETAIL_ENTITIES
        yaml = PLACEHOLDER.sub(
            lambda match: ids.get(card_entities[match[1]], match[0]), template
        )
        details = await hass.async_add_executor_job(
            TEMPLATE.with_name("profile-details-card.yaml").read_text, "utf-8"
        )
        details_yaml = PLACEHOLDER.sub(
            lambda match: ids.get(DETAIL_ENTITIES[match[1]], match[0]), details
        )
        return {"yaml": yaml, "details_yaml": details_yaml}

    hass.services.async_register(
        DOMAIN,
        "generate_card",
        generate_card,
        schema=vol.Schema({vol.Required("device_id"): str}),
        supports_response=SupportsResponse.ONLY,
    )
