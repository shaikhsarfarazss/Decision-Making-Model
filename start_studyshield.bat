@echo off
title StudyShield — 3-Layer YouTube Local AI Server
echo ====================================================================
echo   StudyShield: Starting 3-Layer YouTube Local AI Server (Port 8000)
echo ====================================================================
start "" "http://127.0.0.1:8000/"
python backend\server.py
pause
