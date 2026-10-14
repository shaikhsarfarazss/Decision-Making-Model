@echo off
title StudyShield — Desktop Control Center
echo Starting StudyShield Local Server & Desktop App...
start /B python backend\server.py
timeout /t 1 /nobreak >nul
python desktop_app.py
