@echo off
chcp 65001 >nul
echo Starting Focus Timer with Administrator privileges...
echo.

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python and ensure it's in your system PATH
    pause
    exit /b 1
)

:: Run the admin launcher
python admin_launcher.py

:: If there's an error, pause so user can see the message
if errorlevel 1 pause