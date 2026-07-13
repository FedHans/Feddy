@echo off
title Crypto News Alerts

:: Check if already running
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq Crypto News Alerts" 2>NUL | find /I /N "python.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo Another instance is already running!
    echo Press any key to exit...
    pause >nul
    exit
)

echo ============================================================
echo 📰 Starting Real-Time News Alerts...
echo ============================================================
cd /d "C:\Users\Federico Hans\Documents\ICT practice\marketbrief"
call "C:\Users\Federico Hans\Documents\ICT practice\venv\Scripts\activate"
python news_alert.py