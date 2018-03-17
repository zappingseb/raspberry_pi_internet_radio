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

## Linux Setup

Install omxplayer

store the `radio.py` script into `/share`

insert into `/etc/rc.local`
```
sudo python /share/radio.py
```

## Photos of my radio

![Radio1](https://raw.githubusercontent.com/zappingseb/raspberry_pi_internet_radio/master/images/ima3.jpeg)

![Radio2](https://raw.githubusercontent.com/zappingseb/raspberry_pi_internet_radio/master/images/ima1.jpg)

![Radio3](https://raw.githubusercontent.com/zappingseb/raspberry_pi_internet_radio/master/images/ima2.jpeg)
