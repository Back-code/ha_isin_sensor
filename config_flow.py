"""Config Flow and Options Flow for ISIN Sensor integration."""
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


class ISINSensorFlowBase:
    """Base class for shared logic between ConfigFlow and OptionsFlow."""

    def __init__(self):
        """Initialize the flow."""
        self.sensors = []

    async def _add_sensor(self, user_input):
        """Handle adding a new sensor."""
        # Check for duplicate ISINs
        existing_isins = [sensor["isin"] for sensor in self.sensors]
        if user_input["isin"] in existing_isins:
            return {"isin": "isin_already_exists"}

        # Validate ISIN
        if not await is_valid_isin(user_input["isin"]):
            return {"isin": "invalid_isin"}

        # Add sensor to the list
        self.sensors.append({"isin": user_input["isin"], "name": user_input["name"]})
        return None


class ISINSensorConfigFlow(config_entries.ConfigFlow, ISINSensorFlowBase, domain=DOMAIN):
    """Handle the main config flow for ISIN Sensor."""

    VERSION = 1

    def __init__(self):
        """Initialize the flow."""
        super().__init__()
        self.hub_name = None

    async def async_step_user(self, user_input=None):
        """Handle the initial step to set up a hub."""
        data_schema = vol.Schema(
            {
                vol.Required("hub_name"): str,
            }
        )
        description = "Bitte geben Sie den Namen des Hubs ein."

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

        # Display hub name input form
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            description_placeholders={"hub_name": description},
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
        description = "Fügen Sie einen neuen Sensor hinzu."

        if user_input is not None:
            errors = await self._add_sensor(user_input)
            if errors:
                return self.async_show_form(
                    step_id="add_sensor",
                    data_schema=data_schema,
                    description_placeholders={"isin": description},
                    errors=errors,
                )

            # Check if the user wants to add more sensors
            if user_input.get("add_more_sensors"):
                return await self.async_step_add_sensor()

            # Finalize the entry creation
            return self.async_create_entry(
                title=self.hub_name,
                data={"hub_name": self.hub_name, "sensors": self.sensors},
            )

        # Display form to add sensors
        return self.async_show_form(
            step_id="add_sensor",
            data_schema=data_schema,
            description_placeholders={"isin": description},
            errors={}
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow handler."""
        return ISINSensorOptionsFlow(config_entry)


class ISINSensorOptionsFlow(config_entries.OptionsFlow, ISINSensorFlowBase):
    """Handle options flow for ISIN Sensor."""

    def __init__(self, config_entry):
        """Initialize the options flow."""
        super().__init__()
        self.config_entry = config_entry
        self.sensors = config_entry.data.get("sensors", [])

    async def async_step_init(self, user_input=None):
        """Initial step for the options flow."""
        return await self.async_step_add_sensor()

    async def async_step_add_sensor(self, user_input=None):
        """Add new sensors to the existing hub."""
        data_schema = vol.Schema(
            {
                vol.Required("isin"): str,
                vol.Required("name"): str,
                vol.Optional("add_more_sensors", default=False): bool,
            }
        )
        description = "Fügen Sie einen neuen Sensor hinzu."

        if user_input is not None:
            # Überprüfe auf doppelte ISINs
            errors = await self._add_sensor(user_input)
            if errors:
                return self.async_show_form(
                    step_id="add_sensor",
                    data_schema=data_schema,
                    description_placeholders={"isin": description},
                    errors=errors,
                )

            # Aktualisiere die config_entry-Daten
            updated_data = {
                "hub_name": self.config_entry.data["hub_name"],
                "sensors": self.sensors,  # Aktualisierte Sensorliste
            }
            self.hass.config_entries.async_update_entry(self.config_entry, data=updated_data)

            # Überprüfe, ob der Benutzer weitere Sensoren hinzufügen möchte
            if user_input.get("add_more_sensors"):
                return await self.async_step_add_sensor()

            # Beende den Optionsflow
            return self.async_create_entry(title="", data={})

        # Zeige das Formular zum Hinzufügen von Sensoren an
        return self.async_show_form(
            step_id="add_sensor",
            data_schema=data_schema,
            description_placeholders={"isin": description},
            errors={}
        )
