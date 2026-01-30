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

    # ------------------------------------------------------------------
    # CORE: subsonic.play_media
    # ------------------------------------------------------------------
    async def async_handle_play_media(call: ServiceCall) -> None:
        """Handle subsonic.play_media service."""

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

        # resolve track list ผ่าน SubsonicApi
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

        # TODO: ถ้าคุณอยากทำ queue management ฝั่ง integration
        # สามารถเก็บ tracks ลง hass.data[DOMAIN]["queue"] ที่นี่ได้

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

    # ------------------------------------------------------------------
    # WRAPPERS: play_album / play_playlist / play_track / play_artist
    # ------------------------------------------------------------------

    async def async_handle_play_album(call: ServiceCall) -> None:
        """Handle subsonic.play_album – wrapper around play_media."""
        entity_ids = async_extract_entity_ids(hass, call)
        if not entity_ids:
            _LOGGER.warning("subsonic.play_album called without target media_player")
            return

        album_id: str = call.data.get("album_id")
        shuffle: bool = call.data.get("shuffle", False)
        enqueue: bool = call.data.get("enqueue", False)

        if not album_id:
            _LOGGER.warning("subsonic.play_album missing album_id")
            return

        data = {
            ATTR_ENTITY_ID: entity_ids,
            "media_content_type": "album",
            "media_content_id": album_id,
            "shuffle": shuffle,
            "enqueue": enqueue,
        }

        await hass.services.async_call(
            DOMAIN,
            "play_media",
            data,
            blocking=False,
        )

    async def async_handle_play_playlist(call: ServiceCall) -> None:
        """Handle subsonic.play_playlist – wrapper around play_media."""
        entity_ids = async_extract_entity_ids(hass, call)
        if not entity_ids:
            _LOGGER.warning("subsonic.play_playlist called without target media_player")
            return

        playlist_id: str = call.data.get("playlist_id")
        shuffle: bool = call.data.get("shuffle", False)
        enqueue: bool = call.data.get("enqueue", False)

        if not playlist_id:
            _LOGGER.warning("subsonic.play_playlist missing playlist_id")
            return

        data = {
            ATTR_ENTITY_ID: entity_ids,
            "media_content_type": "playlist",
            "media_content_id": playlist_id,
            "shuffle": shuffle,
            "enqueue": enqueue,
        }

        await hass.services.async_call(
            DOMAIN,
            "play_media",
            data,
            blocking=False,
        )

    async def async_handle_play_track(call: ServiceCall) -> None:
        """Handle subsonic.play_track – wrapper around play_media."""
        entity_ids = async_extract_entity_ids(hass, call)
        if not entity_ids:
            _LOGGER.warning("subsonic.play_track called without target media_player")
            return

        track_id: str = call.data.get("track_id")
        enqueue: bool = call.data.get("enqueue", False)

        if not track_id:
            _LOGGER.warning("subsonic.play_track missing track_id")
            return

        data = {
            ATTR_ENTITY_ID: entity_ids,
            "media_content_type": "track",
            "media_content_id": track_id,
            "enqueue": enqueue,
        }

        await hass.services.async_call(
            DOMAIN,
            "play_media",
            data,
            blocking=False,
        )

    async def async_handle_play_artist(call: ServiceCall) -> None:
        """Handle subsonic.play_artist – wrapper around play_media."""
        entity_ids = async_extract_entity_ids(hass, call)
        if not entity_ids:
            _LOGGER.warning("subsonic.play_artist called without target media_player")
            return

        artist_id: str = call.data.get("artist_id")
        shuffle: bool = call.data.get("shuffle", True)
        enqueue: bool = call.data.get("enqueue", False)

        if not artist_id:
            _LOGGER.warning("subsonic.play_artist missing artist_id")
            return

        data = {
            ATTR_ENTITY_ID: entity_ids,
            "media_content_type": "artist",
            "media_content_id": artist_id,
            "shuffle": shuffle,
            "enqueue": enqueue,
        }

        await hass.services.async_call(
            DOMAIN,
            "play_media",
            data,
            blocking=False,
        )

    # ------------------------------------------------------------------
    # RANDOM ALBUM
    # ------------------------------------------------------------------

    async def async_handle_play_random_album(call: ServiceCall) -> None:
        """Handle subsonic.play_random_album – pick album then call play_media."""

        entity_ids = async_extract_entity_ids(hass, call)
        if not entity_ids:
            _LOGGER.warning(
                "subsonic.play_random_album called without target media_player"
            )
            return

        genre: str | None = call.data.get("genre")
        year_from = call.data.get("year_from")
        year_to = call.data.get("year_to")
        shuffle: bool = call.data.get("shuffle", True)
        enqueue: bool = call.data.get("enqueue", False)

        # เบื้องต้น: ใช้ getAlbums() แบบที่คุณมีอยู่ แล้ว random จาก list นั้น
        try:
            albums = await api.getAlbums()
        except Exception as err:
            _LOGGER.error("Error fetching albums for random_album: %s", err)
            return

        if not albums:
            _LOGGER.warning("subsonic.play_random_album: no albums available")
            return

        # filter year ถ้ามี field year ใน album
        def _match_year(a: dict) -> bool:
            if not year_from and not year_to:
                return True
            try:
                year = int(a.get("year", 0))
            except Exception:
                return False
            if year_from and year < year_from:
                return False
            if year_to and year > year_to:
                return False
            return True

        candidates = [a for a in albums if _match_year(a)]

        # TODO: filter by genre ถ้าคุณ map genre กับ album ได้ (ตอนนี้ยังไม่รู้ schema แน่นอน)
        # ถ้าคุณมี field "genre" บน album ก็ใส่ filter ตรงนี้ได้เลย
        if genre:
            g = genre.lower()
            candidates = [
                a
                for a in candidates
                if g in str(a.get("genre", "")).lower()
            ]

        if not candidates:
            _LOGGER.warning("subsonic.play_random_album: no matching albums after filter")
            return

        import random

        album = random.choice(candidates)
        album_id = album.get("id")
        if not album_id:
            _LOGGER.warning("subsonic.play_random_album: chosen album has no id")
            return

        _LOGGER.debug("Random album chosen: %s (%s)", album.get("name"), album_id)

        data = {
            ATTR_ENTITY_ID: entity_ids,
            "media_content_type": "album",
            "media_content_id": album_id,
            "shuffle": shuffle,
            "enqueue": enqueue,
        }

        await hass.services.async_call(
            DOMAIN,
            "play_media",
            data,
            blocking=False,
        )

    # ------------------------------------------------------------------
    # LIBRARY / MAINTENANCE (stubs – log only for now)
    # ------------------------------------------------------------------

    async def async_handle_sync_library(call: ServiceCall) -> None:
        """Handle subsonic.sync_library."""
        full = call.data.get("full", False)
        _LOGGER.info("subsonic.sync_library called (full=%s)", full)
        # TODO: implement sync logic (pull all albums/tracks/playlists, update sensors etc.)

    async def async_handle_refresh_recent(call: ServiceCall) -> None:
        """Handle subsonic.refresh_recent."""
        _LOGGER.info("subsonic.refresh_recent called")
        # TODO: implement refreshing recently added sensor(s)

    async def async_handle_refresh_playlists(call: ServiceCall) -> None:
        """Handle subsonic.refresh_playlists."""
        _LOGGER.info("subsonic.refresh_playlists called")
        # TODO: implement refreshing playlists cache / entities

    async def async_handle_refresh_random_cache(call: ServiceCall) -> None:
        """Handle subsonic.refresh_random_cache."""
        _LOGGER.info("subsonic.refresh_random_cache called")
        # TODO: implement caching of random items if needed

    # ------------------------------------------------------------------
    # REGISTER ALL SERVICES
    # ------------------------------------------------------------------

    if not hass.services.has_service(DOMAIN, "play_media"):
        hass.services.async_register(DOMAIN, "play_media", async_handle_play_media)

    if not hass.services.has_service(DOMAIN, "play_album"):
        hass.services.async_register(DOMAIN, "play_album", async_handle_play_album)

    if not hass.services.has_service(DOMAIN, "play_playlist"):
        hass.services.async_register(DOMAIN, "play_playlist", async_handle_play_playlist)

    if not hass.services.has_service(DOMAIN, "play_track"):
        hass.services.async_register(DOMAIN, "play_track", async_handle_play_track)

    if not hass.services.has_service(DOMAIN, "play_artist"):
        hass.services.async_register(DOMAIN, "play_artist", async_handle_play_artist)

    if not hass.services.has_service(DOMAIN, "play_random_album"):
        hass.services.async_register(
            DOMAIN, "play_random_album", async_handle_play_random_album
        )

    if not hass.services.has_service(DOMAIN, "sync_library"):
        hass.services.async_register(DOMAIN, "sync_library", async_handle_sync_library)

    if not hass.services.has_service(DOMAIN, "refresh_recent"):
        hass.services.async_register(
            DOMAIN, "refresh_recent", async_handle_refresh_recent
        )

    if not hass.services.has_service(DOMAIN, "refresh_playlists"):
        hass.services.async_register(
            DOMAIN, "refresh_playlists", async_handle_refresh_playlists
        )

    if not hass.services.has_service(DOMAIN, "refresh_random_cache"):
        hass.services.async_register(
            DOMAIN, "refresh_random_cache", async_handle_refresh_random_cache
        )
