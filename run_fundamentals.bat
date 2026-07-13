@echo off
echo ============================================================
echo 📊 Fetching Coin Fundamentals...
echo ============================================================
cd /d "C:\Users\Federico Hans\Documents\ICT practice\marketbrief"
call "C:\Users\Federico Hans\Documents\ICT practice\venv\Scripts\activate"
python send_fundamentals.py %1
pause