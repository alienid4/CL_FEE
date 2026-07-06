# AI_FEE 一次性開發提示詞 v2.1

本版是 All-in-One Build Pack：一包包含總指揮、開發規則、本機儀表板與 audit 糾察隊。

使用者不需要像組 PC 一樣分別挑 CPU、RAM、硬碟；本包要像 Notebook 一樣，拿到就能啟動新系統開發或接手既有專案。

目前主版本就是本目錄：

```text
docs/一次性開發提示詞_v2.1/
```

2.0 以前版本皆為舊資料 / 歷史參考。若舊版規則與本目錄衝突，以本目錄為準。

若是從 0 開發新系統，請先讀 `ALL_IN_ONE_BUILD_PACK.md`。
若是既有專案日常接手，請先讀 `INDEX.md`。
本檔是母版規則，不是日常第一讀文件。

v2.1 延續 v2.0 目錄化成果，並解決 v1.9 / v2.0 的主要缺點：

- 文件太長，日常接手吃 token。
- 目標、規則與目前真實狀態容易混在一起。
- 小修 / 中型 / 大型功能仍可能被誤判。
- 測試要求容易散落在不同章節。
- 第一版範圍很大，AI 容易一次開太多線。

## 閱讀順序

日常開發請依序閱讀：

1. `CURRENT_STATUS.md`
2. `START_NEXT.md`
3. 當前切片相關程式碼與測試
4. 必要時才讀本檔與其他規則文件

只有在以下情況才讀完整規則：

- 總盤點
- 交接
- 架構決策
- 功能範圍爭議
- 正式資料 / DB / 權限 / 部署相關變更

## 文件索引

| 檔案 | 用途 |
| --- | --- |
| `ALL_IN_ONE_BUILD_PACK.md` | v2.1 一包式入口，包含 CIO Build Mode、MVP 契約、全速開發與 Demo Gate。 |
| `README.md` | v2.1 母版入口，定義總原則與文件閱讀方式。 |
| `INDEX.md` | 第一入口，依使用情境導向需要閱讀的文件。 |
| `CURRENT_STATUS.md` | 目前真實狀態，日常接手第一讀。 |
| `START_NEXT.md` | 下一輪開發指令，保持短小明確。 |
| `OPERATING_LOOP.md` | 固定改善 LOOP：讀取、切片、修改、驗證、稽核、更新、檢討。 |
| `AUTO_DEV_LOOP.md` | 自動開發迴圈，定義每圈必問、狀態契約與禁止事項。 |
| `AGENT_RUNTIME_RULES.md` | 一鍵 runtime 入口，負責 profile、驗證、audit 與狀態檔。 |
| `PROJECT_PROFILE_RULES.md` | 跨專案 profile 偵測與測試命令替換規則。 |
| `SPEED_RULES.md` | Fast / Standard / Release 速度檔，壓縮低風險小修等待時間。 |
| `GATE_CATALOG.md` | 從 v1.5 到目前版本整理出的 Gate 清單，區分 Auto / Manual Gate。 |
| `MVP_EVIDENCE_CHECKLIST.md` | 第一版 MVP Scope Gate 的最終驗收證據表。 |
| `DEVELOPMENT_RULES.md` | 小修 / 中型 / 大型 / 高風險流程規則。 |
| `VERIFICATION_RULES.md` | 測試與驗證分級。 |
| `MODULE_ROADMAP.md` | 第一版功能切片順序與完成定義。 |
| `SECURITY_RULES.md` | 日常資安、資料安全與 Agent 行為底線。 |
| `SECURITY_SCAN_RULES.md` | 白箱 / 黑箱漏洞掃描與 release 前資安檢查。 |
| `SECURITY_COMMANDS.md` | 可執行資安檢查命令與替代檢查方式。 |
| `AGENT_AUDIT_RULES.md` | 確認 Agent 是否遵守本專案規則的稽核表。 |
| `UNIVERSAL_PROJECT_GUIDE.md` | 如何把本提示詞包套用到其他專案。 |
| `CHANGELOG.md` | 版本差異與升級原因。 |

## 核心原則

小事快跑，大事走流程；砍掉無效等待，不砍必要驗證。
在不降低測試、資料安全與可追溯性的前提下提速。

