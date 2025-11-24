@echo off
echo Setting up virtual environment...

:: Check if python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH.
    pause
    exit /b
)

:: Create venv if it doesn't exist
if not exist venv (
    echo Creating venv...
    python -m venv venv
) else (
    echo venv already exists.
)

:: Activate venv and install requirements
call venv\Scripts\activate
if exist requirements.txt (
    echo Installing requirements...
    pip install -r requirements.txt
) else (
    echo requirements.txt not found.
)

echo Setup complete.
pause
