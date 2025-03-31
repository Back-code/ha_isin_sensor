"""ISIN Sensor Integration."""
import aiohttp
import asyncio
import logging
from datetime import timedelta  # Import für SCAN_INTERVAL
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import Entity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=5)  # Setze das Abfrageintervall auf 5 Minuten

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
        entities.append(ISINSensor(sensor["isin"], sensor["name"], hub_name, sensor.get("quantity", 0)))

    if entities:
        async_add_entities(entities, update_before_add=True)
    else:
        _LOGGER.warning("No valid sensors to add for hub: %s", hub_name)

class ISINSensor(SensorEntity):
    """Representation of an ISIN Sensor."""

    def __init__(self, isin, name, hub_name, quantity):
        """Initialize the sensor."""
        self._isin = isin
        self._name = name
        self._hub_name = hub_name
        self._quantity = quantity
        self._state = None
        self._attributes = {}
        self._total_value = None  # Neuer Zustand für price * quantity

    #async def async_added_to_hass(self):
    #    """Create a helper for the quantity."""
        # Ersetze ungültige Zeichen in hub_name und name
    #   sanitized_hub_name = self._hub_name.replace(" ", "_").replace("-", "_").lower()
    #   sanitized_name = self._name.replace(" ", "_").replace("-", "_").lower()
    #   helper_name = f"{sanitized_hub_name}_{sanitized_name}_quantity"
    #    if not self.hass.states.get(helper_name):
    #        self.hass.states.async_set(helper_name, self._quantity, {"unit_of_measurement": "pcs"})

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._hub_name} - {self._name}"

    @property
    def unique_id(self):
        """Return the unique ID of the sensor."""
        return self._isin.upper()  # ISIN immer in Großbuchstaben

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
        attributes = self._attributes.copy()
        attributes["quantity"] = round(self._quantity, 2)  # Rundung auf 2 Nachkommastellen
        attributes["total_value"] = self._total_value  # Füge den berechneten Wert hinzu
        return attributes

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
                    self._state = data.get('price')
                    self._total_value = self._state * self._quantity if self._state is not None else None

                    # Dynamische Attributerstellung basierend auf instrumentTypeDisplayName
                    instrument_type = data.get("instrumentType", {}).get("mainType")
                    _LOGGER.debug("Instrument type for ISIN %s: %s", self._isin, instrument_type)

                    if instrument_type == "Share": # Aktie
                        self._attributes = {
                            "name": data.get("name"),
                            "instrumentTypeDisplayName": data.get("instrumentTypeDisplayName"),
                            "close": data.get("close"),
                            "changePercent": data.get("changePercent"),
                            "changeAbsolute": data.get("changeAbsolute"),
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
                            "quantity": self._quantity,
                        }
                    elif instrument_type == "Fund": # Fonds & ETF
                        self._attributes = {
                            "name": data.get("name"),
                            "instrumentTypeDisplayName": data.get("instrumentTypeDisplayName"),
                            "close": data.get("close"),
                            "changePercent": data.get("changePercent"),
                            "changeAbsolute": data.get("changeAbsolute"),
                            "wkn": data.get("wkn"),
                            "isin": data.get("isin"),
                            "internalIsin": data.get("internalIsin"),
                            "stockMarket": data.get("stockMarket"),
                            "priceChangeDate": data.get("priceChangeDate"),
                            "currency": data.get("currency"),
                            "currencySign": data.get("currencySign"),
                            "quantity": self._quantity,
                        }

                    elif instrument_type == "Bond": # Anleihe
                        self._attributes = {
                            "name": data.get("name"),
                            "instrumentTypeDisplayName": data.get("instrumentTypeDisplayName"),
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
                            "quantity": self._quantity,
                        }
                    else:  # Standardfall oder unbekannter Typ
                        self._attributes = {
                            "name": data.get("name"),
                            "currency": data.get("currency"),
                            "priceChangeDate": data.get("priceChangeDate"),
                            "wkn": data.get("wkn"),
                            "isin": data.get("isin"),
                            "internalIsin": data.get("internalIsin"),
                            "stockMarket": data.get("stockMarket"),
                            "currency": data.get("currency"),
                            "currencySign": data.get("currencySign"), 
                            "quantity": self._quantity,
                        }
                    
                    _LOGGER.debug("Updated sensor %s with data: %s", self._isin, data)

        except aiohttp.ClientError as e:
            _LOGGER.error("Error fetching data for ISIN %s: %s", self._isin, e)
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout fetching data for ISIN %s", self._isin)
        except Exception as e:
            _LOGGER.exception("Unexpected error fetching data for ISIN %s: %s", self._isin, e)