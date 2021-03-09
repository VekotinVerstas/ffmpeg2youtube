# ffmpeg2youtube
Live video feed manipulation with ffmpg (add logos, sensor and other text info to stream ) used in Urban Eco Islands project.

clone to /usr/local/bin/ or fix path at least in crontab entries

ffmpeg2youtube is simple script to call ffmpeg to read from camera rstp stream, modify stream and to send it to youtube

ais directory has ais.py script to find passing ship info to ais.txt file. ais.txt is used to feed info to ffmpeg

uiras.py is collecting Uiras (local water temp) and local weather station info to sensor.txt file whis is again read by ffmpeg to insert sensor info to stream.

