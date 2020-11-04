#!/usr/bin/python
#
# PiTextReader - Raspberry Pi Printed Text-to-Speech Reader
#
# Allows sight impaired person to have printed text read using
# OCR and text-to-speech.
#
# Normally run by pi crontab at bootup
# Turn off by commenting out @reboot... using $ crontab -e; sudo reboot
# Manually run using $ python pitextreader.py
#
# This is a simplistic (i.e. not pretty) python program
# Just runs cmd-line pgms raspistill, tesseract-ocr, flite to do all the work
#
# Version 1.0 2018.02.10 - initial release - rgrokett
# v1.1 - added some text cleanup to improve reading
# v1.2 - removed tabs
#
# http://kd.grokett.com/
#
# License: GPLv3, see: www.gnu.org/licenses/gpl-3.0.html
#

import RPi.GPIO as GPIO
import os, sys
import logging
import subprocess
import threading
import time
from pygame import mixer
# from rpi_ws281x import ws, Color, Adafruit_NeoPixel

# LED strip configuration:
LED_1_COUNT = 30        # Number of LED pixels.
LED_1_PIN = 18          # GPIO pin connected to the pixels (must support PWM! GPIO 13 and 18 on RPi 3).
LED_1_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_1_DMA = 10          # DMA channel to use for generating signal (Between 1 and 14)
LED_1_BRIGHTNESS = 128  # Set to 0 for darkest and 255 for brightest
LED_1_INVERT = False    # True to invert the signal (when using NPN transistor level shift)
LED_1_CHANNEL = 0       # 0 or 1
# LED_1_STRIP = ws.WS2811_STRIP_GRB

LED_2_COUNT = 15        # Number of LED pixels.
LED_2_PIN = 13          # GPIO pin connected to the pixels (must support PWM! GPIO 13 or 18 on RPi 3).
LED_2_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_2_DMA = 11          # DMA channel to use for generating signal (Between 1 and 14)
LED_2_BRIGHTNESS = 128  # Set to 0 for darkest and 255 for brightest
LED_2_INVERT = False    # True to invert the signal (when using NPN transistor level shift)
LED_2_CHANNEL = 1       # 0 or 1
# LED_2_STRIP = ws.WS2811_STRIP_GRB

##### USER VARIABLES
DEBUG   = 0 # Debug 0/1 off/on (writes to debug.log)
SPEED   = 1.0   # Speech speed, 0.5 - 2.0
VOLUME  = 90    # Audio volume

# OTHER SETTINGS
SOUNDS  = "/home/pi/PiTextReader/sounds/" # Directory for sound effect(s)
CAMERA  = "raspistill -cfx 128:128 --awb auto -rot 180 -t 500 -o /tmp/image.jpg"

# GPIO BUTTONS
BTN1    = 24    # The button!
LED     = 18    # The button's LED!


# TEXT READING CMD
ESPEAK_VOICE = "mb/mb-fr4"
ESPEAK_CMD = ["/usr/bin/espeak-ng", "-v", ESPEAK_VOICE, "-f", "/tmp/text.txt", "&"]

### FUNCTIONS
# Thread controls for background processing
class RaspberryThread(threading.Thread):
    def __init__(self, function):
        self.running = False
        self.function = function
        super(RaspberryThread, self).__init__()

    def start(self):
        self.running = True
        super(RaspberryThread, self).start()

    def run(self):
        while self.running:
            self.function()

    def stop(self):
        self.running = False

# NEOPIXELS INIT
# strip1 = Adafruit_NeoPixel(LED_1_COUNT, LED_1_PIN, LED_1_FREQ_HZ,
#                                LED_1_DMA, LED_1_INVERT, LED_1_BRIGHTNESS,
#                                LED_1_CHANNEL, LED_1_STRIP)

# strip2 = Adafruit_NeoPixel(LED_2_COUNT, LED_2_PIN, LED_2_FREQ_HZ,
#                                LED_2_DMA, LED_2_INVERT, LED_2_BRIGHTNESS,
#                                LED_2_CHANNEL, LED_2_STRIP)

# # Intialize the library (must be called once before other functions).
# strip1.begin()
# strip2.begin()


# LED ON/OFF
def led(val):
    logger.info('led('+str(val)+')')
    if val:
       GPIO.output(LED,GPIO.HIGH)
    else:
       GPIO.output(LED,GPIO.LOW)

# PLAY SOUND
def sound(val): # Play a sound
    logger.info('sound()')
    time.sleep(0.2)
    cmd = "/usr/bin/aplay -q "+str(val)
    logger.info(cmd)
    os.system(cmd)
    return

