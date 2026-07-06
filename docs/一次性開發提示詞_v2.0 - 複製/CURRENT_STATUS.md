# CURRENT_STATUS

本檔是 AI_FEE v2.0 提示詞包的短版狀態檔。
日常接手請先讀本檔，再讀 `START_NEXT.md`。

## 目前完成度

整體估計約 48%。

目前屬於可展示、可操作、可測的本機開發版，但還不是完整可上線 MVP。

## 最新可通過測試

目前已知可通過：

```powershell
pytest tests -q
```

目前已知 Documents UI regression 可通過：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\test_ui_documents.ps1
```

## 當前風險

- 直接跑 `pytest -q` 會收進 `archive/old_api_local_web_20260704-135900/tests` 舊測試，造成新舊測試污染。
- `archive/` 是歷史參考，不能作為主程式來源。
- 第一版功能範圍很大，必須用小切片推進。
- 正式 MSSQL、正式 AD、正式部署與正式資料尚未確認，不可假裝完成。

## 下一個建議切片

1. 修正 pytest archive 污染，讓 `pytest -q` 預設只測主程式。
2. 驗證：

```powershell
pytest -q
pytest tests -q
```

## 不可碰規則

- 不刪除 archive。
- 不搬移 archive。
- 不從 archive 複製主程式。
- 不碰正式資料、正式 DB、正式憑證。
- 不做不可逆 migration。
- 不把 AI 判斷直接寫入正式金額或正式狀態。
- 不做無關重構。

## 是否需要重啟 FastAPI

目前僅建立提示詞文件，不需要重啟 FastAPI。

若後續改 FastAPI route、schema、store 或 DB 初始化，需重新判斷是否重啟。

## archive 注意事項

`archive/old_api_local_web_20260704-135900` 只能作為歷史參考。

若 pytest 預設收集 archive 測試，應用 pytest 設定排除，不得刪除或搬移 archive。
