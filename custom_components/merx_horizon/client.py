"""
Copyright (c) 2026, Silas Mariusz Grzybacz

API Client for MERX Horizon IPC Camera.
"""
import asyncio
import logging
from typing import Any, Dict, Optional
import hashlib
import base64

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
        self.cookies = {}
        self.auth_header = None
        self.token = None

    def _generate_digest_auth(self, method: str, path: str, authenticate_header: str) -> str:
        """Generate Digest Auth header."""
        parts = authenticate_header.replace('Digest ', '').split(',')
        auth_dict = {}
        for part in parts:
            if '=' in part:
                k, v = part.split('=', 1)
                auth_dict[k.strip()] = v.strip().strip('"')
            
        realm = auth_dict.get('realm', '')
        nonce = auth_dict.get('nonce', '')
        qop = auth_dict.get('qop', 'auth')
        
        nc = "00000001"
        cnonce = "0a4f113b"
        
        ha1 = hashlib.md5(f"{self.username}:{realm}:{self.password}".encode('utf-8')).hexdigest()
        ha2 = hashlib.md5(f"{method}:{path}".encode('utf-8')).hexdigest()
        response = hashlib.md5(f"{ha1}:{nonce}:{nc}:{cnonce}:{qop}:{ha2}".encode('utf-8')).hexdigest()
        
        return f'Digest username="{self.username}", realm="{realm}", nonce="{nonce}", uri="{path}", qop={qop}, nc={nc}, cnonce="{cnonce}", response="{response}"'

    async def login(self) -> bool:
        """Login to the camera and get cookies."""
        url = f"{self.base_url}/API/Web/Login"
        payload = {"version": "1.0", "data": {}}
        
        try:
            async with self.session.post(url, json=payload) as resp1:
                if resp1.status == 401:
                    auth_header = resp1.headers.get('WWW-Authenticate')
                    if auth_header and 'Digest' in auth_header:
                        self.auth_header = self._generate_digest_auth('POST', '/API/Web/Login', auth_header)
                        
                        headers = {
                            "Authorization": self.auth_header,
                            "Content-Type": "application/json"
                        }
                        async with self.session.post(url, json=payload, headers=headers) as resp2:
                            if resp2.status == 200:
                                self.cookies = resp2.cookies
                                data = await resp2.json()
                                if "data" in data and "token" in data["data"]:
                                    self.token = data["data"]["token"]
                                return True
                            else:
                                _LOGGER.error("Login failed with status %s: %s", resp2.status, await resp2.text())
                                return False
                elif resp1.status == 200:
                    self.cookies = resp1.cookies
                    return True
        except Exception as err:
            _LOGGER.error("Error during login: %s", err)
            
        return False

    async def _request(self, method: str, path: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make an API request."""
        if not self.cookies and not self.auth_header:
            await self.login()
            
        url = f"{self.base_url}{path}"
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["token"] = self.token
            
        payload = {"version": "1.0", "data": json_data if json_data else {}}

        try:
            async with self.session.request(
                method, url, json=payload, headers=headers, cookies=self.cookies, timeout=10
            ) as response:
                if response.status == 401:
                    if await self.login():
                        async with self.session.request(
                            method, url, json=payload, headers=headers, cookies=self.cookies, timeout=10
                        ) as retry_response:
                            response = retry_response
                
                if response.status == 400:
                    text = await response.text()
                    if "one_IE" in text:
                        # Session conflict, try to re-login
                        self.cookies = {}
                        if await self.login():
                            async with self.session.request(
                                method, url, json=payload, headers=headers, cookies=self.cookies, timeout=10
                            ) as retry_response:
                                response = retry_response

                response.raise_for_status()
                return await response.json()
        except Exception as err:
            _LOGGER.error("Error communicating with MERX Horizon API: %s", err)
            raise

    async def get_device_info(self) -> Dict[str, Any]:
        """Get device information."""
        return await self._request("POST", "/API/Login/DeviceInfo/Get")

    async def get_snapshot(self, channel: str = "CH1") -> bytes:
        """Get a snapshot from the camera."""
        payload = {
            "channel": channel,
            "snapshot_resolution": "640 x 480",
            "reset_session_timeout": False
        }
        try:
            response = await self._request("POST", "/API/Snapshot/Get", json_data=payload)
            if "data" in response and "img_data" in response["data"]:
                return base64.b64decode(response["data"]["img_data"])
        except Exception as err:
            _LOGGER.error("Failed to get snapshot: %s", err)
        return b""

    async def control_ptz(self, channel: str, cmd: str, speed: int = 50) -> Dict[str, Any]:
        """Control PTZ."""
        data = {
            "channel": channel,
            "cmd": cmd,
            "speed": speed
        }
        return await self._request("POST", "/API/PreviewChannel/PTZ/Control", json_data=data)

    async def check_events(self) -> Dict[str, Any]:
        """Poll for events."""
        return await self._request("POST", "/API/Event/Check")

    async def search_recordings(self, channel: str, start_time: str, end_time: str) -> Dict[str, Any]:
        """Search for recordings on the SD card."""
        data = {
            "channel": channel,
            "start_time": start_time,
            "end_time": end_time
        }
        return await self._request("POST", "/API/Playback/SearchRecord/Search", json_data=data)
