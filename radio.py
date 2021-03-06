# Script to run an internet radio by two buttons for
# on / off and
# up / down
#

# include RPi libraries in to Python code
import RPi.GPIO as GPIO
import time
from omxplayer.player import OMXPlayer
import smbus
import calendar
import pylast
import os
import yaml
import datetime
from datetime import timedelta
import json
from pylast import NetworkError, WSError
from lxml import html
import requests
from subprocess import call


def get_secret_djam(website_link):
    now = (datetime.datetime.now() - timedelta(hours=2)) - datetime.datetime(1970, 1, 1)

    page = requests.get(website_link)

    try:

      # print(page.content)
      webpage = html.fromstring(page.content)

      string = webpage.xpath('//table[@class="tablelist-schedule"]//tbody//tr[1]//td[2]//text()')[0].split(' - ', 1)
      if len(string)==1:
        string = webpage.xpath('//table[@class="tablelist-schedule"]//tbody//tr[1]//td[2]//text()')[0].split(' von ', 1)
        if(len(string)==1):
          artist = radio_stations[i]
          track = string
        else:
          artist = string[1]
          track = string[0]
      else:
        artist = string[0]
        track = string[1]

      tracklist = [{"title": track,
                    "artist": artist,
                    "timestamp": now.total_seconds()}]
    except:
      tracklist = [{"title": "try",
                    "artist": "catch",
                    "timestamp": now.total_seconds()}]

    return tracklist


def get_secret_dict(secrets_file="/share/pylast.yaml"):
    if os.path.isfile(secrets_file):
        with open(secrets_file, "r") as f:  # see example_test_pylast.yaml
            doc = yaml.load(f)
    else:
        return dict()
    return doc


class LastFMRadioScrobble():
    """ A class to derive basic connectivities with
    the last.fm API

    On init it connects to the last.fm API with a session key

    Without a session key it will cause a WSError
    """

    def __init__(self, network=None):
        doc = get_secret_dict()

        if network is None:
            f = open('/share/api_key.txt', 'r')
            api_key = str(f.read())
            f.close()
            self.network = pylast.LastFMNetwork(api_key=doc['api_key'], api_secret=doc['api_secret'],
                                                username='zappingseb', password_hash=api_key)
        else:
            self.network = network

    def derive_track_dict(self, station):

        lastfm_user = self.network.get_user(station)
        tracklist = lastfm_user.get_recent_tracks(
            time_from=(calendar.timegm(datetime.datetime.now().utctimetuple()) - 12000),
            time_to=calendar.timegm(datetime.datetime.now().utctimetuple()) - 3600,
            limit=3)
        try:
            if len(tracklist) > 0:
                for i, track in enumerate(tracklist):
                    song_tuples = [(i, " - ".join([track.track.artist.name,
                                                   track.track.title]))
                                   for i, track in enumerate(tracklist)]

                    songlist_form_hidden_data = [{"title": track.track.title,
                                                  "artist": track.track.artist.name,
                                                  "timestamp": track.timestamp}
                                                 for track in tracklist]
            else:
                song_tuples = []
                songlist_form_hidden_data = ""

        except NetworkError:
            song_tuples = [(1, "testsong"),
                           (2, "testsong2")]

            songlist_form_hidden_data = ""

        return songlist_form_hidden_data

    def scrobble_from_json(self, in_dict=[], indeces=list(), has_timestamp=True):
        """From a json of Songs and a list of indeces scrobble songs to the last.fm API

        This uses pylast.scrobble_many to simply scrobbe a list of songs from a jsonstring
        that contains these songs and a list of indeces which songs to take from that list

        :param jsonstring: A json put into a string. the json was compiled by :func:`songlist_form_hidden_data

        :param indeces: A list of integers telling which elements to take from the songlist and scrobble them

        :return: The list of songs as "Artist - Title - Timestamp" to be displayed in the app
        """
        data_list = in_dict

        try:
            data_list[indeces[0]]["timestamp"]
        except KeyError:
            has_timestamp = False

        if has_timestamp:
            tracklist = [{"title": data_list[index]["title"],
                          "artist": data_list[index]["artist"],
                          "timestamp": data_list[index]["timestamp"]}
                         for index in indeces]
        else:
            tracklist = [{"title": data_list[index]["title"],
                          "artist": data_list[index]["artist"],
                          "timestamp": datetime.now()}
                         for index in indeces]
        try:
            self.network.scrobble_many(tracks=tracklist)

            if has_timestamp:
                scrobbling_list = [" - ".join([
                    data_list[index]["artist"],
                    data_list[index]["title"],
                    datetime.datetime.fromtimestamp(int(
                        data_list[index]["timestamp"])
                    ).strftime('%Y-%m-%d %H:%M')
                ]) for index in indeces]
            else:
                scrobbling_list = [" - ".join([
                    data_list[index]["artist"],
                    data_list[index]["title"]]) for index in indeces]
        except (WSError, NetworkError, KeyError) as d:
            print(d)
            scrobbling_list = False

        return scrobbling_list


