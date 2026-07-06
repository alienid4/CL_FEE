# CMDB 關聯預留規劃

## 決策

系統分兩階段處理 CMDB：

1. 第一階段：先做費用合約控管本體，保留 CMDB 關聯欄位。
2. 第二階段：再接 CMDB 查詢或匯入。

這樣可以避免第一階段被 CMDB 欄位、API 權限、同步週期卡住，同時保留未來關聯能力。

## 第一階段範圍

第一階段不直接連 CMDB，但所有核心資料需要預留 CMDB 關聯欄位與舉證位置。

預留欄位：

- `cmdb_ci_id`
- `cmdb_ci_name`
- `cmdb_system_name`
- `cmdb_service_name`
- `cmdb_owner_department`
- `cmdb_environment`
- `cmdb_import_batch_id`
- `cmdb_last_synced_at`
- `cmdb_match_status`
- `cmdb_evidence_note`

建議可掛載對象：

- Case Master
- 專案
- 合約
- 付款排程
- 文件 / 附件
- 舉證鏈

## 第二階段範圍

第二階段依 CMDB 實際提供方式接入：

- CMDB API 查詢。
- CMDB Excel 匯出匯入。
- CMDB CSV 匯出匯入。
- 人工關聯。

第二階段要支援：

- 依系統名稱、服務名稱、CI ID 查詢。
- 匯入 CMDB 清單。
- 將 Case / 合約 / 專案 關聯到 CMDB CI。
- 顯示 CMDB 同步時間。
- 顯示比對狀態：已匹配、待確認、找不到、多筆候選、已人工覆核。
- 保留來源舉證。

## Case 360 顯示方式

Case 360 未來需顯示：

- 關聯 CMDB CI。
- 系統名稱。
- 服務名稱。
- 環境別。
- CMDB 負責部門。
- 最後同步時間。
- 比對狀態。
- 來源：API / Excel / CSV / 人工。

## 搜尋與下鑽

全文檢索需支援：

- CI ID。
- 系統名稱。
- 服務名稱。
- CMDB 負責部門。
- 環境別。

Dashboard 數字下鑽未來可支援：

- 哪些案件已關聯 CMDB。
- 哪些案件尚未關聯 CMDB。
- 哪些案件 CMDB 比對異常。
- 哪些付款或合約屬於同一個 CMDB 服務。

## 驗收標準

第一階段：

- 系統不依賴 CMDB 也能運作。
- 文件與 API 清楚標示 CMDB 為預留功能。
- Excel mapping 與 Case 360 需求保留 CMDB 欄位。

第二階段：

- 可從 Case 360 查到 CMDB 資產或服務。
- 可依 CMDB 欄位搜尋案件、合約、付款與文件。
- 可看出 CMDB 資料來源與最後同步時間。
- 可處理找不到、多筆候選、人工覆核等資料品質狀態。
