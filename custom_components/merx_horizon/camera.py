"""
Copyright (c) 2026, Silas Mariusz Grzybacz

Camera platform for MERX Horizon IPC Camera.
"""
import logging

from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME

from .const import DOMAIN, CONF_RTSP_PORT

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the MERX Horizon camera from a config entry."""
    # TODO: Fetch device info and create camera entities for main and sub streams
    async_add_entities([MerxHorizonCamera(config_entry)])


class MerxHorizonCamera(Camera):
    """Representation of a MERX Horizon IPC Camera."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the camera."""
        super().__init__()
        self._config_entry = config_entry
        self._host = config_entry.data[CONF_HOST]
        self._username = config_entry.data[CONF_USERNAME]
        self._password = config_entry.data[CONF_PASSWORD]
        self._rtsp_port = config_entry.data.get(CONF_RTSP_PORT, 554)
        
        self._attr_name = f"MERX Camera {self._host}"
        self._attr_unique_id = f"{config_entry.entry_id}_camera"
        self._attr_supported_features = CameraEntityFeature.STREAM | CameraEntityFeature.ON_OFF
        self._attr_brand = "MERX"
        self._attr_model = "Horizon IPC"

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return bytes of camera image."""
        # TODO: Implement API call to fetch snapshot
        return None

    async def stream_source(self) -> str | None:
        """Return the source of the stream."""
        # TODO: Return actual RTSP URL based on API documentation
        # Format usually: rtsp://username:password@host:port/stream_path
        return f"rtsp://{self._username}:{self._password}@{self._host}:{self._rtsp_port}/cam/realmonitor?channel=1&subtype=0"

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
