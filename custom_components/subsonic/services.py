from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.service import async_extract_entity_ids
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.components.media_player import DOMAIN as MP_DOMAIN

from .const import DOMAIN
from .subsonicApi import SubsonicApi

_LOGGER = logging.getLogger(__name__)


async def async_register_services(hass: HomeAssistant, api: SubsonicApi) -> None:
    """Register Subsonic/Navidrome services."""

    async def async_handle_play_media(call: ServiceCall) -> None:
        """Handle subsonic.play_media service."""

        # 1) ดึง media_player เป้าหมายจาก target
        entity_ids = async_extract_entity_ids(hass, call)
        if not entity_ids:
            _LOGGER.warning("subsonic.play_media called without target media_player")
            return

        media_type: str = call.data.get("media_content_type")
        media_id: str = call.data.get("media_content_id")
        shuffle: bool = call.data.get("shuffle", False)
        enqueue: bool = call.data.get("enqueue", False)

        if not media_type or not media_id:
            _LOGGER.warning(
                "subsonic.play_media missing media_content_type or media_content_id"
            )
            return

        _LOGGER.debug(
            "subsonic.play_media: type=%s id=%s shuffle=%s enqueue=%s targets=%s",
            media_type,
            media_id,
            shuffle,
            enqueue,
            entity_ids,
        )

        # 2) resolve track list ผ่าน SubsonicApi.async_resolve_tracks()
        try:
            tracks = await api.async_resolve_tracks(
                media_type=media_type,
                media_id=media_id,
                shuffle=shuffle,
            )
        except Exception as err:
            _LOGGER.error("Error resolving tracks from Subsonic: %s", err)
            return

        if not tracks:
            _LOGGER.warning(
                "subsonic.play_media: no tracks resolved for type=%s id=%s",
                media_type,
                media_id,
            )
            return

        # 3) queue management (optional – ตอนนี้ยังไม่มี queue entity ก็ข้ามไปก่อน)
        # ถ้าคุณอยากใช้ queue ฝั่ง HA เอง สามารถเก็บ tracks ลง hass.data[DOMAIN]["queue"] ตรงนี้ได้

        # 4) เล่น track แรกบน media_player เป้าหมายทุกตัว
        first_track = tracks[0]
        stream_url = first_track.get("stream_url")
        mime_type = first_track.get("mime_type", "music")

        if not stream_url:
            _LOGGER.error(
                "First track has no stream_url (media_type=%s id=%s)",
                media_type,
                media_id,
            )
            return

        for entity_id in entity_ids:
            service_data = {
                ATTR_ENTITY_ID: entity_id,
                "media_content_id": stream_url,
                "media_content_type": mime_type,
            }

            _LOGGER.debug(
                "Calling media_player.play_media on %s with url=%s type=%s",
                entity_id,
                stream_url,
                mime_type,
            )

            await hass.services.async_call(
                MP_DOMAIN,
                "play_media",
                service_data,
                blocking=False,
            )

    # register service
    if not hass.services.has_service(DOMAIN, "play_media"):
        hass.services.async_register(DOMAIN, "play_media", async_handle_play_media)
