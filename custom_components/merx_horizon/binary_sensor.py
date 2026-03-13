"""
Copyright (c) 2026, Silas Mariusz Grzybacz

Binary sensor platform for MERX Horizon IPC Camera.
"""
import logging
from datetime import timedelta

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN
from .client import MerxHorizonClient

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=5)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the MERX Horizon binary sensors from a config entry."""
    client: MerxHorizonClient = hass.data[DOMAIN][config_entry.entry_id]

    # Add heartbeat timestamp
    client.last_heartbeat = None
    import time

    async def async_update_data():
        """Fetch data from API endpoint."""
        try:
            # Check if we need to send a heartbeat (every 25 seconds)
            current_time = time.time()
            if getattr(client, "last_heartbeat", None) is None or current_time - client.last_heartbeat > 25:
                await client.send_heartbeat()
                client.last_heartbeat = current_time

            # Polling the /API/Event/Check endpoint
            events = await client.check_events()
            return events.get("data", {})
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {type(err).__name__} {str(err)}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="merx_horizon_events",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as ex:
        _LOGGER.warning("First refresh failed, sensors will be created anyway: %s", ex)

    sensors = [
        MerxHorizonBinarySensor(coordinator, config_entry, "motion_alarm", "Motion Detection", BinarySensorDeviceClass.MOTION),
        MerxHorizonBinarySensor(coordinator, config_entry, "human_detected", "Human Detection", BinarySensorDeviceClass.OCCUPANCY, "mdi:human"),
        MerxHorizonBinarySensor(coordinator, config_entry, "vehicle_detected", "Vehicle Detection", BinarySensorDeviceClass.OCCUPANCY, "mdi:car"),
        MerxHorizonBinarySensor(coordinator, config_entry, "face_detected", "Face Detection", BinarySensorDeviceClass.OCCUPANCY, "mdi:face-recognition"),
        MerxHorizonBinarySensor(coordinator, config_entry, "lpr_detected", "License Plate Detection", BinarySensorDeviceClass.OCCUPANCY, "mdi:car-info"),
    ]

    async_add_entities(sensors)


class MerxHorizonBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a MERX Horizon Binary Sensor."""

    def __init__(self, coordinator, config_entry, event_key, name, device_class, icon=None):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._event_key = event_key
        self._attr_name = f"MERX Camera {config_entry.data['host']} {name}"
        self._attr_unique_id = f"{config_entry.entry_id}_{event_key}"
        self._attr_device_class = device_class
        if icon:
            self._attr_icon = icon
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": f"MERX Camera {config_entry.data['host']}",
            "manufacturer": "MERX",
            "model": "Horizon IPC",
        }

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        # The API returns true/false for alarms like motion_alarm
        # We check if the event_key exists in the data and is true
        if self.coordinator.data:
            return self.coordinator.data.get(self._event_key, False)
        return False