# Define some device parameters
I2C_ADDR = 0x27  # I2C device address
LCD_WIDTH = 16  # Maximum characters per line

# Define some device constants
LCD_CHR = 1  # Mode - Sending data
LCD_CMD = 0  # Mode - Sending command

LCD_LINE_1 = 0x80  # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0  # LCD RAM address for the 2nd line
LCD_LINE_3 = 0x94  # LCD RAM address for the 3rd line
LCD_LINE_4 = 0xD4  # LCD RAM address for the 4th line

LCD_BACKLIGHT = 0x08  # On
# LCD_BACKLIGHT = 0x00  # Off

ENABLE = 0b00000100  # Enable bit

# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005

# Open I2C interface
#### bus = smbus.SMBus(0)  # Rev 1 Pi uses 0
bus = smbus.SMBus(1)  # Rev 2 Pi uses 1

# instantiate GPIO as an object
GPIO.setmode(GPIO.BCM)


########## LCD Disply usage ##############

def lcd_init():
    # Initialise display
    lcd_byte(0x33, LCD_CMD)  # 110011 Initialise
    lcd_byte(0x32, LCD_CMD)  # 110010 Initialise
    lcd_byte(0x06, LCD_CMD)  # 000110 Cursor move direction
    lcd_byte(0x0C, LCD_CMD)  # 001100 Display On,Cursor Off, Blink Off
    lcd_byte(0x28, LCD_CMD)  # 101000 Data length, number of lines, font size
    lcd_byte(0x01, LCD_CMD)  # 000001 Clear display
    time.sleep(E_DELAY)


def lcd_byte(bits, mode):
    # Send byte to data pins
    # bits = the data
    # mode = 1 for data
    #        0 for command

    bits_high = mode | (bits & 0xF0) | LCD_BACKLIGHT
    bits_low = mode | ((bits << 4) & 0xF0) | LCD_BACKLIGHT

    # High bits
    bus.write_byte(I2C_ADDR, bits_high)
    lcd_toggle_enable(bits_high)

    # Low bits
    bus.write_byte(I2C_ADDR, bits_low)
    lcd_toggle_enable(bits_low)


def lcd_toggle_enable(bits):
    # Toggle enable
    time.sleep(E_DELAY)
    bus.write_byte(I2C_ADDR, (bits | ENABLE))
    time.sleep(E_PULSE)
    bus.write_byte(I2C_ADDR, (bits & ~ENABLE))
    time.sleep(E_DELAY)


def lcd_string(message, line):
    # Send string to display

    message = message.ljust(LCD_WIDTH, " ")

    lcd_byte(line, LCD_CMD)

    for i in range(LCD_WIDTH):
        lcd_byte(ord(message[i]), LCD_CHR)

