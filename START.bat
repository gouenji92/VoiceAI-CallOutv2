@echo off
REM ========================================
REM VoiceAI - One-Click Startup
REM Double-click this file to start everything
REM ========================================

echo.
echo ========================================
echo   VOICEAI - STARTING ALL SERVICES
echo ========================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Run PowerShell script with execution policy bypass
powershell.exe -ExecutionPolicy Bypass -File ".\start_all.ps1" -WithAgent

echo.
echo ========================================
echo   STARTUP COMPLETE
echo ========================================
echo.
echo API running at: http://127.0.0.1:8000/docs
echo RL Monitor: http://127.0.0.1:8000/api/rl-monitor/status
echo.
echo To stop: Close the API/Agent windows and run "docker compose down"
echo.
pause
