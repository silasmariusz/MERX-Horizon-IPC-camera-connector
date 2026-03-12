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
        # item.identifier contains the RTSP playback URL
        if not item.identifier.startswith("rtsp://"):
            raise Unresolvable("Invalid media identifier")

        return PlayMedia(item.identifier, "application/x-rtsp")

    async def async_browse_media(
        self, item: MediaSourceItem
    ) -> BrowseMediaSource:
        """Return media."""
        if item.identifier:
            # Here we would parse the identifier to know which camera/date we are browsing
            # For simplicity, we just return an empty list if an identifier is provided
            # A real implementation would query the API for recordings on that date
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

        # Root directory - list all cameras
        cameras = self.hass.data.get(DOMAIN, {})
        children = []

        for entry_id, client in cameras.items():
            # Create a dummy recording entry for demonstration
            # In a full implementation, this would call `client.search_recordings()`
            # and build a tree of dates -> recordings
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
