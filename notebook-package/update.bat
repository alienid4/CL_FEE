@echo off
setlocal
cd /d "%~dp0"

set "REPO_ZIP_URL=https://github.com/alienid4/CL_FEE/archive/refs/heads/main.zip"
set "TMPZIP=%TEMP%\CL_FEE_update.zip"
set "TMPDIR=%TEMP%\CL_FEE_update_extract"

echo ============================================
echo   CL_FEE Update (download latest code)
echo ============================================
echo.
echo Downloading latest code from GitHub...
curl --ssl-no-revoke -L -o "%TMPZIP%" "%REPO_ZIP_URL%"
if errorlevel 1 (
    echo.
    echo Download failed. Check your network connection.
    pause
    exit /b 1
)

echo Extracting...
if exist "%TMPDIR%" rmdir /s /q "%TMPDIR%"
powershell -NoProfile -Command "Expand-Archive -Path '%TMPZIP%' -DestinationPath '%TMPDIR%' -Force"

echo Updating app and tests folders...
robocopy "%TMPDIR%\CL_FEE-main\app" "%~dp0app" /MIR /NFL /NDL /NJH /NJS >nul
robocopy "%TMPDIR%\CL_FEE-main\tests" "%~dp0tests" /MIR /NFL /NDL /NJH /NJS >nul
copy /Y "%TMPDIR%\CL_FEE-main\requirements.txt" "%~dp0requirements.txt" >nul
copy /Y "%TMPDIR%\CL_FEE-main\pytest.ini" "%~dp0pytest.ini" >nul

echo Cleaning up temp files...
del /q "%TMPZIP%" >nul 2>&1
rmdir /s /q "%TMPDIR%" >nul 2>&1

echo.
echo Reinstalling dependencies (in case new packages were added)...

REM On some Windows setups "python" is the Microsoft Store App Execution Alias, which
REM exits with 9009 without running anything. Probe for an interpreter that really works.
set "PY="
py -3 --version >nul 2>&1
if not errorlevel 1 (set "PY=py -3" & goto :py_ok)
python --version >nul 2>&1
if not errorlevel 1 (set "PY=python" & goto :py_ok)
python3 --version >nul 2>&1
if not errorlevel 1 (set "PY=python3" & goto :py_ok)
echo.
echo WARNING: no working Python 3 found ^(tried py -3, python, python3^).
echo The code was still updated; only the dependency install was skipped.
goto :deps_done

:py_ok
echo Using Python: %PY%
%PY% -m pip install -q -r requirements.txt
if errorlevel 1 echo WARNING: dependency install failed. The code itself was still updated.

:deps_done
echo.
echo ============================================
echo   Update complete!
echo   Restart the service (service.bat) to use the new code.
echo ============================================
pause
