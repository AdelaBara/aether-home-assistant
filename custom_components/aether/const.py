"""Constants for the Aether integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "aether"
NAME: Final = "Aether"
VERSION: Final = "1.0.0"

PLATFORMS: Final = ["sensor"]

CONF_BACKEND_URL: Final = "backend_url"
CONF_API_TOKEN: Final = "api_token"
CONF_PV_POWER_SENSOR: Final = "pv_power_sensor"
CONF_CONSUMPTION_SENSOR: Final = "consumption_sensor"
CONF_BATTERY_SENSOR: Final = "battery_sensor"

SERVICE_EXPORT_HISTORY: Final = "export_history"

ATTR_START_TIME: Final = "start_time"
ATTR_END_TIME: Final = "end_time"

ATTR_LAST_UPLOAD_STATUS: Final = "last_upload_status"
ATTR_LAST_UPLOAD_TIMESTAMP: Final = "last_upload_timestamp"
ATTR_LAST_RESPONSE_LATENCY: Final = "last_response_latency"
ATTR_LAST_EXPORTED_RECORDS: Final = "last_exported_records"

STATUS_NEVER_UPLOADED: Final = "never_uploaded"
STATUS_SUCCESS: Final = "success"
STATUS_ERROR: Final = "error"
