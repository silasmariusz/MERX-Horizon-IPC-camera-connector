"""
Copyright (c) 2026, Silas Mariusz Grzybacz

Config flow for MERX Horizon IPC Camera integration.
"""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, CONF_RTSP_PORT, DEFAULT_PORT, DEFAULT_RTSP_PORT

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_RTSP_PORT, default=DEFAULT_RTSP_PORT): int,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)

class MerxHorizonConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MERX Horizon."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> config_entries.FlowResult:
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            # TODO: Validate connection to the camera here
            return self.async_create_entry(title=user_input[CONF_HOST], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
