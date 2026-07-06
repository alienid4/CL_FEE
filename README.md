# Project Baseline Kit 強化版

Version: 2026-07-02

Enterprise addendum: `README_ENTERPRISE_ADDONS.md`

2026-07-03 補強重點：

- 主包維持基本功：AI 不猜、不偷懶、不迎合、改前先查、改後要證據。
- 新增附屬包策略：WBS、主管簡報、安全掃描、UI 治理、MSSQL / AD / Email 可獨立套用。
- 公司正式系統未指定 DB 時，預設 Microsoft SQL Server。
- 企業 UI 預設支援全文檢索、表格排序、數字下鑽、模組管理介面與新增 / 修改 / 刪除一致性。
- 弱點掃描分成白箱與黑箱，發版依變更大小決定掃描強度。

這是一包可重複套用在新專案與既有專案的「基本功補強包」。它不是框架，也不是要把系統重寫；它的用途是先把專案講清楚、測得出來、交接得出去，讓 AI、工程師與新人不要每次都從猜測開始。

## 這包的優勢

| 優勢 | 說明 |
| --- | --- |
| 降低重複說明 | 把專案目的、資料、流程、風險、測試、部署、交接都固定成模板。 |
| 降低亂修風險 | 要求先確認資料模型與狀態流程，再做最小範圍修改。 |
| 降低 AI 幻覺 | 明定「不知道就說不知道，先收證據，不把假設講成事實」。 |
| 改善 Debug 速度 | 提供安全診斷腳本與 debug intake，避免每次人工重新問資料。 |
| 改善交接品質 | 提供公司 GPT / Codex / 新人接手用的 handoff index、takeover prompt、snapshot 與 checklist。 |
| 改善改版品質 | 把小修、中修、大修分級，對應不同驗證強度與 release 注意事項。 |
| 可衡量導入成效 | 透過 baseline metrics 與 project health score 追蹤開案、debug、測試、交接是否變快。 |

## 適用情境

- 新專案開發前，先建立基本文件與測試骨架。
- 已開發一段時間的專案，需要補救整理，不想推倒重來。
- 要把專案交給公司內部 GPT、Codex、外包、新人或其他維運人員。
- 常常發生「修 A 壞 B」、「一直問同樣資料」、「不知道現在版本能不能發」。
- 需要建立可去敏化的 debug 資料收集方式。

## 不適用情境

- 只想一次產出完整系統，且不想補文件、測試、交接資料。
- 沒有任何程式碼或需求，只想靠 AI 猜完整規格。
- 要處理高風險正式環境異動，但沒有備份、rollback、測試環境或人工核准。

## 內容

```text
templates/
  AGENTS.md
  HANDOFF_INDEX.md
  Memory.md
  docs/
    ai_handoff.md
    ai_readonly_api_contract.md
    ai_takeover_prompt.md
    ai_truth_and_evidence.md
    api_capabilities.md
    baseline_metrics.md
    change_impact_matrix.md
    change_size_policy.md
    current_state_snapshot.md
    data_dictionary.md
    data_quality_rules.md
    debug_intake.md
    definition_of_ready_done.md
    effort_estimation.md
    handoff_checklist.md
    migration_rollback.md
    project_overview.md
    regression_catalog.md
    release_checklist.md
    risk_register.md
    runbook.md
    security_data_handling.md
    system_capability_map.md
    test_plan.md
    ui_workflow_principles.md
    workflow_state.md
    adr/
      0001-template.md
skills/
  project-foundation/
  coding-guardrails/
  debug-release-loop/
  project-rescue-audit/
  agent-triad-review/
scripts/
  bootstrap_project_baseline.py
  validate_baseline.py
  project_audit.py
  project_health_score.py
  effort_estimator.py
  diagnostics_safe.ps1
  diagnostics_safe.sh
  install_skills.ps1
examples/
  project_inventory.csv
  agent_run_report.md
```

## 最快使用方式

把模板套到既有專案：

