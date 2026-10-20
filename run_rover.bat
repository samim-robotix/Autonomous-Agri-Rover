@echo off
cd /d "%~dp0"

echo =====================================================================
echo    STARTING AUTONOMOUS AGRICULTURE ROVER
echo =====================================================================

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

python main.py %*
if %errorlevel% neq 0 (
    echo.
    echo Rover exited with an error. Running in mock simulation mode for verification...
    python main.py --mock
)
pause
