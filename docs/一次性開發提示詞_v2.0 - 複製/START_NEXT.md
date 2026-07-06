# START_NEXT

本檔定義下一輪開發指令，必須保持短小明確。

## 請先讀

1. `CURRENT_STATUS.md`
2. 本檔
3. 當前切片相關程式碼與測試

## 本輪目標

修正 pytest archive 污染，讓：

```powershell
pytest -q
```

預設只測主程式，不收集 `archive/old_api_local_web_20260704-135900/tests`。

## 不可碰

- 不刪除 archive。
- 不搬移 archive。
- 不從 archive 複製主程式。
- 不做無關重構。
- 不修改與 pytest 收集範圍無關的功能。

## 預期做法

優先使用 pytest 設定排除 archive，例如 `pytest.ini` 或等效設定。

## 驗證

完成後必須跑：

```powershell
pytest -q
pytest tests -q
```

## 完成回報

- 本次完成項目
- 跟上次差異
- 變更檔案
- 驗證命令與結果
- 是否需要重啟 FastAPI
- 下一個建議切片
