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
            # We must pass the audio/video options and enable WebRTC/HLS properly
            # DynamicStreamSettings was correctly passed, but the format might need specific options.
            # Using basic options often helps stream component handle generic RTSP streams.
            stream_options = {
                "rtsp_transport": "tcp",
            }
            stream = create_stream(self.hass, item.identifier, stream_options, DynamicStreamSettings())
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
                        # Camera level: Query API for available dates
                        entry_id = item.identifier.replace("camera_", "")
                        client = cameras.get(entry_id)
                        if not client:
                            raise BrowseError("Camera not found")

                        # Default to current month
                        now = datetime.datetime.now()
                        month = now.month
                        year = now.year
                        
                        children = []
                        
                        try:
                            # Use default channel CH1
                            channel = "CH1"
                            month_data = await client.get_playback_month(channel, month, year)
                            
                            if month_data and "data" in month_data and "is_has_rec" in month_data["data"]:
                                is_has_rec = month_data["data"]["is_has_rec"]
                                # API returns 31 array elements (0-indexed for days 1-31)
                                # is_has_rec[i] == 1 means recordings exist for day i+1
                                
                                # Process from end of month to beginning
                                for i in range(len(is_has_rec) - 1, -1, -1):
                                    if is_has_rec[i] == 1:
                                        day = i + 1
                                        # Skip future days
                                        if year == now.year and month == now.month and day > now.day:
                                            continue
                                            
                                        # Construct date strings
                                        date_obj = datetime.datetime(year, month, day)
                                        date_str = date_obj.strftime("%m-%d-%Y")
                                        display_date = date_obj.strftime("%Y-%m-%d")
                                        
                                        # Show "Today" or "Yesterday" if applicable
                                        if date_obj.date() == now.date():
                                            display_date = "Today"
                                        elif date_obj.date() == (now - datetime.timedelta(days=1)).date():
                                            display_date = "Yesterday"
                                            
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
                                        
                            # If no recordings found or error, provide an empty list
                            if not children:
                                children.append(
                                    BrowseMediaSource(
                                        domain=DOMAIN,
                                        identifier=f"empty_{entry_id}",
                                        media_class="directory",
                                        media_content_type="video",
                                        title="No recordings found this month",
                                        can_play=False,
                                        can_expand=False,
                                    )
                                )
                                
                        except Exception as err:
                            _LOGGER.error("Error fetching available dates: %s", err)

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
                    "record_type_ex": [4294967295],
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
