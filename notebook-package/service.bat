@echo off
setlocal
cd /d "%~dp0"
set PORT=8888
set "LOGDIR=%~dp0logs"
set "LOGFILE=%LOGDIR%\service.log"

if not exist "%LOGDIR%" mkdir "%LOGDIR%"

:menu
cls
echo ============================================
echo   CL_FEE Service Control (port %PORT%)
echo ============================================
echo.
echo   1. Start service
echo   2. Stop service
echo   3. Restart service
echo   4. Status
echo   5. View recent log (last 50 lines)
echo   0. Exit
echo.
echo   Log file: %LOGFILE%
echo.
set /p choice=Choose an option:

if "%choice%"=="1" goto do_start
if "%choice%"=="2" goto do_stop
if "%choice%"=="3" goto do_restart
if "%choice%"=="4" goto do_status
if "%choice%"=="5" goto do_log
if "%choice%"=="0" goto end
goto menu

:do_start
echo Starting service on port %PORT%...
echo ---- start %DATE% %TIME% ---- >> "%LOGFILE%"
start "CL_FEE_service" powershell -NoProfile -Command "python -m uvicorn app.main:app --host 127.0.0.1 --port %PORT% 2>&1 | Tee-Object -FilePath '%LOGFILE%' -Append"
timeout /t 2 >nul
start "" http://127.0.0.1:%PORT%
echo Started. Press any key to return to menu.
pause >nul
goto menu

:do_stop
echo Stopping service on port %PORT%...
echo ---- stop %DATE% %TIME% ---- >> "%LOGFILE%"
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :%PORT% ^| findstr LISTENING') do (
    taskkill /PID %%p /F >nul 2>&1
)
echo Stopped. Press any key to return to menu.
pause >nul
goto menu

:do_restart
echo Restarting service on port %PORT%...
echo ---- restart %DATE% %TIME% ---- >> "%LOGFILE%"
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :%PORT% ^| findstr LISTENING') do (
    taskkill /PID %%p /F >nul 2>&1
)
timeout /t 1 >nul
start "CL_FEE_service" powershell -NoProfile -Command "python -m uvicorn app.main:app --host 127.0.0.1 --port %PORT% 2>&1 | Tee-Object -FilePath '%LOGFILE%' -Append"
timeout /t 2 >nul
start "" http://127.0.0.1:%PORT%
echo Restarted. Press any key to return to menu.
pause >nul
goto menu

:do_status
echo.
set FOUND=0
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :%PORT% ^| findstr LISTENING') do (
    set FOUND=1
    echo Service IS RUNNING on port %PORT% (PID %%p)
)
if "%FOUND%"=="0" echo Service is NOT running on port %PORT%.
echo.
echo Press any key to return to menu.
pause >nul
goto menu

:do_log
echo.
if not exist "%LOGFILE%" (
    echo No log file yet. Start the service first.
) else (
    powershell -NoProfile -Command "Get-Content -Path '%LOGFILE%' -Tail 50"
)
echo.
echo Press any key to return to menu.
pause >nul
goto menu

:end
endlocal
