@echo off
setlocal

REM ============================================================================
REM  ASCII ONLY ON PURPOSE (Big5 escape-byte problem - see downloadpatch.bat).
REM
REM  This file was renamed to downloadpatch.bat and moved to the project root,
REM  next to upload.bat: "upload / downloadpatch" reads as one pair and says
REM  which way it goes, and sitting in the root removes the "copy it to the root
REM  first" step (the script uses its own folder as the project root).
REM  Machines that already have this old name keep working through this shim
REM  instead of silently doing nothing.
REM ============================================================================

echo.
echo   NOTE: download.bat has been renamed to downloadpatch.bat
echo         ^(upload = send to GitHub, downloadpatch = get the patch from GitHub^)
echo.

if exist "%~dp0downloadpatch.bat" (
    echo   Running downloadpatch.bat for you now...
    echo.
    call "%~dp0downloadpatch.bat"
    endlocal
    exit /b 0
)

REM  One level up: on a machine where this shim still sits in notebook-package\
REM  while the new updater already landed in the project root.
if exist "%~dp0..\downloadpatch.bat" (
    echo   Running downloadpatch.bat from the project root...
    echo.
    call "%~dp0..\downloadpatch.bat"
    endlocal
    exit /b 0
)

echo   ERROR: downloadpatch.bat not found.
echo   Run this updater once more, or download the package again.
echo.
pause
endlocal
exit /b 1
