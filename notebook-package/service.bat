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

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS1%"

if errorlevel 1 (
    echo.
    echo   The control panel exited with an error. See logs\service.log
    echo.
    pause
)

endlocal