```powershell
cd project-baseline-kit_v2026-07-02
python scripts/bootstrap_project_baseline.py --target "D:\path\to\project"
python scripts/validate_baseline.py --target "D:\path\to\project"
```

做一次安全盤點：

```powershell
python scripts/project_audit.py --target "D:\path\to\project" --output audit.json
python scripts/project_health_score.py --target "D:\path\to\project" --output health_score.json
```

評估一個需求大概多難：

```powershell
python scripts/effort_estimator.py --code-size 2 --data-complexity 3 --test-gap 3 --deploy-risk 2 --security-risk 2 --ui-flow-risk 2
```

安裝 Codex skills：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_skills.ps1
```

若要同時安裝 WBS、簡報、安全掃描、UI 治理、DB / AD / Email 等附屬包 skills：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_skills.ps1 -IncludeAddons
```

安裝後可以這樣要求 Codex：

```text
Use project-foundation to prepare this new project before writing code.
Use project-rescue-audit to stabilize this existing project without rewriting it.
Use debug-release-loop when fixing a bug and preparing a patch.
Use agent-triad-review to run Code/Test/Review role checks.
```

## 建議導入順序

1. 先跑 `bootstrap_project_baseline.py`，把文件模板放進專案。
2. 填 `docs/project_overview.md`、`docs/data_dictionary.md`、`docs/workflow_state.md`。
3. 補 `docs/security_data_handling.md`，先定義哪些資料不可外流。
4. 補 `docs/test_plan.md` 與最小 smoke test。
5. 補 `docs/ai_truth_and_evidence.md`，要求 AI 不確定就收證據。
6. 補 `HANDOFF_INDEX.md` 與 `docs/current_state_snapshot.md`，讓接手者知道從哪裡看。
7. 每次改版後更新 `Memory.md`、`docs/regression_catalog.md`、`docs/release_checklist.md`。

## 交接給公司 GPT / Codex 的方式

交接時請先給接手者這幾份文件：

1. `HANDOFF_INDEX.md`
2. `Memory.md`
3. `docs/current_state_snapshot.md`
4. `docs/ai_takeover_prompt.md`
5. `docs/project_overview.md`
6. `docs/data_dictionary.md`
7. `docs/workflow_state.md`
8. `docs/runbook.md`
9. `docs/test_plan.md`
10. `docs/security_data_handling.md`

原則很簡單：接手者先讀文件，再看程式，再提計畫。不要一接手就改 code。

## 注意事項

- 不要把真實密碼、token、private key、cookie、session、憑證放進文件或 debug bundle。
- 公司內部資料也要分級。能用摘要、數量、hash、遮罩樣本，就不要貼完整清單。
- 外部 AI 一律使用去敏化資料。
- AI 可以提出合理假設，但必須標示為假設，不能當成事實。
- 公司環境、部署狀態、資料筆數、版本、錯誤原因，要以程式、log、API、測試或使用者提供的診斷輸出為準。
- 高風險異動前要先有備份、rollback、測試方式與人工核准。
- 小修可以快速驗證；中修、大修要補測試與文件。
- 不要讓多個 agent 同時修改同一批檔案。可以多 agent 審查，但只讓一個 agent 實作。

## Definition Of Done

一個需求要算完成，至少要有：

- 需求與影響範圍清楚。
- 相關文件或狀態規則已更新。
- 有測試或可重現的驗證證據。
- 若不能測試，已說明原因與替代驗證。
- 沒有新增敏感資料外洩風險。
- 有 release note 或交接紀錄。

## 成效怎麼量

導入前後請記錄：

- 從需求到可開始 coding 的時間。
- Debug 來回次數。
- 修 A 壞 B 的次數。
- 每次 release 需要多久。
- 交接給另一位工程師或 GPT 需要補問幾次。
- 測試、文件、rollback 是否齊全。

可以用 `docs/baseline_metrics.md` 記錄，也可以用 `scripts/project_health_score.py` 做初步評分。
