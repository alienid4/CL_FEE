# VERIFICATION_RULES

本檔定義 AI_FEE 的測試與驗證分級。

## 小修驗證

小修至少要：

```powershell
pytest tests -q
```

若小修只改文件，可不跑測試，但回報必須明確寫：

```text
未跑測試，原因：僅文件變更。
```

## 中型功能驗證

中型功能至少要：

- 跑 API / unit 測試。
- 跑 smoke test。
- 若改 UI，跑對應 UI regression。
- 回報是否需要重啟 FastAPI。

## 大型或高風險功能驗證

大型或高風險功能必須：

- 跑完整測試。
- 檢查 archive 未誤用。
- 檢查敏感資料未誤入 Git。
- 更新相關文件與設計圖。
- 由 Tester / Reviewer 驗證。

## 固定命令

一般後端 / API / 測試設定修改後，至少跑：

```powershell
pytest tests -q
```

修完 archive 測試污染後，必須跑：

```powershell
pytest -q
pytest tests -q
```

若有改 Web UI 或 Documents workflow，必須跑：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\test_ui_documents.ps1
```

## FastAPI 重啟判斷

若改以下內容，需判斷是否重啟 FastAPI：

- route
- schema
- store
- DB 初始化
- static mount
- app settings

回報格式：

```text
是否需要重啟 FastAPI：需要 / 不需要，原因是...
```
