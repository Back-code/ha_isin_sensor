"""ISIN Sensor Integration."""
import aiohttp
import asyncio
import logging
from homeassistant.components.sensor import SensorEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up ISIN Sensor from a config entry."""
    sensors = config_entry.data["sensors"]
    entities = [ISINSensor(sensor["isin"], sensor["name"]) for sensor in sensors]
    async_add_entities(entities)

class ISINSensor(SensorEntity):
    """Representation of an ISIN Sensor."""

    def __init__(self, isin, name):
        """Initialize the sensor."""
        self._isin = isin
        self._name = name
        self._state = None
        self._attributes = {}

    async def async_is_valid_isin(self, isin):
        """Validate the ISIN format asynchronously."""
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

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"stockpocket-{self._name}"

    @property
    def unique_id(self):
        """Return the unique ID of the sensor."""
        return self._isin

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
                        "ask": data.get("ask"),
                        "isin": data.get("isin"),
                        "internalIsin": data.get("internalIsin"),
                        "stockMarket": data.get("stockMarket"),
                        "priceChangeDate": data.get("priceChangeDate"),
                        "currency": data.get("currency"),
                        "changePercent": data.get("changePercent"),
                        "wkn": data.get("wkn"),
                        "changeAbsolute": data.get("changeAbsolute"),
                    }
        except aiohttp.ClientError as e:
            _LOGGER.error("Error fetching data: %s", e)