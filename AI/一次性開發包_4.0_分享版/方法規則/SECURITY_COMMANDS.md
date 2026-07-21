# SECURITY_COMMANDS

本檔提供 AI_FEE 可執行的資安檢查命令與替代檢查方式。

若工具不可用，必須回報「未能執行」與替代檢查方式，不得假裝已掃描。

## 基本工作區檢查

優先使用自動化腳本：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\security_check.ps1 -IncludePytestCollect
```

若要把 warnings 視為失敗：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\security_check.ps1 -IncludePytestCollect -FailOnWarnings
```

進階資安入口：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\deep_security_check.ps1
```

本機授權服務的非侵入 DAST smoke：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\deep_security_check.ps1 -IncludeDast -BaseUrl http://127.0.0.1:8888
```

`deep_security_check.ps1` 會先跑基礎 security check，並在工具存在時嘗試 bandit、pip-audit、semgrep。缺工具會回報 warning，不得假裝已完成完整 SAST / DAST。

也可手動執行以下分項命令。

```powershell
git status --short
git diff --check
```

用途：

- 確認變更範圍。
- 檢查 whitespace / patch 格式問題。
- 確認是否有不該納入的檔案。

## 敏感字串檢查

```powershell
rg -n "password|passwd|secret|token|api[_-]?key|private key|BEGIN RSA|BEGIN OPENSSH|connection string|Trusted_Connection|User ID|UID=|PWD=" .
```

若結果命中，需判斷是否為：

- 真實敏感資料
- 範例文字
- 文件中的禁止規則
- 測試假資料

不得只因有命中就直接刪除；需先確認上下文。

## 不應提交檔案檢查

```powershell
rg -n "\.env|\.db|\.sqlite|\.xlsx|\.xls|\.pdf|cookie|session" .gitignore docs app tests scripts
```

用途：

- 確認 `.gitignore` 是否涵蓋敏感或大型資料類型。
- 確認文件是否提醒不可提交敏感資料。

## archive 誤用檢查

```powershell
rg -n "old_api_local_web|archive/old_api|archive\\old_api" app tests scripts
```

期待：

- 主程式、測試、腳本不得引用 archive 舊碼。
- 若只在 docs 中出現禁止規則，可以接受。

## Python 測試

完整本機基礎驗證可用：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\test_all.ps1 -IncludePromptPack -IncludeSecurity
```

自動化基礎檢查：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\check_automation_foundation.ps1
```

提示詞包完整性檢查：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\check_prompt_pack.ps1
```

```powershell
pytest tests -q
```

修正 pytest archive 污染後，必須也跑：

```powershell
pytest -q
```

## UI regression

若改 Web UI 或 Documents workflow：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\test_ui_documents.ps1
```

## 依賴風險檢查

若新增或升級 Python 依賴，至少檢查：

```powershell
python -m pip list
python -m pip check
```

如環境有安裝 `pip-audit`，可執行：

```powershell
python -m pip_audit
```

若沒有 `pip-audit`，回報：

```text
未執行 pip-audit，原因：目前環境未安裝。已用 pip check 做替代一致性檢查。
```

## 黑箱檢查提示

若服務正在本機執行，可做基本 HTTP 檢查：

```powershell
Invoke-RestMethod http://127.0.0.1:8888/health
Invoke-RestMethod http://127.0.0.1:8888/openapi.json
```

若有正式或測試環境 URL，需先確認使用者授權。
未授權不得對非本機環境做 DAST 或探測。

## 回報格式

```text
資安命令檢查：
- 工作區檢查：
- 敏感字串檢查：
- archive 誤用檢查：
- 測試：
- 依賴檢查：
- 黑箱檢查：
- 未執行項目與原因：
```
