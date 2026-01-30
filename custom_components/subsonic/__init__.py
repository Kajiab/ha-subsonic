from __future__ import annotations

from homeassistant.const import __version__
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, LOGGER
from .subsonicApi import SubsonicApi
from .services import async_register_services  # ← ไฟล์ใหม่ที่เราจะสร้าง


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Subsonic/Navidrome (ha-subsonic) from a config entry."""

    session = async_get_clientsession(hass)
    user_agent = f"Home Assistant/{__version__}"

    LOGGER.info("Setting up Subsonic integration")

    api = SubsonicApi(
        session=session,
        userAgent=user_agent,
        config=entry.data,
    )

    # ทดสอบ ping server
    try:
        result = await api.ping()
    except Exception as err:
        # ถ้า ping ไม่สำเร็จ ให้ raise ConfigEntryNotReady เพื่อให้ HA ลองใหม่ทีหลัง
        raise ConfigEntryNotReady("Could not connect to Subsonic API") from e

    # เก็บ api ลงใน hass.data (รองรับหลาย config entry ในอนาคต)
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
    }

    # Register services (play_media, play_album, play_playlist, ...)
    await async_register_services(hass, api)

    return result


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # ลบข้อมูลของ entry นี้ออกจาก hass.data
    if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
        del hass.data[DOMAIN][entry.entry_id]

    # ถ้าคุณอยากจะ unregister services ตอน unload entry สุดท้าย
    # สามารถเช็ค len(hass.data[DOMAIN]) == 0 แล้ว unregister ที่นี่ได้
    # (ตอนนี้ยังไม่ทำ เพื่อความง่าย)
    return True
