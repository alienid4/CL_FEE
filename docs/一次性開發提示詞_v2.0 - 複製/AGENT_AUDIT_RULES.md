# AGENT_AUDIT_RULES

本檔用來確認 Agent 是否符合使用者要求。

它不是替代測試，而是確認 Agent 沒有自說自話、越界、跳過驗證或誤用 archive。

## 何時使用

小修：

- 完成回報中簡短檢查即可。

中型功能：

- Coder 完成後，Tester 或主流程需依本表檢查。

大型 / 高風險功能：

- Reviewer 必須依本表檢查，並記錄 findings。

## Agent 稽核表

| 檢查項 | 結果 | 證據 | 風險 |
| --- | --- | --- | --- |
| 是否遵守本輪切片範圍 | pass/fail | 變更檔案 / diff 摘要 |  |
| 是否未做無關重構 | pass/fail | 變更檔案 |  |
| archive 未被當主程式來源 | pass/fail | rg / diff / 說明 |  |
| archive 未被 pytest 預設收集 | pass/fail | pytest collect / pytest 設定 |  |
| 是否未碰正式資料 | pass/fail | 回報 / 檔案檢查 |  |
| 是否未新增敏感資料 | pass/fail | git diff / rg |  |
| 是否未把 AI 判斷寫入正式金額或狀態 | pass/fail | 變更說明 |  |
| 是否有跑該跑的測試 | pass/fail | 測試命令與結果 |  |
| 是否有判斷 FastAPI 是否需重啟 | pass/fail | 回報文字 |  |
| 是否更新 CURRENT_STATUS.md / START_NEXT.md | pass/fail | 檔案連結 |  |
| 第二版功能是否只記錄未偷做 | pass/fail | docs / diff |  |
| 是否有證據而非口頭宣稱 | pass/fail | log / command / file refs |  |

## Agent 證據要求

若聲稱使用獨立 Agent，必須提供至少一種證據：

- sub-agent id
- Calling Agent 區塊
- 工具呼叫紀錄
- agent 回傳摘要
- orchestrator 呼叫紀錄

`.github/agents/*.agent.md` 只代表設定存在，不代表 Agent 已實際執行。

若沒有證據，只能寫：

```text
獨立 Agent 未啟動；本輪由主流程直接執行。
```

或：

```text
本輪為角色模擬，非獨立 Agent。
```

## Reviewer Findings 格式

Reviewer 或主流程發現問題時，使用以下格式：

```text
Finding:
- Severity: P1/P2/P3
- File:
- Evidence:
- Impact:
- Recommendation:
```

## 完成回報最低稽核

每個切片完成時，至少回報：

- 切片範圍是否遵守
- archive 是否未被誤用
- 敏感資料是否未新增
- 測試是否已執行
- 是否需要重啟 FastAPI
- 下一步是否已更新
