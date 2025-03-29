"""ISIN Sensor Integration."""
import aiohttp
import asyncio
import logging
from homeassistant.components.sensor import SensorEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up ISIN Sensor from a config entry."""
    hub_name = config_entry.data["hub_name"]
    sensors = config_entry.data.get("sensors", [])

    if not sensors:
        _LOGGER.warning("No sensors found for hub: %s", hub_name)
        return

    _LOGGER.debug("Setting up sensors for hub: %s with sensors: %s", hub_name, sensors)

    entities = []
    for sensor in sensors:
        if "isin" not in sensor or "name" not in sensor:
            _LOGGER.error("Invalid sensor configuration: %s", sensor)
            continue
        _LOGGER.debug("Registering sensor: %s with ISIN: %s for hub: %s", sensor["name"], sensor["isin"], hub_name)
        entities.append(ISINSensor(sensor["isin"], sensor["name"], hub_name))

    if entities:
        async_add_entities(entities, update_before_add=True)
    else:
        _LOGGER.warning("No valid sensors to add for hub: %s", hub_name)

class ISINSensor(SensorEntity):
    """Representation of an ISIN Sensor."""

    def __init__(self, isin, name, hub_name):
        """Initialize the sensor."""
        self._isin = isin
        self._name = name
        self._hub_name = hub_name  # Verknüpfe den Sensor mit dem Hub
        self._state = None
        self._attributes = {}

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._hub_name} - {self._name}"  # Sensorname enthält den Hub-Namen

    @property
    def unique_id(self):
        """Return the unique ID of the sensor."""
        return f"{self._hub_name}_{self._isin}"  # Eindeutige ID enthält den Hub-Namen

    @property
    def state(self):
        """Return the current price as the state."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._attributes.get("currency")

    @property
    def extra_state_attributes(self):
        """Return the sensor attributes."""
        return self._attributes

    @property
    def should_poll(self):
        """Return True to enable polling."""
        return True

    async def async_update(self):
        """Fetch data from the API asynchronously."""
        url = f"https://component-api.wertpapiere.ing.de/api/v1/components/instrumentheader/{self._isin}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status != 200:
                        _LOGGER.warning("Non-200 response for ISIN %s: %s", self._isin, response.status)
                        return

                    data = await response.json()
                    if not data or "price" not in data:
                        _LOGGER.warning("Invalid or empty response for ISIN %s", self._isin)
                        return

                    # Update state and attributes
                    self._state = data.get("price")
                    self._attributes = {
                        "name": data.get("name"),
                        "close": data.get("close"),
                        "bid": data.get("bid"),
                        "bidDate": data.get("bidDate"),
                        "ask": data.get("ask"),
                        "askDate": data.get("askDate"),
                        "wkn": data.get("wkn"),
                        "isin": data.get("isin"),
                        "internalIsin": data.get("internalIsin"),
                        "stockMarket": data.get("stockMarket"),
                        "priceChangeDate": data.get("priceChangeDate"),
                        "currency": data.get("currency"),
                        "currencySign": data.get("currencySign"),
                        "changePercent": data.get("changePercent"),
                        "changeAbsolute": data.get("changeAbsolute"),
                    }
                    _LOGGER.debug("Updated sensor %s with data: %s", self._isin, data)

        except aiohttp.ClientError as e:
            _LOGGER.error("Error fetching data for ISIN %s: %s", self._isin, e)
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout fetching data for ISIN %s", self._isin)
        except Exception as e:
            _LOGGER.exception("Unexpected error fetching data for ISIN %s: %s", self._isin, e)