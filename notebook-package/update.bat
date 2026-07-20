@echo off
setlocal

REM ============================================================================
REM  ASCII ONLY ON PURPOSE (Big5 escape-byte problem - see download.bat).
REM
REM  This file was renamed to download.bat, because "upload / download" is an
REM  obvious pair while "upload / update" differs by two letters and points the
REM  opposite way. Machines that already have a copy of the old name keep
REM  working through this shim instead of silently doing nothing.
REM ============================================================================

echo.
echo   NOTE: update.bat has been renamed to download.bat
echo         ^(upload = send to GitHub, download = get from GitHub^)
echo.
echo   Running download.bat for you now...
echo.

if not exist "%~dp0download.bat" (
    echo   ERROR: download.bat not found next to this file.
    echo   Copy the whole notebook-package folder again.
    echo.
    pause
    exit /b 1
)

call "%~dp0download.bat"
endlocal
