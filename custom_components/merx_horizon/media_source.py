"""
Copyright (c) 2026, Silas Mariusz Grzybacz

Media Source implementation for MERX Horizon IPC Camera.
"""
from __future__ import annotations

import logging
from typing import Tuple

from homeassistant.components.media_player import BrowseError, BrowseMedia
from homeassistant.components.media_source.error import Unresolvable
from homeassistant.components.media_source.models import (
    BrowseMediaSource,
    MediaSource,
    MediaSourceItem,
    PlayMedia,
)
from homeassistant.core import HomeAssistant

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
        # In order to play RTSP streams in the browser via Home Assistant,
        # we shouldn't return 'application/x-rtsp' because browsers don't support it natively.
        # Instead, we should rely on Home Assistant's stream component to proxy it.
        # For camera entities, HA handles this automatically, but for Media Source,
        # we might need to return a format that HA can proxy, or use the camera entity's HLS stream.
        
        # However, for direct RTSP playback from Media Source, HA's stream component
        # can handle 'application/x-rtsp' if the frontend supports it via HLS proxying,
        # but sometimes it requires 'video/mp4' or similar if we are downloading the file.
        # Since the API returns an RTSP URL for playback:
        
        if not item.identifier.startswith("rtsp://"):
            raise Unresolvable("Invalid media identifier")

        # Returning application/x-rtsp tells HA to use the stream component to convert it to HLS
        return PlayMedia(item.identifier, "application/x-rtsp")

    async def async_browse_media(
        self, item: MediaSourceItem
    ) -> BrowseMediaSource:
        """Return media."""
        if item.identifier:
            return BrowseMediaSource(
                domain=DOMAIN,
                identifier=item.identifier,
                media_class="directory",
                media_content_type="video",
                title="Recordings",
                can_play=False,
                can_expand=True,
                children_media_class="video",
                children=[],
            )

        cameras = self.hass.data.get(DOMAIN, {})
        children = []

        for entry_id, client in cameras.items():
            # For testing, we provide the RTSP playback URL
            playback_url = f"rtsp://{client.username}:{client.password}@{client.host}:{client.port}/rtsp/playback?channel=1&subtype=0&starttime=2026-03-12T00:00:00Z&endtime=2026-03-12T23:59:59Z"
            
            children.append(
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=playback_url,
                    media_class="video",
                    media_content_type="application/x-rtsp",
                    title=f"Camera {client.host} - Today's Recording",
                    can_play=True,
                    can_expand=False,
                    thumbnail="https://brands.home-assistant.io/camera/icon.png" # Placeholder thumbnail
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
            children_media_class="video",
            children=children,
        )
