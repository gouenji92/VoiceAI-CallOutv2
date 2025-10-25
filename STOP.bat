@echo off
REM ========================================
REM VoiceAI - Stop All Services
REM Double-click to gracefully stop everything
REM ========================================

echo.
echo ========================================
echo   VOICEAI - STOPPING ALL SERVICES
echo ========================================
echo.

cd /d "%~dp0"

echo Stopping Docker services...
docker compose down

echo.
echo ========================================
echo   STOPPED
echo ========================================
echo.
echo Note: Close any remaining API/Agent windows manually
echo.
pause
