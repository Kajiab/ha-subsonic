from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_URL, CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, LOGGER
from .subsonicApi import SubsonicApi


class CannotConnect(HomeAssistantError):
    """Error to indicate cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate bad authentication."""


DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate user input by calling SubsonicApi.ping()."""

    session = async_get_clientsession(hass)
    api = SubsonicApi(
        session=session,
        userAgent="HomeAssistant",
        config={
            "url": data[CONF_URL],
            "user": data[CONF_USERNAME],
            "password": data[CONF_PASSWORD],
        },
    )

    try:
        ok = await api.ping()
    except Exception as err:
        LOGGER.error("Subsonic: Cannot connect: %s", err)
        raise CannotConnect from err

    if not ok:
        # ถ้า ping แล้วไม่ ok แต่ไม่มี exception ให้ถือว่า connect ไม่ได้เหมือนกัน
        raise CannotConnect

    return data


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Subsonic."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # ป้องกันเพิ่มซ้ำ
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()

            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                # สร้าง config entry
                return self.async_create_entry(
                    title="Subsonic",
                    data={
                        # เก็บทั้งแบบ generic และแบบที่ SubsonicApi ใช้เดิม
                        CONF_URL: info[CONF_URL],
                        "url": info[CONF_URL],
                        "user": info[CONF_USERNAME],
                        "password": info[CONF_PASSWORD],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reconfiguration via UI (optional)."""
        # ตอนนี้ยังไม่ทำ options แยก ใช้ user step ซ้ำไปก่อน
        return await self.async_step_user(user_input)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for Subsonic (future use)."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        return self.async_show_form(step_id="init")