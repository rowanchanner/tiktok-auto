@echo off
title Auto TikTok Poster (CMD)
echo =========================================
echo    Starting Auto TikTok Poster in CMD
echo =========================================
echo.

echo [1/2] Applying patches...
python patch_uploader.py >nul 2>&1

echo [2/2] Running Bot...
echo.
python main.py
pause
