"""ISIN Sensor Integration."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from .const import DOMAIN

class ISINHub:
    """Class to manage ISIN Hub."""

    def __init__(self, hub_name, sensors):
        self.hub_name = hub_name
        self.sensors = sensors

    def update_sensors(self, sensors):
        """Update the sensors in the hub."""
        self.sensors = sensors
        # Hier kannst du zusätzliche Logik hinzufügen, um den Hub zu aktualisieren

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the ISIN Sensor integration from configuration.yaml."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the ISIN Sensor integration from a config entry."""
    hub_name = entry.data["hub_name"]
    sensors = entry.data["sensors"]

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][hub_name] = ISINHub(hub_name, sensors)

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
