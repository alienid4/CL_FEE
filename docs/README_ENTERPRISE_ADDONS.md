# Enterprise Add-ons And Rules

Version: 2026-07-03

這份文件補強 Project Baseline Kit 的企業版使用規則。主包仍然負責所有專案都需要的基本功；附屬包只放特定場景才需要的能力，例如 WBS、主管簡報、安全掃描、UI 治理、DB / AD / Email 設定。

## 主包與附屬包

建議採用「主包 + 附屬包」設計。

主包必放：

- AI 不猜、不假裝完成、不迎合不合理需求。
- 需求不清楚時，先給建議答案、優缺點、風險，再問問題。
- 預設公司正式系統使用 Microsoft SQL Server；除非需求明確指定其他資料庫。
- 每次修改都要有驗證證據，不能只說完成。
- UI、資料、權限、安全、交接、回滾與測試的最低標準。

附屬包可選：

- WBS Planning Pack：產生 WBS、時程、里程碑、責任分工與驗收項目。
- Executive Presentation Pack：產生 CIO / 客戶簡報、效益、風險與案例故事。
- Security Scan Pack：白箱、黑箱、弱點掃描與敏感資訊檢查。
- Enterprise UI Governance Pack：企業內部系統 UI 密度、表格、全文檢索、數字下鑽與管理介面規則。
- Enterprise DB Auth Pack：MSSQL、AD 登入、Email 設定與測試。

附屬包不能取代主包。任何附屬包都必須先遵守主包的安全、測試、交接與反偷懶規則。

## 公司 Codex Enterprise 預設

- 使用情境：PC 上的 VS Code / Codex Enterprise，透過 Linux 主機開發、測試或部署。
- 未指定資料庫時，正式系統預設 Microsoft SQL Server。
- 原型或離線小工具可以暫用 JSON / SQLite，但文件必須說明正式環境的 MSSQL migration 路徑。
- 不得把真實帳號、密碼、Token、主機清單、個資、內部 IP 或公司敏感資料交給外部工具。
- 診斷指令必須預設輸出到 `/tmp` 或本機 temp，且要遮罩或 hash 敏感資訊。

## 減少每次都按同意

不要用繞過安全的方式減少同意。正確做法是把常用安全動作變成固定腳本：

- 讀取狀態：提供 read-only diagnostics script。
- 小修部署：提供 quick patch script。
- 完整驗證：提供 full verification script。
- 發版：提供 release automation script。

腳本要清楚列出會做什麼，預設不得刪資料、覆蓋資料或外傳資料。破壞性動作仍然需要人工確認。

## AI 不偷懶規則

AI 必須做到：

- 改 code 前先讀現況。
- 結論要有證據，例如測試輸出、API 回應、截圖、log 摘要或檔案路徑。
- 不知道就說不知道，並提供可去敏的查詢指令。
- 不把「看起來像」當成「已確認」。
- 不因為使用者希望某答案成立就附和。
- 如果需求不合理，先提出建議方案與優缺點，再問是否採用。
- 小修可以快速驗證；大修必須完整驗證。

## UI 基本規則

- 內部系統不要留大量空白。資訊要密，但要有秩序。
- 一頁聚焦一個主要功能，盡量不要讓使用者長距離捲動。
- 同一功能內的子功能用 tab 分開。
- 表格必須可排序。
- 預設不要攤開巨大表格；搜尋、篩選、點數字卡或按顯示全部後再展開。
- 必須有全文檢索。
- 所有數字卡都要可點擊下鑽到明細。
- 有新增按鈕，就要有修改與刪除或停用入口。
- 每個模組都要有管理介面、開關與設定頁。

## 管理介面規則

每個模組都要有自己的設定：

- 模組啟用 / 停用。
- 權限與角色。
- 連線設定。
- 預設值。
- 通知設定。
- 稽核紀錄。
- 測試連線或健康檢查。

開發 A 模組時，A 模組的設定要在管理介面的 A 模組底下，不要散落到全域設定。

## 登入與 Email

- 預設設計 AD 登入。
- 必須保留登入測試與權限測試。
- Email / SMTP / Graph API 設定要能在管理介面測試。
- Email 設定不得寫死在程式碼。
- 登入與 Email 測試結果要能留下稽核紀錄。

## 弱點掃描

白箱掃描：

- Dependency / package vulnerability。
- SAST。
- Secret scan。
- License scan。
- Config / IaC scan。
- 權限與資料流檢查。

黑箱掃描：

- HTTP security headers。
- TLS / certificate。
- Auth / session。
- Rate limit。
- DAST。
- Port exposure。
- Error leakage。

正式發版至少要有 secret scan、dependency scan、基本 DAST 或替代檢查。

