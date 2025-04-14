#!/usr/bin/env bash
# exit on error
set -o errexit

# Install system dependencies
apt-get update
apt-get install -y python3-opencv libsm6 libxext6 libxrender-dev libglib2.0-0

# Install Python dependencies
pip install --upgrade pip
pip install cmake
pip install dlib --no-cache-dir
pip install -r requirements.txt
