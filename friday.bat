@echo off
title Jarvis AI Assistant
echo Starting Jarvis AI Assistant...
echo.
echo Checking environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH.
    pause
    exit /b
)

echo.
echo Starting Main Application...
python Main.py
if %errorlevel% neq 0 (
    echo.
    echo Application exited with an error.
    pause
)
