"""ISIN Sensor Integration."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from datetime import timedelta
from homeassistant.helpers.event import async_track_time_interval
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

class ISINHub:
    """Class to manage ISIN Hub."""

    def __init__(self, hub_name, sensors, update_interval, hass):
        self.hub_name = hub_name
        self.sensors = sensors
        self.update_interval = update_interval
        self.hass = hass
        self._update_listener = None

    def start_updating(self):
        """Start periodic updates."""
        if self._update_listener:
            self._update_listener()  # Remove previous listener
        self._update_listener = async_track_time_interval(
            self.hass, self._update_sensors, timedelta(seconds=self.update_interval)
        )

    async def _update_sensors(self, now):
        """Update sensors periodically."""
        _LOGGER.debug("Updating sensors for hub: %s", self.hub_name)
        # Logic for sensor update can be added here

    def update_sensors(self, sensors):
        """Update the sensors in the hub."""
        _LOGGER.debug("Updating sensors for hub: %s with sensors: %s", self.hub_name, sensors)
        self.sensors = sensors

    def update_interval(self, interval):
        """Update the interval and restart the updater."""
        self.update_interval = interval
        self.start_updating()

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the ISIN Sensor integration from configuration.yaml."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the ISIN Sensor integration from a config entry."""
    hub_name = entry.data["hub_name"]
    sensors = entry.options.get("sensors", entry.data.get("sensors", []))
    update_interval = entry.data.get("update_interval", 60)  # Default value: 60 seconds

    _LOGGER.debug("Setting up hub: %s with sensors: %s and update interval: %s seconds", hub_name, sensors, update_interval)

    hass.data.setdefault(DOMAIN, {})
    hub = ISINHub(hub_name, sensors, update_interval, hass)
    hass.data[DOMAIN][hub_name] = hub

    hub.start_updating()  # Start periodic updates

    try:
        # Forward the entry setup to the sensor platform
        await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    except Exception as e:
        # Log the error and raise ConfigEntryNotReady if setup fails
        hass.data[DOMAIN].pop(hub_name, None)
        raise ConfigEntryNotReady(f"Error setting up ISIN Sensor: {e}")

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload an ISIN Sensor config entry."""
    hub_name = entry.data["hub_name"]

    # Unload the sensor platform
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    if unload_ok:
        hass.data[DOMAIN].pop(hub_name, None)

    return unload_ok

async def async_update_options(hass: HomeAssistant, entry: ConfigEntry):
    """Handle updates to the options of a config entry."""
    hub_name = entry.data["hub_name"]
    sensors = entry.options.get("sensors", entry.data.get("sensors", []))

    # Update the hub with the new sensors
    if hub_name in hass.data[DOMAIN]:
        hass.data[DOMAIN][hub_name].update_sensors(sensors)

    # Update the config entry data
    hass.config_entries.async_update_entry(
        entry,
        data={**entry.data, "sensors": sensors},
    )

    # Reload the entry to apply changes
    await hass.config_entries.async_reload(entry.entry_id)

async def async_update_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle updates to a config entry."""
    hub_name = entry.data["hub_name"]
    sensors = entry.options.get("sensors", entry.data.get("sensors", []))

    _LOGGER.debug("Updating hub: %s with sensors: %s", hub_name, sensors)

    # Update the sensors in the hub
    if hub_name in hass.data[DOMAIN]:
        hass.data[DOMAIN][hub_name].update_sensors(sensors)

    # Reload the sensor platform to register the new sensors
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    await hass.config_entries.async_forward_entry_setup(entry, "sensor")
