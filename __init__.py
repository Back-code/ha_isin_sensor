"""ISIN Sensor Integration."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the ISIN Sensor integration from configuration.yaml."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the ISIN Sensor integration from a config entry."""
    hub_name = entry.data["hub_name"]
    sensors = entry.data["sensors"]

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][hub_name] = sensors

    # Sensoren registrieren
    for sensor in sensors:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, "sensor")
        )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload an ISIN Sensor config entry."""
    hub_name = entry.data["hub_name"]
    if hub_name in hass.data[DOMAIN]:
        hass.data[DOMAIN].pop(hub_name)

    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    return True
