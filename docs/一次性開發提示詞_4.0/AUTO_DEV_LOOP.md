# AUTO_DEV_LOOP

本檔定義 AI_FEE 與可重用專案的自動開發迴圈。

目標不是讓 AI 無限制自行變更，而是讓 AI 在安全邊界內反覆：

```text
goal -> inspect -> plan -> change -> test -> audit -> update status -> next loop
```

## 每圈必問

每個 LOOP 開始前，Agent 必須先自己回答：

1. 本圈唯一目標是什麼？
2. 這是小修、中型、大型還是高風險？
3. 會改哪些檔案類型？
4. 需要跑哪些測試或檢查？
5. 是否涉及正式資料、正式 DB、憑證、部署或不可逆操作？
6. 完成後要更新哪些狀態文件？

若第 5 題答案是「是」或不確定，必須停下回報風險，不得自行執行。

## 自主判斷與自主修復

Agent 的預設行為是自己判斷、自己修復、自己驗證。不要把低風險小事丟回給使用者決定。

必須自行處理：

- 明確 bug。
- 文件、提示詞包、測試設定、CI 腳本的小修。
- 可用本機測試驗證的低風險問題。
- 測試失敗且原因明確、修復範圍小的問題。
- audit gate 擋下的可修正問題。

必須先問使用者或升級回報：

- 正式資料、正式 DB、正式憑證、正式部署。
- 不可逆 migration、刪除資料、覆蓋資料。
- 權限 / AD / SSO / 角色規則會改變使用者可見權限。
- 金額、付款、發票、正式狀態邏輯會影響真實決策。
- 需求有兩個以上合理方向，且選錯會造成返工或風險。
- 需要使用者提供業務規則、正式環境資訊或敏感資料。

若只是需要澄清但可先安全推進，先做不會鎖死方向的小切片，並在回報中列出假設。

## 每圈狀態

每圈至少要留下以下狀態：

```json
{
  "loop": 1,
  "goal": "",
  "classification": "small|medium|large|high-risk",
  "changed_files": [],
  "verification": [],
  "security_check": "",
  "audit_result": "",
  "remaining_gap": "",
  "next_loop": ""
}
```

## 最小可執行順序

1. Read
   - 讀 `INDEX.md`
   - 讀 `CURRENT_STATUS.md`
   - 讀 `START_NEXT.md`
   - 讀本圈相關文件與程式

2. Decide
   - 決定本圈唯一目標
   - 決定驗證命令
   - 決定是否需要 Agent 分工

3. Change
   - 只改本圈需要的檔案
   - 不做無關重構
   - 不碰正式資料

4. Verify
   - 執行驗證命令
   - 若失敗，分析原因並在安全範圍內修復
   - 若連續失敗，縮小範圍或回報阻塞

5. Audit
   - 使用 `AGENT_AUDIT_RULES.md`
   - 寫入 JSONL audit log
   - 執行 audit gate；audit 是使用者的糾察隊，不是選填項
   - 可使用：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\write_agent_audit_log.ps1 -Goal "..." -Classification small -Verification "pytest -q"
powershell -ExecutionPolicy Bypass -File scripts\check_audit_gate.ps1 -RequireLog
```

6. Update
   - 更新 `CURRENT_STATUS.md`
   - 更新 `START_NEXT.md`
   - 更新相關規則文件

7. Continue
   - 若下一步安全、低風險、可本機驗證，進入下一圈
   - 若下一步高風險，停下回報
   - 若下一步只是明確小修，不需等待使用者指示

## 禁止事項

- 不得用「測試通過」當作唯一完成證據。
- 不得沒有 audit log 就宣稱自動開發完成。
- 不得 audit gate 未通過就宣稱完成。
- 不得在 UI 主畫面直接顯示內部註解；必要說明需收進 tooltip、help、details 或 docs。
- 不得把沒有證據的 Agent 工作寫成已完成。
- 不得把正式資料或憑證寫入 log。
- 不得跨多個功能線同時修改。
- 不得把低風險、可驗證的小修交回使用者決定。
- 不得用「需要確認」拖延可以安全先做的修復。

## 推薦驗證

一般自動開發 LOOP 至少跑：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\check_prompt_pack.ps1
powershell -ExecutionPolicy Bypass -File scripts\test_all.ps1 -IncludePromptPack -IncludeSecurity
```
