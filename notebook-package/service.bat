@echo off
setlocal

REM ============================================================================
REM  ASCII ONLY ON PURPOSE. Do not put Chinese text in this file.
REM
REM  cmd.exe parses .bat using the system ANSI codepage (cp950/Big5 on a
REM  Traditional Chinese Windows). Several Big5 characters have a trailing byte
REM  of 0x5C, which cmd treats as an escape character, so the line falls apart
REM  and you get errors like "'xx' is not recognized as an internal command".
REM
REM  All user-facing text and logic live in service.ps1 (UTF-8) instead.
REM  This file only launches it.
REM ============================================================================

set "PS1=%~dp0service.ps1"

if not exist "%PS1%" (
    echo.
    echo   ERROR: service.ps1 not found next to this file.
    echo   Expected: %PS1%
    echo.
    echo   Copy the whole notebook-package folder, not just the .bat file.
    echo.
    pause
    exit /b 1
)

where powershell >nul 2>&1
if errorlevel 1 (
    echo.
    echo   ERROR: powershell.exe not found on this machine.
    echo   This tool needs Windows PowerShell 5.1 or later.
    echo.
    pause
    exit /b 1
)

if not exist "%~dp0logs" mkdir "%~dp0logs" >nul 2>&1
set "ERRLOG=%~dp0logs\service_error.log"

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS1%" 2>"%ERRLOG%"
set "RC=%ERRORLEVEL%"

REM Unconditional pause: if PowerShell fails to start at all (blocked execution
REM policy, syntax error in the .ps1), the window would otherwise close instantly
REM and the user would see nothing. Never let this window vanish silently.
if not "%RC%"=="0" (
    echo.
    echo ============================================================
    echo   The control panel stopped with exit code %RC%.
    echo ============================================================
    echo.
    echo   Error output ^(also saved to logs\service_error.log^):
    echo ------------------------------------------------------------
    type "%ERRLOG%" 2>nul
    echo ------------------------------------------------------------
    echo.
    echo   Common causes:
    echo     - PowerShell execution policy blocked by company Group Policy
    echo     - service.ps1 was edited and now has a syntax error
    echo.
)

echo.
pause
endlocal
