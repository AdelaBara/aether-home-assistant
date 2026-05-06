"""Diagnostic sensors for the Aether integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_LAST_EXPORTED_RECORDS,
    ATTR_LAST_RESPONSE_LATENCY,
    ATTR_LAST_UPLOAD_STATUS,
    ATTR_LAST_UPLOAD_TIMESTAMP,
    DOMAIN,
    NAME,
)
from .coordinator import AetherDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class AetherSensorEntityDescription(SensorEntityDescription):
    """Description for an Aether diagnostic sensor."""

    value_fn: Callable[[dict[str, Any]], str | datetime | float | None]


SENSOR_DESCRIPTIONS: tuple[AetherSensorEntityDescription, ...] = (
    AetherSensorEntityDescription(
        key=ATTR_LAST_UPLOAD_STATUS,
        translation_key=ATTR_LAST_UPLOAD_STATUS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get(ATTR_LAST_UPLOAD_STATUS),
    ),
    AetherSensorEntityDescription(
        key=ATTR_LAST_UPLOAD_TIMESTAMP,
        translation_key=ATTR_LAST_UPLOAD_TIMESTAMP,
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get(ATTR_LAST_UPLOAD_TIMESTAMP),
    ),
    AetherSensorEntityDescription(
        key=ATTR_LAST_RESPONSE_LATENCY,
        translation_key=ATTR_LAST_RESPONSE_LATENCY,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get(ATTR_LAST_RESPONSE_LATENCY),
    ),
    AetherSensorEntityDescription(
        key=ATTR_LAST_EXPORTED_RECORDS,
        translation_key=ATTR_LAST_EXPORTED_RECORDS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get(ATTR_LAST_EXPORTED_RECORDS),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Aether diagnostic sensors."""
    coordinator: AetherDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        AetherSensor(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    )


class AetherSensor(CoordinatorEntity[AetherDataUpdateCoordinator], SensorEntity):
    """Aether diagnostic sensor."""

    entity_description: AetherSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AetherDataUpdateCoordinator,
        entry: ConfigEntry,
        description: AetherSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": NAME,
            "manufacturer": "Aether",
            "model": "Energy history exporter",
        }

    @property
    def native_value(self) -> str | datetime | float | None:
        """Return the native value."""
        return self.entity_description.value_fn(self.coordinator.data or {})
