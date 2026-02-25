@echo off
setlocal enabledelayedexpansion

set "ROOT=%~dp0"
cd /d "%ROOT%"

set "RELEASE_DIR=build\portable"
set "APP_DIR=%RELEASE_DIR%\app"
set "BACKEND_DIR=%RELEASE_DIR%\backend"
set "FRONTEND_SRC="
set "FRONTEND_EXE="
set "LOG_FILE=package.log.txt"
set "ROBO_OPTS=/E /R:1 /W:1"

> "%LOG_FILE%" echo [%DATE% %TIME%] package.bat started in %CD%

call :log [package] Preparing portable release layout...
if exist "%RELEASE_DIR%" (
    call :log [package] Cleaning existing "%RELEASE_DIR%"...
    rmdir /S /Q "%RELEASE_DIR%" >> "%LOG_FILE%" 2>&1
    if exist "%RELEASE_DIR%" (
        call :log [package] ERROR: Unable to clean "%RELEASE_DIR%". Close running app/processes and retry.
        exit /b 1
    )
)

mkdir "%APP_DIR%" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    call :log [package] ERROR: Failed to create "%APP_DIR%".
    exit /b 1
)
mkdir "%BACKEND_DIR%" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    call :log [package] ERROR: Failed to create "%BACKEND_DIR%".
    exit /b 1
)

call :detect_frontend_runtime
if not defined FRONTEND_SRC (
    call :log [package] ERROR: Frontend executable not found.
    call :log [package] Build frontend first from frontend/ using: npm run electron:build
    call :log [package] Checked: frontend\dist_electron\win-unpacked, frontend\dist_electron\win-x64-unpacked, frontend\dist_electron\win-arm64-unpacked, frontend\dist_electron\app, build\app
    exit /b 1
)

call :log [package] Copying frontend runtime from "%FRONTEND_SRC%" (entry exe: "%FRONTEND_EXE%")...
robocopy "%FRONTEND_SRC%" "%APP_DIR%" %ROBO_OPTS% /NFL /NDL /NJH /NJS /NP >> "%LOG_FILE%" 2>&1
set "ROBO_CODE=%ERRORLEVEL%"
if !ROBO_CODE! GEQ 8 (
    call :log [package] ERROR: Failed to copy frontend runtime - robocopy code !ROBO_CODE!.
    call :log [package] See "%LOG_FILE%" for details.
    exit /b 1
)

call :log [package] Copying backend runtime assets...
robocopy "backend" "%BACKEND_DIR%" %ROBO_OPTS% /NFL /NDL /NJH /NJS /NP /XF *.pyc /XD ^
    ".venv" ^
    ".vscode" ^
    ".pytest_cache" ^
    "tests" ^
    "__pycache__" ^
    "build_py" ^
    "dist_py" >> "%LOG_FILE%" 2>&1
set "ROBO_CODE=%ERRORLEVEL%"
if !ROBO_CODE! GEQ 8 (
    call :log [package] ERROR: Failed to copy backend runtime - robocopy code !ROBO_CODE!.
    call :log [package] See "%LOG_FILE%" for details.
    exit /b 1
)

call :log [package] Copying launcher/config artifacts...
copy /Y "run.bat" "%RELEASE_DIR%\run.bat" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    call :log [package] ERROR: Failed to copy run.bat.
    exit /b 1
)
if exist "setup-config.bat" copy /Y "setup-config.bat" "%RELEASE_DIR%\setup-config.bat" >> "%LOG_FILE%" 2>&1
if exist "config.template.json" copy /Y "config.template.json" "%RELEASE_DIR%\config.template.json" >> "%LOG_FILE%" 2>&1
if exist ".env.example" copy /Y ".env.example" "%RELEASE_DIR%\.env.example" >> "%LOG_FILE%" 2>&1
if exist "translators.json" copy /Y "translators.json" "%RELEASE_DIR%\translators.json" >> "%LOG_FILE%" 2>&1
if exist "scripts" (
    robocopy "scripts" "%RELEASE_DIR%\scripts" %ROBO_OPTS% /NFL /NDL /NJH /NJS /NP >> "%LOG_FILE%" 2>&1
    set "ROBO_CODE=%ERRORLEVEL%"
    if !ROBO_CODE! GEQ 8 (
        call :log [package] ERROR: Failed to copy scripts folder - robocopy code !ROBO_CODE!.
        call :log [package] See "%LOG_FILE%" for details.
        exit /b 1
    )
)

call :log [package] Running release smoke check...
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\release_smoke_check.ps1" -ReleaseDir "%RELEASE_DIR%" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    call :log [package] ERROR: Release smoke check failed. See "%LOG_FILE%".
    exit /b 1
)

call :log [package] Portable release assembled at "%RELEASE_DIR%".
call :log [package] Detailed logs: "%LOG_FILE%".
exit /b 0

:detect_frontend_runtime
set "FRONTEND_SRC="
set "FRONTEND_EXE="

call :try_frontend_dir "frontend\dist_electron\app"
if defined FRONTEND_SRC exit /b 0
call :try_frontend_dir "frontend\dist_electron\win-unpacked"
if defined FRONTEND_SRC exit /b 0
call :try_frontend_dir "frontend\dist_electron\win-x64-unpacked"
if defined FRONTEND_SRC exit /b 0
call :try_frontend_dir "frontend\dist_electron\win-arm64-unpacked"
if defined FRONTEND_SRC exit /b 0
call :try_frontend_dir "build\app"
if defined FRONTEND_SRC exit /b 0

exit /b 0

:try_frontend_dir
set "CANDIDATE_DIR=%~1"
if not exist "%CANDIDATE_DIR%" exit /b 0

for /f "delims=" %%F in ('dir /b /a-d "%CANDIDATE_DIR%\*.exe" 2^>nul') do (
    if /I not "%%~F"=="elevate.exe" (
        set "FRONTEND_SRC=%CANDIDATE_DIR%"
        set "FRONTEND_EXE=%%~F"
        exit /b 0
    )
)

exit /b 0

:log
echo %*
>> "%LOG_FILE%" echo %*
exit /b 0
