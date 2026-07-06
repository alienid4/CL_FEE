# START_NEXT

本檔定義下一輪開發指令，必須保持短小明確。

## 請先讀

1. `CURRENT_STATUS.md`
2. 本檔
3. 當前切片相關程式碼與測試

## 本輪目標

下一輪建議：Import Preview UI 顯示 cases-only dry-run plan。

目前 v2.1 本機自動開發控制台 MVP 已新增；下一輪回到產品 backlog。
v2.1 已改為 All-in-One Build Pack；新系統從 0 到 MVP 時先讀 `ALL_IN_ONE_BUILD_PACK.md`。

建議先跑：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\local_ci.ps1
pytest tests -q
```

此切片是 import-confirm 的 read-only UI 前置實作，速度檔至少是 Standard Lane。只允許呼叫 `dry_run=true`，不得新增正式寫入按鈕。

若暫時不做 UI，下一個安全切片是：formal confirm 前的 Reviewer/Security 設計切片，不直接寫正式資料。

## 不可碰

- 不刪除 archive。
- 不搬移 archive。
- 不從 archive 複製主程式。
- 不做無關重構。
- 不碰正式部署 credential。
- 不推送遠端 repository，除非使用者明確要求。

## 預期做法

依 `docs/import_confirm_write_mvp_design.md` 與既有 `POST /api/import-batches/{batch_id}/confirm` dry-run API，在 Import Preview UI 顯示 dry-run plan。
要求：

- UI 只能送 `dry_run=true`。
- UI 只能送 `target_tables=["cases"]`。
- 只顯示 plan，不新增正式 confirm button。
- domain counts 必須不變。
- 若 preview 還有 errors 或缺 confirmed_fields，顯示後端錯誤，不自行修正資料。

## 驗證

完成後必須跑：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\local_ci.ps1
pytest -q
pytest tests -q
powershell -ExecutionPolicy Bypass -File scripts\test_ui_import_preview.ps1
```

## 完成回報

- 本次完成項目
- 速度檔
- 跟上次差異
- 變更檔案
- 驗證命令與結果
- 是否需要重啟 FastAPI
- 下一個建議切片