新系統開發預設採 CIO Build Mode：

- 先訪談。
- 產出 MVP 契約。
- 契約確認後全速開發。
- 低風險問題 Agent 自己判斷、自己修、自己驗。
- 重大事項才問使用者。
- 最後用 Demo Gate 交付可展示 MVP。

速度採三檔：

- Fast Lane：文件、小修、明確 bug，目標 10-30 分鐘。
- Standard Lane：一般產品切片，目標 45-90 分鐘。
- Release Lane：DB、權限、匯入回匯、部署、資安與交付前檢查。

若 Fast Lane 碰到高風險項目，必須依 `SPEED_RULES.md` 自動升級，不得硬闖。

v1.5 的第一版必做功能屬於 `MVP Scope Gate`：

- 第一版驗收前必須逐項檢查。
- 不要求每個小修都完成全部。
- 每輪若碰到相關模組，不得破壞既有 MVP 能力。

## 狀態來源規則

本提示詞包定義目標、規則與邊界。
目前真實完成度、最新測試結果、當前風險與下一步，以 `CURRENT_STATUS.md` 為準。

使用者可直接觀察 `CURRENT_STATUS.md` 確認 Codex 是否仍在工作。每個切片開始、切片完成、測試結果改變、阻塞狀態改變或切換下一步時，必須更新 `CURRENT_STATUS.md`。

若本提示詞包與 `CURRENT_STATUS.md` 對目前狀態描述不同：

- 目標與規則以本提示詞包為準。
- 實際進度、最新測試結果、當前風險與下一步以 `CURRENT_STATUS.md` 為準。

## 版本升級規則

若未來修改以下內容，必須升級本一次性開發提示詞版本：

- 第一版範圍
- 不做範圍
- Agent 使用策略
- 測試與驗證邊界
- 部署策略
- 資料安全與正式資料規則
- Token 控制與接手流程

不得只把重要規則留在對話中。
重要規則需寫回新版提示詞包，並同步更新 `CURRENT_STATUS.md` 或 `START_NEXT.md`。

## 專案目標

開發「費用合約控管系統」第一版，做出可供主管、業助、承辦人操作的系統本體。

使用者必須可以查案件、看預算、專案、簽呈、合約、請購、付款、發票、附件與舉證狀態。
系統不是單純查表工具，而是費用、專案、簽呈、合約、付款、發票與來源舉證的控管追蹤系統。

第一版以本機 / 開發環境可展示、可驗證、可中斷續跑為目標。
正式 AD、正式 MSSQL、真實 PDF 解析、正式外部系統介接可先預留，不得假裝已完成。

## 第一版必做功能

1. 八項控管看板：預算、專案、簽呈、案件管理、核准、合約、請購、付款、資料檢核。
2. 全文檢索：可搜尋案件、合約、簽呈、付款、發票、廠商、負責人、附件。
3. Dashboard 數字下鑽：每個數字都要能點出明細。
4. Case 360：每個案件要能看到基本資料、時間線、簽呈、合約、付款、發票、附件、舉證。
5. 時間線：顯示預算、專案、簽呈、核准、合約、請購、付款、發票節點。
6. 處理優先矩陣：讓主管知道哪些案件要先處理，並可點進案件明細。
7. 附件管理：PDF 可作為附件登錄與關聯，但第一版不做 PDF 自動解析。
8. Excel 匯入匯出預留：先做欄位 mapping、匯入批次、暫存與檢核概念。
9. 發票、簽呈、合約、付款資料都要有欄位與畫面位置。
10. 廠商視角：可看廠商相關合約、付款、發票、案件。
11. 負責人視角：可看負責人手上案件、未完成、金額與待辦。
12. CMDB 預留：第一版只保留 CMDB 關聯欄位與畫面，不串接 CMDB。
13. 稽核紀錄：重要新增、修改、停用、刪除、匯入確認與狀態變更需保留 audit log 或預留欄位。
14. 來源舉證鏈：資料至少要預留來源檔、Sheet、列號、欄位、原始值、文件或附件關聯。

## 第一版不做

