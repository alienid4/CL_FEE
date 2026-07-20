@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

REM ============================================================================
REM  ASCII ONLY ON PURPOSE. Do not put Chinese text in this file.
REM  cmd.exe parses .bat using the system ANSI codepage (cp950/Big5 here), and
REM  several Big5 characters end with byte 0x5C, which cmd treats as an escape.
REM  Chinese text in a .bat WILL eventually break the parser.
REM
REM  This script also deliberately keeps the console quiet. curl's progress table
REM  and pip's "WARNING/notice" lines are harmless, but they look like failures
REM  to anyone who is not a developer, and that is exactly how a successful
REM  update gets reported as "it failed".
REM ============================================================================

set "REPO_ZIP_URL=https://github.com/alienid4/CL_FEE/archive/refs/heads/main.zip"
set "TMPZIP=%TEMP%\CL_FEE_update.zip"
set "TMPDIR=%TEMP%\CL_FEE_update_extract"
set "SRC=%TMPDIR%\CL_FEE-main"

echo ============================================
echo   CL_FEE Update
echo ============================================
echo.

REM --- Record the version we have right now, so we can prove it changed -------
set "OLDVER=(unknown)"
if exist "%~dp0app\main.py" (
    for /f "tokens=2 delims== " %%v in ('findstr /c:"BACKEND_BUILD = " "%~dp0app\main.py"') do (
        if "!OLDVER!"=="(unknown)" set "OLDVER=%%~v"
    )
)
for /f "tokens=1 delims= " %%a in ("!OLDVER!") do set "OLDVER=%%a"
echo   Current version: !OLDVER!
echo.

echo   [1/4] Downloading latest code from GitHub...
curl -sS --ssl-no-revoke -L -o "%TMPZIP%" "%REPO_ZIP_URL%"
if errorlevel 1 (
    echo.
    echo   FAILED: could not download from GitHub.
    echo   Check the network connection, then run this again.
    echo.
    pause
    exit /b 1
)

echo   [2/4] Extracting...
if exist "%TMPDIR%" rmdir /s /q "%TMPDIR%"
powershell -NoProfile -Command "Expand-Archive -Path '%TMPZIP%' -DestinationPath '%TMPDIR%' -Force" >nul 2>&1
if not exist "%SRC%\app\main.py" (
    echo.
    echo   FAILED: the downloaded package looks wrong ^(app\main.py missing^).
    echo   The download may have been cut short. Run this again.
    echo.
    pause
    exit /b 1
)

echo   [3/4] Updating app and tests folders...
robocopy "%SRC%\app" "%~dp0app" /MIR /NFL /NDL /NJH /NJS >nul
if errorlevel 8 (
    echo.
    echo   FAILED: could not replace the app folder.
    echo   Usually this means the service is still running and holding files.
    echo   Open service.bat, choose 2 to stop it, then run this again.
    echo.
    pause
    exit /b 1
)
robocopy "%SRC%\tests" "%~dp0tests" /MIR /NFL /NDL /NJH /NJS >nul
copy /Y "%SRC%\requirements.txt" "%~dp0requirements.txt" >nul
copy /Y "%SRC%\pytest.ini" "%~dp0pytest.ini" >nul

del /q "%TMPZIP%" >nul 2>&1
rmdir /s /q "%TMPDIR%" >nul 2>&1

REM --- Dependencies. Optional: the code is already updated at this point. -----
echo   [4/4] Checking dependencies...
set "PY="
py -3 --version >nul 2>&1
if not errorlevel 1 (set "PY=py -3" & goto :py_ok)
python --version >nul 2>&1
if not errorlevel 1 (set "PY=python" & goto :py_ok)
python3 --version >nul 2>&1
if not errorlevel 1 (set "PY=python3" & goto :py_ok)
echo         No working Python found - skipped ^(code was still updated^).
goto :deps_done

:py_ok
%PY% -m pip install -q --disable-pip-version-check --no-warn-script-location -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo         Dependency install failed - skipped ^(code was still updated^).
    echo         If the system does not start, open service.bat and choose 6.
) else (
    echo         OK
)

:deps_done

REM --- Prove it worked: show the version we ended up with ---------------------
set "NEWVER=(unknown)"
for /f "tokens=2 delims== " %%v in ('findstr /c:"BACKEND_BUILD = " "%~dp0app\main.py"') do (
    if "!NEWVER!"=="(unknown)" set "NEWVER=%%~v"
)
for /f "tokens=1 delims= " %%a in ("!NEWVER!") do set "NEWVER=%%a"

echo.
echo ============================================
if "!OLDVER!"=="!NEWVER!" (
    echo   Already up to date.
    echo   Version: !NEWVER!
) else (
    echo   Update complete.
    echo   !OLDVER!  --^>  !NEWVER!
)
echo ============================================
echo.
echo   Next: open service.bat and choose 3 to restart,
echo         then press Ctrl+Shift+R in the browser.
echo.
pause
endlocal
