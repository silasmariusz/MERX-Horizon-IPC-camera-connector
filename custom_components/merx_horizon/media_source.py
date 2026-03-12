"""
Copyright (c) 2026, Silas Mariusz Grzybacz

Media Source implementation for MERX Horizon IPC Camera.
"""
from __future__ import annotations

import logging
from typing import Tuple
import datetime

from homeassistant.components.media_player import BrowseError, BrowseMedia
from homeassistant.components.media_source.error import Unresolvable
from homeassistant.components.media_source.models import (
    BrowseMediaSource,
    MediaSource,
    MediaSourceItem,
    PlayMedia,
)
from homeassistant.core import HomeAssistant
from homeassistant.components.stream import create_stream
from homeassistant.components.camera import DynamicStreamSettings

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_get_media_source(hass: HomeAssistant) -> MerxHorizonMediaSource:
    """Set up MERX Horizon media source."""
    return MerxHorizonMediaSource(hass)

class MerxHorizonMediaSource(MediaSource):
    """Provide MERX Horizon IPC Camera recordings as media sources."""

    name: str = "MERX Horizon Recordings"

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize MERX Horizon media source."""
        super().__init__(DOMAIN)
        self.hass = hass

    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        """Resolve media to a url."""
        if not item.identifier.startswith("rtsp://"):
            raise Unresolvable("Invalid media identifier")

        try:
            # Create a stream to proxy the RTSP URL to HLS
            stream = create_stream(self.hass, item.identifier, {}, DynamicStreamSettings())
            stream.add_provider("hls")
            url = stream.endpoint_url("hls")
            return PlayMedia(url, "application/vnd.apple.mpegurl")
        except Exception as err:
            _LOGGER.error("Failed to create stream: %s", err)
            # Fallback
            return PlayMedia(item.identifier, "application/x-rtsp")

    async def async_browse_media(
        self, item: MediaSourceItem
    ) -> BrowseMediaSource:
        """Return media."""
        cameras = self.hass.data.get(DOMAIN, {})

        if not item.identifier:
            # Root level: List cameras
            children = []
            for entry_id, client in cameras.items():
                children.append(
                    BrowseMediaSource(
                        domain=DOMAIN,
                        identifier=f"camera_{entry_id}",
                        media_class="directory",
                        media_content_type="video",
                        title=f"MERX Camera {client.host}",
                        can_play=False,
                        can_expand=True,
                        thumbnail="/api/brands/integration/merx_horizon/icon.png"
                    )
                )

            return BrowseMediaSource(
                domain=DOMAIN,
                identifier="",
                media_class="directory",
                media_content_type="video",
                title=self.name,
                can_play=False,
                can_expand=True,
                children_media_class="directory",
                children=children,
            )

        if item.identifier.startswith("camera_"):
            # Camera level: List dates (Today, Yesterday, 2 Days Ago)
            entry_id = item.identifier.replace("camera_", "")
            
            children = []
            for i in range(3):
                date = datetime.datetime.now() - datetime.timedelta(days=i)
                date_str = date.strftime("%m-%d-%Y") # Use dashes for identifier to avoid URL routing issues
                display_date = "Today" if i == 0 else "Yesterday" if i == 1 else date.strftime("%Y-%m-%d")
                
                children.append(
                    BrowseMediaSource(
                        domain=DOMAIN,
                        identifier=f"date_{entry_id}_{date_str}",
                        media_class="directory",
                        media_content_type="video",
                        title=display_date,
                        can_play=False,
                        can_expand=True,
                    )
                )

            return BrowseMediaSource(
                domain=DOMAIN,
                identifier=item.identifier,
                media_class="directory",
                media_content_type="video",
                title="Select Date",
                can_play=False,
                can_expand=True,
                children_media_class="directory",
                children=children,
            )

        if item.identifier.startswith("date_"):
            # Date level: List recordings for that date
            parts = item.identifier.split("_")
            entry_id = parts[1]
            date_str_dashed = parts[2] # MM-DD-YYYY
            date_str = date_str_dashed.replace("-", "/") # Convert back to MM/DD/YYYY for API
            
                        client = cameras.get(entry_id)
                        if not client:
                            raise BrowseError("Camera not found")

                        # Get RTSP port from config entry
                        config_entry = self.hass.config_entries.async_get_entry(entry_id)
                        rtsp_port = config_entry.data.get("rtsp_port", 554) if config_entry else 554

                        children = []
            
            try:
                # Search for recordings on this date
                # record_type 4294967295 means all records
                            payload = {
                                "channel": ["CH1"],
                                "start_date": date_str,
                                "start_time": "00:00:00",
                                "end_date": date_str,
                                "end_time": "23:59:59",
                                "record_type": 4294967295,
                                "stream_mode": "Mainstream"
                            }
                
                response = await client._request("POST", "/API/Playback/SearchRecord/Search", json_data=payload)
                
                if response and "data" in response and "record" in response["data"]:
                    records = response["data"]["record"]
                    if records and len(records) > 0:
                        for rec in records[0]:
                            start_time = rec.get("start_time", "")
                            end_time = rec.get("end_time", "")
                            rec_type = rec.get("record_type", 0)
                            
                            # Determine event type name
                            type_name = "Normal"
                            if rec_type & 0x2: type_name = "Alarm"
                            if rec_type & 0x4: type_name = "Motion"
                            if rec_type & 0x8: type_name = "IO Alarm"
                            if rec_type & 0x80000: type_name = "Smart"
                            if rec_type & 0x200000: type_name = "Person"
                            if rec_type & 0x400000: type_name = "Face"
                            
                            # Construct RTSP playback URL
                            # Format: rtsp://user:pass@ip:port/rtsp/playback?channel=1&subtype=0&starttime=YYYY-MM-DDTHH:MM:SSZ&endtime=...
                            # We need to convert MM/DD/YYYY to YYYY-MM-DD
                            m, d, y = date_str.split("/")
                            iso_date = f"{y}-{m}-{d}"
                            
                                        start_iso = f"{iso_date}T{start_time}Z"
                                        end_iso = f"{iso_date}T{end_time}Z"
                                        
                                        playback_url = f"rtsp://{client.username}:{client.password}@{client.host}:{rtsp_port}/rtsp/playback?channel=1&subtype=0&starttime={start_iso}&endtime={end_iso}"
                                        
                                        children.append(
                                BrowseMediaSource(
                                    domain=DOMAIN,
                                    identifier=playback_url,
                                    media_class="video",
                                    media_content_type="video/mp4",
                                    title=f"{start_time} - {end_time} ({type_name})",
                                    can_play=True,
                                    can_expand=False,
                                )
                            )
            except Exception as err:
                _LOGGER.error("Error fetching recordings: %s", err)

            return BrowseMediaSource(
                domain=DOMAIN,
                identifier=item.identifier,
                media_class="directory",
                media_content_type="video",
                title=f"Recordings for {date_str}",
                can_play=False,
                can_expand=True,
                children_media_class="video",
                children=children,
            )

        raise BrowseError(f"Unknown item: {item.identifier}")
