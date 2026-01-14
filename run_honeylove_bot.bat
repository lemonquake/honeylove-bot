@echo off
TITLE Honeylove Announcer Bot
echo Starting Honeylove Announcer Bot...
echo.

:: Change directory to the location of this script
cd /d "%~dp0"

:: Activate virtual environment if it exists
IF EXIST "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) ELSE (
    echo Virtual environment not found in venv\Scripts\activate.bat.
    echo Attempting to run with global python...
)

:: Run the bot
python main.py

echo.
echo Bot process has ended.
pause
