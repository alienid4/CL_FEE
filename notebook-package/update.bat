@echo off
setlocal

REM ============================================================================
REM  ASCII ONLY ON PURPOSE (Big5 escape-byte problem - see download.bat).
REM
REM  This file is now called downloadpatch.bat and lives in the project root
REM  (it was update.bat, then download.bat). "upload / downloadpatch" is an
REM  obvious pair and says which way it goes. Machines that still have this old
REM  name keep working through this shim instead of silently doing nothing.
REM ============================================================================

echo.
echo   NOTE: update.bat is now called downloadpatch.bat
echo         ^(upload = send to GitHub, downloadpatch = get the patch from GitHub^)
echo.

for %%P in ("%~dp0downloadpatch.bat" "%~dp0..\downloadpatch.bat" "%~dp0download.bat") do (
    if exist %%P (
        echo   Running %%~nxP for you now...
        echo.
        call %%P
        endlocal
        exit /b 0
    )
)

echo   ERROR: downloadpatch.bat not found.
echo   Run the updater once more, or download the package again.
echo.
pause
endlocal
exit /b 1
