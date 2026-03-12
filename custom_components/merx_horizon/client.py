"""
Copyright (c) 2026, Silas Mariusz Grzybacz

API Client for MERX Horizon IPC Camera.
"""
import asyncio
import logging
from typing import Any, Dict, Optional

import aiohttp

_LOGGER = logging.getLogger(__name__)

class MerxHorizonClient:
    """Client for MERX Horizon IPC Camera API."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize the client."""
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.session = session
        self.base_url = f"http://{host}:{port}"
        # Some cameras use Digest auth, some use Basic. aiohttp handles Basic easily, 
        # but for Digest we might need aiohttp.BasicAuth or a custom handler.
        # Assuming BasicAuth for now as per standard IPCs unless specified.
        self.auth = aiohttp.BasicAuth(username, password)

    async def _request(self, method: str, path: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make an API request."""
        url = f"{self.base_url}{path}"
        headers = {"Content-Type": "application/json"}
        
        payload = None
        if json_data:
            payload = {
                "version": "1.0",
                "data": json_data
            }

        try:
            async with self.session.request(
                method, url, json=payload, headers=headers, auth=self.auth, timeout=10
            ) as response:
                response.raise_for_status()
                if response.content_type == "application/json":
                    return await response.json()
                return {"status": response.status, "content": await response.read()}
        except Exception as err:
            _LOGGER.error("Error communicating with MERX Horizon API: %s", err)
            raise

    async def get_device_info(self) -> Dict[str, Any]:
        """Get device information."""
        return await self._request("POST", "/API/Login/DeviceInfo/Get")

    async def get_snapshot(self, channel: str = "CH1") -> bytes:
        """Get a snapshot from the camera."""
        # Note: API might use a different endpoint for snapshots, 
        # often /cgi-bin/snapshot.cgi or /API/Event/Check for event snapshots.
        # Assuming standard snapshot path or returning empty for now if undocumented.
        url = f"{self.base_url}/cgi-bin/snapshot.cgi?channel={channel}"
        try:
            async with self.session.get(url, auth=self.auth, timeout=10) as response:
                response.raise_for_status()
                return await response.read()
        except Exception as err:
            _LOGGER.error("Failed to get snapshot: %s", err)
            return b""

    async def control_ptz(self, channel: str, cmd: str, speed: int = 50) -> Dict[str, Any]:
        """Control PTZ."""
        # cmd can be: Ptz_Cmd_Up, Ptz_Cmd_Down, Ptz_Cmd_Left, Ptz_Cmd_Right, Ptz_Cmd_ZoomAdd, Ptz_Cmd_ZoomMinus, etc.
        data = {
            "channel": channel,
            "cmd": cmd,
            "speed": speed
        }
        return await self._request("POST", "/API/PreviewChannel/PTZ/Control", json_data=data)

    async def check_events(self) -> Dict[str, Any]:
        """Poll for events."""
        # Used to poll to obtain device alarms.
        return await self._request("POST", "/API/Event/Check")

    async def search_recordings(self, channel: str, start_time: str, end_time: str) -> Dict[str, Any]:
        """Search for recordings on the SD card."""
        data = {
            "channel": channel,
            "start_time": start_time,
            "end_time": end_time
        }
        return await self._request("POST", "/API/Playback/SearchRecord/Search", json_data=data)
