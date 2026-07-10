# MVP_EVIDENCE_CHECKLIST

本檔是第一版 MVP Scope Gate 的最終驗收證據表。

它不是每輪小修 gate，而是第一版接近完成或準備交付時使用。

## 使用方式

每個項目都要填：

- Status：not-started / partial / passed / blocked
- Evidence：測試、API、UI regression、截圖、文件或手動驗證
- Gap：尚缺什麼
- Next：下一步

## 證據表

| MVP Scope | Status | Evidence | Gap | Next |
| --- | --- | --- | --- | --- |
| 八項控管看板 | partial | 目前有 Web UI 與 Dashboard 基礎；完整八項仍待補 | 控管看板尚未全部獨立呈現 | 補 Dashboard / navigation evidence |
| 全文檢索 | partial | `/api/search` 基礎存在 | 搜尋分組與所有模組覆蓋待確認 | 補搜尋覆蓋測試 |
| Dashboard 數字下鑽 | partial | Dashboard summary 基礎存在 | 下鑽到明細尚未完整 | 補 drilldown API/UI |
| Case 360 | partial | `/api/cases/{case_id}/360` 基礎存在 | 時間線、舉證鏈需深化 | 補 Case 360 regression |
| 時間線 | partial | Case 360 有基礎 totals / related data | A-G 節點與顏色規則待補 | 補狀態規則 |
| 處理優先矩陣 | not-started | 尚未見完整 priority matrix evidence | 主管優先矩陣待實作 | 建立 priority API/UI |
| 附件管理 | partial | Documents CRUD / UI regression 通過 | 真實附件檔案管理與關聯深化待補 | 補 document evidence chain |
| Excel 匯入匯出預留 | partial | import preview / mapping draft 已有進展 | 匯入確認與正式表寫入未完成 | 做 validation filtering / import confirm |
| 發票 / 簽呈 / 合約 / 付款欄位 | partial | contracts / payments / documents 已有基礎 | invoice / signing 深化待補 | 補資料模型與 UI |
| 廠商視角 | partial | contracts 有 vendor_name | vendor view 尚未完整 | 補 vendor drilldown |
| 負責人視角 | partial | cases 有 owner | owner view / workload 尚未完整 | 補 owner report |
| CMDB 預留 | partial | `/api/cmdb` placeholder 存在 | CMDB UI / 欄位深化待補 | 補 CMDB evidence |

## 最終驗收規則

第一版交付前：

- 不得有 `blocked` 項目未說明。
- `partial` 項目必須有明確缺口與下一步。
- 若使用者接受 partial，需記錄為第一版限制或第二版待辦。
- 不得把未完成的第二版功能寫成已完成。
