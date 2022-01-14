#!/bin/bash

sudo apt-get update
sudo apt-get install -y \
   ola \
   git \
   ola-python \
   python3-pip

cd ../
python3 -m pip install --user -r src/requirements.txt

sudo adduser pi olad

cd /etc/ola/
sudo cp ola-ftdidmx.conf ola-ftdidmx.conf.bak
sudo cp ola-usbserial.conf ola-usbserial.conf.bak
sudo cp ola-opendmx.conf ola-opendmx.conf.bak

sudo tee ./ola-ftdidmx.conf > /dev/null <<EOL
enabled = true
frequency = 30
EOL

sudo tee ./ola-usbserial.conf > /dev/null <<EOF
device_dir = /dev
device_prefix = ttyUSB
device_prefix = cu.usbserial-
device_prefix = ttyU
enabled = false
pro_fps_limit = 190
tri_use_raw_rdm = false
ultra_fps_limit = 40
EOF

sudo tee ./ola-opendmx.conf > /dev/null <<EOF
device = /dev/dmx0
enabled = false
EOF

sudo killall -s SIGHUP olad
sudo service restart olad

sleep 10

echo "DEV INFO ============="
ola_dev_info | grep FT232R
echo "======================"

echo "PATCH COMMAND EXAMPLE:"
echo "ola_patch -d 8 -p 1 -u 0"
echo "======================"
