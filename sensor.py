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

    _LOGGER.debug("Setting up sensors for hub: %s with sensors: %s", hub_name, sensors)

    entities = []
    for sensor in sensors:
        _LOGGER.debug("Registering sensor: %s with ISIN: %s for hub: %s", sensor["name"], sensor["isin"], hub_name)
        entities.append(ISINSensor(sensor["isin"], sensor["name"], hub_name))

    async_add_entities(entities, update_before_add=True)

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

    async def async_update(self):
        """Fetch data from the API asynchronously."""
        try:
            url = f"https://component-api.wertpapiere.ing.de/api/v1/components/instrumentheader/{self._isin}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    response.raise_for_status()
                    data = await response.json()

                    self._state = data.get("price")
                    self._attributes = {
                        "name": data.get("name"),
                        "close": data.get("close"),
                        "bit": data.get("bit"),
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
        except aiohttp.ClientError as e:
            _LOGGER.error("Error fetching data for ISIN %s: %s", self._isin, e)