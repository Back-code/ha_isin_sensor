"""Config Flow for ISIN Sensor integration."""
import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import logging
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def is_valid_isin(isin):
    """Validate the ISIN format by checking the API asynchronously."""
    url = f"https://component-api.wertpapiere.ing.de/api/v1/components/instrumentheader/{isin}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 404:
                    return False
                response.raise_for_status()
                return True
    except aiohttp.ClientError as e:
        _LOGGER.error("Error validating ISIN: %s", e)
        return False


class ISINSensorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the main config flow for ISIN Sensor."""

    VERSION = 1

    def __init__(self):
        """Initialize the flow."""
        self.hub_name = None
        self.sensors = []

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
            return await self.async_step_add_sensor()

        # Display hub name input form
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            description_placeholders={
                "hub_name": description
            }
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
            # Check for duplicate ISINs
            existing_isins = [sensor["isin"] for sensor in self.sensors]
            if user_input["isin"] in existing_isins:
                return self.async_show_form(
                    step_id="add_sensor",
                    data_schema=data_schema,
                    description_placeholders={
                        "isin": description,
                        "name": "Name des Sensors",
                        "add_more_sensors": "Weiteren Sensor hinzufügen"
                    },
                    errors={"isin": "isin_already_exists"},
                )

            # Validate ISIN
            if not await is_valid_isin(user_input["isin"]):
                return self.async_show_form(
                    step_id="add_sensor",
                    data_schema=data_schema,
                    description_placeholders={
                        "isin": description,
                        "name": "Name des Sensors",
                        "add_more_sensors": "Weiteren Sensor hinzufügen"
                    },
                    errors={"isin": "invalid_isin"},
                )

            # Add sensor to the list
            self.sensors.append({"isin": user_input["isin"], "name": user_input["name"]})

            # Check if the user wants to add more sensors
            if user_input.get("add_more_sensors"):
                # Restart the same step to add another sensor
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
            description_placeholders={
                "isin": description,
                "name": "Name des Sensors",
                "add_more_sensors": "Weiteren Sensor hinzufügen"
            }
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow handler."""
        return ISINSensorOptionsFlow(config_entry)


class ISINSensorOptionsFlow(config_entries.OptionsFlow, domain=DOMAIN):
    """Handle options flow for ISIN Sensor."""

    def __init__(self, config_entry):
        """Initialize the options flow."""
        self.config_entry_id = config_entry.entry_id
        self.sensors = config_entry.data.get("sensors", [])

    async def async_step_init(self, user_input=None):
        """Einstiegspunkt für den Optionsfluss."""
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required("isin"): str,
                    vol.Required("name"): str,
                    vol.Optional("add_more_sensors", default=False): bool,
                }
            ),
            description_placeholders={
                "isin": "ISIN (z. B. DE000BASF111)",
                "name": "Name des Sensors",
                "add_more_sensors": "Weitere Sensoren hinzufügen"
            }
        )

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
            # Check for duplicate ISINs
            existing_isins = [sensor["isin"] for sensor in self.sensors]
            if user_input["isin"] in existing_isins:
                return self.async_show_form(
                    step_id="add_sensor",
                    data_schema=data_schema,
                    description_placeholders={
                        "isin": description,
                        "name": "Name des Sensors",
                        "add_more_sensors": "Weiteren Sensor hinzufügen"
                    },
                    errors={"isin": "isin_already_exists"},
                )

            # Validate ISIN
            if not await is_valid_isin(user_input["isin"]):
                return self.async_show_form(
                    step_id="add_sensor",
                    data_schema=data_schema,
                    description_placeholders={
                        "isin": description,
                        "name": "Name des Sensors",
                        "add_more_sensors": "Weiteren Sensor hinzufügen"
                    },
                    errors={"isin": "invalid_isin"},
                )

            # Add sensor to the list
            self.sensors.append({"isin": user_input["isin"], "name": user_input["name"]})

            # Check if the user wants to add more sensors
            if user_input.get("add_more_sensors"):
                # Restart the same step to add another sensor
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
            description_placeholders={
                "isin": description,
                "name": "Name des Sensors",
                "add_more_sensors": "Weiteren Sensor hinzufügen"
            }
        )


class ISINSensor:
    def __init__(self, isin, name):
        self.isin = isin
        self.name = name

    async def is_valid_isin(self, isin):
        """Validate the ISIN format by checking the API asynchronously."""
        url = f"https://component-api.wertpapiere.ing.de/api/v1/components/instrumentheader/{isin}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 404:
                        return False
                    response.raise_for_status()
                    return True
        except aiohttp.ClientError as e:
            _LOGGER.error("Error validating ISIN: %s", e)
            return False


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up ISIN sensors from a config entry."""
    sensors = config_entry.data.get("sensors", [])
    entities = []

    for sensor in sensors:
        isin_sensor = ISINSensor(sensor["isin"], sensor["name"])
        if await isin_sensor.is_valid_isin(sensor["isin"]):  # Await the async method
            entities.append(isin_sensor)

    async_add_entities(entities)
