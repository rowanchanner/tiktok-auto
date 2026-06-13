#!/bin/bash

# Activate the virtual environment where all the packages were installed
source /opt/venv/bin/activate

# Start a dummy web server on the port Railway provides so it doesn't kill the app
PORT=${PORT:-8080}
python -m http.server $PORT &

# Start the actual bot
python main.py --auto
