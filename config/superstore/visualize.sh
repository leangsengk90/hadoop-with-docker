#!/bin/bash
sudo apt update
sudo apt install python3-pip
pip3 --version
pip3 install matplotlib

python3 visualize.py