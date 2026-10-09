@echo off
title VulnLab - Deliberately Vulnerable Web Application
echo ===================================================================
echo   [!] VULNLAB - LOCAL CYBERSECURITY TESTING LAB
echo   [!] Initializing SQLite Database and starting Flask Server...
echo   [!] Access the site at: http://127.0.0.1:5000
echo   [!] Press Ctrl+C in this terminal to stop the server anytime.
echo ===================================================================
python -m pip install -r requirements.txt
python database.py
python app.py
pause
