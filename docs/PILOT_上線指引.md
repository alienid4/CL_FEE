# CL_FEE Pilot 上線指引（Windows localhost）

對象：小範圍試營運（少數助理／主管）。單機、瀏覽器在同一台，走 HTTP 即可（流量不出本機）。

## 1. 設定帳號密碼與金鑰（只做一次）

編輯專案根目錄的 `.env`（此檔已被 git 忽略，不會進版控）：

```
# 每個帳號一組密碼，請各自改成不同的強密碼
AP01_PASSWORD=（處長/CIO 的密碼）
AP02_PASSWORD=（主管/助理 的密碼）
AP03_PASSWORD=（承辦 的密碼）

# session 簽章金鑰，請換成一段夠長的隨機字串（例：PowerShell 執行 [guid]::NewGuid().ToString("N") 兩次接起來）
SESSION_SECRET=（一段長隨機 hex）
```

- 帳號固定為 `ap01`（處長/CIO）、`ap02`（主管/助理）、`ap03`（承辦）。
- 密碼只放 `.env`，程式碼裡沒有任何寫死密碼；啟動時各自加鹽雜湊。

## 2. 啟動

PowerShell，於專案根目錄：

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8888
```

啟動後開瀏覽器：`http://127.0.0.1:8888`，用上面設定的帳號密碼登入。

要開機自動啟動，可用「工作排程器」建立一個登入時執行上面指令的工作（之後可再協助設定）。

## 3. 備份（重要）

資料都在單一 SQLite 檔：`data/fee_control.db`。備份就是複製這個檔：

```powershell
Copy-Item data\fee_control.db ("backup\fee_control_" + (Get-Date -Format yyyyMMdd_HHmm) + ".db")
```

建議每天收工前複製一次到另一顆磁碟或雲端資料夾。復原就是把備份檔複製回 `data\fee_control.db`。

## 4. 目前已具備的安全性

- 所有 `/api` 都要先登入（未登入一律 401）。
- session cookie 有 HMAC 簽章，偽造無效；密碼 pbkdf2 加鹽雜湊、常數時間比對。
- 稽核 `audit_logs` 記錄真實操作者。
- 刪除有子列的資料會被擋（避免孤立），建議一律用「作廢」而非刪除。

## 5. 誠實的已知限制（pilot 階段可接受，正式擴大前要處理）

- **無角色權限細分**：目前「有登入就能操作所有功能」。承辦/主管/處長還沒做「只能做各自的事」。
- **session 8 小時過期**：cookie 逾時需重新登入（可用 `SESSION_MAX_AGE_SECONDS` 調整）；重啟服務或更換 `SESSION_SECRET` 也會讓所有人重新登入。
- **僅限本機 HTTP**：不要把 8888 埠開放到公司網路或外網；要跨機器使用需另加 HTTPS 與強化。
- **資料庫為 SQLite**：適合 pilot 小量使用；使用者變多或要正式化，再遷 Microsoft SQL Server（已列為未來重大事項）。

## 6. 出問題時

- 登不進去：檢查 `.env` 是否有設 `AP0X_PASSWORD`；改完 `.env` 需重新啟動服務。
- 想確認系統健康：瀏覽器開 `http://127.0.0.1:8888/health` 應回 `{"ok": true, ...}`。
- 開發者若要驗證整體：於專案根目錄執行 `python -m pytest -q`（應全綠）與 `python .project/checks.py`。
