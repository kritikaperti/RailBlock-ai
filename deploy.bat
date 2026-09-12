@echo off
echo =========================================================================
echo   [IR] RailBlock AI - Automated Production Deployment Script (Windows)
echo =========================================================================
echo.

echo [1/3] Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH.
    pause
    exit /b 1
)

echo [2/3] Installing/updating production dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error installing dependencies.
    pause
    exit /b 1
)

echo [3/3] Launching RailBlock AI Production Server...
python run.py

pause
