#!/bin/bash
# Install PiTextReader
# 
# Run using:
# $ sh install.sh
#
# Can be safely run multiple times
#
# version 20180210
#

if [ "$EUID" -ne 0 ]
  then echo "Must run as root: 'sudo ./install.sh'"
  exit
fi

# Make sure python requirements are installed
apt-get -y update
apt-get -y upgrade


echo  

# Install packages
apt-get install -y tesseract-ocr flite alsa-utils
apt-get install -y python3-rpi.gpio python3-gpiozero

# Verify Camera is configured
X=`raspistill -o test.jpg 2>&1|grep Failed`

if [ -z "$X" ];
then
        echo "Found Camera OK"
else
	echo $X
        echo "NO Camera Detected! SEE DOCS Troubleshooting section."
	exit
fi 

# Configure asound for desktopless environment
echo "pcm.!default {
        type hw
        card 0
}

ctl.!default {
        type hw           
        card 0
}
" > /home/pi/.asoundrc

chown pi:pi /home/pi/.asoundrc

# Power On/Off control button, enable GPIO port
cp /boot/config.txt /boot/config.txt.bak
echo " "  >> /boot/config.txt
echo "# Enable power On/Off swith control ============="  >> /boot/config.txt
echo "dtoverlay=gpio-shutdown" >> /boot/config.txt


# Install custom software
crontab ./cronfile
echo "Crontab entry installed for pi userid. OK"
 
# FINISHED!
echo "Finished installation. See Readme.md for more info"
echo "Reboot your pi now:  $ sudo reboot"
echo 

