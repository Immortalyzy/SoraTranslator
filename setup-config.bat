@echo off
setlocal

for %%I in ("%~dp0.") do set "ROOT=%%~fI"
set "SETUP_SCRIPT=%ROOT%\scripts\setup-config.ps1"

if not exist "%SETUP_SCRIPT%" (
    echo [setup] ERROR: Missing setup script at "%SETUP_SCRIPT%".
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%SETUP_SCRIPT%" -RootPath "%ROOT%"
set "SETUP_EXIT=%ERRORLEVEL%"
if %SETUP_EXIT% NEQ 0 (
    echo [setup] Setup failed.
    exit /b %SETUP_EXIT%
)

echo [setup] Configuration completed.
exit /b 0
