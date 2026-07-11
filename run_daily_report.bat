@echo off
echo ============================================================
echo 📊 Running Daily Crypto Market Briefing...
echo ============================================================
cd /d "C:\Users\Federico Hans\Documents\ICT practice\marketbrief"
call "C:\Users\Federico Hans\Documents\ICT practice\venv\Scripts\activate"
python send_full_report.py
echo.
echo ✅ Daily report sent!
pause