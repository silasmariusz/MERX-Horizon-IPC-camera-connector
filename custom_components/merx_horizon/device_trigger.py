"""
Copyright (c) 2026, Silas Mariusz Grzybacz

Device triggers for MERX Horizon IPC Camera.
"""
import voluptuous as vol

from homeassistant.components.device_automation import DEVICE_TRIGGER_BASE_SCHEMA
from homeassistant.const import CONF_DEVICE_ID, CONF_DOMAIN, CONF_PLATFORM, CONF_TYPE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.components.homeassistant.triggers import event as event_trigger

from .const import DOMAIN

# Comprehensive list of events supported by MERX Horizon API
TRIGGER_TYPES = {
    "motion_detected",
    "io_alarm",
    "pir_alarm",
    "sound_detected",
    "occlusion_detected",
    "human_detected",
    "vehicle_detected",
    "face_detected",
    "lpr_detected",
    "fire_smoke_detected",
    "wander_detected",
    "parcel_detected",
    "pos_alarm",
}

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
    event_config = event_trigger.TRIGGER_SCHEMA(
        {
            event_trigger.CONF_PLATFORM: "event",
            event_trigger.CONF_EVENT_TYPE: f"{DOMAIN}_event",
            event_trigger.CONF_EVENT_DATA: {
                CONF_DEVICE_ID: config[CONF_DEVICE_ID],
                CONF_TYPE: config[CONF_TYPE],
            },
        }
    )
    return await event_trigger.async_attach_trigger(
        hass, event_config, action, trigger_info, platform_type="device"
    )
