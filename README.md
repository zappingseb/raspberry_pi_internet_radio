## Description

This script is used for an internet radio inside an old radio.

The internet radio has a display showing the channels. The display was set up by

https://tutorials-raspberrypi.de/hd44780-lcd-display-per-i2c-mit-dem-raspberry-pi-ansteuern/

Additionally it has two switches set up as explained in:

http://razzpisampler.oreilly.com/ch07.html

It uses OMX player to play music after

http://python-omxplayer-wrapper.readthedocs.io

## Basic functionality

* Switch ON
   * if not `already_playing`
     * Start OmxPlayer with radio channel of choice
     * set `already_playing` to *true*
* Switch OFF
   * try to switch OFF OmxPlayer
   * set `already_playing` to *false*
   + switch_2 UP
     * increase the radio channel by 1
     * display the radio channel name
   * switch_2 DOWN
     * reduce the radio channel by 1
     * display the radio channel name
