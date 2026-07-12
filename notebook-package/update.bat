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
curl -L -o "%TMPZIP%" "%REPO_ZIP_URL%"
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
python -m pip install -q -r requirements.txt

echo.
echo ============================================
echo   Update complete!
echo   Restart the service (service.bat) to use the new code.
echo ============================================
pause
