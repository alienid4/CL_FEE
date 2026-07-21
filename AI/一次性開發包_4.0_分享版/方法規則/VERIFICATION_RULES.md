# VERIFICATION_RULES

本檔定義 AI_FEE 的測試與驗證規則。

速度檔與時間預算以 `SPEED_RULES.md` 為準；本檔只定義各情境要跑哪些驗證。

## 最低驗證

一般後端 / API / 測試設定修改後，至少跑：

```powershell
pytest tests -q
```

Fast Lane 可使用：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\fast_ci.ps1
```

若本輪只改文件或提示詞包，仍需至少跑對應文件檢查：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\fast_ci.ps1 -IncludePromptPack -IncludeAutomationFoundation
```

## 中型功能驗證

中型功能至少要有：

- 相關 API / unit 測試。
- smoke test 或可重現驗證。
- 若改 Web UI，需跑對應 UI regression。
- 回報是否需要重啟 FastAPI。

預設使用 Standard Lane：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\local_ci.ps1
```

## 大功能 / 高風險驗證

大功能或高風險功能至少要檢查：

- 相關測試。
- archive 不被 pytest 收集。
- 不含敏感資料或憑證。
- 資料安全與權限邊界。
- Tester / Reviewer 驗證紀錄。

預設使用 Release Lane，依情境加參數：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\test_all.ps1 -IncludePromptPack -IncludeAutomationFoundation -IncludeSecurity -IncludeAuditGate -RequireAuditLog
```

## 固定命令

本機 CI：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\local_ci.ps1
```

快速 CI：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\fast_ci.ps1
```

完整可加選項驗證：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\test_all.ps1 -IncludePromptPack -IncludeAutomationFoundation -IncludeSecurity
```

自動化基礎檢查：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\check_automation_foundation.ps1
```

提示詞包檢查：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\check_prompt_pack.ps1
```

Audit gate：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\check_audit_gate.ps1 -RequireLog
```

一般小修 / API / 測試設定修改後，至少跑：

```powershell
pytest tests -q
```

修正 archive 測試污染後，必須跑：

```powershell
pytest -q
pytest tests -q
```

若有改 Web UI 或 Documents workflow，必須跑：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\test_ui_documents.ps1
```

若有改 Import Preview UI，必須跑：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\test_ui_import_preview.ps1
```

## FastAPI 重啟判斷

完成回報必須說明是否需要重啟 FastAPI。

通常需要重啟：

- route
- schema
- store
- DB 設定
- static mount
- app settings

通常不需要重啟：

- 純文件。
- 純測試。
- 外部 CI 腳本。
- 不影響執行中 app 的提示詞包規則。

回報格式：

```text
是否需要重啟 FastAPI：需要 / 不需要，原因：...
```
