FROM python:3.10-slim

# Install system dependencies including ffmpeg for yt-dlp
RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install phantomwright browser and its system dependencies
RUN python -m phantomwright_driver install chromium
RUN python -m phantomwright_driver install-deps

# Copy the rest of the project
COPY . .

# Run the bot in auto mode
CMD ["python", "main.py", "--auto"]
