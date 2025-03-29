"""ISIN Sensor Integration."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

class ISINHub:
    """Class to manage ISIN Hub."""

    def __init__(self, hub_name, sensors):
        self.hub_name = hub_name
        self.sensors = sensors

    def update_sensors(self, sensors):
        """Update the sensors in the hub."""
        _LOGGER.debug("Updating sensors for hub: %s with sensors: %s", self.hub_name, sensors)
        self.sensors = sensors

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the ISIN Sensor integration from configuration.yaml."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the ISIN Sensor integration from a config entry."""
    hub_name = entry.data["hub_name"]
    sensors = entry.data.get("sensors", [])

    # Synchronisiere Optionen mit Daten
    if entry.options:
        sensors = entry.options.get("sensors", sensors)
# Aktualisiere config_entry.data mit den Optionen
        hass.config_entries.async_update_entry(
            entry,
            data={**entry.data, "sensors": sensors},
            options={**entry.options, "sensors": sensors},  # Synchronisiere die Sensoren mit "options"
        )

    _LOGGER.debug("Setting up hub: %s with sensors: %s", hub_name, sensors)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][hub_name] = ISINHub(hub_name, sensors)

    try:
        # Forward the entry setup to the sensor platform
        await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    except Exception as e:
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
        data={**entry.data, "sensors": sensors},  # Synchronisiere die Sensoren mit "data"
        options={**entry.options, "sensors": sensors},  # Synchronisiere die Sensoren mit "options"
    )

    # Reload the entry to apply changes
    await hass.config_entries.async_reload(entry.entry_id)

async def async_update_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle updates to a config entry."""
    hub_name = entry.data["hub_name"]
    sensors = entry.options.get("sensors", entry.data.get("sensors", []))

    _LOGGER.debug("Updating hub: %s with sensors: %s", hub_name, sensors)

    # Update the hub with the new sensors
    if hub_name in hass.data[DOMAIN]:
        hass.data[DOMAIN][hub_name].update_sensors(sensors)

    # Reload the sensor platform to apply changes
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    await hass.config_entries.async_forward_entry_setup(entry, "sensor")
