# Change Impact Matrix

每次修改前先填。目的不是寫文件給人看，而是避免修 A 壞 B。

| 區域 | 是否影響 | 檢查方式 | 備註 |
| --- | --- | --- | --- |
| UI / template | 否 |  |  |
| Frontend JS | 否 |  |  |
| API route | 否 |  |  |
| Service / business rule | 否 |  |  |
| Database / schema | 否 |  |  |
| Background job | 否 |  |  |
| Auth / permission | 否 |  |  |
| Config / env | 否 |  |  |
| Install / release package | 否 |  |  |
| Tests | 否 |  |  |
| Docs / handoff | 否 |  |  |

## 風險判斷

- 小：只影響一個畫面或一個小函式，有明確測試。
- 中：影響 API、資料轉換、狀態流程或多個畫面。
- 大：影響部署、資料庫、權限、帳號、批次 job 或正式資料。

## 本次變更摘要

- 需求：
- 風險等級：
- 最小修改範圍：
- 驗證方式：
