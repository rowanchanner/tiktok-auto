#!/bin/bash

# Start a dummy web server on the port Railway provides so it doesn't kill the app
PORT=${PORT:-8080}
python -m http.server $PORT &

# Start the actual bot
python main.py --auto
