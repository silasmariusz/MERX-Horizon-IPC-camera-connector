"""
Copyright (c) 2026, Silas Mariusz Grzybacz

Camera platform for MERX Horizon IPC Camera.
"""
import asyncio
import logging
import voluptuous as vol

from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, CONF_RTSP_PORT

_LOGGER = logging.getLogger(__name__)

SERVICE_PTZ_CONTROL = "ptz_control"

PTZ_SCHEMA = {
    vol.Required("cmd"): cv.string,
    vol.Optional("speed", default=50): cv.positive_int,
    vol.Optional("state"): cv.string,
}

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the MERX Horizon camera from a config entry."""
    client = hass.data[DOMAIN][config_entry.entry_id]
    
    # Add Main Stream Camera
    async_add_entities([MerxHorizonCamera(config_entry, client, "CH1", 0, "Main Stream")])
    # Add Sub Stream Camera
    async_add_entities([MerxHorizonCamera(config_entry, client, "CH1", 1, "Sub Stream")])

    platform = entity_platform.async_get_current_platform()
    
    platform.async_register_entity_service(
        SERVICE_PTZ_CONTROL,
        PTZ_SCHEMA,
        "async_ptz_control",
    )


class MerxHorizonCamera(Camera):
    """Representation of a MERX Horizon IPC Camera."""

    def __init__(self, config_entry: ConfigEntry, client, channel: str, subtype: int, name_suffix: str) -> None:
        """Initialize the camera."""
        super().__init__()
        self._client = client
        self._channel = channel
        self._subtype = subtype
        self._config_entry = config_entry
        self._host = config_entry.data[CONF_HOST]
        self._username = config_entry.data[CONF_USERNAME]
        self._password = config_entry.data[CONF_PASSWORD]
        self._rtsp_port = config_entry.data.get(CONF_RTSP_PORT, 554)
        
        self._attr_name = f"MERX Camera {self._host} {name_suffix}"
        self._attr_unique_id = f"{config_entry.entry_id}_{channel}_{subtype}"
        self._attr_supported_features = CameraEntityFeature.STREAM | CameraEntityFeature.ON_OFF
        self._attr_brand = "MERX"
        self._attr_model = "Horizon IPC"
        self._attr_icon = "phu:merx-ipc-horizon-dome"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": f"MERX Camera {self._host}",
            "manufacturer": "MERX",
            "model": "Horizon IPC",
        }

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return bytes of camera image."""
        return await self._client.get_snapshot(self._channel)

    async def stream_source(self) -> str | None:
        """Return the source of the stream."""
        return f"rtsp://{self._username}:{self._password}@{self._host}:{self._rtsp_port}/rtsp/streaming?channel={self._channel.replace('CH', '')}&subtype={self._subtype}"

    async def async_turn_on(self) -> None:
        """Turn on camera."""
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self) -> None:
        """Turn off camera."""
        self._attr_is_on = False
        self.async_write_ha_state()

    async def async_enable_motion_detection(self) -> None:
        """Enable motion detection in the camera."""
        self._attr_motion_detection_enabled = True
        self.async_write_ha_state()

    async def async_disable_motion_detection(self) -> None:
        """Disable motion detection in camera."""
        self._attr_motion_detection_enabled = False
        self.async_write_ha_state()

    async def async_ptz_control(self, cmd: str, speed: int, state: str = None) -> None:
        """Control PTZ."""
        if state:
            await self._client.control_ptz(self._channel, cmd, speed, state)
        else:
            # If no state is provided, some cameras prefer simply sending the command
            # For others, a stop needs to be sent. We try just sending the command first,
            # then stop after a brief moment to be safe.
            await self._client.control_ptz(self._channel, cmd, speed, "Start")
            await asyncio.sleep(0.5)
            await self._client.control_ptz(self._channel, cmd, speed, "Stop")