# SPEAK STATUS
def speak(val): # TTS Speak
    logger.info('speak()')
    #cmd = "/usr/bin/flite -voice awb --setf duration_stretch="+str(SPEED)+" -t \""+str(val)+"\""
    cmd = 'spd-say -l fr "%s"' % str(val)
    logger.info(cmd)
    os.system(cmd)
    return

# SET VOLUME
def volume(val): # Set Volume for Launch
    logger.info('volume('+str(val)+')')
    vol = int(val)
    cmd = "sudo amixer -q sset PCM,0 "+str(vol)+"%"
    logger.info(cmd)
    os.system(cmd)
    return

# TEXT CLEANUP
def cleanText():
    logger.info('cleanText()')
    cmd = "sed -e 's/\([0-9]\)/& /g' -e 's/[[:punct:]]/ /g' -e 'G' -i /tmp/text.txt"
    logger.info(cmd)
    os.system(cmd)
    return

# Play TTS (Allow Interrupt)
def playTTS():
    logger.info('playTTS()')
    global current_tts
    current_tts=subprocess.Popen(ESPEAK_CMD,
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,close_fds=True)
    # Kick off stop audio thread
    rt.start()
    # Wait until finished speaking (unless interrupted)
    current_tts.communicate()
    return


# Stop TTS (with Interrupt)
def stopTTS():
    global current_tts
    # If button pressed, then stop audio
    if GPIO.input(BTN1) == GPIO.LOW:
        logger.info('stopTTS()')
        #current_tts.terminate()
        current_tts.kill()
        time.sleep(0.5)
    return

# GRAB IMAGE AND CONVERT
def getData():
    logger.info('getData()')
    led(0) # Turn off Button LED

    # # switch on white leds
    # for i in range(strip1.numPixels()):
    #     strip1.setPixelColor(i, Color(255, 255, 255))
    #     strip2.setPixelColor(i, Color(255, 255, 255))
    # strip1.show()
    # strip2.show()

    # Take photo
    sound(SOUNDS+"camera-shutter.wav")
    cmd = CAMERA
    logger.info(cmd)
    os.system(cmd)

    # OCR to text
    speak("now working. attendez s'il vous plait.")
    cmd = "/usr/bin/tesseract /tmp/image.jpg /tmp/text --psm 1"
    logger.info(cmd)
    # play song
    mixer.init()
    mixer.music.load(SOUNDS+'orange.mp3')
    mixer.music.play()

    # Disco
    # for i in range(strip1.numPixels()):
    #     strip1.setPixelColor(i, Color(255, 0, 0))
    #     strip2.setPixelColor(i, Color(0, 0, 255))
    # strip1.show()
    # strip2.show()

    os.system(cmd)

    # green everywhere
    # for i in range(strip1.numPixels()):
    #     strip1.setPixelColor(i, Color(0, 255, 0))
    #     strip2.setPixelColor(i, Color(0, 255, 0))
    # strip1.show()
    # strip2.show()

    # black everywhere
    # for i in range(strip1.numPixels()):
    #     strip1.setPixelColor(i, Color(0, 0, 0))
    #     strip2.setPixelColor(i, Color(0, 0, 0))
    # strip1.show()
    # strip2.show()

    # stop song
    mixer.music.stop()

    # Cleanup text
    cleanText()

    # Start reading text
    playTTS()

    # green everywhere
    # for i in range(strip1.numPixels()):
    #     strip1.setPixelColor(i, Color(0, 0, 0))
    #     strip2.setPixelColor(i, Color(0, 0, 0))
    # strip1.show()
    # strip2.show()
    return


######
# MAIN
######
try:
    global rt
    # Setup Logging
    logger = logging.getLogger()
    handler = logging.FileHandler('debug.log')
    if DEBUG:
        logger.setLevel(logging.INFO)
        handler.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.ERROR)
        handler.setLevel(logging.ERROR)
    log_format = '%(asctime)-6s: %(name)s - %(levelname)s - %(message)s'
    handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(handler)
    logger.info('Starting')

    # Setup GPIO buttons
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings (False)

    GPIO.setup(BTN1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(LED, GPIO.OUT)

    # Threaded audio player
    #rt = RaspberryThread( function = repeatTTS ) # Repeat Speak text
    rt = RaspberryThread( function = stopTTS ) # Stop Speaking text

    volume(VOLUME)
    speak("OK, on est pret")
    led(1)

    while True:
        if GPIO.input(BTN1) == GPIO.LOW:
            # Btn 1
            getData()
            rt.stop()
            rt = RaspberryThread( function = stopTTS ) # Stop Speaking text
            led(1)
            time.sleep(0.5)
            speak("OK, on est pret")
        time.sleep(0.2)

except KeyboardInterrupt:
    logger.info("exiting")

GPIO.cleanup() #Reset GPIOs
sys.exit(0)
