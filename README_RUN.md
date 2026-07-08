# CL_FEE 費用合約控管系統 — 執行說明（pilot）

FastAPI + SQLite 的本機試營運版。單機、免安裝資料庫伺服器。

## 1. 環境需求
- Python 3.11+（開發用 3.13）
- 套件：`fastapi`、`uvicorn`、`pydantic`（測試另需 `httpx`、`pytest`、`playwright`）

```bash
pip install fastapi uvicorn pydantic httpx pytest
python -m playwright install chromium   # 只有要跑 E2E 才需要
```

## 2. 設定 .env（放在專案根目錄，已被 gitignore）
```
SESSION_SECRET=<自己產一組 64 位十六進位亂數>
AP01_PASSWORD=<CIO 密碼>
AP02_PASSWORD=<主管/助理 密碼>
AP03_PASSWORD=<承辦 密碼>
AP04_PASSWORD=<助理B 密碼>
```
> 測試階段四組密碼統一為 `1qaz@WSX`。正式 pilot 請各自改成不同強密碼。
> 未設定的帳號無法登入；密碼絕不寫進原始碼。

## 3. 啟動
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
瀏覽器開 http://127.0.0.1:8000 。

## 4. 帳號與角色
| 帳號 | 角色 | 看得到什麼 |
|---|---|---|
| ap01 | CIO | 只有「決策總覽」：資金看板、圖表、下月要出的款、逐層下探。唯讀。 |
| ap02 | 主管/助理 | 全功能：八大模組、雙人複核、催辦、匯出。 |
| ap03 | 承辦 | 只看自己案件（含案件下的合約/付款/專案/請購/簽呈）。 |
| ap04 | 助理B | 同 ap02；用於雙人複核（不能核自己建的案件，需另一位助理）。 |
| admin | 系統管理員 | 只進「系統管理」後台：SMTP/通知設定、系統狀態、稽核紀錄。 |

> 密碼由 `AP01~AP04_PASSWORD` 與 `ADMIN_PASSWORD` 環境變數提供。
> **SMTP／email 通知請登入 admin，到「系統管理」後台設定**（不需改檔）；密碼存 DB、不回顯。

## 5. 快速體驗
1. 用 **ap02** 登入 →「案件管理 / 主管儀表板」→ 按「載入示範資料」（明顯標示 DEMO-）。
2. 逛八大模組、看圖表與催辦清單。
3. 登出換 **ap01（CIO）** 看決策總覽。
4. 正式上線前，用 ap02 按「清空示範資料」。

## 6. 測試
```bash
python -m pytest -q          # 單元/整合測試
python tests/e2e_ui.py       # 端到端（真 Chromium）
python .project/checks.py    # C1 關卡：git/密鑰/測試/決策一致
```

## 7. 資料庫
- 預設 SQLite 檔（路徑由 `SQLITE_PATH` 環境變數決定，未設則用專案內建路徑）。
- 備份＝複製該 .db 檔；還原＝覆蓋回去。
- 遷 MSSQL 為未來規劃，見 [KNOWN_LIMITS.md](KNOWN_LIMITS.md)。
