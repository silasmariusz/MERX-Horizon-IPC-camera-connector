"""
Copyright (c) 2026, Silas Mariusz Grzybacz

The MERX Horizon IPC Camera integration.
"""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .client import MerxHorizonClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["camera", "binary_sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MERX Horizon from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    session = async_get_clientsession(hass)
    client = MerxHorizonClient(
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        session=session,
    )
    
    hass.data[DOMAIN][entry.entry_id] = client
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
