@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ============================================
echo   CL_FEE 費用合約控管系統 - 一鍵啟動
echo ============================================
echo.

REM 1) 找出一個「真的能跑」的 Python
REM    不能用 where python 判斷：Windows 預設在 WindowsApps 放了一個微軟商店的
REM    空殼 python.exe，where 找得到、執行卻立刻以 9009 結束且不印任何東西。
REM    舊版就是這樣「檢查通過、後面才silently失敗」，錯誤訊息叫人看上方訊息，
REM    但上方是空的。這裡改成實際執行 --version 驗證，能跑才算數。
set "PY="
py -3 --version >nul 2>&1
if not errorlevel 1 (set "PY=py -3" & goto :py_ok)
python --version >nul 2>&1
if not errorlevel 1 (set "PY=python" & goto :py_ok)
python3 --version >nul 2>&1
if not errorlevel 1 (set "PY=python3" & goto :py_ok)

echo [錯誤] 這台電腦找不到可以執行的 Python。
echo.
echo        注意：即使「開始功能表」看得到 Python，也可能是微軟商店的空殼程式
echo        （執行後立刻結束、不做任何事），那個不算數。
echo.
echo        請到 https://www.python.org/downloads/ 安裝 Python 3.11 以上，
echo        安裝時務必勾選「Add python.exe to PATH」。
echo.
pause
exit /b 1

:py_ok
echo [1/4] 使用 Python：!PY!
%PY% -m pip install -q -r requirements.txt
if errorlevel 1 goto :pip_failed
%PY% -m pip install -q httpx pytest
if errorlevel 1 goto :pip_failed
goto :pip_ok

:pip_failed
echo.
echo [錯誤] 套件安裝失敗。
echo        常見原因：沒有網路連線，或公司防火牆擋住 pip。
echo        可以手動執行下面這行看完整錯誤訊息：
echo            %PY% -m pip install -r requirements.txt
echo.
pause
exit /b 1

:pip_ok

REM 3) 沒有 .env 就自動建一份測試用的
if not exist ".env" (
    echo [2/4] 找不到 .env，自動建立測試用設定（密碼皆為 1qaz@WSX）...
    (
        echo SESSION_SECRET=%RANDOM%%RANDOM%%RANDOM%%RANDOM%%RANDOM%%RANDOM%%RANDOM%%RANDOM%
        echo AP01_PASSWORD=1qaz@WSX
        echo AP02_PASSWORD=1qaz@WSX
        echo AP03_PASSWORD=1qaz@WSX
        echo AP04_PASSWORD=1qaz@WSX
        echo ADMIN_PASSWORD=1qaz@WSX
    ) > .env
) else (
    echo [2/4] 已找到既有 .env，沿用。
)

REM 4) 啟動伺服器（用內附的測試資料 data\preview.db，免密碼登入模式）
echo [3/4] 啟動伺服器（http://127.0.0.1:8025）...
set SQLITE_PATH=data/preview.db
set PILOT_PASSWORDLESS=1
start "" http://127.0.0.1:8025
echo [4/4] 瀏覽器即將自動開啟，登入頁下拉選帳號即可（免密碼）。
echo       關閉這個黑色視窗即可停止伺服器。
echo.
%PY% -m uvicorn app.main:app --host 127.0.0.1 --port 8025

pause
