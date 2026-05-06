# Aether for Home Assistant

Aether is a Home Assistant custom integration that exports historical energy data from Home Assistant Recorder to the Aether backend.

The integration reads three configured sensor entities:

- Load or consumption
- PV generation
- Battery

It sends aligned historical readings to Aether so they can be used for energy analysis, forecasting, and optimization workflows.

## Requirements

- Home Assistant 2024.1.0 or newer
- Home Assistant Recorder enabled
- Three numeric sensor entities for load, PV generation, and battery data
- An Aether account and API token
- Network access from Home Assistant to the Aether backend

## Installation with HACS

1. Open Home Assistant.
2. Go to **HACS**.
3. Open the three-dot menu and select **Custom repositories**.
4. Add this repository URL:

   ```text
   https://github.com/AdelaBara/aether-home-assistant
   ```

5. Select category **Integration**.
6. Click **Add**.
7. Search for **Aether** in HACS and install it.
8. Restart Home Assistant.

## Manual Installation

Copy the integration folder:

```text
custom_components/aether
```

into your Home Assistant configuration directory:

```text
/config/custom_components/aether
```

After copying, restart Home Assistant.

The final structure should look like this:

```text
/config/custom_components/aether/__init__.py
/config/custom_components/aether/config_flow.py
/config/custom_components/aether/const.py
/config/custom_components/aether/coordinator.py
/config/custom_components/aether/manifest.json
/config/custom_components/aether/sensor.py
/config/custom_components/aether/services.yaml
/config/custom_components/aether/strings.json
/config/custom_components/aether/translations/en.json
```

## Configuration

1. In Home Assistant, go to **Settings > Devices & services**.
2. Click **Add integration**.
3. Search for **Aether**.
4. Enter the required fields:

| Field | Description |
| --- | --- |
| Backend URL | Aether backend URL. You can enter the base backend URL or the full history endpoint. |
| API token | Bearer token generated from your Aether account. |
| PV power sensor | Home Assistant sensor containing PV generation values. |
| Load/consumption sensor | Home Assistant sensor containing load or consumption values. |
| Battery sensor | Home Assistant sensor containing battery values. |

Default Aether history endpoint:

```text
https://ase.open4cec.eu/aetherha/api/energy/history
```

The integration also accepts a backend URL ending in `/api/energy` or a base URL. It will resolve it to the history endpoint automatically.

## API Token

Generate or copy your token from the Aether application:

1. Log in to Aether.
2. Open the Home Assistant integration section.
3. Generate or copy the API token.
4. Paste the token into the Aether integration setup form in Home Assistant.

The token is used as a bearer token when Home Assistant uploads historical readings.

## Export Historical Data

Aether exports data on demand using a Home Assistant action.

In Home Assistant:

1. Go to **Developer Tools**.
2. Open the **Actions** tab.
3. Select **Aether: Export history**.
4. Provide a start and optional end time.
5. Click **Perform action**.

YAML example:

```yaml
action: aether.export_history
data:
  start_time: "2026-04-01 00:00:00"
  end_time: "2026-05-01 00:00:00"
```

If `end_time` is omitted, Aether exports 24 hours starting from `start_time`.

## Diagnostic Sensors

After setup, the integration creates diagnostic sensors for the latest export:

- Last upload status
- Last upload timestamp
- Last response latency
- Last exported records

These sensors help confirm whether the export completed successfully and how many records were sent.

## Timestamp Behavior

Home Assistant stores Recorder history internally in UTC. Aether converts timestamps back to the Home Assistant local timezone before sending them to the backend.

For example, if Home Assistant is configured for `Europe/Bucharest`, this local time:

```text
2026-04-01T12:00:00+03:00
```

is sent as a local timestamp for Aether processing.

## Troubleshooting

### Aether does not appear in Add Integration

Restart Home Assistant after installing the integration. If it still does not appear, check that the files are located under:

```text
/config/custom_components/aether
```

### Export returns zero records

Check that:

- Home Assistant Recorder is enabled.
- The selected sensors have historical states in the requested time window.
- The selected sensor states are numeric.
- The start and end times cover a period where all three sensors have data.

### Upload fails

Check that:

- The backend URL is reachable from Home Assistant.
- The API token is valid.
- Home Assistant has internet access.
- The Aether backend is available.

Home Assistant logs may contain additional details under the `custom_components.aether` logger.

## Support

For documentation, visit:

```text
https://ase.open4cec.eu/aether/
```

For issues, use the repository issue tracker:

```text
https://github.com/AdelaBara/aether-home-assistant/issues
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
