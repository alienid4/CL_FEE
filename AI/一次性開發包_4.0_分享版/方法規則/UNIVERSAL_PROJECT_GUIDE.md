# UNIVERSAL_PROJECT_GUIDE

本檔說明如何把 v2.1 All-in-One Build Pack 套用到其他專案。

這份提示詞包目前以 AI_FEE 為例，但工作方式可套用到多數企業內部系統、資料工具、Web API、管理後台與自動化專案。

## 新專案套用方式

複製本目錄後，優先改以下內容：

1. `README.md`
   - 專案名稱
   - 專案目標
   - 第一版必做功能
   - 第一版不做功能
   - 資料與權限策略

2. `CURRENT_STATUS.md`
   - 目前完成度
   - 最新可通過測試
   - 當前風險
   - 下一個建議切片
   - 不可碰規則

3. `START_NEXT.md`
   - 本輪唯一目標
   - 不可碰事項
   - 驗證命令

4. `MODULE_ROADMAP.md`
   - 功能切片順序
   - 每個切片完成定義

5. `SECURITY_RULES.md`
   - 是否涉及正式資料
   - 是否涉及個資
   - 是否涉及金流、合約、權限、憑證

## 新手接手最短流程

如果你是第一次接手，不要先讀全部文件。

請照順序做：

1. 讀 `INDEX.md`。
2. 讀 `CURRENT_STATUS.md`。
3. 讀 `START_NEXT.md`。
4. 讀本輪相關程式碼與測試。
5. 依 `OPERATING_LOOP.md` 做一輪。
6. 完成後更新 `CURRENT_STATUS.md` 與 `START_NEXT.md`。

## 每個專案都適用的核心問題

接手任何專案前，先回答：

- 這個系統服務誰？
- 第一版最小可用範圍是什麼？
- 哪些功能明確不做？
- 哪些資料不可碰？
- 哪些操作需要人工確認？
- 測試怎麼跑？
- 下一步只做哪一個切片？
- 完成後怎麼證明真的完成？

## 不同專案的調整方式

| 專案類型 | 必改重點 |
| --- | --- |
| Web API | API endpoint、schema、auth、OpenAPI、測試命令 |
| 管理後台 | 角色、表格、搜尋、排序、下鑽、操作稽核 |
| Excel / 資料工具 | 匯入、暫存、檢核、回匯、來源舉證 |
| AI 工具 | AI 不直接寫正式資料、人工確認、prompt / model 記錄 |
| 部署工具 | rollback、權限、環境變數、正式機器確認 |
| 資安敏感系統 | 白箱 / 黑箱掃描、權限、敏感資料、稽核 |

## 不能省略的文件

每個專案至少保留：

- `INDEX.md`
- `CURRENT_STATUS.md`
- `START_NEXT.md`
- `DEVELOPMENT_RULES.md`
- `VERIFICATION_RULES.md`
- `SECURITY_RULES.md`
- `AGENT_AUDIT_RULES.md`

其他文件可依專案大小增減。

## 跨專案使用原則

- 不要把 AI_FEE 的業務範圍原封不動套到其他專案。
- 可以保留工作方式、驗證方式、資安與稽核規則。
- 每個新專案都要重新定義第一版必做與不做。
- 不確定的正式資料、正式 DB、正式部署，一律先標示待確認。
- 不要讓提示詞包取代需求訪談；它只能讓接手和開發更穩。
