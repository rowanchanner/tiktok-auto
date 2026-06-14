@echo off
title Auto TikTok Poster
echo =========================================
echo    Starting Auto TikTok Poster locally
echo =========================================
echo.

echo [1/3] Checking dependencies...
pip install -r requirements.txt >nul 2>&1

echo [2/3] Applying TikTok library patches...
python patch_uploader.py >nul 2>&1

echo [3/3] Starting Local Dashboard...
echo.
echo ========================================================
echo Bot is running! Open your browser to: http://127.0.0.1:8080
echo Leave this window open in the background!
echo ========================================================
python app.py
pause
