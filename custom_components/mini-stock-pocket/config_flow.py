"""Config Flow for ISIN Sensor integration."""
import aiohttp
import asyncio
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import config_validation as cv  # Import für Float-Validierung
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
                vol.Optional("quantity", default=0.0): cv.positive_float,  # Ändere zu Float mit Validierung
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
            self.sensors.append({
                "isin": user_input["isin"],
                "name": user_input["name"],
                "quantity": round(user_input["quantity"], 2),  # Rundung auf 2 Nachkommastellen
            })

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
        self.selected_isin = None

    async def async_step_init(self, user_input=None):
        """Initial step to choose an action."""
        if user_input is not None:
            if user_input["action"] == "add_stock":
                return await self.async_step_add_sensor()
            elif user_input["action"] == "edit_quantity":
                return await self.async_step_edit_quantity()
            elif user_input["action"] == "delete_stock":
                return await self.async_step_delete_sensor()

        data_schema = vol.Schema(
            {
                vol.Required("action"): vol.In(
                    {
                        "add_stock": "Neue Aktie hinzufügen",
                        "edit_quantity": "Aktien Anzahl ändern",
                        "delete_stock": "Aktie löschen",
                    }
                )
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema)

    async def async_step_add_sensor(self, user_input=None):
        """Add a new stock."""
        config_entry = self.hass.config_entries.async_get_entry(self.config_entry_id)
        sensors = config_entry.data.get("sensors", [])

        data_schema = vol.Schema(
            {
                vol.Required("isin"): str,
                vol.Required("name"): str,
                vol.Optional("quantity", default=0.0): cv.positive_float,  # Ändere zu Float mit Validierung
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
            if any(sensor["isin"] == user_input["isin"] for sensor in sensors):
                return self.async_show_form(
                    step_id="add_sensor",
                    data_schema=data_schema,
                    errors={"isin": "isin_already_exists"},
                )

            # Add sensor to the list
            sensors.append({
                "isin": user_input["isin"],
                "name": user_input["name"],
                "quantity": round(user_input["quantity"], 2),  # Rundung auf 2 Nachkommastellen
            })

            # Update the config entry
            self.hass.config_entries.async_update_entry(
                config_entry,
                data={**config_entry.data, "sensors": sensors},
                options={**config_entry.options, "sensors": sensors},
            )

            # Check if the user wants to add more sensors
            if user_input.get("add_more_sensors"):
                return await self.async_step_add_sensor()

            # Reload the config entry to apply changes
            await self.hass.config_entries.async_reload(config_entry.entry_id)
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="add_sensor",
            data_schema=data_schema,
            errors={}
        )

    async def async_step_edit_quantity(self, user_input=None):
        """Step 1: Select a stock to edit its quantity."""
        config_entry = self.hass.config_entries.async_get_entry(self.config_entry_id)
        sensors = config_entry.data.get("sensors", [])
        
        # Sort the sensor choices alphabetically by name
        sensor_choices = {sensor["isin"]: sensor["name"] for sensor in sorted(sensors, key=lambda x: x["name"].lower())}

        if user_input is not None:
            # Store the selected ISIN and proceed to the next step
            self.selected_isin = user_input["isin"]
            return await self.async_step_edit_quantity_value()

        # Show the form to select a stock
        data_schema = vol.Schema(
            {
                vol.Required("isin"): vol.In(sensor_choices),
            }
        )
        return self.async_show_form(step_id="edit_quantity", data_schema=data_schema)

    async def async_step_edit_quantity_value(self, user_input=None):
        """Step 2: Edit the quantity of the selected stock."""
        config_entry = self.hass.config_entries.async_get_entry(self.config_entry_id)
        sensors = config_entry.data.get("sensors", [])

        # Find the selected sensor
        selected_sensor = next(
            (sensor for sensor in sensors if sensor["isin"] == self.selected_isin),
            None
        )

        if not selected_sensor:
            # If the sensor is not found, return to the previous step
            return await self.async_step_edit_quantity()

        if user_input is not None:
            # Update the quantity for the selected ISIN
            selected_sensor["quantity"] = round(user_input["quantity"], 2)  # Rundung auf 2 Nachkommastellen

            # Update the config entry
            self.hass.config_entries.async_update_entry(
                config_entry,
                data={**config_entry.data, "sensors": sensors},
            )
            await self.hass.config_entries.async_reload(config_entry.entry_id)
            return self.async_create_entry(title="", data={})

        # Show the form to edit the quantity
        data_schema = vol.Schema(
            {
                vol.Required("quantity", default=selected_sensor["quantity"]): cv.positive_float,  # Float-Validierung
            }
        )
        return self.async_show_form(
            step_id="edit_quantity_value",
            data_schema=data_schema,
            description_placeholders={
                "selected_stock": f"{selected_sensor['name']} (ISIN: {selected_sensor['isin']})"
            }
        )

    async def async_step_delete_sensor(self, user_input=None):
        """Delete an existing stock."""
        config_entry = self.hass.config_entries.async_get_entry(self.config_entry_id)
        sensors = config_entry.data.get("sensors", [])

        # Sort the sensor choices alphabetically by name
        sensor_choices = {sensor["isin"]: sensor["name"] for sensor in sorted(sensors, key=lambda x: x["name"].lower())}

        if user_input is not None:
            selected_sensor = next(
                (sensor for sensor in sensors if sensor["isin"] == user_input["isin"]),
                None
            )
            if selected_sensor:
                _LOGGER.debug("Selected sensor for deletion: %s", selected_sensor)

                # Remove the sensor from the sensors list
                sensors = [sensor for sensor in sensors if sensor["isin"] != user_input["isin"]]

                # Update the config entry
                self.hass.config_entries.async_update_entry(
                    config_entry,
                    data={**config_entry.data, "sensors": sensors},
                    options={**config_entry.options, "sensors": sensors},
                )
                _LOGGER.debug("Updated config entry: %s", config_entry.data)

                # Remove the entity from the Entity Registry using unique_id
                entity_registry = er.async_get(self.hass)
                unique_id = selected_sensor["isin"].upper()  # ISIN in Großbuchstaben als unique_id
                _LOGGER.debug("Generated unique_id for deletion: %s", unique_id)

                # Find the entity by unique_id
                entity_entry = next(
                    (entry for entry in entity_registry.entities.values() if entry.unique_id == unique_id),
                    None
                )
                if entity_entry:
                    _LOGGER.debug("Entity found in registry with unique_id: %s", unique_id)

                    # Remove the entity directly from the Entity Registry
                    entity_registry.async_remove(entity_entry.entity_id)
                    _LOGGER.debug("Entity removed from registry: %s", entity_entry.entity_id)
                else:
                    _LOGGER.warning("Entity not found in registry with unique_id: %s", unique_id)

                # Reload the config entry to apply changes
                await self.hass.config_entries.async_reload(config_entry.entry_id)
                _LOGGER.debug("Config entry reloaded: %s", config_entry.entry_id)

                return self.async_create_entry(title="", data={})

            # If the selected sensor is not found, show an error
            _LOGGER.warning("Selected sensor not found: %s", user_input["isin"])
            return self.async_show_form(
                step_id="delete_sensor",
                data_schema=vol.Schema(
                    {
                        vol.Required("isin"): vol.In(sensor_choices),
                    }
                ),
                errors={"base": "sensor_not_found"}
            )

        # Show the form to select a stock
        data_schema = vol.Schema(
            {
                vol.Required("isin"): vol.In(sensor_choices),
            }
        )

        return self.async_show_form(
            step_id="delete_sensor",
            data_schema=data_schema,
            description_placeholders={
                "selected_stock": "Wählen Sie eine Aktie aus der Liste aus."
            }
        )