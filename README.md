# Subsonic Source
My custom HA-Subsonic integration

This is work flow   Navidrome --> transcode to mp3 ---> ha-subsonic --> mini-media player

Example for using

type: custom:mushroom-media-player-card
entity: media_player.media_player_living_room
use_media_info: true
show_volume: false
collapsible_controls: true
artwork: none
icon: mdi:music-circle

card_mod:
  style: |
    mushroom-media-player-card {
      --media-player-artwork: url("{{ states('sensor.last_album_art') }}");
    }
