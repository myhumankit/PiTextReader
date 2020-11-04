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

# Make sure python requirements are installed
sudo apt-get update
#sudo apt-get install -y build-essential python-pip python-dev 

echo  

# Install packages
sudo apt-get install -y tesseract-ocr #flite

###################
# add config ReadForMe, mhk Fabrikarium 2020
sudo apt-get install speech-dispatcher

# rgb led strip dependency
sudo pip install rpi_ws281x

# installation mbrola
wget http://steinerdatenbank.de/software/mbrola3.0.1h_armhf.deb
sudo dpkg -i mbrola3.0.1h_armhf.deb
sudo apt-get install -y mbrola-fr1

# fin config ReadForMe
###################

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

# Install custom software
crontab ./cronfile
echo "Crontab entry installed for pi userid. OK"
 
# FINISHED!
echo "Finished installation. See Readme.md for more info"
echo "Reboot your pi now:  $ sudo reboot"
echo 

