@echo off
title StudyShield - Local Laya Decision Server
echo ==================================================================
echo         StudyShield: Local Laya Decision Microservice
echo         Offline System 1 AI Engine for Live YouTube Filtering
echo ==================================================================
echo.
cd /d "%~dp0backend"
echo Starting FastAPI server on http://localhost:8000 ...
python server.py
pause
