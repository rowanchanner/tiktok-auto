@echo off
title Auto TikTok Poster (Remote Access)
echo ========================================================
echo    Starting Auto TikTok Poster with Remote Access
echo ========================================================
echo.

echo [1/3] Checking dependencies...
pip install -r requirements.txt >nul 2>&1

echo [2/3] Applying TikTok library patches...
python patch_uploader.py >nul 2>&1

echo [3/3] Starting Local Dashboard...
start /b python app.py >nul 2>&1

echo.
echo ========================================================
echo Bot is running in the background!
echo Generating your public internet URL...
echo ========================================================
echo.
echo Look for the URL ending in ".lhr.life" below. 
echo You can access that link from your phone anywhere in the world!
echo.
ssh -o StrictHostKeyChecking=no -R 80:localhost:8080 nokey@localhost.run
pause
