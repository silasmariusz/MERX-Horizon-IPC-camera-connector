"""
Copyright (c) 2026, Silas Mariusz Grzybacz

Device triggers for MERX Horizon IPC Camera.
"""
import voluptuous as vol

from homeassistant.components.device_automation import DEVICE_TRIGGER_BASE_SCHEMA
from homeassistant.const import CONF_DEVICE_ID, CONF_DOMAIN, CONF_PLATFORM, CONF_TYPE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN

TRIGGER_TYPES = {"motion_detected", "human_detected", "lpr_detected"}

TRIGGER_SCHEMA = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(TRIGGER_TYPES),
    }
)

async def async_get_triggers(hass: HomeAssistant, device_id: str) -> list[dict]:
    """Return a list of triggers."""
    device_registry = dr.async_get(hass)
    device = device_registry.async_get(device_id)

    triggers = []

    # TODO: Determine which triggers are supported by this specific device_id
    for trigger_type in TRIGGER_TYPES:
        triggers.append(
            {
                CONF_PLATFORM: "device",
                CONF_DOMAIN: DOMAIN,
                CONF_DEVICE_ID: device_id,
                CONF_TYPE: trigger_type,
            }
        )

    return triggers

async def async_attach_trigger(
    hass: HomeAssistant, config: dict, action, trigger_info
) -> callback:
    """Attach a trigger."""
    # TODO: Implement event subscription and trigger attachment
    pass
