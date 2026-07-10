# DEVELOPMENT_RULES

本檔定義 AI_FEE 的開發分級與流程。

## 核心原則

小事快跑，大事走流程；砍掉無效等待，不砍必要驗證。

採用「產出優先 + 輕量監控」模式：

- 每輪先依 `SPEED_RULES.md` 選 Fast / Standard / Release 速度檔。
- 小修目標時間為 10-30 分鐘，一般功能切片目標時間為 45-90 分鐘。
- 不用長篇 heartbeat 取代實作。
- 文件只在切片完成、測試結果改變、阻塞狀態改變、完成度改變或 Agent 狀態改變時更新。
- 小修由主模型直接做；中型功能才啟動 Coder + Tester；高風險才啟動 Architect + Coder + Tester + Reviewer。

## 小修

可視為小修：

- 測試設定修正
- 明確 UI bug
- 明確 API 小錯誤
- 文案或文件小修
- 不改資料模型、不改權限、不改核心流程的修正

流程：

- 直接修。
- 直接跑相關測試。
- 不啟動完整多 Agent 流程。
- 回報變更檔案、測試結果、是否需重啟。

不得視為小修：

- DB schema 變更
- Excel 匯入 / 回匯
- 權限 / AD / 登入
- MSSQL adapter
- 部署流程
- 報表金額邏輯
- 會影響正式資料或資料正確性的行為

## 中型功能

適用：

- 單一模組功能
- 單一 API + UI 切片
- 可局部驗證的功能

流程：

- 使用 Coder + Tester。
- Coder 實作。
- Tester 驗證。
- 必須有測試或可重現驗證。

## 大功能 / 跨模組功能

適用：

- DB schema
- Excel 匯入 / 回匯
- 權限 / AD
- MSSQL
- 部署
- 資料安全
- 報表邏輯
- 跨模組資料一致性

流程：

- 使用 Architect + Coder + Tester + Reviewer。
- Architect 定義切片與風險。
- Coder 實作。
- Tester 驗證。
- Reviewer 檢查風險、範圍、測試、archive 誤用與資料安全。

## 高風險操作

涉及以下項目時必須保守，必要時停下回報：

- 正式資料
- 正式 DB
- 正式憑證
- 不可逆 migration
- 正式部署
- 權限 / AD / SSO
- 匯入回匯覆蓋風險

## Agent 證據規則

- 若實際啟動獨立 Agent，必須記錄 sub-agent id、Calling Agent 區塊、工具呼叫紀錄或回傳摘要。
- `.github/agents/*.agent.md` 只算設定，不算實際呼叫證據。
- 若沒有獨立 Agent 呼叫證據，不得寫「獨立 Agent 已完成」；只能寫「角色模擬」或「獨立 Agent 未啟動」。
