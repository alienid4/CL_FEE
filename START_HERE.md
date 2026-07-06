# START HERE

先讀：`README_ENTERPRISE_ADDONS.md`。它定義公司環境常用預設，包括 MSSQL、AD 登入、Email 測試、附屬包、UI 規則、安全掃描與 AI 不偷懶規則。

若這是新專案，先套主包；若需要 WBS、簡報、安全掃描、UI 治理或 DB / AD / Email，再套 `addon-packs/` 裡的附屬包。

這份文件是拿到 KIT 後的第一頁。請照順序做，不要一開始就改 code。

## 你現在是哪一種情境

| 情境 | 先做什麼 |
| --- | --- |
| 新專案 | 建立專案目的、資料模型、流程狀態、測試策略。 |
| 舊專案補救 | 先盤點現況與風險，不急著重構。 |
| 要交接給 GPT 或新人 | 先補 `HANDOFF_INDEX.md`、`Memory.md`、`current_state_snapshot.md`。 |
| 要修 bug | 先用 debug intake 收證據，再修最小範圍。 |
| 要做 release | 先確認 change size、測試、rollback、敏感資料掃描。 |

## Pass 1: 讓專案看得懂

把模板放進專案：

```powershell
python scripts/bootstrap_project_baseline.py --target "D:\path\to\project"
```

先填這幾份，不用一次填完全部：

- `docs/project_overview.md`
- `docs/data_dictionary.md`
- `docs/workflow_state.md`
- `docs/security_data_handling.md`
- `docs/test_plan.md`
- `HANDOFF_INDEX.md`

## Pass 2: 讓專案查得出問題

執行：

```powershell
python scripts/validate_baseline.py --target "D:\path\to\project"
python scripts/project_audit.py --target "D:\path\to\project" --output audit.json
python scripts/project_health_score.py --target "D:\path\to\project" --output health_score.json
```

如果專案沒有測試，先補一個 smoke test。不要等功能很大才補。

## Pass 3: 讓 AI 或工程師可以安全修改

每次修改都照這個循環：

```text
需求確認 -> 讀現況 -> 收證據 -> 最小修改 -> 測試 -> 審查 -> 交接紀錄
```

若資料不足，要先輸出安全診斷指令，不要猜。

## Pass 4: 大改前先做風險分級

用 `docs/change_size_policy.md` 判斷小修、中修、大修。

- 小修：可快速煙霧測試與 release note。
- 中修：要有目標測試、影響面檢查、rollback note。
- 大修：要完整測試、人工核准、資料備份、回復演練。

## Pass 5: 交接

交接時，請先讓接手者讀：

1. `HANDOFF_INDEX.md`
2. `Memory.md`
3. `docs/current_state_snapshot.md`
4. `docs/ai_takeover_prompt.md`
5. `docs/runbook.md`
6. `docs/test_plan.md`
7. `docs/security_data_handling.md`

接手者讀完後，應先回覆「理解到的現況、風險、下一步驗證方式」，不能直接開始大改。
