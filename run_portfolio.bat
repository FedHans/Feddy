@echo off
echo ============================================================
echo 📊 Running Portfolio Analysis...
echo ============================================================
cd /d "C:\Users\Federico Hans\Documents\ICT practice\marketbrief"
call "C:\Users\Federico Hans\Documents\ICT practice\venv\Scripts\activate"
python portfolio_analysis.py
echo.
echo ✅ Portfolio analysis complete!
pause