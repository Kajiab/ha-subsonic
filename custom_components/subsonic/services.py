from __future__ import annotations

import logging
from typing import List

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.service import async_extract_entity_ids
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.components.media_player import DOMAIN as MP_DOMAIN

from .const import DOMAIN
from .subsonicApi import SubsonicApi  # api ของคุณเอง

_LOGGER = logging.getLogger(__name__)


async def async_register_services(hass: HomeAssistant, api: SubsonicApi) -> None:
    """Register Subsonic/Navidrome services."""

    # ---- core: play_media ----
    async def async_handle_play_media(call: ServiceCall) -> None:
        """Handle subsonic.play_media service."""

        # 1) target media_player(s)
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

        # 2) ขอ list tracks จาก SubsonicApi ของคุณ
        # NOTE: ตรงนี้ต้องไป match กับ method จริงของ SubsonicApi
        #       ผมสมมติว่าคุณจะเพิ่ม method ชื่อ async_resolve_tracks
        try:
            tracks = await api.async_resolve_tracks(
                media_type=media_type,
                media_id=media_id,
                shuffle=shuffle,
            )
        except AttributeError:
            _LOGGER.error(
                "SubsonicApi.async_resolve_tracks is not implemented yet. "
                "Please implement this method to resolve media_type+id → tracks."
            )
            return
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

        # 3) ถ้าไม่ enqueue → clear queue ฝั่ง api (ถ้าคุณมี)
        if not enqueue:
            if hasattr(api, "async_clear_queue"):
                try:
                    await api.async_clear_queue()
                except Exception as err:
                    _LOGGER.debug("Error clearing Subsonic queue: %s", err)

        # 4) เก็บ queue ฝั่ง api (optional)
        if hasattr(api, "async_set_current_queue"):
            try:
                await api.async_set_current_queue(tracks)
            except Exception as err:
                _LOGGER.debug("Error setting Subsonic queue: %s", err)

        # 5) เอา track แรกไปเล่นบน media_player เป้าหมาย
        first_track = tracks[0]

        # สมมติ track object ของคุณมี key stream_url / mime_type
        stream_url = getattr(first_track, "stream_url", None)
        mime_type = getattr(first_track, "mime_type", None) or "music"

        if not stream_url:
            _LOGGER.error("First track has no stream_url, cannot play")
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

    # Register core service ถ้ายังไม่มี
    if not hass.services.has_service(DOMAIN, "play_media"):
        hass.services.async_register(DOMAIN, "play_media", async_handle_play_media)