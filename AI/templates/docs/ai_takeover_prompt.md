# AI Takeover Prompt

把這段交給公司 GPT、Codex 或其他接手 AI。必要時補上專案名稱與目標。

```text
你現在接手這個專案。請先讀取以下文件，不要直接改 code：

1. HANDOFF_INDEX.md
2. Memory.md
3. docs/current_state_snapshot.md
4. docs/project_overview.md
5. docs/data_dictionary.md
6. docs/workflow_state.md
7. docs/runbook.md
8. docs/test_plan.md
9. docs/security_data_handling.md
10. docs/ai_truth_and_evidence.md

工作規則：
- 不知道就說不知道，不要猜。
- 可以提出假設，但必須標示為假設。
- 公司環境、部署狀態、版本、資料筆數、錯誤原因，都需要證據。
- 如果證據不足，請提供一次性、安全、去敏化的診斷指令。
- 先做最小範圍修改，不做無關重構。
- 每次修改後要提供驗證方式、結果、風險與 rollback 注意事項。

請先回覆：
1. 你理解的系統用途。
2. 你看到的主要資料模型與流程。
3. 目前最高風險。
4. 你需要先驗證的資料。
5. 下一步最小安全行動。
```
