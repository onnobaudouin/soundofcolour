# soundofcolour

using real-time colour tracking of coloured sphere (4 / 5 colours) create interactive 
sound landscapes.

  
### Python

for performance reasons the colour tracking anc calibration is done
via python (using OpenCV 3 and numpy) and the data is then sent
to a html page (and javascript) over a Socket Server.

### Raspberry PI

the code is tested on both Windows 10 PC and Raspberry PI, also
the colour tracking algorithm therefore needs to be simple to allow
for 30FPS 5 colour tracking. 

To allow low cost we also can track the information via a websocket.

### HTML / Javascript

we seperated out the visual tracking from the sound code to allow
quicker iteration (and multiple interpretation). i.e. it's a lot quicker 
restarting a browserpage then a whole video processing cycle. 

Camera -> Raspberry PI -> Python <-> SocketServer <-> HTML -> Howler.js 



### Installation

#### Hardware

- 1 x Raspberry Pi v3 - with Heatsinks
- 1 x good 5v 2A powersupply for RPi 3
- 1 x Raspberry Pi Camera model 2.     (i presume version 1 will also work, with modified camera settings)
- 1 x GOOD quality SD-Card, 8GB or more. 

#### Software

All following was done on Feb 06 2018

##### Operating System for PI (Raspbian)

Download the latest Raspbian https://www.raspberrypi.org/downloads/raspbian/ 

We used:
 
    RASPBIAN STRETCH WITH DESKTOP
    Image with desktop based on Debian Stretch  
    Version:November 2017  
    Release date:2017-11-29
    Kernel version:4.9

Strictly speaking we would not need a desktop but makes it harder to setup / test. 

Unzip the file so you get the single ".img" file.

