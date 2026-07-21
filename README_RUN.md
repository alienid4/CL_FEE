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

## 8. Windows 這台機器常見的 commit 地雷

> **2026-07-21：專案已從 OneDrive 搬到 `C:\AiProject\CL_FEE`。**
> 下面標「OneDrive」的三項因此**不會再發生**，保留是為了：(1) 萬一日後有人又把 repo 放進
> 雲端同步資料夾，能認出症狀；(2) 記住為什麼不要那樣做。
> **只有「pre-commit hook」那項與 OneDrive 無關，現在仍然有效。**

- ~~**`git commit` 卡在 `unable to append to '.git/logs/HEAD'`**~~（搬離 OneDrive 後不再發生）：專案放在 OneDrive 同步資料夾裡，OneDrive 偶爾會鎖住 log 檔造成 git 寫不進去。一次性修：`git config windows.appendAtomically false`（本機 repo 設定，不影響其他機器）。
- **pre-commit hook 明明 checks 會過卻還是擋下**：這台的 PATH 把 `python` 指到 WindowsApps 的假樁執行檔（不會真的執行、也不報錯）。`.git/hooks/pre-commit` 已經改成自動找「py -3 / python3 / python」第一個能跑的直譯器，來源在 [docs/一次性開發提示詞_C1/kit/pre-commit](docs/一次性開發提示詞_C1/kit/pre-commit)；換新機器要重裝這個 hook 時記得從這份複製，不要抄舊版。
- **改完 pptx 之後 git add 說 Permission denied**：檔案還開在 PowerPoint（搬家前也可能是 OneDrive 正在同步）。關掉檔案再重試，或另存一份帶時間戳記的檔名先進版控，之後再取代。
- ~~**`git status` 突然把整個專案的檔案都列成「D」又同時列成「??」**~~（搬離 OneDrive 後不再發生）：不是真的刪檔、也沒有資料遺失，是 `.git/index` 這個 git 內部的記帳檔被 OneDrive 同步搞丟了（雲端佔位檔／搬移衝突造成）。確認方式：`ls .git/index` 顯示不存在。修法很安全、不會動到工作目錄裡的檔案：`git reset`（不加 `--hard`，預設 mixed 模式只重建 index、不碰檔案）。**看到「全專案突然整批 D+??」先別慌，更別下 `git checkout .` / `git clean -f`，先檢查 `.git/index` 是不是不見了。**
