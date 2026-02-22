@echo off
title AD-HTC Streamlit Launcher
echo ============================================
echo   AD-HTC Application Launcher
echo   Developed by Ferdinand Agobe
echo ============================================
echo.

REM Activate virtual environment (.venv folder)
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo ERROR: Virtual environment not found!
    echo Expected location: %cd%\.venv\Scripts\activate.bat
    echo.
    echo Please make sure:
    echo 1. The .venv folder exists in this directory
    echo 2. You've run: python -m venv .venv
    pause
    exit /b 1
)

REM Verify Python
echo.
echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not available in virtual environment.
    pause
    exit /b 1
) else (
    python --version
)

REM Check/Install Streamlit
echo.
echo Checking Streamlit...
python -c "import streamlit" 2>nul
if errorlevel 1 (
    echo Streamlit not found. Installing...
    python -m pip install --quiet streamlit
    if errorlevel 1 (
        echo ERROR: Failed to install Streamlit.
        pause
        exit /b 1
    ) else (
        echo Streamlit installed successfully.
    )
) else (
    echo Streamlit is ready.
)

REM Check if app.py exists
echo.
if not exist "app.py" (
    echo ERROR: app.py not found in current directory!
    echo Current location: %cd%
    dir *.py
    pause
    exit /b 1
)

REM Launch the app
echo.
echo ============================================
echo Launching AD-HTC Application...
echo ============================================
echo.
python -m streamlit run app.py

if errorlevel 1 (
    echo.
    echo ERROR: Failed to launch application.
    pause
    exit /b 1
)

pause