Using Etcher (https://etcher.io/) burn the img to the SD Card. 

Put SD inside the RPI (connected with screen and keyboard) and start. 

open a terminal and update OS to the latest libraries etc. 

Full instructions: https://www.raspberrypi.org/documentation/installation/installing-images/README.md    

    sudo apt-get purge wolfram-engine
    sudo apt-get purge libreoffice*
    sudo apt-get clean
    sudo apt-get autoremove
    
    sudo apt-get update && sudo apt-get upgrade
    
Also we need to enable the pi camera in raspi_config.

    sudo raspi-config 
    
Enable camera and SSH and reboot or type manually...        
    
    sudo reboot 


##### Python 3 

We will use Python 3.5.+ and OpenCV 3.4.0+ 

The installation below is largely based on :

https://www.pyimagesearch.com/2017/09/04/raspbian-stretch-install-opencv-3-python-on-your-raspberry-pi/


##### OpenCV

-> This will take over 2 hours! as we need to compile OpenCV to the fastest possible edition. 

Essentially this guide but with newer opencv and correct URLS...

https://www.pyimagesearch.com/2017/10/09/optimizing-opencv-on-the-raspberry-pi/

    sudo apt-get update && sudo apt-get upgrade
    sudo apt-get install build-essential cmake pkg-config
    sudo apt-get install libjpeg-dev libtiff5-dev libjasper-dev libpng12-dev
    sudo apt-get install libavcodec-dev libavformat-dev libswscale-dev libv4l-dev
    sudo apt-get install libxvidcore-dev libx264-dev
    sudo apt-get install libgtk2.0-dev libgtk-3-dev
    sudo apt-get install libcanberra-gtk*
    sudo apt-get install libatlas-base-dev gfortran
    sudo apt-get install python2.7-dev python3-dev
    
    wget -O opencv.zip https://github.com/opencv/opencv/archive/3.4.0.zip
    unzip opencv.zip
    wget -O opencv_contrib.zip https://github.com/opencv/opencv_contrib/archive/3.4.0.zip
    unzip opencv_contrib.zip
    
    
    sudo pip install virtualenv virtualenvwrapper
    sudo rm -rf ~/.cache/pip
    
    nano ~/.profile
    
Then add these lines at the end: ~/.profile

    # virtualenv and virtualenvwrapper
    export WORKON_HOME=$HOME/.virtualenvs
    source /usr/local/bin/virtualenvwrapper.sh
    
CTRL + O (write), CTRL + X (quit)

    source ~/.profile
    mkvirtualenv cv -p python3
    pip install numpy   
    
    cd ~/opencv-3.4.0/
    mkdir build
    cd build
    cmake -D CMAKE_BUILD_TYPE=RELEASE \
        -D CMAKE_INSTALL_PREFIX=/usr/local \
        -D OPENCV_EXTRA_MODULES_PATH=~/opencv_contrib-3.4.0/modules \
        -D ENABLE_NEON=ON \
        -D ENABLE_VFPV3=ON \
        -D BUILD_TESTS=OFF \
        -D INSTALL_PYTHON_EXAMPLES=OFF \
        -D BUILD_EXAMPLES=OFF ..    
        
Now we optimize the compilation by creating a bigger swapfile

    sudo nano /etc/dphys-swapfile
    
End change to 1024 /etc/dphys-swapfile

    CONF_SWAPSIZE=1024            
    
CTRL + O (write), CTRL + X (quit)

    sudo /etc/init.d/dphys-swapfile stop
    sudo /etc/init.d/dphys-swapfile start
  
Time to build the latest opencv.. this will take 2 hours or more and the CPU will be at 100% at all times 

    make -j4 #takes around 2 HOURS
    
    sudo make install
    sudo ldconfig
    
Reduce swapfile

    sudo nano /etc/dphys-swapfile
    
End change to 100 /etc/dphys-swapfile

    CONF_SWAPSIZE=100            
    
CTRL + O (write), CTRL + X (quit)

    sudo /etc/init.d/dphys-swapfile stop
    sudo /etc/init.d/dphys-swapfile start
    
Now make sure the virtualenv (cv) can use opencv

    cd /usr/local/lib/python3.5/site-packages/
    sudo mv cv2.cpython-35m-arm-linux-gnueabihf.so cv2.so
    cd ~/.virtualenvs/cv/lib/python3.5/site-packages/
    ln -s /usr/local/lib/python3.5/site-packages/cv2.so cv2.so
    
#### PiCamera

Still in your cv env:

    pip install picamera


 
 
#### Sound of colour


git clone https://username:password@github.com/MediaInnovationStudio/soundofcolour

https://opgbaudouin@github.com/MediaInnovationStudio/soundofcolour
#### Setup the PI as access point

We will set this up with 

SSID = SoundOfColour
PASS = asdfvbnm

It's a G-Only network and WPA2 PSK. If your device doesn't support this -> no luck.

Note: when now using the Desktop

https://www.raspberrypi.org/documentation/configuration/wireless/access-point.md

    sudo apt-get install dnsmasq hostapd
    sudo systemctl stop dnsmasq
    sudo systemctl stop hostapd
    
    sudo nano /etc/dhcpcd.conf
    
Now edit the file /etc/dhcpcd.conf

    interface wlan0
    static ip_address=192.168.20.1/24    
    
Save and close

    sudo systemctl restart dhcpcd
    sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig  
    sudo nano /etc/dnsmasq.conf 

Write the NEW file /etc/dnsmasq.conf 

    interface=wlan0     
    dhcp-range=192.168.20.68,192.168.4.168,255.255.255.0,24h  
    
    sudo nano /etc/hostapd.conf 
    
Write the NEW file  /etc/hostapd.conf 
    
    interface=wlan0
    driver=nl80211
    ssid=NameOfNetwork
    hw_mode=g
    channel=7
    wmm_enabled=0
    macaddr_acl=0
    auth_algs=1
    ignore_broadcast_ssid=0
    wpa=2
    wpa_passphrase=AardvarkBadgerHedgehog
    wpa_key_mgmt=WPA-PSK
    wpa_pairwise=TKIP
    rsn_pairwise=CCMP    
    
Then
   
    sudo nano /etc/default/hostapd
    
and edit file:  /etc/default/hostapd

    DAEMON_CONF="/etc/hostapd.conf"   
    
Then
    
    sudo systemctl start hostapd
    sudo systemctl start dnsmasq      
    
    sudo nano /etc/sysctl.conf
    
Edit

    net.ipv4.ip_forward=1
    
Save and Quit

    sudo iptables -t nat -A  POSTROUTING -o eth0 -j MASQUERADE
    sudo sh -c "iptables-save > /etc/iptables.ipv4.nat"
      
    sudo /etc/rc.local
    
Edit file (just above the exit 0)

    iptables-restore < /etc/iptables.ipv4.nat
    
    sudo reboot
    
### TODO VNC for debugging?                   