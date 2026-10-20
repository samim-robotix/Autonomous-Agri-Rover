@echo off
echo =====================================================================
echo    Agriculture Rover - Windows Development Environment Setup
echo =====================================================================

cd /d "%~dp0"

echo [1/4] Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH! Please install Python 3.9 - 3.11.
    pause
    exit /b 1
)

echo.
echo [2/4] Creating virtual environment (.venv)...
if not exist ".venv" (
    python -m venv .venv
    echo Virtual environment created.
) else (
    echo Virtual environment already exists.
)

echo.
echo [3/4] Activating virtual environment & installing dependencies...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo [4/4] Initializing model weights...
python models\download_weights.py

echo.
echo =====================================================================
echo    SETUP COMPLETE! You can now run the rover using:
echo       run_rover.bat
echo       or: python main.py --mock
echo =====================================================================
pause
