@echo off
title Voice-First Accessible App Launcher
echo =====================================================================
echo    VOICE-FIRST: ACCESSIBLE VOICE NOTE-TAKING AND STUDY APP
echo    Specially Engineered for Visually Impaired and Blind Students
echo =====================================================================
echo.

set PYTHON_EXE=C:\Users\Priyanshi\AppData\Local\Programs\Python\Python314\python.exe
if not exist "%PYTHON_EXE%" (
    set PYTHON_EXE=python
)

set FLUTTER_BAT=C:\src\flutter\flutter\bin\flutter.bat
if not exist "%FLUTTER_BAT%" (
    set FLUTTER_BAT=flutter
)

echo [1/3] Checking environment...
echo Using Python: %PYTHON_EXE%
echo Using Flutter: %FLUTTER_BAT%
echo.

echo [2/3] Starting VoiceFirst Flask Backend on http://127.0.0.1:5000 ...
start "VoiceFirst Backend (Port 5000)" cmd /k "cd /d %~dp0backend && "%PYTHON_EXE%" app.py"

echo Waiting 3 seconds for backend server initialization...
timeout /t 3 /nobreak > nul

echo.
echo [3/3] Launching Flutter Frontend on Chrome (Port 3000)...
echo Press Spacebar in the app to toggle microphone / hands-free mode!
echo.
cd /d %~dp0frontend
call "%FLUTTER_BAT%" run -d chrome --web-port=3000

pause
