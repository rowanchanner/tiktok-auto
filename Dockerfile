FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# Install ffmpeg for yt-dlp
RUN apt-get update && apt-get install -y ffmpeg nodejs && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m phantomwright_driver install chromium

COPY . .
RUN cp CookieFilerowanoutdoors.json TK_cookies_rowanoutdoors.json 2>/dev/null || true
RUN python patch_uploader.py

# Memory-saving settings for 512MB Render Starter plan
ENV MALLOC_ARENA_MAX=2
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV PYTORCH_NO_CUDA=1
ENV PYTHONUNBUFFERED=1

# Run the web dashboard (2 threads so website stays responsive during uploads)
CMD gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 300 app:app
