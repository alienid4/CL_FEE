# API / DB / UI 開發重點 v2.0

## 1. API 開發優先順序

第一批 API：

1. `/health`
2. `/api/dashboard/*`
3. `/api/cost-contract-items`
4. `/api/signing-cases`
5. `/api/audit-logs`
6. `/api/search`

第二批 API：

1. 匯入 / 回匯。
2. 文件 / PDF / 文字索引。
3. 金額驗證。
4. 報表快照。
5. AI suggestions。

## 2. DB 開發優先順序

第一批表：

1. users / roles / user_roles
2. cost_contract_items
3. signing_cases
4. signing_case_logs
5. contracts
6. payment_schedules
7. reimbursements
8. amount_changes
9. price_histories
10. audit_logs

第二批表：

1. documents
2. document_texts
3. source_references
4. ai_suggestions
5. amount_extractions
6. import_batches / import_rows
7. export_batches / export_rows
8. report_snapshots

## 3. UI 開發重點

### 3.1 處長

TAB：總覽、支出時間線、待決策、已完成、差異分析、案件履歷。

處長不主打 PM 進度線。

### 3.2 管理者 / 助理

TAB：總覽、案件管理、資料健檢、匯入回匯、金額驗證、全文搜尋、報表快照、動作紀錄、案件履歷。

管理者 / 助理可新增、編輯、作廢案件。

### 3.3 主管

TAB：總覽、PM 時間線、簽呈看板、差異比較、明細、已完成、案件履歷。

主管狀態統計必須平衡。

### 3.4 承辦

TAB：我的待辦、新增案件、PM 時間線、簽呈看板、文件補件、核銷更新、案件履歷。

承辦要有新增案件入口。

## 4. 統計平衡

同一組篩選條件下：

```text
全部 = 未啟動 + 進行中 + 逾期 + 完成
```

風險標籤不納入主狀態加總。

## 5. 下鑽標準

```text
L1 Dashboard 摘要
→ L2 條件清單
→ L3 案件履歷
→ L4 原始來源 / PDF / Excel / 動作紀錄
```

## 6. 資料來源追溯

| 來源 | 必備資訊 |
|---|---|
| Excel | 檔名、Sheet、Row、匯入批次 |
| PDF | 檔名、頁碼、命中段落 |
| 系統 | 詳情頁、建立人、建立時間 |
| AI | 建議值、來源、確認狀態 |
| 報表 | 快照版本、產出人、產出時間 |
