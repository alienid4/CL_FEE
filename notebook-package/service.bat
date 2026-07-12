@echo off
setlocal
cd /d "%~dp0"
set PORT=8888

:menu
cls
echo ============================================
echo   CL_FEE Service Control (port %PORT%)
echo ============================================
echo.
echo   1. Start service
echo   2. Stop service
echo   3. Restart service
echo   0. Exit
echo.
set /p choice=Choose an option:

if "%choice%"=="1" goto do_start
if "%choice%"=="2" goto do_stop
if "%choice%"=="3" goto do_restart
if "%choice%"=="0" goto end
goto menu

:do_start
echo Starting service on port %PORT%...
start "CL_FEE_service" cmd /k "python -m uvicorn app.main:app --host 127.0.0.1 --port %PORT%"
timeout /t 2 >nul
start "" http://127.0.0.1:%PORT%
echo Started. Press any key to return to menu.
pause >nul
goto menu

:do_stop
echo Stopping service on port %PORT%...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :%PORT% ^| findstr LISTENING') do (
    taskkill /PID %%p /F >nul 2>&1
)
echo Stopped. Press any key to return to menu.
pause >nul
goto menu

:do_restart
echo Restarting service on port %PORT%...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :%PORT% ^| findstr LISTENING') do (
    taskkill /PID %%p /F >nul 2>&1
)
timeout /t 1 >nul
start "CL_FEE_service" cmd /k "python -m uvicorn app.main:app --host 127.0.0.1 --port %PORT%"
timeout /t 2 >nul
start "" http://127.0.0.1:%PORT%
echo Restarted. Press any key to return to menu.
pause >nul
goto menu

:end
endlocal
