"""Expose the C411 dashboard installer to the Home Assistant frontend."""

from pathlib import Path

import voluptuous as vol
import yaml

from homeassistant.components import frontend, websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry


async def async_register_dashboard_installer(hass):
    """Load the device-page button and its authenticated card endpoint."""
    websocket_api.async_register_command(hass, async_dashboard_card)
    await hass.http.async_register_static_paths([
        StaticPathConfig(
            "/c411_dashboard_installer.js",
            str(Path(__file__).with_name("dashboard_installer.js")),
            False,
        )
    ])
    frontend.add_extra_js_url(hass, "/c411_dashboard_installer.js")


@websocket_api.websocket_command({
    vol.Required("type"): "c411/dashboard_card",
    vol.Required("device_id"): str,
    vol.Optional("check_only", default=False): bool,
})
@websocket_api.require_admin
@websocket_api.async_response
async def async_dashboard_card(hass, connection, msg):
    """Generate a card using the existing C411 action and real entity IDs."""
    device = device_registry.async_get(hass).async_get(msg["device_id"])
    if not device or not any(domain == "c411" for domain, _ in device.identifiers):
        connection.send_error(msg["id"], "not_found", "C411 device not found")
        return
    if msg["check_only"]:
        connection.send_result(msg["id"], True)
        return
    try:
        generated = await hass.services.async_call(
            "c411",
            "generate_card",
            {"device_id": device.id},
            blocking=True,
            return_response=True,
            context=connection.context(msg),
        )
        card = yaml.safe_load(generated["yaml"])
    except (HomeAssistantError, yaml.YAMLError) as err:
        connection.send_error(msg["id"], "card_unavailable", str(err))
        return
    connection.send_result(msg["id"], card)
