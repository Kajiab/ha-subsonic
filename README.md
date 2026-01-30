# Subsonic Source
My custom HA-Subsonic integration modified from original
Due to code havn't self media player, it' just link between Navidrome and home assistant.
But the problem is my nest mini not support Flac. So, need to transcode to mp3.

This is work flow   Navidrome --> transcode to mp3 ---> ha-subsonic --> mini-media player  --> google nest mini

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
