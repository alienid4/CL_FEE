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

echo   [1/5] Downloading latest code from GitHub...
curl -sS --ssl-no-revoke -L -o "%TMPZIP%" "%REPO_ZIP_URL%"
if errorlevel 1 (
    echo.
    echo   FAILED: could not download from GitHub.
    echo   Check the network connection, then run this again.
    echo.
    pause
    exit /b 1
)

echo   [2/5] Extracting...
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

echo   [3/5] Updating app and tests folders...
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
REM  requirements.txt pulls in requirements-runtime.txt with a -r line, so the
REM  two files must always travel together. Copying only the first one leaves a
REM  requirements.txt pointing at a file that is missing (or worse, stale), and
REM  pip fails with an error that says nothing about the real cause.
copy /Y "%SRC%\requirements-runtime.txt" "%~dp0requirements-runtime.txt" >nul
copy /Y "%SRC%\pytest.ini" "%~dp0pytest.ini" >nul

REM --- Helper scripts (service.bat / service.ps1 / docs) ----------------------
REM  These used to be left behind: only app\ and tests\ were mirrored, so a fix
REM  to the control panel itself could never reach the machines that needed it.
REM  The scripts live in notebook-package\ inside the repo, so they are already
REM  in the zip we just extracted - they just were not copied out.
echo   [4/5] Updating helper scripts...
set "PKG=%SRC%\notebook-package"
if not exist "%PKG%\service.ps1" (
    echo         SKIPPED: notebook-package not found in the download.
    echo         The code is updated; only the helper scripts were left as-is.
    goto :helpers_done
)
REM  demo_start.bat / demo_start.sh are deliberately NOT synced. They launch a
REM  different thing: port 8025 against data\preview.db (a throwaway demo
REM  database that gets auto-created empty), while service.bat runs the real
REM  system on 8888 against data\fee_control.db. They used to be called
REM  start.bat / start.sh, which read like the obvious button to press - the
REM  demo_ prefix is there so nobody has to read a document to tell them apart.
REM  NOTEBOOK_SETUP.md is also skipped: it documents the 8025 demo mode, which
REM  is not what a deployment machine runs. Shipping it there just invites
REM  someone to follow instructions for the wrong system.
for %%F in (service.bat service.ps1) do (
    if exist "%PKG%\%%F" copy /Y "%PKG%\%%F" "%~dp0%%F" >nul
)

REM  download.bat and update.bat cannot overwrite themselves while running:
REM  cmd.exe reads a .bat incrementally from disk, so replacing the file
REM  mid-run makes it jump to garbage. Stage them as .new and let a background
REM  helper swap them in after this window closes.
set "STAGED="
for %%F in (download.bat update.bat) do (
    if exist "%PKG%\%%F" (
        fc /b "%PKG%\%%F" "%~dp0%%F" >nul 2>&1
        if errorlevel 1 (
            copy /Y "%PKG%\%%F" "%~dp0%%F.new" >nul
            set "STAGED=1"
        )
    )
)
if defined STAGED echo         Note: this updater itself was updated - it takes effect next run.
echo         OK

:helpers_done

del /q "%TMPZIP%" >nul 2>&1
rmdir /s /q "%TMPDIR%" >nul 2>&1

REM --- Dependencies. Optional: the code is already updated at this point. -----
echo   [5/5] Checking dependencies...
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
REM  Runtime deps only, matching service.ps1. A deployed machine only has to run
REM  the system, not test it; playwright in particular downloads browser binaries
REM  on top of a large wheel, which is an extra failure point on a locked-down
REM  corporate network for something this machine never uses.
%PY% -m pip install -q --disable-pip-version-check --no-warn-script-location -r requirements-runtime.txt >nul 2>&1
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

REM --- Swap in the staged updater after this window exits ---------------------
REM  Runs detached, waits for us to finish, moves the .new files into place,
REM  then deletes itself. Nothing here can break the current run.
if defined STAGED (
    > "%TEMP%\cl_fee_dl_swap.bat" echo @echo off
    >> "%TEMP%\cl_fee_dl_swap.bat" echo timeout /t 3 /nobreak ^>nul 2^>^&1
    >> "%TEMP%\cl_fee_dl_swap.bat" echo if exist "%~dp0download.bat.new" move /y "%~dp0download.bat.new" "%~dp0download.bat" ^>nul 2^>^&1
    >> "%TEMP%\cl_fee_dl_swap.bat" echo if exist "%~dp0update.bat.new" move /y "%~dp0update.bat.new" "%~dp0update.bat" ^>nul 2^>^&1
    >> "%TEMP%\cl_fee_dl_swap.bat" echo del "%%~f0" ^>nul 2^>^&1
    start "" /min "%TEMP%\cl_fee_dl_swap.bat"
)

pause
endlocal
