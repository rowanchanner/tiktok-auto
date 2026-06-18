FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# Install ffmpeg for yt-dlp
RUN apt-get update && apt-get install -y ffmpeg nodejs && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m phantomwright_driver install chromium

COPY . .
RUN python patch_uploader.py

# Run the web dashboard using gunicorn with strict memory limits and a long timeout
CMD gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 1 --preload --timeout 300 --max-requests 10 --max-requests-jitter 2 app:app
