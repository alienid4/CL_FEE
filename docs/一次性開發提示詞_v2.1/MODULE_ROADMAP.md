# MODULE_ROADMAP

本檔定義 AI_FEE 第一版建議切片順序。

## 推進原則

- 每輪只做一個小切片。
- 不一次開多條功能線。
- 完成後更新 `CURRENT_STATUS.md` 與 `START_NEXT.md`。
- 大型功能先拆成可測的小切片。

## 建議順序

1. 修正 pytest archive 污染，讓 `pytest -q` 預設只測主程式。
2. Excel 匯入暫存 API。
3. Excel 欄位 mapping 草稿。
4. 匯入檢核：必填、金額、日期、重複。
5. 匯入確認寫入正式表。
6. 角色權限 mock。
7. MSSQL adapter 介面骨架。
8. 報表 / Dashboard 下鑽。
9. 稽核紀錄與來源舉證鏈。
10. Case 360 深化。
11. 廠商視角與負責人視角深化。
12. 部署與維運文件。

## 完成定義

每個切片完成時至少要有：

- 明確變更檔案。
- 測試或可重現驗證。
- 是否需重啟 FastAPI 的判斷。
- 已知限制。
- 下一個建議切片。

## 第一版完成條件

第一版可視為接近 MVP 時，至少應具備：

- 核心資料 CRUD lifecycle。
- Case 360 可追案件全貌。
- Dashboard 數字可下鑽。
- 搜尋可跨主要模組。
- Excel 匯入暫存與欄位 mapping。
- 角色 mock 與權限欄位預留。
- 稽核紀錄或稽核欄位。
- 來源舉證鏈預留。
- 測試與 UI regression 可重跑。
- 文件可讓下一位開發者接手。

第一版最終驗收還必須對照 `GATE_CATALOG.md` 的 `MVP Scope Gate` 逐項檢查。
MVP Scope Gate 是終點 gate，不是每個小修都要完成全部。
