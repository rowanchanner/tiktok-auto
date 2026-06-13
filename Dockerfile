FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# Install ffmpeg for yt-dlp
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install phantomwright browser
RUN python -m phantomwright_driver install chromium

COPY . .

# Run the web dashboard using gunicorn
CMD gunicorn --bind 0.0.0.0:$PORT app:app