#----------------------------------------------------------------------------------------------
# K40 class to control K40 controler
class KY040:

    CLOCKWISE = 0
    ANTICLOCKWISE = 1
    DEBOUNCE = 150

    def __init__(self, clockPin, dataPin, switchPin, rotaryCallback, switchCallback):
        #persist values
        self.clockPin = clockPin
        self.dataPin = dataPin
        self.switchPin = switchPin
        self.rotaryCallback = rotaryCallback
        self.switchCallback = switchCallback
        self.status = False

        #setup pins
        GPIO.setup(clockPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(dataPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(switchPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def start(self):
        self.status = True
        GPIO.add_event_detect(self.clockPin, GPIO.FALLING, callback=self._clockCallback, bouncetime=self.DEBOUNCE)
        GPIO.add_event_detect(self.switchPin, GPIO.FALLING, callback=self.switchCallback, bouncetime=self.DEBOUNCE)

    def stop(self):
        self.status = False
        GPIO.remove_event_detect(self.clockPin)
        GPIO.remove_event_detect(self.switchPin)

    def _clockCallback(self, pin):
        if GPIO.input(self.clockPin) == 0:
            self.rotaryCallback(GPIO.input(self.dataPin))
        """
            data = GPIO.input(self.dataPin)
            if data == 1:
                self.rotaryCallback(self.ANTICLOCKWISE)
            else:
                self.rotaryCallback(self.CLOCKWISE)

        self.rotaryCallback(GPIO.input(self.dataPin))
        """

    def _switchCallback(self, pin):
        """
        if GPIO.input(self.switchPin) == 0:
            self.switchCallback()
        """
        self.switchCallback()

def kill_radio():
    if 'radio_player' in locals() or 'radio_player' in globals():
        try:
            radio_player.quit()
        except AttributeError, SystemError:
            call(["pkill", "omxplayer.bin"])
            print(time.strftime("%d-%m-%y %H:%M"))
            print("Player had problem quitting")
        try:
            radio_player.quit()
        except AttributeError, SystemError:
            call(["pkill", "omxplayer.bin"])
            print(time.strftime("%d-%m-%y %H:%M"))
            print("2nd try Player had problem quitting")
    call(["pkill", "omxplayer.bin"])

#--------------------------------------------------------------------------------------------------
# Define radio stations
#                       0        1               2                   3            4       5       6         7
radio_stations = ["  egoFM", "  mdrInfo", "  Deutschlandfunk", "  JazzRadio", "  DJAM", "  BBC6", "  BR2", "  FM4"]

radio_urls = [
    "http://mp3ad.egofm.c.nmdn.net/ps-egofm_128/livestream.mp3",
    "http://mdr-284340-0.cast.mdr.de/mdr/284340/0/mp3/high/stream.mp3",
    "http://st01.dlf.de/dlf/01/128/mp3/stream.mp3",
    "http://jazz-wr03.ice.infomaniak.ch/jazz-wr03-128.mp3",
    "http://ledjamradio.ice.infomaniak.ch/ledjamradio.mp3?x=0.8474474848604379",
    "http://bbcmedia.ic.llnwd.net/stream/bbcmedia_6music_mf_p",
    "http://br-br2-sued.cast.addradio.de/br/br2/sued/mp3/128/stream.mp3",
    "http://mp3stream1.apasf.apa.at"
]

website_urls = [
    "http://onlineradiobox.com/de/ego/playlist/?cs=fr.ledjamra",  # egoFM
    "http://onlineradiobox.com/de/mdraktuell/playlist/?cs=fr.ledjamra",  # mdrInfo
    "http://onlineradiobox.com/de/deutschlandfunk/playlist/?cs=fr.ledjamra",  # DLF
    "http://onlineradiobox.com/fr/jazzradioneworleans/playlist/?cs=fr.ledjamra",  # Jazzradio
    "http://onlineradiobox.com/fr/ledjamra/playlist/?lang=en",  # DJAM
    "",  # bbc6,
    "",  # BR2
    ""  # FM4

]

# Define global variables

global i

lcd_init()
f = open('/share/lastplay.txt', 'r')
i = int(f.read())
f.close()

already_playing = False
choosing = False
stored_timestamp = '0'
stored_djam = ""
sleep_count = 0

GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)

CLOCKPIN = 22
DATAPIN = 23
SWITCHPIN = 24

def rotaryChange(direction):
  time.sleep(0.1)
  if direction == 0:
    global i
    if i != 0:
        i -= 1
    lcd_string(radio_stations[i], LCD_LINE_1)
  else:
    global i

    if i < (len(radio_stations)-1):
        i += 1
    lcd_string(radio_stations[i], LCD_LINE_1)

def switchPressed(pin):
    lcd_init()
    global i
    lcd_string("  Wait...", LCD_LINE_2)
    lcd_string(radio_stations[i], LCD_LINE_1)

k40 = KY040(CLOCKPIN, DATAPIN, SWITCHPIN, rotaryChange, switchPressed)

while True:

    # read out on off button
    # print(GPIO.input(18))
    button_switch = GPIO.input(18)

    if button_switch:
        # Switch off radio
        already_playing = False
        
        kill_radio()
            
        if not choosing:
			lcd_string("  Choosing...", LCD_LINE_2)
			choosing = True

			if not k40.status:
				k40.start()

			#button_choose = GPIO.input(17)
			#if button_choose:
			#    if i >= (len(radio_stations) - 1):

			#        i = (len(radio_stations) - 1)
			#    else:
			#        i = i + 1
			#lcd_string(radio_stations[i], LCD_LINE_1)
			#else:
			#    if i != 0:
			#        i = i - 1
			#    lcd_string(radio_stations[i], LCD_LINE_1)

    else:

        k40.stop()
        choosing = False

        # Start playing
        if not already_playing:
            kill_radio()
            try:
                lcd_string("  Wait...", LCD_LINE_2)
                radio_player = OMXPlayer(radio_urls[i],args=['-b --vol -2000'])
                time.sleep(1)
                radio_player.set_volume(-1000)
                already_playing = True
            except Exception,e:
                print(time.strftime("%d-%m-%y %H:%M"))
                print(str(e))
                print("problem init")
                kill_radio()
                lcd_string("  PLEASE RESTART ", LCD_LINE_2)
                time.sleep(5)
            f = open('/share/lastplay.txt', 'w')
            f.write(str(i))
            f.close()
            lcd_string(radio_stations[i], LCD_LINE_1)
        else:
            try:
                lcd_string(" ".join(["  PLAY", time.strftime("%H:%M")]), LCD_LINE_2)
                if(radio_player.volume()==0):
                    radio_player.set_volume(-2000)
            except:
                print(time.strftime("%d-%m-%y %H:%M"))
                print("No radioplayer found")
                lcd_string("  ERROR  ", LCD_LINE_2)
                already_playing = False
            # Radio Station BBC
            if i == 5:
                # Increase sleep count
                sleep_count = sleep_count + 1
                # After 20 seconds try scrobbling
                if sleep_count > 10:

                    # reset sleep count
                    sleep_count = 0

                    # Connect to last.fm
                    last_fm_scrobble = LastFMRadioScrobble()

                    # Derive bbc tracks
                    last_tracks = last_fm_scrobble.derive_track_dict("bbc6music")

                    # Check last played track timestamp
                    if last_tracks[0]["timestamp"] != stored_timestamp:
                        # Reset last timestamp to now
                        stored_timestamp = last_tracks[0]["timestamp"]

                        print(stored_timestamp)

                        # scrobble last track
                        scrob_list = last_fm_scrobble.scrobble_from_json(in_dict=last_tracks, indeces=[0],
                                                                         has_timestamp=True)
                        print(scrob_list)
            # Scrobble by http://onlineradiobox.com/
            elif i == 4 or i == 0 or i == 1 or i == 2 or i == 3:
                # Increase sleep count
                sleep_count = sleep_count + 1
                # After 20 seconds try scrobbling
                if sleep_count > 40:
                    try:
                        # reset sleep count
                        sleep_count = 0

                        # Connect to last.fm
                        last_fm_scrobble = LastFMRadioScrobble()

                        # Derive djam tracks
                        last_tracks = get_secret_djam(website_urls[i])

                        # Check last played track timestamp
                        if last_tracks[0]["title"] != stored_djam and last_tracks[0]["title"]!="try":
                            # Reset last timestamp to now
                            stored_djam = last_tracks[0]["title"]

                            print(stored_djam)

                            # scrobble last track
                            scrob_list = last_fm_scrobble.scrobble_from_json(in_dict=last_tracks, indeces=[0],
                                                                             has_timestamp=True)
                            print(scrob_list)
                    except:
                        print(" ".join(["last.fm error on ", time.strftime("%H:%M"), radio_urls[i]]))

    time.sleep(0.5)

