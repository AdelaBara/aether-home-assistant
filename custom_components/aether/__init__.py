"""The Aether integration."""

from __future__ import annotations

import logging
from datetime import timedelta

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType

from .const import ATTR_END_TIME, ATTR_START_TIME, DOMAIN, SERVICE_EXPORT_HISTORY
from .coordinator import AetherDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

SERVICE_EXPORT_HISTORY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_START_TIME): cv.datetime,
        vol.Optional(ATTR_END_TIME): cv.datetime,
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Aether services."""
    hass.data.setdefault(DOMAIN, {})

    async def async_export_history(call: ServiceCall) -> None:
        """Export recorder history for all configured Aether entries."""
        coordinators: list[AetherDataUpdateCoordinator] = [
            coordinator
            for coordinator in hass.data.get(DOMAIN, {}).values()
            if isinstance(coordinator, AetherDataUpdateCoordinator)
        ]

        if not coordinators:
            _LOGGER.warning("Aether export_history service called with no loaded entries")
            return

        start_time = call.data[ATTR_START_TIME]
        end_time = call.data.get(ATTR_END_TIME) or start_time + timedelta(days=1)

        for coordinator in coordinators:
            await coordinator.async_export_history(start_time, end_time)

    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPORT_HISTORY,
        async_export_history,
        schema=SERVICE_EXPORT_HISTORY_SCHEMA,
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Aether from a config entry."""
    coordinator = AetherDataUpdateCoordinator(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload an Aether config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Clean up after an Aether config entry is removed."""
    if not hass.config_entries.async_entries(DOMAIN):
        hass.services.async_remove(DOMAIN, SERVICE_EXPORT_HISTORY)
