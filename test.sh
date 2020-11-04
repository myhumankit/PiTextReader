#!/bin/bash
# TEST RASPI 


# CLEANUP
rm -f test.jpg test.txt


# ADJUST AUDIO VOLUME
# Change VOLUME to increase/decrease 0-100%
VOLUME=90%
echo "Setting volume to $VOLUME"
sudo amixer -q sset PCM,0 ${VOLUME}


# PLAY SPEECH 
echo "playing TTS"
espeak-ng -v mb/mb-fr4 "Bonjour le monde ! Ceci est un test de texte vers parole"

# TEST CAMERA
echo "taking photo"
raspistill -cfx 128:128 --awb auto -rot 180 -t 500 -o test.jpg
ls -l test.jpg

# OCR test
echo "Converting to Text, standby..."
tesseract test.jpg test
cat test.txt

# SPEAK TEXT
espeak-ng -v mb/mb-fr4 -f test.txt

# Run a web server to view photo
IP=`hostname -I`
IP=${IP%?}
echo "To see photo, browse to http://$IP:8080/test.jpg"
echo "Press Ctrl-C to exit"
python -m SimpleHTTPServer 8080

