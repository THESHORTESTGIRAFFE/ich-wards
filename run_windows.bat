@echo off
:: Set title of the Command Prompt window
title ICH-Wards Management System - Production Server

echo ============================================================
echo   🏥 ICH-WARDS MANAGEMENT SYSTEM - WINDOWS LAUNCHER
echo ============================================================
echo.

:: 1. Check for Python installation
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found on your system!
    echo Please download and install Python 3.10 or higher from:
    echo https://www.python.org/downloads/
    echo Make sure to check the box "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: 2. Setup/Verify Virtual Environment
if not exist venv (
    echo [INFO] Virtual environment not found. Creating one...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created successfully.
)

:: 3. Activate Virtual Environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment!
    pause
    exit /b 1
)

:: 4. Auto-create .env file if it doesn't exist
if not exist .env (
    echo [INFO] .env file not found. Copying from .env.template...
    copy .env.template .env >nul
    echo [SUCCESS] Created .env file. Please update SECRET_KEY if needed.
)

:: 5. Install/Upgrade Dependencies
echo [INFO] Installing / updating required dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies!
    pause
    exit /b 1
)
echo [SUCCESS] All dependencies are ready.
echo.

:: 6. Launch Production Server
python run_production.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] The server stopped unexpectedly or failed to start.
    pause
)

:: Deactivate venv on exit
call deactivate
