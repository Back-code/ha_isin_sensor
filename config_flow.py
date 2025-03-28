"""Config Flow for ISIN Sensor integration."""
import aiohttp
import asyncio
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
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
            existing_entries = [
                entry for entry in self._async_current_entries() if entry.data.get("hub_name") == user_input["hub_name"]
            ]
            if existing_entries:
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
            existing_isins = [sensor["isin"] for sensor in self.sensors]
            if user_input["isin"] in existing_isins:
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