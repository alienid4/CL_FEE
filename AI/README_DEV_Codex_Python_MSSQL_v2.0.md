# 費用合約控管系統 - Python + MSSQL 開發規格 v2.0

## 1. 技術選型

本版以 Python + MSSQL 為正式方向。

| 分層 | 建議技術 |
|---|---|
| 後端 API | Python FastAPI |
| API 文件 | OpenAPI / Swagger，FastAPI 內建 `/docs` 可用 |
| 資料庫 | Microsoft SQL Server |
| ORM / DB 存取 | SQLAlchemy 2.x 或 pyodbc + service/repository 分層 |
| 前端 | 第一版可用 vanilla HTML / CSS / JS |
| 檔案 | PDF / Excel 附件需保存原檔與來源位置 |
| 搜尋 | 第一版可先以 DB LIKE / Full-Text Search 預留，正式可用 SQL Server Full-Text Search |

## 2. 必要目錄結構

建議 Codex 建立：

```text
fee-contract-control/
├─ README.md
├─ README_Codex_接手總覽_v2.0.md
├─ pyproject.toml 或 requirements.txt
├─ .env.example
├─ app/
│  ├─ main.py
│  ├─ core/
│  │  ├─ config.py
│  │  ├─ security.py
│  │  └─ logging.py
│  ├─ db/
│  │  ├─ session.py
│  │  ├─ base.py
│  │  └─ migrations/
│  ├─ models/
│  ├─ schemas/
│  ├─ repositories/
│  ├─ services/
│  ├─ api/
│  │  ├─ router.py
│  │  └─ routes/
│  └─ tests/
├─ public/
│  ├─ index.html
│  ├─ css/
│  └─ js/
├─ docs/
└─ skills/
```

## 3. 啟動與健康檢查

必須提供：

```text
GET /health
```

回應範例：

```json
{
  "ok": true,
  "service": "fee-contract-control",
  "runtime": "python-fastapi",
  "database": "FeeContractControl",
  "time": "2026-06-10T00:00:00+08:00"
}
```

## 4. 開發指令建議

若使用 `requirements.txt`：

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

若使用 `pyproject.toml` / uv：

```bash
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 5. MSSQL 連線設定

`.env.example` 至少包含：

```text
APP_NAME=fee-contract-control
APP_ENV=dev
APP_HOST=0.0.0.0
APP_PORT=8000
DB_DRIVER=ODBC Driver 17 for SQL Server
DB_SERVER=your-mssql-host
DB_PORT=1433
DB_NAME=FeeContractControl
DB_USER=fee_contract_app
DB_PASSWORD=change_me
DB_TRUST_CERT=yes
```

AP 帳號權限原則：

- 不給 SA。
- 不給 sysadmin。
- 原則上不給 db_owner 作為日常執行帳號。
- 給本 DB 讀、寫、必要 SP 執行。
- 建表、改表、升版使用 DBA / 部署帳號另行處理。

## 6. 核心資料表

第一版至少建立以下資料表或對應 ORM models：

| 表 | 用途 |
|---|---|
| users | 使用者 |
| roles | 角色 |
| user_roles | 使用者角色 |
| cost_contract_items | 費用合約主檔 |
| budget_items | 預算資料 |
| contracts | 合約資料 |
| signing_cases | 簽呈案件 |
| signing_case_logs | 簽呈流程歷程 |
| payment_schedules | 付款期別 |
| reimbursements | 核銷資料 |
| amount_changes | 金額變更 |
| price_histories | 歷史價格 |
| documents | 附件 |
| document_texts | PDF / 文件文字索引 |
| source_references | 來源連結 / 證據鏈 |
| ai_suggestions | AI 建議 |
| amount_extractions | PDF / AI 金額解析暫存 |
| import_batches | 匯入批次 |
| import_rows | 匯入明細 |
| export_batches | 匯出批次 |
| export_rows | 匯出列 |
| report_snapshots | 報表快照 |
| audit_logs | 異動紀錄 |

## 7. 通用欄位

正式資料表建議包含：

```text
id
created_at
updated_at
created_by
updated_by
version
status
is_deleted
row_version
```

SQL Server 可使用 `rowversion` 防止 Excel 回匯覆蓋新資料。

## 8. API 模組

建議 API：

```text
GET /health
GET /api/dashboard/executive
GET /api/dashboard/manager
GET /api/dashboard/assistant
GET /api/dashboard/handler
GET /api/cost-contract-items
POST /api/cost-contract-items
GET /api/cost-contract-items/{id}
PUT /api/cost-contract-items/{id}
POST /api/cost-contract-items/{id}/void
GET /api/signing-cases
POST /api/signing-cases
PUT /api/signing-cases/{id}
POST /api/signing-cases/{id}/status
GET /api/signing-cases/{id}/logs
GET /api/monthly-spending
GET /api/amount-validations
POST /api/amount-validations/{id}/confirm
POST /api/imports/excel
GET /api/imports/{id}
POST /api/imports/{id}/confirm
POST /api/reimports/excel
GET /api/reimports/{id}/diff
POST /api/reimports/{id}/apply
POST /api/documents
GET /api/documents/{id}
GET /api/documents/{id}/preview
GET /api/search
GET /api/search/documents
GET /api/report-snapshots
GET /api/audit-logs
```

## 9. API 回應格式

成功：

```json
{
  "ok": true,
  "data": {}
}
```

失敗：

```json
{
  "ok": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "錯誤訊息"
  }
}
```

## 10. 金額與 AI 規則

AI / OCR / PDF 解析資料只可進暫存或建議區，不得直接寫入正式金額。

正式報表只可使用：

- 人工確認金額。
- 主管確認金額。
- 會計付款確認金額。

不得直接使用：

- AI 解析值。
- OCR 未確認值。
- 來源衝突值。
- 待確認值。

除非報表明確標示「待確認」。

## 11. 匯入 / 回匯規則

Excel 匯入：

```text
Excel → import_batches / import_rows → 欄位對應 → 檢核 → 助理確認 → 正式資料
```

Excel 回匯：

```text
系統匯出可回匯 Excel
→ Excel 含 systemId / version / exportBatchId
→ 使用者修改
→ 回匯
→ 差異比對
→ 風險分級
→ 人工確認
→ 寫入正式資料
→ audit_logs
```

不得直接覆蓋正式資料。

## 12. UI 要求

- 四角色入口。
- 功能以 TAB 呈現。
- 左側導覽不佔大版面。
- 使用者畫面不得顯示內部討論文字。
- 所有表格可排序。
- 所有卡片、數字、清單列可下鑽。
- 案件履歷需有基本資料、簽呈流程、合約資訊、付款核銷、金額變更、歷史價格、附件、AI 建議、動作紀錄、來源資料。

## 13. 驗收命令

Codex 需提供對應命令，例如：

```bash
python -m compileall app
pytest
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

若尚未建立測試，也需先建立 smoke test：

- `/health` 可回應。
- OpenAPI 可打開。
- 首頁可打開。
- DB 設定缺少時有清楚錯誤訊息，不應靜默失敗。
