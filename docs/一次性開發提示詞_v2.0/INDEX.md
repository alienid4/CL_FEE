# INDEX

本檔是 AI_FEE v2.1 一包式開發提示詞包的入口導覽。

如果是新系統從 0 到 MVP，先讀 `ALL_IN_ONE_BUILD_PACK.md`。
如果是既有專案日常接手，先讀本檔。

目前主版本是 v2.1 All-in-One Build Pack，文件仍放在本目錄：`docs/一次性開發提示詞_v2.0/`。
2.0 以前的單檔提示詞皆為舊資料 / 歷史參考。

本目錄的日常入口是 `INDEX.md`，不是 `README.md`。
`README.md` 是母版規則，只有在需要理解完整專案目標、範圍或規則衝突時才讀。

## 快速閱讀路徑

### 新手最短路徑

如果你是第一次接手既有專案，只做這六步：

1. 讀 `INDEX.md`。
2. 讀 `CURRENT_STATUS.md`。
3. 讀 `START_NEXT.md`。
4. 讀本輪相關程式碼與測試。
5. 依 `OPERATING_LOOP.md` 完成一輪。
6. 完成後更新 `CURRENT_STATUS.md` 與 `START_NEXT.md`。

### 新系統最短路徑

如果使用者說「我要開發一套 XX 系統」，只做這五步：

1. 讀 `ALL_IN_ONE_BUILD_PACK.md`。
2. 進入 CIO Build Mode 訪談。
3. 產出 MVP 契約。
4. 契約確認後全速開發。
5. 用 audit gate 與 Demo Gate 收尾。

| 情境 | 必讀文件 | 可選文件 |
| --- | --- | --- |
| 日常小修 | `CURRENT_STATUS.md`, `START_NEXT.md`, `DEVELOPMENT_RULES.md`, `VERIFICATION_RULES.md` | `AGENT_AUDIT_RULES.md` |
| 中型功能 | `CURRENT_STATUS.md`, `START_NEXT.md`, `DEVELOPMENT_RULES.md`, `VERIFICATION_RULES.md`, `AGENT_AUDIT_RULES.md` | `MODULE_ROADMAP.md` |
| 大型 / 跨模組功能 | `README.md`, `CURRENT_STATUS.md`, `DEVELOPMENT_RULES.md`, `VERIFICATION_RULES.md`, `MODULE_ROADMAP.md`, `AGENT_AUDIT_RULES.md` | `SECURITY_RULES.md`, `SECURITY_SCAN_RULES.md` |
| DB / 權限 / 匯入回匯 / 部署 | `README.md`, `SECURITY_RULES.md`, `SECURITY_SCAN_RULES.md`, `SECURITY_COMMANDS.md`, `AGENT_AUDIT_RULES.md` | `MODULE_ROADMAP.md` |
| Release 前 | `CURRENT_STATUS.md`, `VERIFICATION_RULES.md`, `SECURITY_RULES.md`, `SECURITY_SCAN_RULES.md`, `SECURITY_COMMANDS.md`, `AGENT_AUDIT_RULES.md` | `README.md` |
| 總盤點 / 交接 | 全部讀取 | 既有 WBS / AI 進度 / agent report |

## 文件責任邊界

| 文件 | 只負責 |
| --- | --- |
| `ALL_IN_ONE_BUILD_PACK.md` | 一包式入口：總指揮、法律、儀表板、糾察隊。 |
| `README.md` | 永久目標、第一版範圍、總原則。 |
| `INDEX.md` | 入口導覽與使用情境閱讀路徑。 |
| `CURRENT_STATUS.md` | 真實完成度、最新測試、當前風險。 |
| `START_NEXT.md` | 下一輪唯一目標與驗證命令。 |
| `OPERATING_LOOP.md` | 固定改善 LOOP 與回報格式。 |
| `AUTO_DEV_LOOP.md` | 自動開發迴圈、每圈必問、狀態契約與禁止事項。 |
| `AGENT_RUNTIME_RULES.md` | 一鍵 runtime 入口、狀態檔與限制。 |
| `PROJECT_PROFILE_RULES.md` | 跨專案 profile 偵測與非 Python / 非 Web 套用方式。 |
| `SPEED_RULES.md` | Fast / Standard / Release 速度檔、升級條件與時間預算。 |
| `GATE_CATALOG.md` | 從 v1.5 到 v2.0 整理出的 Gate 清單，區分 Auto / Manual Gate。 |
| `MVP_EVIDENCE_CHECKLIST.md` | 第一版 MVP Scope Gate 的最終驗收證據表。 |
| `DEVELOPMENT_RULES.md` | 工作分級與 Agent 使用方式。 |
| `VERIFICATION_RULES.md` | 測試分級與固定驗證命令。 |
| `MODULE_ROADMAP.md` | 功能切片順序與完成定義。 |
| `SECURITY_RULES.md` | 日常資安與資料安全底線。 |
| `SECURITY_SCAN_RULES.md` | 白箱 / 黑箱漏洞掃描規則。 |
| `SECURITY_COMMANDS.md` | 可執行資安檢查命令與替代方案。 |
| `AGENT_AUDIT_RULES.md` | Agent 稽核表與完成回報模板。 |
| `UNIVERSAL_PROJECT_GUIDE.md` | 如何把本提示詞包套用到其他專案。 |
| `CHANGELOG.md` | 版本差異與升級原因。 |

## 狀態更新要求

每個切片完成後，至少更新：

- `CURRENT_STATUS.md`
- `START_NEXT.md`

若改了規則、範圍、驗證方式或資安要求，還要更新對應規則文件與 `README.md`。

若沒有更新 `CURRENT_STATUS.md` 與 `START_NEXT.md`，本輪切片不得視為完成。

## 使用者觀察檔

使用者若只想確認 Codex 是否仍在工作，請觀察：

```text
docs/一次性開發提示詞_v2.0/CURRENT_STATUS.md
```

只要此檔的最後更新時間、目前切片、跟上次差異、測試結果或下一步有變化，就代表本輪有實際推進。

## 防止文件漂移

- 目前真實狀態只寫在 `CURRENT_STATUS.md`。
- 下一步只寫在 `START_NEXT.md`。
- 永久規則才寫進 `README.md` 或規則文件。
- 不要把同一條規則複製到太多地方；若必須引用，請指向責任文件。

## 給新手的判斷規則

如果不確定要不要繼續做，先問自己：

- 這是不是本輪 `START_NEXT.md` 指定的唯一目標？
- 這會不會碰正式資料、正式 DB、憑證或部署？
- 這會不會改資料模型、權限或核心流程？
- 我是否知道要跑哪個測試？
- 我是否選對速度檔，且沒有碰到需要升級的風險？
- 完成後是否能用命令或檔案證明？

如果答案不清楚，先縮小切片或回報風險。
