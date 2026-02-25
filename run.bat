@echo off
setlocal

set "ROOT=%~dp0"
set "LAUNCHER=%ROOT%scripts\launcher.ps1"

if not exist "%LAUNCHER%" (
    echo [launcher] ERROR: Missing launcher script "%LAUNCHER%".
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%LAUNCHER%" %*
set "EXIT_CODE=%ERRORLEVEL%"
exit /b %EXIT_CODE%
