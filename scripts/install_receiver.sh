#!/bin/bash

sudo apt-get update
sudo apt-get install -y \
   git \
   python3-pip

cd ../
python3 -m pip install --user -r src/requirements.txt
