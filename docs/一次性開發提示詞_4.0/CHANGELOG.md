# CHANGELOG

本檔記錄一次性開發提示詞包的重要版本變更。

## 4.0

4.0 在 v2.2「一包式開發」之上，加一層「自主迴圈」，讓使用者**按一次、走開**；只在絆線 / 煞車 / 卡住時才回來。v2.2 所有 gate 一律沿用、不放寬。

新增：

- 自主迴圈契約：讀現況 → 拉一件 → 定義完成 → 只改這塊 → 自驗 → commit → 下一圈，自己一路跑，不逐圈等使用者。
- 待辦佇列（backlog）：做完自己拉下一件，不用使用者派；清空後自檢「還缺什麼」再補，直到真的做完。
- Governor 預算煞車：明確回合 / 時間 / 每件失敗上限，到頂停下並出「待續」報告（＝敢放手的安全帶）。
- 卡住升級：同一件連續失敗 N 次（預設 3）→ 標 `blocked`、寫進 `decisions.json`、停下問人，不無限鬼打牆。
- 串接真實管線：改綁 `.project/snapshot.py`（看現況）、`.project/checks.py`（自驗關卡）、`.project/decisions.json`（絆線）、`.project/review.py`（多 agent 對抗式審查）。
- 誠實原則：能自主跑到底才叫「做到」；仍需人逐圈推的部分如實標為「半自動」，不得宣稱全自動。

相對 v2.2 的定位：v2.2 是 3.5（gate 齊全、但逐圈人推），4.0 補上「待辦自動拉、預算煞車、卡住升級」三塊 → 目標為「按一次跑到底」。

檔案：`docs/一次性開發提示詞_4.0_FINAL.md`（人類閱讀版）。

### 4.0.1（2026-07-10）提問閘門

- 第 4 節「篩選規則／絆線」補上**「方向 vs 細節」閘門**：只有同時「難以逆轉」＋「賭上範圍/價值觀分歧」才停下問人；細節別包裝成決策丟回，挑合理預設＋一句話說明＋直接做，讓使用者看結果再修。
- 特別點名：「規則／推導邏輯對不對」直接做出來給使用者看，不要空對規格要確認。
- 來源：實戰回饋（AI 把細節升級成一堆提問拖慢節奏）；同步落地於全域 `~/.claude/CLAUDE.md` 決策提問格式與專案記憶 `ask-only-directional`。
待補：`.project/loop.py` 自主驅動器——建好後即為真正無人駕駛的 4.0（連貼啟動語都省）。

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
