#!/bin/bash
# CL_FEE 一鍵啟動（macOS / Linux / Git Bash）
set -e
cd "$(dirname "$0")"

echo "============================================"
echo "  CL_FEE 費用合約控管系統 - 一鍵啟動"
echo "============================================"

command -v python3 >/dev/null 2>&1 && PY=python3 || PY=python
if ! command -v "$PY" >/dev/null 2>&1; then
    echo "[錯誤] 找不到 python，請先安裝 Python 3.11+"
    exit 1
fi

echo "[1/4] 安裝套件中..."
"$PY" -m pip install -q -r requirements.txt
"$PY" -m pip install -q httpx pytest

if [ ! -f .env ]; then
    echo "[2/4] 找不到 .env，自動建立測試用設定（密碼皆為 1qaz@WSX）..."
    cat > .env <<EOF
SESSION_SECRET=$(openssl rand -hex 32 2>/dev/null || echo "$RANDOM$RANDOM$RANDOM$RANDOM")
AP01_PASSWORD=1qaz@WSX
AP02_PASSWORD=1qaz@WSX
AP03_PASSWORD=1qaz@WSX
AP04_PASSWORD=1qaz@WSX
ADMIN_PASSWORD=1qaz@WSX
EOF
else
    echo "[2/4] 已找到既有 .env，沿用。"
fi

echo "[3/4] 啟動伺服器（http://127.0.0.1:8025）..."
export SQLITE_PATH=data/preview.db
export PILOT_PASSWORDLESS=1
echo "[4/4] 請自行開瀏覽器連 http://127.0.0.1:8025 ，登入頁下拉選帳號即可（免密碼）。"
echo "      Ctrl+C 即可停止伺服器。"
"$PY" -m uvicorn app.main:app --host 127.0.0.1 --port 8025
