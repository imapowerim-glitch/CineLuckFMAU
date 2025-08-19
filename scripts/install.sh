#!/bin/bash

# Update package lists
sudo apt update

# Install dependencies
sudo apt install -y python3 python3-pip

# Clone the CineLuck camera app repository
git clone https://github.com/username/CineLuckCameraApp.git

# Navigate into the cloned directory
cd CineLuckCameraApp

# Install required Python packages
pip3 install -r requirements.txt

# Run the app (optional)
# python3 app.py
