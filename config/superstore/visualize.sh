#!/bin/bash
sudo apt update
sudo apt install python3-pip -y
pip3 --version
# source venv/bin/activate
pip3 install matplotlib
# python3 -m pip install matplotlib

python3 visualize.py