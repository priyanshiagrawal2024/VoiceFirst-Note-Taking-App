# Voice-First Accessible App Launcher (PowerShell)
Write-Host "=====================================================================" -ForegroundColor Yellow
Write-Host "   VOICE-FIRST: ACCESSIBLE VOICE NOTE-TAKING AND STUDY APP" -ForegroundColor Cyan
Write-Host "   Specially Engineered for Visually Impaired and Blind Students" -ForegroundColor Green
Write-Host "=====================================================================" -ForegroundColor Yellow
Write-Host ""

$PythonExe = "C:\Users\Priyanshi\AppData\Local\Programs\Python\Python314\python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python"
}

$FlutterBat = "C:\src\flutter\flutter\bin\flutter.bat"
if (-not (Test-Path $FlutterBat)) {
    $FlutterBat = "flutter"
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "[1/3] Environment verified." -ForegroundColor Cyan
Write-Host "Python  : $PythonExe"
Write-Host "Flutter : $FlutterBat"
Write-Host ""

Write-Host "[2/3] Launching Flask Backend on http://127.0.0.1:5000..." -ForegroundColor Cyan
Start-Process -FilePath "cmd.exe" -ArgumentList "/k cd /d `"$ScriptDir\backend`" && `"$PythonExe`" app.py" -WindowStyle Normal

Write-Host "Waiting 3 seconds for backend initialization..." -ForegroundColor Gray
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "[3/3] Launching Flutter Frontend on Chrome (Port 3000)..." -ForegroundColor Cyan
Write-Host "Tip: Press Spacebar in the app anytime to toggle microphone or interrupt speech!" -ForegroundColor Yellow
Write-Host ""

Set-Location -Path "$ScriptDir\frontend"
& $FlutterBat run -d chrome --web-port=3000
