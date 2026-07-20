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
REM  All user-facing text and logic live in upload.ps1 (UTF-8) instead.
REM  This file only launches it.
REM
REM  The pause at the end is UNCONDITIONAL on purpose: if PowerShell fails to
REM  start at all (blocked execution policy, missing powershell.exe, syntax
REM  error in the .ps1), the window would otherwise close instantly and the
REM  user would see nothing at all. Never let this window vanish silently.
REM ============================================================================

set "PS1=%~dp0upload.ps1"
set "ERRLOG=%~dp0logs\upload_error.log"

if not exist "%~dp0logs" mkdir "%~dp0logs" >nul 2>&1

if not exist "%PS1%" (
    echo.
    echo   ERROR: upload.ps1 not found next to this file.
    echo   Expected: %PS1%
    echo.
    echo   Copy the whole CL_FEE folder, not just the .bat file.
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

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS1%" 2>"%ERRLOG%"
set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
    echo.
    echo ============================================================
    echo   The upload tool stopped with exit code %RC%.
    echo ============================================================
    echo.
    echo   Error output ^(also saved to logs\upload_error.log^):
    echo ------------------------------------------------------------
    type "%ERRLOG%" 2>nul
    echo ------------------------------------------------------------
    echo.
    echo   Common causes:
    echo     - PowerShell execution policy blocked by company Group Policy
    echo     - git not installed or not on PATH
    echo     - upload.ps1 was edited and now has a syntax error
    echo.
)

echo.
pause
endlocal
