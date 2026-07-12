# 這份打包內容說明（給另一台 Notebook 用）

這是從家用機打包出來的**測試用副本**，不含 `.git` 版控歷史（沒有設定 GitHub remote，
以後更新走「重新打包 patch zip」的方式，見下方「以後怎麼更新」），
也**不含 `.env`**（裡面有真實密碼／SESSION_SECRET，基於安全考量沒放進來——一鍵啟動腳本會自動幫你補一份測試用的）。

## 一鍵啟動（推薦）

- **Windows**：直接雙擊 **`start.bat`**
- **macOS / Linux / Git Bash**：終端機執行 `bash start.sh`

腳本會自動：① 裝套件 ② 沒有 `.env` 就自動生一份（密碼都是 `1qaz@WSX`）③ 用內附的
`data/preview.db` 啟動伺服器 ④（Windows 版）自動開瀏覽器連 http://127.0.0.1:8025 。
第一次跑會裝套件、慢一點；之後每次啟動幾乎瞬間。**關掉黑色視窗／按 Ctrl+C 即可停止。**

若沒有 Python，腳本會提示你先安裝 Python 3.11+（記得裝的時候勾選「Add to PATH」）。

登入頁因為是免密碼模式，直接下拉選帳號（見下方帳號表）即可，不用打密碼。

---

## 以後怎麼更新（上 patch）

沒有設定 git remote，所以更新走「重新打包只含程式碼的 patch zip」：

1. 家用機這邊改完、確認測試過後，跑 `scripts/package_notebook_patch.ps1`，
   會在專案根目錄生出 `CL_FEE_patch_<版本號>.zip`（**只含 `app/`、`tests/`、
   `requirements.txt`、`pytest.ini`**，不含 `data/`、`.env`、`.claude`）。
2. 把這個 patch zip 傳到 Notebook 上，**直接解壓縮覆蓋**到現有的專案資料夾。
   因為 patch zip 裡沒有 `data/`、`.env` 這些檔案，Notebook 上原本的測試資料
   跟帳號密碼設定**不會被動到**，可以放心覆蓋。
3. 重新執行 `start.bat` / `start.sh`（會自動重裝套件，若有新增依賴會一併裝上）。

> 提醒：Notebook 上如果自己新增/修改過測試資料（`data/preview.db`），
> 這個更新方式完全不會碰到它，資料會維持 Notebook 自己累積的狀態。

---

## 手動啟動（腳本跑不動、或要自訂設定時才需要）

### 1. 安裝套件
```bash
cd CL_FEE_package
pip install -r requirements.txt
pip install httpx pytest          # 測試用
python -m playwright install chromium   # 只有要跑 E2E (tests/e2e_ui.py) 才需要
```

### 2. 建立 .env（放在專案根目錄，同 `.env.example` 格式）
```
SESSION_SECRET=<自己隨便打一串英數混合的長字串>
AP01_PASSWORD=1qaz@WSX
AP02_PASSWORD=1qaz@WSX
AP03_PASSWORD=1qaz@WSX
AP04_PASSWORD=1qaz@WSX
ADMIN_PASSWORD=1qaz@WSX
```
（測試方便可以四組密碼都設一樣；正式使用請改成各自不同的強密碼。）

### 3. 啟動（用內附的測試資料 `data/preview.db`）
```bash
# Windows PowerShell
$env:SQLITE_PATH="data/preview.db"; $env:PILOT_PASSWORDLESS="1"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8025
```
```bash
# Git Bash / macOS / Linux
SQLITE_PATH=data/preview.db PILOT_PASSWORDLESS=1 python -m uvicorn app.main:app --host 127.0.0.1 --port 8025
```
瀏覽器開 http://127.0.0.1:8025 。

`PILOT_PASSWORDLESS=1` 是測試用的免密碼登入（登入頁直接下拉選帳號、不用打密碼）。
**正式環境不要開這個環境變數**，一律要密碼。

---

## 內附的測試資料裡有什麼
`data/preview.db` 是打包當下（2026-07-12）家用機 8025 預覽站的完整快照，包含：
- 5 個內建帳號（ap01~ap04、admin，見下表）
- 1 個自建測試帳號 **ap10 / 洪似妮（承辦）**——免密碼登入模式下登入頁下拉會看到
- 34 筆案件（含真實匯入的專案資料，如 EDR、AI專案系列等），部分案件負責人顯示「未指派」
  是正常現象（負責人姓名對不到任何登入帳號時，系統刻意留白不瞎猜，不是 bug）

| 帳號 | 角色 | 看得到什麼 |
|---|---|---|
| ap01 | CIO | 只有「決策總覽」，唯讀 |
| ap02 | 主管/助理 | 全功能，含主管儀表板/系統工具等維運功能 |
| ap03 | 承辦 | 只看自己案件範圍 |
| ap04 | 助理B | 同 ap02，用於雙人複核 |
| ap10 | 承辦（洪似妮） | 只看自己案件範圍 |
| admin | 系統管理員 | 只進「系統管理」後台 |

## 測試（選用）
```bash
python -m pytest -q
```
應該全過（截至打包當下 232 個測試）。

## 版本
打包當下版本：**v0.9.98**（見 `app/main.py` 的 `BACKEND_BUILD`，或啟動後畫面右上角版本徽章）。
