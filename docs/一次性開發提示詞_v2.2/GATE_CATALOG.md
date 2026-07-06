# GATE_CATALOG

本檔把 v1.5 到 v2.0 中「不是建議，而是完成門檻」的要求整理成 Gate。

Gate 分成兩種：

- Auto Gate：可由腳本檢查。
- Manual Gate：需要 Agent / Reviewer 提供證據與判斷。

另依觸發時機分成：

- Per-Loop Audit Gate：每個切片都要檢查，防止越界、漏測、無證據、敏感資料與狀態漂移。
- MVP Scope Gate：第一版結束前必須逐項驗收，不要求每個小修都完成全部。

## MVP Scope Gate

目的：確保 v1.5 的第一版必做功能沒有在長期開發中遺失。

這些不是每輪都要擋的 gate，而是第一版驗收前的終點 gate。
每個切片若碰到相關模組，不得破壞對應 MVP 能力。

第一版必做功能：

| 功能 | MVP 驗收要求 | 每輪觸發條件 |
| --- | --- | --- |
| 八項控管看板 | 預算、專案、簽呈、案件管理、核准、合約、請購、付款、資料檢核有畫面或預留位置 | 改 Dashboard / UI navigation 時 |
| 全文檢索 | 可搜尋案件、合約、簽呈、付款、發票、廠商、負責人、附件 | 新增核心資料表或搜尋 API 時 |
| Dashboard 數字下鑽 | Dashboard 數字可追到明細來源 | 改 Dashboard 統計或金額邏輯時 |
| Case 360 | 案件可看基本資料、時間線、簽呈、合約、付款、發票、附件、舉證 | 改 Case / Contract / Payment / Document 時 |
| 時間線 | 預算、專案、簽呈、核准、合約、請購、付款、發票節點有狀態概念 | 改狀態規則或 Case 360 時 |
| 處理優先矩陣 | 可呈現主管先處理哪些案件，並可進明細 | 改主管 Dashboard / priority logic 時 |
| 附件管理 | PDF 可作為附件登錄與關聯，但第一版不做 PDF 自動解析 | 改 documents / attachments 時 |
| Excel 匯入匯出預留 | 有欄位 mapping、匯入批次、暫存與檢核概念 | 改 import / export / mapping 時 |
| 發票 / 簽呈 / 合約 / 付款欄位 | 相關資料有欄位與畫面位置 | 改資料模型或 UI 表單時 |
| 廠商視角 | 可看廠商相關合約、付款、發票、案件 | 改 vendor / contract / report 時 |
| 負責人視角 | 可看負責人手上案件、未完成、金額與待辦 | 改 owner / task / report 時 |
| CMDB 預留 | 保留 CMDB 關聯欄位與畫面，不串接 CMDB | 改 CMDB placeholder 或 asset 欄位時 |

MVP Scope Gate 的判斷：

- 不要求每個小修都完成全部 MVP 功能。
- 若本輪碰到某個 MVP 模組，必須確認沒有破壞該模組既有能力。
- 第一版驗收前，必須逐項產出驗收證據。

## Scope Gate

目的：防止 Agent 偷做、亂擴大或把第二版功能混進第一版。

Auto Gate：

- `START_NEXT.md` 必須存在，且有本輪目標與驗證命令。
- audit log 必須有 `goal`、`classification`、`changed_files`、`verification`、`audit_result`、`next_loop`。

Manual Gate：

- 本輪只做 `START_NEXT.md` 指定的唯一切片。
- 第一版可選與第二版建議只能記錄，不得偷做。
- 涉及正式資料、正式 DB、憑證、部署時必須停下確認。

## Focus Gate

目的：防止 Agent 目標漂移，把輔助工具、控制台、CI、服務重啟或平台整合誤當成本輪主目標。

Auto Gate：

- audit log 必須有明確 `goal`。
- `CURRENT_STATUS.md` 必須寫本輪目標與跟上次差異。

Manual Gate：

- 每輪開始先聲明：本輪目標、本輪不是什麼、允許改什麼、禁止改什麼。
- 工具只能服務本輪目標，不得喧賓奪主。
- 若本輪目標是提示詞本體，不得延伸開發控制台、服務、CI、PowerShell 工具或平台整合，除非直接影響提示詞包可驗證性。
- 若工具驗證卡住超過 10 分鐘或連續 2 次失敗，停止鑽工具，回到本輪目標。
- 若使用者指出「我們不是在討論這個」，Agent 必須立即承認偏航、停止該支線，並回到使用者確認的主目標。

## Autonomy Gate

目的：防止 Agent 過度詢問，把低風險小修推回給使用者，拖慢開發。

Auto Gate：

- audit log 的 `verification` 不可空白。
- audit log 的 `next_loop` 不可空白。

Manual Gate：

- 低風險、可本機驗證的小修，Agent 必須自行判斷、自行修復、自行驗證。
- audit gate 或測試擋下的明確問題，Agent 必須先嘗試安全修復。
- 只有正式資料、正式 DB、憑證、部署、權限、不可逆操作、金額或正式狀態邏輯等重大事項，才需要先問使用者。
- 若需求有多個高風險方向，才停下讓使用者決策。

## Archive Gate

目的：防止舊碼污染新版主程式。

Auto Gate：

- `security_check.ps1` 檢查 `app/`、`tests/`、`scripts/` 不引用 archive 舊路徑。
- pytest collection 不可收集 archive 測試。

Manual Gate：

- 若參考 archive，只能參考概念，不得複製實作。

## Test Gate

目的：防止口頭宣稱完成但未驗證。

Auto Gate：

- `pytest -q`。
- `pytest tests -q`。
- `test_all.ps1`。
- audit log 的 `verification` 不可空白。

Manual Gate：

