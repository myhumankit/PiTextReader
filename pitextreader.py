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

import os, sys
import logging
import subprocess
import threading
import time
import json
import RPi.GPIO as GPIO
from gpiozero import Button
from pygame import mixer
from rpi_ws281x import ws, Color, Adafruit_NeoPixel
from constantes import *


class settings(threading.Thread):
    def __init__(self):
        super(settings,self).__init__()
        self.timer = 0
        try:
            f = open(CONFIG_FILE,"r")
            self.data = json.loads(f.read())
            f.close()
        except Exception as e:
            self.data = DEFAUL_SETTINGS
            self.timer = 1
        # end try
        self.running = True
        self.start()

    def volume_inc(self):
        self.data['volume'] += 4
        self.timer = DELAY_TO_SAVE
        

    def volume_dec(self):
        self.data['volume']-= 4
        self.timer = DELAY_TO_SAVE

    def get_volume(self):
        return self.data['volume']

    def get_volume_help(self):
        return self.data['volume_help']

    def speed_inc(self):
        self.data['speed'] += 5
        self.timer = DELAY_TO_SAVE

    def speed_dec(self):
        self.data['speed'] -= 5
        self.timer = DELAY_TO_SAVE

    def get_speed(self):
        return self.data['speed']

    def get_voice(self):
        return self.data['voice']

    def save(self):
        try:
            f = open(CONFIG_FILE,"w")
            f.write(json.dumps(self.data))
            f.close()
        except Exception as e:
            pass
        # end try

    def run(self):
        while self.running:
            if self.timer != 0:
                self.timer -= 1
                if self.timer == 0:
                    self.save()
                # end if
            # end if
        # end while


##### USER VARIABLES
DEBUG   = 1 # Debug 0/1 off/on (writes to debug.log)

# OTHER SETTINGS
SOUNDS  = "/home/pi/PiTextReader/sounds/" # Directory for sound effect(s)
CAMERA  = "raspistill -n -cfx 128:128 --awb auto -rot 180 -t 500 -o /tmp/image.jpg"

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


# LED ON/OFF
def led(val):
    logger.info('led('+str(val)+')')
    print('led('+str(val)+')')

# LINGTH ON/OFF
def light(val):
    logger.info('light('+str(val)+')')
    print('light('+str(val)+')')

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
    cmd = "sudo amixer -q sset Headphone,0 "+str(vol)+"%"
    logger.info(cmd)
    print(cmd)
    os.system(cmd)
    return

# TEXT CLEANUP
def cleanText():
    logger.info('cleanText()')
    cmd = "sed -e 's/\([0-9]\)/& /g' -e 's/[[:punct:]]/ /g' -e 'G' -i /tmp/text.txt"
    logger.info(cmd)
    print(cmd)
    os.system(cmd)
    return

# Play TTS (Allow Interrupt)
def playTTS():
    logger.info('playTTS()')
    global current_tts
    '''
    current_tts=subprocess.Popen(['/bin/sh', '/home/pi/say.sh'],
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,close_fds=True)
    '''
    cmd = "/usr/bin/espeak -s %d -v %s -f /tmp/text.txt --stdout | aplay -&" % (mySettings.get_speed(), mySettings.get_voice())
    print("CMD %s " % cmd)
    os.system(cmd) 
    # Kick off stop audio thread
    # rt.start()
    # Wait until finished speaking (unless interrupted)
    # current_tts.communicate()
    return


# GRAB IMAGE AND CONVERT
def getData():
    logger.info('getData()')
    led(0) # Turn off Button LED

    # switch on white leds
    light(1)

    # Take photo
    sound(SOUNDS+"camera-shutter.wav")
    cmd = CAMERA
    logger.info(cmd)
    os.system(cmd)

    # OCR to text
    speak("now working. attendez s'il vous plait.")
    cmd = "/usr/bin/tesseract /tmp/image.jpg /tmp/text --psm 3"
    logger.info(cmd)
    # play song
    mixer.init()
    volume(83)
    mixer.music.load('orange.mp3')
    mixer.music.play()

    os.system(cmd)

    light(0)

    # stop song
    mixer.music.stop()

    volume(mySettings.get_volume())
    # Cleanup text
    cleanText()

    # Start reading text
    playTTS()


    return


def volume_inc_cb():
    global mySettings
    logger.info('Volume +')
    mySettings.volume_inc()
    print("VOLUME + ")
    volume(mySettings.get_volume())
    
def volume_dec_cb():
    global mySettings
    logger.info('Volume -')
    mySettings.volume_dec()
    print("VOLUME - ")
    volume(mySettings.get_volume())
    
def speed_inc_cb():
    global mySettings
    logger.info('Speed +')
    mySettings.speed_inc()
    print("SPEED + ")
    
def speed_dec_cb():
    global mySettings
    logger.info('Speed -')
    mySettings.speed_dec()
    print("SPEED - ")
    

def play_start_stop_cb():
    logger.info('Play start stop')
    print("Play start stop")
    # Start reading text
    volume(mySettings.get_volume())
    playTTS()
    volume(mySettings.get_volume_help())
    
def forward_cb():
    logger.info('Forward')
    print("Forward")
    
def backward_cb():
    logger.info('Backward')
    print("Backward")

def battery_level_cb():
    logger.info('Battery level')
    print("Battery level")

def capture_cb():
    # global rt
    getData()
    led(1)
    time.sleep(0.5)
    speak("OK, on est pret")

def cancel_cb():
    logger.info('Cancel')
    print("Cancel")
    
associations = [[GPIO_VOLUME_INC,volume_inc_cb],
                [ GPIO_VOLUME_DEC, volume_dec_cb],
                [ GPIO_SPEED_INC, speed_inc_cb],
                [ GPIO_SPEED_DEC, speed_dec_cb],
                [ GPIO_PLAY_START_STOP, play_start_stop_cb],
                [ GPIO_FORWARD, forward_cb],
                [ GPIO_BACKWARD, backward_cb],
                [ GPIO_BATTERY_LEVEL, battery_level_cb],
                [ GPIO_CAPTURE, capture_cb],
                [ GPIO_CANCEL, cancel_cb]]
######
# MAIN
######
try:
    global rt
    mySettings = settings()
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

    volume(mySettings.get_volume_help())

    speak("OK, on est pret")
    led(1)

    
    buttons = []
    GPIO.setmode(GPIO.BCM)
    for i in range(len(associations)):
        pin = associations[i][0]
        callback = associations[i][1]
        GPIO.setup(pin,GPIO.IN,pull_up_down=GPIO.PUD_UP)
        print("Bouton gpio %d" % (pin))
        button = Button(pin)
        buttons.append(button)
        button.when_pressed = callback
    # end for
    while True:
        time.sleep(10)
    # end while

except KeyboardInterrupt:
    logger.info("exiting")

sys.exit(0)
