@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ============================================
echo   CL_FEE 費用合約控管系統 - 一鍵啟動
echo ============================================
echo.

REM 1) 檢查 Python
where python >nul 2>nul
if errorlevel 1 (
    echo [錯誤] 找不到 python，請先安裝 Python 3.11+ 並確認已加入 PATH。
    pause
    exit /b 1
)

REM 2) 安裝套件（已裝過會很快跳過）
echo [1/4] 安裝套件中...
python -m pip install -q -r requirements.txt
python -m pip install -q httpx pytest
if errorlevel 1 (
    echo [錯誤] 套件安裝失敗，請檢查上方訊息。
    pause
    exit /b 1
)

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
python -m uvicorn app.main:app --host 127.0.0.1 --port 8025

pause
