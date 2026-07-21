# SPEED_RULES

本檔定義 AI_FEE 的速度分級。目標是壓縮無效等待，而不是砍掉必要驗證。

## 核心判斷

每輪開始先選一個速度檔：

| 速度檔 | 適用情境 | 目標時間 | 最低驗證 |
| --- | --- | --- | --- |
| Fast Lane | 文件、小修、明確 bug、測試設定、低風險 UI 文案 | 10-30 分鐘 | `scripts\fast_ci.ps1` 或最窄相關測試 |
| Standard Lane | 一般產品切片、單一 API + UI、單一模組功能 | 45-90 分鐘 | `scripts\local_ci.ps1` |
| Release Lane | 發版前、跨模組、資安、部署、正式資料前檢查 | 半天內拆段完成 | `scripts\test_all.ps1` 加必要 UI / security / audit 參數 |

若一輪超過目標時間，必須縮小切片或回報阻塞，不得默默擴大範圍。

## Fast Lane

可用 Fast Lane：

- 文件或提示詞包小修。
- 明確 bug，且影響範圍可定位。
- 測試設定或 CI 腳本的小修。
- UI 文案、tooltip、help text、欄位 label。
- 不碰資料模型、不碰權限、不碰正式資料、不碰部署。

Fast Lane 預設命令：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\fast_ci.ps1
```

若本輪只改提示詞包或自動化規則，需加：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\fast_ci.ps1 -IncludePromptPack -IncludeAutomationFoundation
```

若本輪有修改狀態、規則或完成回報，需寫 audit log，再跑：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\fast_ci.ps1 -IncludeAuditGate -RequireAuditLog
```

## Standard Lane

可用 Standard Lane：

- 單一產品功能切片。
- 單一 API + UI flow。
- 一般 backend / frontend / tests 修改。
- 新增可重現驗證，但未碰正式資料或部署。

Standard Lane 預設命令：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\local_ci.ps1
```

## Release Lane

必須用 Release Lane：

- DB schema、migration、MSSQL adapter。
- 權限、登入、AD / SSO。
- Excel 匯入、回匯、正式寫入。
- 報表金額邏輯、正式狀態、資料安全。
- 部署、release、交付前檢查。
- 資安掃描與黑箱 / 白箱檢查。

Release Lane 依情境加參數，例如：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\test_all.ps1 -IncludePromptPack -IncludeAutomationFoundation -IncludeSecurity -IncludeAuditGate -RequireAuditLog
```

涉及 UI Documents workflow 時再加：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\test_all.ps1 -IncludeUiDocuments
```

涉及 Import Preview UI 時再加：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\test_all.ps1 -IncludeUiImportPreview
```

## 自動升級規則

原本想用 Fast Lane，但碰到以下任一項，必須升級：

- DB schema / migration / adapter。
- 權限 / 登入 / AD / SSO。
- Excel 匯入、回匯、正式寫入。
- 正式資料、正式 DB、正式憑證。
- 金額、付款、發票、正式狀態邏輯。
- 部署、release、環境設定。
- 資安掃描失敗或疑似敏感資料。
- 測試失敗無法在同一小切片內修完。

## 壓榨效能規則

- 每輪只做一個能驗證的小切片。
- 優先跑最窄測試，通過後再視風險升級。
- 不因為流程完整而拖慢低風險小修。
- 不因為求快而跳過測試、audit log、資料安全。
- 若 30 分鐘內沒有新增實作，必須回報「無新增實作，僅狀態維持」，並改推下一個安全 backlog。
- 若連續兩輪卡在同一阻塞，必須縮小切片、改測試策略或交給使用者決策。

## 回報格式加註

每輪完成回報需加一行：

```text
速度檔：Fast Lane / Standard Lane / Release Lane
```

若速度檔升級，需說明原因。
