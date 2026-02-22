@echo off
title TikTok Live Bot — Setup
echo.
echo  ==========================================
echo   TikTok Live Bot — One-Time Setup
echo  ==========================================
echo.
echo  Installing Python dependencies...
pip install TikTokLive aiohttp aiofiles colorama httpx playwright edge-tts pygame pyinstaller
echo.
echo  Installing Chromium browser (for comment posting)...
playwright install chromium
echo.
echo  Setup complete!
echo  You can now either:
echo    1. Run:  python launcher.py   (to test without building exe)
echo    2. Run:  python build.py      (to package into .exe)
echo.
pause
