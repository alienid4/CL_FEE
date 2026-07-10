# OPERATING_LOOP

本檔定義 AI_FEE 的固定改善 LOOP。

每次開發、修正或強化提示詞包時，都依照此 LOOP 執行。

## 標準 LOOP

1. Read
   - 讀 `INDEX.md`。
   - 讀 `CURRENT_STATUS.md`。
   - 讀 `START_NEXT.md`。
   - 只讀當前切片相關程式碼、測試與規則文件。

2. Scope
   - 確認本輪只做一個小切片。
   - 判斷是小修、中型、大型或高風險。
   - 若涉及正式資料、DB、權限、部署，先停下確認風險。

3. Change
   - 只改當前切片需要的檔案。
   - 不做無關重構。
   - 不從 archive 複製主程式。

4. Verify
   - 依 `VERIFICATION_RULES.md` 跑測試。
   - 如涉及資安，依 `SECURITY_RULES.md`、`SECURITY_SCAN_RULES.md`、`SECURITY_COMMANDS.md` 檢查。

5. Audit
   - 依 `AGENT_AUDIT_RULES.md` 檢查是否符合要求。
   - 若沒有證據，不得填 pass。

6. Update
   - 更新 `CURRENT_STATUS.md`。
   - 更新 `START_NEXT.md`。
   - 若改規則，更新對應規則文件與 `README.md` / `INDEX.md`。
   - 若未更新 `CURRENT_STATUS.md` 與 `START_NEXT.md`，本輪不得視為完成。

7. Review Defects
   - 回顧本輪改善後仍有什麼缺點。
   - 每個缺點都要寫改善方式。
   - 若改善方式是安全、低風險、可本機驗證，進入下一輪 LOOP。

## 30 分鐘輕量 Watchdog

- 每 30 分鐘只做輕量 watchdog，不寫空泛長文。
- 若切片仍在進行，只需簡短回報：
  - 目前動作。
  - 跟上次差異。
  - 阻塞原因。
  - 下一步。
- 若切片開始、切片完成、測試結果改變、阻塞狀態改變、完成度改變或 Agent 狀態改變，必須更新 `CURRENT_STATUS.md`。
- 若切片完成或有實質變更，再同步更新 `docs/AI開發進度.md` 與 `docs/agent_run_report.md`。
- 若連續一次以上無新增實作且無阻塞，不得只回報；必須立即推進 `START_NEXT.md` 中的安全 backlog，或明確說明需要使用者決策。

## 確保仍在執行的證據

每次 watchdog 或切片完成回報，至少提供一項可驗證證據：

- 新增 / 修改的檔案。
- 剛執行的測試命令與結果。
- 目前 active slice 名稱。
- 已啟動或已關閉的 Agent ID。
- 已重啟或確認的 runtime endpoint。

若沒有任何證據，必須寫：

```text
無新增實作，僅狀態維持；下一步立即推進：<安全 backlog 名稱>
```

## 停止條件

可以停止：

- 使用者明確要求停止、暫停、只回報狀態。
- 下一步涉及正式資料、正式 DB、憑證、部署或不可逆操作，需要使用者確認。
- 本輪目標已完成，且下一步已寫入 `START_NEXT.md`。

不可以只因以下原因停止：

- 測試通過。
- 完成一個小功能。
- 文件已更新。
- 沒有新指令但仍有安全 backlog。

## LOOP 回報格式

```text
LOOP 結果：
- 本輪目標：
- 本次完成：
- 跟上次差異：
- 變更檔案：
- 驗證結果：
- Agent / 資安稽核：
- 仍有缺點：
- 缺點改善方式：
- 下一輪建議：
```
