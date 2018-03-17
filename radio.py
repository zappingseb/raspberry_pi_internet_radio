# Script to run an internet radio by two buttons for
# on / off and
# up / down
#

# include RPi libraries in to Python code
import RPi.GPIO as GPIO
import time
from omxplayer.player import OMXPlayer
import smbus
import time

# Define some device parameters
I2C_ADDR  = 0x27 # I2C device address
LCD_WIDTH = 16   # Maximum characters per line

# Define some device constants
LCD_CHR = 1 # Mode - Sending data
LCD_CMD = 0 # Mode - Sending command

LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line
LCD_LINE_3 = 0x94 # LCD RAM address for the 3rd line
LCD_LINE_4 = 0xD4 # LCD RAM address for the 4th line

LCD_BACKLIGHT  = 0x08  # On
#LCD_BACKLIGHT = 0x00  # Off

ENABLE = 0b00000100 # Enable bit

# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005

#Open I2C interface
#### bus = smbus.SMBus(0)  # Rev 1 Pi uses 0
bus = smbus.SMBus(1) # Rev 2 Pi uses 1

# instantiate GPIO as an object
GPIO.setmode(GPIO.BCM)

########## LCD Disply usage ##############

def lcd_init():
  # Initialise display
  lcd_byte(0x33,LCD_CMD) # 110011 Initialise
  lcd_byte(0x32,LCD_CMD) # 110010 Initialise
  lcd_byte(0x06,LCD_CMD) # 000110 Cursor move direction
  lcd_byte(0x0C,LCD_CMD) # 001100 Display On,Cursor Off, Blink Off
  lcd_byte(0x28,LCD_CMD) # 101000 Data length, number of lines, font size
  lcd_byte(0x01,LCD_CMD) # 000001 Clear display
  time.sleep(E_DELAY)

def lcd_byte(bits, mode):
  # Send byte to data pins
  # bits = the data
  # mode = 1 for data
  #        0 for command

  bits_high = mode | (bits & 0xF0) | LCD_BACKLIGHT
  bits_low = mode | ((bits<<4) & 0xF0) | LCD_BACKLIGHT

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
  bus.write_byte(I2C_ADDR,(bits & ~ENABLE))
  time.sleep(E_DELAY)

def lcd_string(message,line):
  # Send string to display

  message = message.ljust(LCD_WIDTH," ")

  lcd_byte(line, LCD_CMD)

  for i in range(LCD_WIDTH):
    lcd_byte(ord(message[i]),LCD_CHR)

# Define radio stations

radio_stations = ["  egoFM", "  mdrInfo", "  Deutschlandfunk", "  JazzRadio", "  BBC6","  BR2","  FM4"]

radio_urls = [
"http://mp3ad.egofm.c.nmdn.net/ps-egofm_128/livestream.mp3",
"http://mdr-284340-0.cast.mdr.de/mdr/284340/0/mp3/high/stream.mp3",
"http://st01.dlf.de/dlf/01/128/mp3/stream.mp3",
"http://jazz-wr03.ice.infomaniak.ch/jazz-wr03-128.mp3",
    "http://bbcmedia.ic.llnwd.net/stream/bbcmedia_6music_mf_p",
"http://br-br2-sued.cast.addradio.de/br/br2/sued/mp3/128/stream.mp3",
    "http://mp3stream1.apasf.apa.at"
]


# Define global variables

lcd_init()
i=0

already_playing = False

GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)

while True:

    # read out on off button
   print(GPIO.input(18))
   button_switch = GPIO.input(18)
   print("--")


   if button_switch:
     # Switch off radio
     already_playing = False
     if 'radio_player' in locals() or 'radio_player' in globals():
       try:
           radio_player.quit()
       except AttributeError, SystemError:
           print("Player had problem quitting")

      # Switch channels by up/down button
     lcd_string("  Choosing...", LCD_LINE_2)
     button_choose = GPIO.input(17)
     if button_choose:
         if i>=(len(radio_stations)-1):
             i=(len(radio_stations)-1)
         else:
            i=i+1
         lcd_string(radio_stations[i], LCD_LINE_1)
     else:
         if i != 0:
            i=i-1
         lcd_string(radio_stations[i], LCD_LINE_1)

   else:
    # Start playing
    print("PLAYMODE")
    if not already_playing:
        radio_player = OMXPlayer(radio_urls[i])
        already_playing = True
        lcd_string(radio_stations[i], LCD_LINE_1)
    lcd_string(" ".join(["  PLAY", time.strftime("%H:%M")]), LCD_LINE_2)

   print("\n")
   time.sleep(2)
