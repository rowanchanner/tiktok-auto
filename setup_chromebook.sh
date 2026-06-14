#!/bin/bash
echo "========================================="
echo "   Setting up Auto TikTok Poster"
echo "========================================="

echo "[1/4] Updating Linux system..."
sudo apt-get update -y
sudo apt-get upgrade -y

echo "[2/4] Installing Python, pip, and dependencies..."
sudo apt-get install -y python3 python3-pip python3-venv xvfb libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxkbcommon0 libpango-1.0-0 libcairo2 libasound2

echo "[3/4] Setting up Python environment..."
# Chromebook Linux sometimes forces virtual environments
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo "[4/4] Installing Playwright Browsers..."
playwright install chromium

echo "========================================="
echo "Setup Complete! You can now run the bot."
echo "========================================="
