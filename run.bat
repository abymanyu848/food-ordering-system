@echo off
title Food Ordering System
echo Starting Food Ordering Management System...
echo.

REM Project root is the folder containing this script.
cd /d "%~dp0"

REM Use a single virtual environment at the project root.
if not exist ".venv\Scripts\python.exe" (
    echo Creating Python virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate
    python -m pip install --upgrade pip
    pip install -r requirements.txt
) else (
    echo Virtual environment found.
    call .venv\Scripts\activate
)

REM Make sure dependencies are installed.
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo.
echo Preparing demo data...
python backend\seed.py

echo.
echo ========================================
echo Food Ordering System is starting!
echo ========================================
echo App:      http://127.0.0.1:8000
echo API Docs: http://127.0.0.1:8000/docs
echo ========================================
echo.
echo Demo Accounts:
echo   Admin:    admin@example.com / admin123
echo   Customer: john@example.com / password123
echo ========================================
echo.

REM Start FastAPI (it serves both the API and the HTML frontend).
python main.py
pause