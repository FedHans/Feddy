@echo off
echo ============================================================
echo 📊 Generating Portfolio Technical Analysis...
echo ============================================================
cd /d "C:\Users\Federico Hans\Documents\ICT practice\marketbrief"
call "C:\Users\Federico Hans\Documents\ICT practice\venv\Scripts\activate"
python send_analysis.py
pause