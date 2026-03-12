"""
Copyright (c) 2026, Silas Mariusz Grzybacz

The MERX Horizon IPC Camera integration.
"""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["camera"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MERX Horizon from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # TODO: Initialize API client here and store it in hass.data[DOMAIN][entry.entry_id]
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
