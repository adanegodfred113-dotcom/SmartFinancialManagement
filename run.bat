@echo off
cd /d "%~dp0"
py -c "import matplotlib" >nul 2>&1
if errorlevel 1 (
    echo Matplotlib is not installed. Installing it now...
    py -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Installation failed. Check your internet connection and Python installation.
        pause
        exit /b 1
    )
)
py main.py
if errorlevel 1 pause
