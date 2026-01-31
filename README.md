# Subsonic Source
My custom HA-Subsonic integration modified from original
Due to code havn't self media player, it' just link between Navidrome and home assistant.
But the problem is my nest mini not support Flac. So, need to transcode to mp3.

This is work flow   Navidrome --> transcode to mp3 ---> ha-subsonic --> mini-media player  --> google nest mini (need do port forward and DNS due to Nest need HTTPS://)
But if you want to play on device (tablet, laptop or mobilephonr), it's can play file.

Example for using

https://github.com/Kajiab/ha-subsonic/blob/master/Example.yaml
