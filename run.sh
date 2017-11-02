#!/bin/bash

pause() {
   read -n1 -rsp $'press to quit\n'
}

source /home/pi/.profile
workon cv

echo Hello

cd /home/pi/balls
python test.py

pause