@echo off
title Hotel Management Expert System - Windows Setup & Launcher
echo ============================================================
echo   AetherStay AI - Hotel Management Expert System Setup
echo ============================================================
echo.

:: Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to PATH!
    echo Please install Python 3.9+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo [1/3] Creating virtual environment (venv)...
if not exist "venv" (
    python -m venv venv
)

echo [2/3] Activating virtual environment and installing dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt

echo [3/3] Starting Hotel Management Expert System Server...
echo.
echo Open your browser and visit: http://127.0.0.1:5000
echo Press CTRL+C in this window to stop the server.
echo.
start http://127.0.0.1:5000
python app.py
pause
