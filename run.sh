#!/bin/bash

#PATH=$PATH:~/.local/bin
#sudo yum -y install python37

#curl -O https://bootstrap.pypa.io/get-pip.py

#python3 get-pip.py --user

#python3 -m pip install --upgrade pandas
python3 -m pip install -r requirements.txt

python3 model.py
