@echo off
setlocal

:: Title and Colors
title OmniScreen Forge Launcher
color 0D

echo ========================================================
echo                 OMNISCREEN FORGE
echo       Universal Multi-Monitor Display Rescaler
echo ========================================================
echo.

:: Check for Python Installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Python is not installed or not in your PATH!
    echo Please install Python 3.9 or higher from python.org
    echo Make sure to check the box "Add Python to PATH" during install.
    echo.
    pause
    exit /b
)

:: Check for FFmpeg Installation
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    color 0E
    echo [WARNING] FFmpeg is not installed or not in your PATH!
    echo OmniScreen Forge can process static images, but you will
    echo NOT be able to render Video files (.mp4, .gif) without FFmpeg.
    echo.
    echo To install FFmpeg on Windows:
    echo 1. Download a Windows build from gyan.dev
    echo 2. Extract the folder to C:\
    echo 3. Add the \bin folder to your Windows Environment Variables PATH.
    echo.
    pause
)

:: Check and Install Dependencies
echo Checking Python Dependencies...
pip install -r requirements.txt >nul 2>&1
if %errorlevel% neq 0 (
    color 0E
    echo [WARNING] Some dependencies may have failed to install.
    echo The application may not run correctly.
    echo.
) else (
    echo Dependencies verified successfully!
    echo.
)

:: Launch Application
color 0A
echo Launching OmniScreen Forge...
start /b pythonw main.py

exit