1. 不解析真實 PDF。
2. 不匯入真實電子發票。
3. 不串接 CMDB。
4. 不要求使用者提供敏感資料。
5. 不做正式 AD / SSO 權限。
6. 不做正式營運資安控管，但要保留未來擴充位置。
7. 不把 AI 判斷直接寫入正式金額或正式狀態。
8. 不直接碰正式資料、正式 DB、正式憑證或不可逆部署。

## 資料與權限策略

- 第一版可先用 SQLite；公司正式系統未指定 DB 時，預設方向是 Microsoft SQL Server。
- 第一版需保留角色與權限模型，但不實作正式 AD / SSO 登入。
- 第一版至少保留 CIO / 高階主管、部門主管 / 業助、承辦人 / 負責人、系統管理者四種角色概念。
- 未來 AD 控權要以後端 API 權限為準，不能只靠前端隱藏按鈕。
- 回匯與匯入不得直接覆蓋正式資料；必須先暫存、檢核、人工確認，再寫入正式表。

## 資安、掃描與 Agent 稽核

資安分成三層，不得混在一起：

1. 日常資安與資料安全底線：讀 `SECURITY_RULES.md`。
2. 白箱 / 黑箱漏洞掃描：讀 `SECURITY_SCAN_RULES.md`。
3. 可執行資安檢查命令：讀 `SECURITY_COMMANDS.md`。
4. Agent 是否照規則做的稽核：讀 `AGENT_AUDIT_RULES.md`。

日常小修至少遵守 `SECURITY_RULES.md` 與 `AGENT_AUDIT_RULES.md`。
DB、權限、登入、匯入回匯、部署或 release 前，必須再依 `SECURITY_SCAN_RULES.md` 判斷白箱 / 黑箱檢查範圍，並依 `SECURITY_COMMANDS.md` 執行可行命令。

## Archive 與舊碼規則

`archive/old_api_local_web_20260704-135900` 是舊版參考，不能作為主程式來源。

- 不刪除 archive。
- 不搬移 archive。
- 不從 archive、舊專案、壓縮包直接複製主程式。
- 若需要參考舊碼，必須先回報：`只參考概念，不複製實作`。
- archive 不可被 pytest 預設收集。
- 若要排除 archive 測試，使用 pytest 設定。

## 完成回報格式

每個切片完成後，請回報：

- 本次完成項目
- 跟上次差異
- 變更檔案
- 驗證命令與結果
- 是否需要重啟 FastAPI
- 已知限制
- 下一個建議切片

## 自動化腳本

v2.1 提示詞包已有基礎自動化：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\local_ci.ps1
powershell -ExecutionPolicy Bypass -File scripts\fast_ci.ps1
powershell -ExecutionPolicy Bypass -File scripts\agent_runtime_once.ps1 -Goal "..." -Lane fast
powershell -ExecutionPolicy Bypass -File scripts\detect_project_profile.ps1
powershell -ExecutionPolicy Bypass -File scripts\deep_security_check.ps1
powershell -ExecutionPolicy Bypass -File scripts\summarize_agent_audit_log.ps1
powershell -ExecutionPolicy Bypass -File scripts\check_prompt_pack.ps1
powershell -ExecutionPolicy Bypass -File scripts\check_automation_foundation.ps1
powershell -ExecutionPolicy Bypass -File scripts\check_audit_gate.ps1 -RequireLog
powershell -ExecutionPolicy Bypass -File scripts\security_check.ps1 -IncludePytestCollect
powershell -ExecutionPolicy Bypass -File scripts\test_all.ps1 -IncludePromptPack -IncludeAutomationFoundation -IncludeSecurity
```

若腳本不可用，必須回報失敗原因與替代檢查方式，不得假裝完成。

Audit 是使用者的糾察隊。完成任何會修改工作區或狀態文件的 LOOP 前，必須寫入 audit log 並通過 `scripts\check_audit_gate.ps1 -RequireLog`。

若尚未接 GitHub / GitLab / Jenkins / Azure DevOps 等平台 CI，必須先使用本機 CI：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\local_ci.ps1
```

未來接平台 CI 時，應優先呼叫同一套本機 CI 或 `scripts\test_all.ps1`，避免本機與雲端檢查規則分裂。
