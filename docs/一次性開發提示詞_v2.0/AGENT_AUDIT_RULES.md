# AGENT_AUDIT_RULES

本檔用來確認 Agent 是否符合使用者要求。

Audit 是使用者的「糾察隊」，不是可有可無的紀錄。
任何 Agent 只要宣稱完成，都必須接受 audit gate 檢查。

它不是替代測試，而是確認 Agent 沒有自說自話、越界、跳過驗證或誤用 archive。

完整 Gate 清單請看 `GATE_CATALOG.md`。
其中 `MVP Scope Gate` 是第一版終點驗收 gate，不是每輪小修 gate。
每輪 audit 只需檢查本輪是否碰到相關 MVP 模組，且是否未破壞既有能力。

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
| 是否已自主處理低風險可修復問題 | pass/fail/不適用 | diff / 測試結果 / 說明 |  |
| 是否只在重大或高風險事項才詢問使用者 | pass/fail/不適用 | 回報 / 風險說明 |  |
| 是否未把 AI 判斷寫入正式金額或狀態 | pass/fail | 變更說明 |  |
| 是否有跑該跑的測試 | pass/fail | 測試命令與結果 |  |
| 是否有判斷 FastAPI 是否需重啟 | pass/fail | 回報文字 |  |
| 是否更新 CURRENT_STATUS.md / START_NEXT.md | pass/fail | 檔案連結 |  |
| 第二版功能是否只記錄未偷做 | pass/fail | docs / diff |  |
| 是否有證據而非口頭宣稱 | pass/fail | log / command / file refs |  |
| UI 主畫面是否未直接顯示內部註解 | pass/fail/不適用 | audit gate / UI regression / screenshot |  |
| 若本輪碰到 MVP 模組，是否未破壞對應 MVP 能力 | pass/fail/不適用 | 測試 / UI regression / API check |  |

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

## JSONL 稽核紀錄

自動開發 LOOP 應寫入 append-only JSONL 紀錄：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\write_agent_audit_log.ps1 -Goal "..." -Classification small -Verification "pytest -q"
```

預設位置：

```text
logs/agent_loop_audit.jsonl
```

不得在 audit log 寫入密碼、token、private key、cookie、session、正式個資或完整敏感資料。

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

若完成回報沒有 Agent 稽核區塊，或沒有說明為何不適用，該切片不得視為完成。

若稽核項目沒有證據，不得填 pass。

## Audit Gate

完成一個 LOOP 後，必須先寫入 audit log：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\write_agent_audit_log.ps1 -Goal "..." -Classification small -Verification "..." -AuditResult "pass"
```

然後執行 audit gate：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\check_audit_gate.ps1 -RequireLog
```

若 audit gate 未通過，不得宣稱本輪完成。
若本輪只有純詢問、沒有任何檔案或狀態變更，必須在回報中明確寫「audit 不適用，原因：純問答未變更工作區」。

## UI 內部註解規則

UI 介面不可直接顯示內部註解。

不可以直接出現在一般使用者主畫面：

- 開發註解
- Prompt / Agent 說明
- TODO / FIXME / debug / 測試用 / 開發中
- 內部流程說明
- 大段教學式說明文字

允許的說明方式：

- tooltip
- info icon
- 可點擊的「說明」或「?」按鈕
- 預設收合的 details / help panel
- 管理者專用 help panel
- docs 文件

Audit gate 會檢查 `app/web` 中常見內部標記。
如果確實需要顯示說明，必須放在可點開的 help / tooltip / details，且回報證據。

## 可複製稽核回報模板

```text
Agent 稽核：
- 切片範圍是否遵守：pass/fail，證據：
- 是否未做無關重構：pass/fail，證據：
- archive 是否未被當主程式來源：pass/fail，證據：
- archive 是否未被 pytest 預設收集：pass/fail/不適用，證據：
- 是否未碰正式資料：pass/fail，證據：
- 是否未新增敏感資料：pass/fail，證據：
- 是否已自主處理低風險可修復問題：pass/fail/不適用，證據：
- 是否只在重大或高風險事項才詢問使用者：pass/fail/不適用，證據：
- 是否已執行應跑測試：pass/fail，命令與結果：
- 是否需要重啟 FastAPI：需要/不需要，原因：
- 是否更新 CURRENT_STATUS.md / START_NEXT.md：pass/fail，證據：
- UI 主畫面是否未直接顯示內部註解：pass/fail/不適用，證據：
- 是否碰到 MVP Scope Gate 模組：是/否；若是，未破壞證據：
- 剩餘風險：
```

## 缺證據處理

若某項檢查沒有證據，不得填 pass。

請填：

```text
未確認，原因：
替代檢查：
下一步：
```
