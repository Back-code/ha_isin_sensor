"""Config Flow for ISIN Sensor integration."""
import aiohttp
import asyncio
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er
import logging
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def is_valid_isin(isin):
    """Validate the ISIN format by checking the API asynchronously."""
    if len(isin) != 12:  # Basic ISIN format validation
        return False

    url = f"https://component-api.wertpapiere.ing.de/api/v1/components/instrumentheader/{isin}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 404:
                    return False
                response.raise_for_status()
                return True
    except asyncio.TimeoutError:
        _LOGGER.error("Timeout while validating ISIN: %s", isin)
        return False
    except aiohttp.ClientError as e:
        _LOGGER.error("Error validating ISIN: %s", e)
        return False


class ISINSensorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for ISIN Sensor."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self.hub_name = None
        self.sensors = []

    async def async_step_user(self, user_input=None):
        """Handle the initial step to set up a hub."""
        data_schema = vol.Schema(
            {
                vol.Required("hub_name"): str,
            }
        )

        if user_input is not None:
            # Check if the hub already exists
            if self._hub_exists(user_input["hub_name"]):
                return self.async_abort(reason="hub_already_exists")

            self.hub_name = user_input["hub_name"]
            self.sensors = []  # Initialize sensors as an empty list
            return await self.async_step_add_sensor()

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors={}
        )

    async def async_step_add_sensor(self, user_input=None):
        """Add new sensors to the hub."""
        data_schema = vol.Schema(
            {
                vol.Required("isin"): str,
                vol.Required("name"): str,
                vol.Optional("add_more_sensors", default=False): bool,
            }
        )

        if user_input is not None:
            # Validate ISIN
            if not await is_valid_isin(user_input["isin"]):
                return self.async_show_form(
                    step_id="add_sensor",
                    data_schema=data_schema,
                    errors={"isin": "invalid_isin"},
                )

            # Check for duplicate ISINs
            if self._isin_exists(user_input["isin"]):
                return self.async_show_form(
                    step_id="add_sensor",
                    data_schema=data_schema,
                    errors={"isin": "isin_already_exists"},
                )

            # Add sensor to the list
            self.sensors.append({"isin": user_input["isin"], "name": user_input["name"]})

            # Check if the user wants to add more sensors
            if user_input.get("add_more_sensors"):
                return await self.async_step_add_sensor()

            # Finalize the entry creation
            return self.async_create_entry(
                title=self.hub_name,
                data={"hub_name": self.hub_name, "sensors": self.sensors},
            )

        return self.async_show_form(
            step_id="add_sensor",
            data_schema=data_schema,
            errors={}
        )

    def _isin_exists(self, isin):
        """Check if an ISIN already exists in the current sensors."""
        return any(sensor["isin"] == isin for sensor in self.sensors)

    def _hub_exists(self, hub_name):
        """Check if a hub with the same name already exists."""
        existing_entries = self._async_current_entries()
        return any(entry.title == hub_name for entry in existing_entries)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow handler."""
        return ISINSensorOptionsFlowHandler(config_entry)


class ISINSensorOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle the options flow for ISIN Sensor."""

    def __init__(self, config_entry):
        """Initialize the options flow."""
        self.config_entry_id = config_entry.entry_id  # Speichere nur die Entry-ID

    async def async_step_init(self, user_input=None):
        """Manage the options for the integration."""
        return await self.async_step_edit_sensor()

    async def async_step_edit_sensor(self, user_input=None):
        """Edit the sensors in the hub."""
        config_entry = self.hass.config_entries.async_get_entry(self.config_entry_id)
        sensors = config_entry.data.get("sensors", [])
        step_id="edit_sensor",
        data_schema = vol.Schema(
            {
                vol.Required("isin"): str,
                vol.Required("name"): str,
                vol.Optional("add_more_sensors", default=False): bool,
            }
        )

        if user_input is not None:
            # Validate ISIN
            if not await is_valid_isin(user_input["isin"]):
                return self.async_show_form(
                    step_id="edit_sensor",
                    data_schema=data_schema,
                    errors={"isin": "invalid_isin"},
                )

            # Check for duplicate ISINs
            if any(sensor["isin"] == user_input["isin"] for sensor in sensors):
                return self.async_show_form(
                    step_id="edit_sensor",
                    data_schema=data_schema,
                    errors={"isin": "isin_already_exists"},
                )

            # Add or update the sensor
            sensors.append({"isin": user_input["isin"], "name": user_input["name"]})

            # Check if the user wants to add more sensors
            if user_input.get("add_more_sensors"):
                return await self.async_step_edit_sensor()
            
            # Logging der aktualisierten Daten
            _LOGGER.debug("Updated sensors: %s", sensors)

            # Speichere die aktualisierten Sensoren in den Config-Entry-Daten und Optionen
            self.hass.config_entries.async_update_entry(
                config_entry,
                data={**config_entry.data, "sensors": sensors},
                options={**config_entry.options, "sensors": sensors},
            )
            _LOGGER.debug("Config entry updated with sensors: %s", sensors)

            # Reload the config entry to apply changes
            await self.hass.config_entries.async_reload(config_entry.entry_id)

            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="edit_sensor",
            data_schema=data_schema,
            errors={}
        )