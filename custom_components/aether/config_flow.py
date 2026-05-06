"""Config flow for the Aether integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    CONF_API_TOKEN,
    CONF_BACKEND_URL,
    CONF_BATTERY_SENSOR,
    CONF_CONSUMPTION_SENSOR,
    CONF_PV_POWER_SENSOR,
    DOMAIN,
    NAME,
)


class AetherConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle an Aether config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            backend_url = user_input[CONF_BACKEND_URL].strip()
            await self.async_set_unique_id(backend_url)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=NAME,
                data={
                    CONF_BACKEND_URL: backend_url,
                    CONF_API_TOKEN: user_input[CONF_API_TOKEN],
                    CONF_PV_POWER_SENSOR: user_input[CONF_PV_POWER_SENSOR],
                    CONF_CONSUMPTION_SENSOR: user_input[CONF_CONSUMPTION_SENSOR],
                    CONF_BATTERY_SENSOR: user_input[CONF_BATTERY_SENSOR],
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=_user_schema(),
            errors=errors,
        )


def _user_schema() -> vol.Schema:
    """Return the user step schema."""
    sensor_selector = selector.EntitySelector(
        selector.EntitySelectorConfig(domain="sensor")
    )

    return vol.Schema(
        {
            vol.Required(CONF_BACKEND_URL): str,
            vol.Required(CONF_API_TOKEN): str,
            vol.Required(CONF_PV_POWER_SENSOR): sensor_selector,
            vol.Required(CONF_CONSUMPTION_SENSOR): sensor_selector,
            vol.Required(CONF_BATTERY_SENSOR): sensor_selector,
        }
    )
