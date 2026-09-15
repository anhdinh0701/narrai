@echo off
title NarrAI - Khoi dong Server
echo ===================================================
echo             KHOI DONG SERVER NARR AI
echo ===================================================
echo.

cd /d "%~dp0"

if exist "venv\Scripts\activate.bat" (
    echo [*] Dang kich hoat virtual environment...
    call venv\Scripts\activate.bat
)

echo [*] Dang khoi dong Backend Server (Port 8000)...
start "NarrAI Server" cmd /k "cd backend && python main.py"

timeout /t 3 /nobreak >nul

echo [*] Dang mo trinh duyet...
start http://localhost:8000

echo.
echo ===================================================
echo Server da san sang tai: http://localhost:8000
echo ===================================================
pause
