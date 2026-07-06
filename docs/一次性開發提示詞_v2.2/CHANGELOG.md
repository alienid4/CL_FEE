# CHANGELOG

本檔記錄一次性開發提示詞包的重要版本變更。

## v2.2

v2.2 補強 v2.1 的前期確認與長時間自動開發風險。

新增：

- 開工門檻。
- 使用者確認紀錄。
- Data Model Gate。
- Permission Matrix Gate。
- Acceptance Case Gate。
- Test Data Gate。
- 多 Agent 互評分數。
- Stop Rule。
- Delivery Package。
- 適用 / 不適用邊界。

## v2.1

v2.1 升級為 All-in-One Build Pack。

主要目的：

- 不再讓使用者像組 PC 一樣分別理解總指揮、規則、儀表板、糾察隊。
- 一包內建 CIO Build Mode、MVP 契約、全速開發、速度檔、本機控制台與 audit gate。
- 建立實體主目錄 `docs/一次性開發提示詞_v2.1/`。
- v2.0 保留為歷史參考。
- 腳本與控制台優先讀取 v2.1，只有缺少 v2.1 時才 fallback 舊版。

## v2.0

v2.0 從單一長文件改為目錄型提示詞包。

主要目的：

- 降低日常接手 token。
- 讓新手知道先讀哪份文件。
- 把目前狀態、下一步、開發規則、驗證規則、資安規則分開。
- 讓每個專案都能套用同一套工作方式。

相對 v1.9 的改善：

- 新增 `INDEX.md` 作為第一入口。
- 新增 `CURRENT_STATUS.md` 作為真實狀態來源。
- 新增 `START_NEXT.md` 作為下一輪唯一目標。
- 新增 `OPERATING_LOOP.md` 定義固定改善 LOOP。
- 新增 `SECURITY_RULES.md` 定義日常資安底線。
- 新增 `SECURITY_SCAN_RULES.md` 定義白箱 / 黑箱安全檢查。
- 新增 `SECURITY_COMMANDS.md` 提供可執行檢查命令。
- 新增 `AGENT_AUDIT_RULES.md` 確認 Agent 是否照規則做。
- 新增 `UNIVERSAL_PROJECT_GUIDE.md` 說明如何套用到其他專案。
- 新增自動化基礎腳本：`local_ci.ps1`、`check_prompt_pack.ps1`、`check_automation_foundation.ps1`、`security_check.ps1`、`test_all.ps1`、`write_agent_audit_log.ps1`。

## 升級原則

若未來修改以下內容，必須升級提示詞包版本：

- 第一版範圍
- 不做範圍
- Agent 使用策略
- 測試與驗證邊界
- 部署策略
- 資料安全與正式資料規則
- Token 控制與接手流程

不得只把重要規則留在對話中。
# 2026-07-05 - Watchdog / Status Source Correction

- 明確 `docs/一次性開發提示詞_v2.0/` 是當時主版本。
- 明確 2.0 以前版本皆為舊資料 / 歷史參考。
- 將使用者觀察檔定為 `CURRENT_STATUS.md`，避免另開單檔造成狀態漂移。
- 新增 30 分鐘輕量 watchdog 規則：短回報、少寫空泛文件、以可驗證產出為主。
- 更新 `START_NEXT.md`，下一輪回到產品 backlog：mapping catalog Web UI display。
