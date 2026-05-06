"""Historical export coordinator for the Aether integration."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
import logging
from time import monotonic
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from aiohttp import ClientError, ClientResponseError, ClientTimeout

from homeassistant.components.recorder import history
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_LAST_EXPORTED_RECORDS,
    ATTR_LAST_RESPONSE_LATENCY,
    ATTR_LAST_UPLOAD_STATUS,
    ATTR_LAST_UPLOAD_TIMESTAMP,
    CONF_API_TOKEN,
    CONF_BACKEND_URL,
    CONF_BATTERY_SENSOR,
    CONF_CONSUMPTION_SENSOR,
    CONF_PV_POWER_SENSOR,
    DOMAIN,
    STATUS_ERROR,
    STATUS_NEVER_UPLOADED,
    STATUS_SUCCESS,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class AetherUploadDiagnostics:
    """Diagnostics describing the most recent Aether upload."""

    last_upload_status: str = STATUS_NEVER_UPLOADED
    last_upload_timestamp: datetime | None = None
    last_response_latency: float | None = None
    last_exported_records: int | None = None

    def as_dict(self) -> dict[str, Any]:
        """Return diagnostics as coordinator data."""
        return {
            ATTR_LAST_UPLOAD_STATUS: self.last_upload_status,
            ATTR_LAST_UPLOAD_TIMESTAMP: self.last_upload_timestamp,
            ATTR_LAST_RESPONSE_LATENCY: self.last_response_latency,
            ATTR_LAST_EXPORTED_RECORDS: self.last_exported_records,
        }


class AetherDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate on-demand Aether historical exports."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.config_entry = entry
        self._diagnostics = AetherUploadDiagnostics()

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=None,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Return the latest export diagnostics."""
        return self._diagnostics.as_dict()

    async def async_export_history(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> None:
        """Export recorder history to the configured backend."""
        start_utc = _as_utc(start_time)
        end_utc = _as_utc(end_time)
        if end_utc <= start_utc:
            raise ValueError("end_time must be after start_time")

        readings = await self.hass.async_add_executor_job(
            self._build_historical_readings,
            start_utc,
            end_utc,
        )
        if not readings:
            self._diagnostics.last_upload_status = STATUS_ERROR
            self._diagnostics.last_upload_timestamp = datetime.now(UTC)
            self._diagnostics.last_response_latency = None
            self._diagnostics.last_exported_records = 0
            self.async_set_updated_data(self._diagnostics.as_dict())
            _LOGGER.warning("Aether historical export produced no readings")
            return

        payload = {
            "source": "home_assistant_history",
            "timezone": str(self.hass.config.time_zone),
            "readings": readings,
        }
        backend_url = _history_endpoint(str(self.config_entry.data[CONF_BACKEND_URL]))
        token = str(self.config_entry.data[CONF_API_TOKEN])

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        session = async_get_clientsession(self.hass)
        started = monotonic()

        try:
            async with session.post(
                backend_url,
                json=payload,
                headers=headers,
                timeout=ClientTimeout(total=20),
            ) as response:
                response.raise_for_status()
        except (asyncio.TimeoutError, ClientError, ClientResponseError) as err:
            self._diagnostics.last_upload_status = STATUS_ERROR
            self._diagnostics.last_upload_timestamp = datetime.now(UTC)
            self._diagnostics.last_response_latency = monotonic() - started
            self._diagnostics.last_exported_records = len(readings)
            self.async_set_updated_data(self._diagnostics.as_dict())
            _LOGGER.warning("Aether historical export failed: %s", err)
            return

        self._diagnostics.last_upload_status = STATUS_SUCCESS
        self._diagnostics.last_upload_timestamp = datetime.now(UTC)
        self._diagnostics.last_response_latency = monotonic() - started
        self._diagnostics.last_exported_records = len(readings)
        self.async_set_updated_data(self._diagnostics.as_dict())

    def _build_historical_readings(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> list[dict[str, Any]]:
        """Build aligned load, generation, and battery rows from recorder history."""
        entity_map = {
            str(self.config_entry.data[CONF_CONSUMPTION_SENSOR]): "load",
            str(self.config_entry.data[CONF_PV_POWER_SENSOR]): "generation",
            str(self.config_entry.data[CONF_BATTERY_SENSOR]): "battery",
        }
        try:
            states_by_entity = history.get_significant_states(
                self.hass,
                start_time,
                end_time,
                list(entity_map),
                significant_changes_only=False,
                minimal_response=False,
                no_attributes=True,
            )
        except TypeError:
            states_by_entity = history.get_significant_states(
                self.hass,
                start_time,
                end_time,
                list(entity_map),
                significant_changes_only=False,
                minimal_response=False,
            )

        events: list[tuple[datetime, str, float]] = []
        for entity_id, states in states_by_entity.items():
            measurement = entity_map.get(entity_id)
            if measurement is None:
                continue
            for state in states:
                value = _state_as_float(state.state, entity_id)
                if value is None:
                    continue
                timestamp = getattr(state, "last_updated", None) or getattr(
                    state, "last_changed", None
                )
                if timestamp is None:
                    continue
                events.append((_as_utc(timestamp), measurement, value))

        events.sort(key=lambda item: item[0])

        current: dict[str, float] = {}
        readings: list[dict[str, Any]] = []
        index = 0
        while index < len(events):
            timestamp = events[index][0]
            while index < len(events) and events[index][0] == timestamp:
                _, measurement, value = events[index]
                current[measurement] = value
                index += 1

            if {"load", "generation", "battery"}.issubset(current):
                readings.append(
                    {
                        "timestamp": _as_local(timestamp).isoformat(),
                        "load": current["load"],
                        "generation": current["generation"],
                        "battery": current["battery"],
                    }
                )

        return readings


def _as_utc(value: datetime) -> datetime:
    """Normalize a datetime to timezone-aware UTC."""
    if value.tzinfo is None:
        value = dt_util.as_local(value)
    return dt_util.as_utc(value)


def _as_local(value: datetime) -> datetime:
    """Normalize a datetime to the Home Assistant local timezone."""
    return dt_util.as_local(_as_utc(value))


def _state_as_float(value: Any, entity_id: str) -> float | None:
    """Return an entity state as a float, skipping unavailable data."""
    if value in {STATE_UNAVAILABLE, STATE_UNKNOWN, ""}:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        _LOGGER.warning(
            "Aether entity %s has non-numeric historical state %r; skipping",
            entity_id,
            value,
        )
        return None


def _history_endpoint(backend_url: str) -> str:
    """Return the history import endpoint for a configured backend URL."""
    parsed = urlsplit(backend_url.strip())
    path = parsed.path.rstrip("/")
    if path.endswith("/api/energy"):
        path = f"{path}/history"
    elif not path.endswith("/api/energy/history"):
        path = f"{path}/api/energy/history"
    return urlunsplit((parsed.scheme, parsed.netloc, path, parsed.query, parsed.fragment))