- UI 變更需跑對應 UI regression 或提供不適用原因。
- Runtime route / schema / store 變更需判斷是否重啟 FastAPI。

## Docs / Status Gate

目的：防止進度散在對話裡。

Auto Gate：

- `CURRENT_STATUS.md` 必須存在。
- `START_NEXT.md` 必須存在。
- `GATE_CATALOG.md` 必須存在。

Manual Gate：

- 每個切片完成後必須更新 `CURRENT_STATUS.md` 與 `START_NEXT.md`。
- 重要決策不得只留在對話中。

## Agent Evidence Gate

目的：防止假稱獨立 Agent 已完成。

Auto Gate：

- audit log 必須有合格 JSONL entry。

Manual Gate：

- 若聲稱獨立 Agent，必須提供 sub-agent id、Calling Agent 區塊、工具呼叫紀錄或回傳摘要。
- 沒有證據只能寫「角色模擬」或「獨立 Agent 未啟動」。

## Security Gate

目的：防止敏感資料與正式環境風險。

Auto Gate：

- `security_check.ps1` 檢查高信心敏感字串。
- `.gitignore` 基本敏感檔案類型檢查。
- `pip check`。

Manual Gate：

- 不碰正式資料、正式 DB、正式憑證。
- 不把 AI 判斷直接寫入正式金額或正式狀態。
- 匯入 / 回匯必須暫存、檢核、人工確認。

## UI Gate

目的：防止內部註解或開發文字直接露給使用者。

Auto Gate：

- `check_audit_gate.ps1` 掃 `app/web` 常見內部標記。

Manual Gate：

- UI 主畫面不得直接顯示 Prompt、Agent、TODO、debug、測試用、開發中、內部流程說明。
- 必要說明需收進 tooltip、info icon、help panel、details 或 docs。
- 企業內部系統應保持資訊密度高、可掃描，不做行銷頁。

## UI Mock Gate / HTML Mock Gate

目的：避免 Agent 直接實作錯畫面，導致後期大量返工。

Auto Gate：

- audit log 的 `verification` 不可空白。

Manual Gate：

- 若系統有 UI，正式 UI 實作前必須先做 UI 模擬確認。
- UI 模擬可用文字版畫面草圖、頁面結構清單、wireframe、截圖式 mock 或可點擊 prototype。
- UI mock 必須確認主要使用者、主要流程、首頁 / Dashboard / 清單 / 明細 / 表單 / 設定、欄位名稱、按鈕狀態與資訊層級。
- 使用者確認 UI 方向後，必須接著做 HTML Mock。
- HTML Mock 必須是可在瀏覽器開啟的靜態 HTML / CSS / JS，使用 mock data，不連正式資料、不寫 DB。
- HTML Mock 必須呈現主要頁面、主要流程、表格、表單、按鈕與狀態。
- 使用者確認 HTML Mock 後，才進入正式 UI / API / DB 實作。
- 若使用者明確同意跳過 UI mock 或 HTML mock，必須在完成回報與 audit 中記錄。

## Data Model Gate

目的：避免 UI 看似正確，但資料結構錯誤導致後期返工。

Manual Gate：

- 正式實作前必須整理 entity / table、欄位、型別、必填、狀態、關聯、金額、日期、匯入來源、audit / source-chain 欄位。
- 涉及金額、正式狀態、權限或正式資料時，必須升級重大事項。

## Permission Matrix Gate

目的：避免權限後補或只靠前端隱藏按鈕。

Manual Gate：

- 建立角色 x 功能 x 可看 / 可新增 / 可修改 / 可停用 / 可刪除 / 可匯出 / 可核准矩陣。
- 權限、AD、SSO、正式角色規則屬重大事項。

## Acceptance Case Gate

目的：避免 MVP 契約只有抽象描述，沒有可驗收案例。

Manual Gate：

- 至少列 3 個正常流程。
- 至少列 3 個錯誤流程。
- 至少列 3 個邊界情境。
- 至少列 1 個權限情境。
- 至少列 1 個資料不寫入 / rollback / 保護情境。

## Test Data Gate

目的：避免 AI 使用敏感資料或不可重置測試資料。

Manual Gate：

- mock data 可用。
- 不得使用真實個資、正式客戶資料、正式金額或公司敏感資料。
- 測試資料要可重置。
- demo data 必須標示為假資料。
- 匯入 / 回匯測試不得覆蓋正式資料。

## Stop Rule Gate

目的：防止長時間自動開發硬衝造成返工或風險。

Manual Gate：

- 同一測試連續失敗 2 次，停下分析。
- 連續 30 分鐘無新增實作，停下回報。
- 需求矛盾、重大風險未授權、工具問題會造成目標漂移時，停下回報。

## Git Gate

目的：防止錯誤檔案進版本控管。

Auto Gate：

- `git status --short`。
- `git diff --check`。
- `.gitignore` 檢查。

Manual Gate：

- 不提交 `.env`、DB、log、Excel、PDF、憑證、cookie、session。
- 若使用者未要求 commit，不自動 commit。

## Deployment Gate

目的：防止假裝部署或碰正式環境。

Auto Gate：

- runtime freshness 可用 `check_runtime_freshness.ps1` 檢查本機 / 授權測試環境。

Manual Gate：

- 未確認 VM、網段、權限前，不得宣稱部署完成。
- 正式部署前需有備份、rollback、驗證方式與人工確認。

## Release / CI Gate

目的：讓速度、穩定、符合要求、自動化形成固定機制。

Auto Gate：

- 本機 CI：`scripts/local_ci.ps1`。
- 未來平台 CI 應呼叫同一套本機 CI 或 `test_all.ps1`。

Manual Gate：

- 平台 CI 未建立前，不得宣稱已有雲端 CI。
- 若 CI 失敗，不得合併或宣稱可交付。
