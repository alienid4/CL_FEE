# START_NEXT

## 目前入口

請不要重頭開始。先讀：

1. `docs/一次性開發提示詞_v2.1/一次性開發提示詞_v2.1_FINAL.md`
2. `docs/一次性開發提示詞_v2.1/CURRENT_STATUS.md`
3. `docs/一次性開發提示詞_v2.1/START_NEXT.md`

## 目前狀態

- 主程式在 AI_FEE 根目錄。
- `archive/old_api_local_web_20260704-135900` 只能當歷史參考，不得作為主程式來源，不刪除、不搬移。
- live UI 以 `http://127.0.0.1:8892/` 為準。
- 使用者不需要手機版；本產品以 1500px 桌面內部系統畫面為主要驗收尺寸。
- 使用者看不懂英文，正式 UI 必須以中文為主；案件代碼、合約代碼等資料 ID 可保留英數代碼。
- 正式 UI 不得出現 demo 角色切換、檢視角色、使用者切換；帳號與權限只決定可見功能與視角。
- formal confirm / import confirm 正式寫入仍維持阻擋，不得新增正式寫入按鈕或資料 commit 流程。

## 已完成的 UI 參考與 checkpoint

- 使用者提供的參考圖已保存於 `docs/ui_reference/target_01_*` 到 `docs/ui_reference/target_19_*`。
- 已完成目前 live checkpoint：
  - `docs/ui_reference/current_8892_ui_rescue_preview_20260706.png`
  - `docs/ui_reference/current_8892_case_tabs_checkpoint_20260706.png`
  - `docs/ui_reference/current_8892_module_batch_checkpoint_verify_20260706.png`

## 本輪完成

- 案件管理六分頁已可互動：
  - 案件清單
  - 主管儀表板
  - 流程圖
  - 線性進度圖
  - 處理優先矩陣
  - 待確認
- 下一批模組畫面已補上第一版：
  - 預算：年度預算編列、主管儀表板、費用預估、已簽承諾支付、資料檢核
  - 專案：專案清單、主管儀表板、工作項目、資料檢核
  - 簽呈：上簽項目、主管儀表板、資料檢核
- 剩餘模組畫面也已補上第一版：
  - 合約：合約清單、主管儀表板、資料檢核
  - 請購：請購清單、主管儀表板、資料檢核
  - 付款：付款清單、主管儀表板、資料檢核
  - 資料檢核總覽：檢核總覽、來源舉證、待補清單
- 已修正正式畫面殘留的 `Dashboard`、`Project` 等英文分頁文字。
- 截圖 gate 結果：1500px 桌面寬度、body scroll width 1500、7 個模組均有資料列、無 duplicate id、無 demo 文字、無角色切換文字、無可見 Dashboard/Project/Budget_ID/Contract code/Amount/alert/formal confirm/commit。

## 下一個安全切片

繼續做 UI checkpoint hardening 與資料檢核細節，不做正式寫入：

1. 把八項模組 checkpoint 規則納入 audit gate 或專用 UI gate script。
2. 補資料檢核 / 來源舉證下鑽，讓使用者能看出每筆資料來自哪個 Excel/PDF/人工欄位。
3. 補 KPI 卡片下鑽互動，點擊數字能定位到明細列。
4. 仍然不得新增正式匯入確認寫入、commit、正式資料寫入按鈕。

目前 1 和 2 已完成。下一輪從第 3 點開始：KPI 卡片與資料檢核項目下鑽定位，不做正式寫入。

完成後必須再提供 8892 checkpoint，並保存截圖到 `docs/ui_reference/current_8892_*_checkpoint_*.png`。

## 每次切片必跑驗證

```powershell
python -m compileall app tests
python -m pytest tests/test_fresh_app.py -q
python -m pytest -q
powershell -ExecutionPolicy Bypass -File scripts\test_ui_import_preview.ps1 -BaseUrl http://127.0.0.1:8892
powershell -ExecutionPolicy Bypass -File scripts\test_ui_documents.ps1 -BaseUrl http://127.0.0.1:8892
powershell -ExecutionPolicy Bypass -File scripts\check_ui_checkpoint.ps1 -BaseUrl http://127.0.0.1:8892
powershell -ExecutionPolicy Bypass -File scripts\check_audit_gate.ps1 -RequireLog
```

UI 相關切片還必須用 Playwright 截圖確認：

- 1500px 桌面寬度沒有水平撐爆。
- 不出現手機版 collapse。
- 不出現 demo 角色切換、檢視角色、使用者切換。
- 正式 UI 不出現英文操作字，例如 Dashboard、Project、Budget_ID、Contract code、Amount。
- 新增模組至少有清單、KPI、資料來源說明或資料檢核入口。

## 回報規則

- 使用者沒有說停就繼續。
- 不要在對話中大量 heartbeat；重要 checkpoint、阻塞、測試失敗、需要使用者操作時才回報。
- 每次 checkpoint 必須更新：
  - `docs/AI開發進度.md`
  - `docs/一次性開發提示詞_v2.1/CURRENT_STATUS.md`
  - `docs/agent_run_report.md`
  - `logs/agent_loop_audit.jsonl`
- 每次回報必須包含「跟上次差異」。
