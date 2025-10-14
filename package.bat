@echo off
setlocal enabledelayedexpansion

REM Copy backend =======================================================================================================

REM Source and destination directories
set SRC=backend
set DEST=build\backend
set BUILDDIR=build

echo Cleaning build directory...
if exist "%BUILDDIR%" (
    rmdir /S /Q "%DEST%"
)
mkdir "%DEST%"

echo Copying backend files to build folder...
echo.

REM Use robocopy to copy everything except excluded folders
robocopy "%SRC%" "%DEST%" /E /XD ^
    ".venv" ^
    ".vscode" ^
    ".pytest_cache" ^
    "tests"

REM Check robocopy result
if %ERRORLEVEL% LSS 8 (
    echo Copy completed successfully.
) else (
    echo Copy encountered an error.
)

endlocal
pause
