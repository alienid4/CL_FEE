# CURRENT_STATUS

## 2026-07-05 23:23 Asia/Taipei - Slice Started

- Current action: started formal confirm preflight hardening tests.
- Difference from last report: moving from Reviewer/Security checklist to executable test hardening; dry-run API/UI remains unchanged; no regression known; blocker unchanged: formal write remains intentionally forbidden.
- Agent mode: Coder is main Codex direct work; independent Tester will be launched after the test patch.
- Scope: tests only unless a small production-code clarification is required by failing tests. No formal import write, no DB schema change, no archive reuse.
- Planned output: strengthen `tests/test_fresh_app.py` for existing `case_code` conflict, `accepted_warning_codes` non-bypass, replay/idempotency blocked, and `dry_run=false` still blocked.
- Tests planned: `pytest -q`, `pytest tests -q`, `powershell -ExecutionPolicy Bypass -File scripts\local_ci.ps1`, audit log/gate.
- Overall project completion: about 63% unchanged until this slice is completed and verified.

## 2026-07-05 23:35 Asia/Taipei - Slice Completed

- Current action: completed formal confirm preflight hardening tests.
- Difference from last report: added executable regression coverage in `tests/test_fresh_app.py`; dry-run API/UI remains unchanged; no regression; no new blocker. Test count increased from 21 to 23.
- Agent mode: Coder was main Codex direct work; Tester was independent Agent `019f32c6-5930-7403-80d3-17d30d61f51a`.
- Completed output:
  - `accepted_warning_codes` cannot bypass preview error gate.
  - `accepted_warning_codes` cannot bypass `requires_confirmation`.
  - existing `cases.case_code`/replay remains blocked and does not create imported cases.
  - `dry_run=false` remains blocked.
- Test result:
  - `python -m pytest tests/test_fresh_app.py -q`: 23 passed, 1 warning.
  - `python -m pytest -q`: 23 passed, 1 warning.
  - `python -m pytest tests -q`: 23 passed, 1 warning.
  - `powershell -ExecutionPolicy Bypass -File scripts\local_ci.ps1`: PASS.
  - `powershell -ExecutionPolicy Bypass -File scripts\check_prompt_pack.ps1`: PASS.
- Blocker: formal write remains intentionally blocked. `accepted_warning_codes` is currently conservative/no-op; any real allowlist needs a separate high-risk slice.
- Restart needed: no. Tests/status only; no app runtime change.
- KPI: formal-write safety 100%; preflight regression coverage improved; pytest/local CI 100%; archive exclusion 100%.
- Overall project completion: about 64%.
- Next step: audit/source-chain display or preflight endpoint design; still no formal writes.

## 2026-07-05 22:53 Asia/Taipei - Slice Started

- Current action: formal confirm pre-write Reviewer/Security design slice started.
- Difference from last report: new work started; dry-run UI/API remains unchanged; no regression known; no new blocker. Independent agents started for architecture and security review.
- Agent mode: independent agents, not role simulation.
  - Architect Agent: `019f32ae-f077-7310-99f5-6a4ef234b399`
  - Reviewer/Security Agent: `019f32af-9169-77c1-9b95-33eb85324d73`
- Scope: design/checklist only. No formal import write, no DB schema change, no archive reuse.
- Expected output: `docs/import_confirm_reviewer_security_checklist.md`.
- Tests planned after doc slice: `pytest -q`, `pytest tests -q`, `powershell -ExecutionPolicy Bypass -File scripts\check_prompt_pack.ps1`, and local CI if needed.
- Overall project completion: about 62% unchanged until this slice is completed and verified.

## 2026-07-05 23:08 Asia/Taipei - Slice Completed

- Current action: completed formal confirm pre-write Reviewer/Security checklist.
- Difference from last report: added `docs/import_confirm_reviewer_security_checklist.md`; Architect and Reviewer/Security independently agreed formal write is not approved yet. Existing dry-run UI/API is unchanged; no regression; no new blocker.
- Agent mode: independent agents, not role simulation.
  - Architect Agent: `019f32ae-f077-7310-99f5-6a4ef234b399` completed.
  - Reviewer/Security Agent: `019f32af-9169-77c1-9b95-33eb85324d73` completed.
- Completed output: formal write blocking gates for transaction, source-chain, duplicate/update, rollback, stale preview, accepted warning policy, actor/authorization, idempotency/replay, and UI release.
- Test result:
  - `python -m pytest -q`: 21 passed, 1 warning.
  - `python -m pytest tests -q`: 21 passed, 1 warning.
  - `powershell -ExecutionPolicy Bypass -File scripts\check_prompt_pack.ps1`: PASS.
  - `powershell -ExecutionPolicy Bypass -File scripts\local_ci.ps1`: PASS.
  - `powershell -ExecutionPolicy Bypass -File scripts\check_audit_gate.ps1 -RequireLog`: PASS.
- Blocker: formal write remains intentionally blocked until preflight hardening tests/source-chain/stale/actor/idempotency gates exist.
- Restart needed: no. Documentation/status only.
- KPI: formal-write safety 100%; independent review coverage 100%; pytest/local CI/audit gate 100%.
- Overall project completion: about 63%.
- Next step: Coder + Tester slice for formal confirm preflight hardening tests, still no formal writes.

本檔是 AI_FEE v2.0 提示詞包的短版狀態檔。
日常接手請先讀本檔，再讀 `START_NEXT.md`。

## 目前完成度

最後更新時間：2026-07-05 22:31 Asia/Taipei

整體估計約 62%。

目前屬於可展示、可操作、可測的本機開發版，但還不是完整可上線 MVP。

本檔也是使用者觀察 Codex 是否仍在工作的固定 MD。若本檔的最後更新時間、目前切片、跟上次差異、測試結果或下一步有變化，代表本輪有實際推進。

## 最新可通過測試

目前完整基礎驗證可通過：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\local_ci.ps1
pytest -q
pytest tests -q
powershell -ExecutionPolicy Bypass -File scripts\test_ui_import_preview.ps1
powershell -ExecutionPolicy Bypass -File scripts\test_ui_documents.ps1
```

最新已知結果：

- `pytest -q`：21 passed, 1 warning
- `pytest tests -q`：21 passed, 1 warning
- `python -m compileall app tests`：passed
- live `GET /api/import-mapping-draft` on `127.0.0.1:8888`：200
- Import Preview UI regression：passed
- Documents UI regression：passed
- `scripts\fast_ci.ps1 -IncludePromptPack -IncludeAutomationFoundation`：PASS，16 passed, 1 warning，約 4 秒
- `scripts\fast_ci.ps1 -IncludeAuditGate -RequireAuditLog`：PASS，16 passed, 1 warning，約 4 秒
- `scripts\local_ci.ps1`：PASS，pytest -q / pytest tests -q 各 16 passed, 1 warning，security check PASS
- `scripts\agent_runtime_once.ps1 -Goal "Validate v2.0 automation hardening runtime" -Lane fast`：PASS，已完成 profile -> fast_ci -> audit log -> audit gate
- `.github\workflows\local-ci.yml`：新增平台 CI 範本，呼叫同一套 `scripts\local_ci.ps1`
- `scripts\deep_security_check.ps1`：baseline PASS；bandit、pip-audit、semgrep 未安裝，已正確回報 warning
- `GET /dev-console`：live 200，v2.1 本機自動開發控制台 MVP 可開啟
- `GET /api/dev-console/status`：live PASS，version=`v2.1-local-control-panel-mvp`，白名單命令 6 個
- targeted pytest：2 passed, 1 warning
- `scripts\fast_ci.ps1 -IncludePromptPack -IncludeAutomationFoundation`：PASS，21 passed, 1 warning
- `scripts\local_ci.ps1`：PASS，pytest -q / pytest tests -q 各 21 passed, 1 warning，security check PASS

## 當前風險

- pytest archive 污染已修正，`pytest -q` 目前只測主程式。
- `archive/` 是歷史參考，不能作為主程式來源。
- 第一版功能範圍很大，必須用小切片推進。
- 正式 MSSQL、正式 AD、正式部署與正式資料尚未確認，不可假裝完成。
- 一般 shell runner 曾出現 `-1073741205`，目前可用 Node child-process 備援驗證。
- 速度已分成 Fast / Standard / Release 三檔；若低風險小修仍跑完整重流程，會拖慢交付。
- 已加入 Autonomy Gate：低風險、可驗證問題由 Agent 自己判斷、自己修、自己驗；重大或高風險才問使用者。
- 已新增一鍵 runtime、project profile、deep security 入口；進階 SAST / DAST 仍取決於本機是否安裝 bandit、pip-audit、semgrep，且 DAST 預設只允許 localhost。
- v2.1 定位已改為 All-in-One Build Pack：不是主副工具拆裝，而是一包包含 CIO Build Mode、開發規則、本機控制台與 audit 糾察隊。

## 下一個建議切片

1. formal confirm 前的 Reviewer/Security 設計切片。
2. 或 audit/source-chain display，先顯示既有暫存來源資訊，不寫正式表。
3. 完成後驗證：

```powershell
pytest -q
pytest tests -q
powershell -ExecutionPolicy Bypass -File scripts\test_ui_import_preview.ps1
```

- 目前切片：Import Preview UI 顯示 cases-only dry-run plan 完成。
- 目前動作：已在 Import Preview UI 顯示 cases dry-run plan；UI 只呼叫 `dry_run=true` 與 `target_tables=["cases"]`，未新增正式寫入按鈕。
- 跟上次差異：新增 dry-run plan UI、Dry Run Cases 按鈕、plan result 顯示與 UI regression；既有 Mapping Draft、warnings filter、Documents UI 維持通過；無退步；無新增阻塞。
- 最近完成：`app/web/index.html`、`app/web/app.js`、`app/web/styles.css`、`tests/ui_import_preview_regression.py` 已更新。
- 阻塞原因：無。
- 下一步：formal confirm 前的 Reviewer/Security 設計切片；仍不直接寫正式資料。
- 是否需要重啟 FastAPI：已重啟 `127.0.0.1:8888` 載入 static UI，暫不需要再重啟。

## 本提示詞包狀態

- v2.0 已採用目錄型提示詞包。
- 已新增 `INDEX.md` 作為第一入口。
- 已新增 `OPERATING_LOOP.md` 定義固定改善 LOOP。
- 已新增 `GATE_CATALOG.md`，把 v1.5 到 v2.0 中可 Gate 化的要求整理成 Auto / Manual Gate。
- 已補 `MVP Scope Gate` 與 `Per-Loop Audit Gate` 的差異：v1.5 必做功能是第一版終點 gate，不是每輪小修 gate。
- 已新增資安三層文件：`SECURITY_RULES.md`、`SECURITY_SCAN_RULES.md`、`SECURITY_COMMANDS.md`。
- 已新增 `AGENT_AUDIT_RULES.md` 可複製稽核模板。
- 已新增 `UNIVERSAL_PROJECT_GUIDE.md`，讓本提示詞包可套用到其他專案。
- 已新增 `CHANGELOG.md`，記錄 v2.0 相對 v1.9 的改善。
- 已新增自動化腳本：
  - `scripts/local_ci.ps1`
  - `scripts/check_prompt_pack.ps1`
  - `scripts/check_automation_foundation.ps1`
  - `scripts/check_audit_gate.ps1`
  - `scripts/security_check.ps1`
  - `scripts/test_all.ps1`
  - `scripts/write_agent_audit_log.ps1`
  - `scripts/summarize_agent_audit_log.ps1`
- 已新增 `MVP_EVIDENCE_CHECKLIST.md`，作為第一版 MVP Scope Gate 的最終驗收證據表。
- 已新增 `scripts/summarize_agent_audit_log.ps1`，可把 JSONL audit log 彙整成 Markdown 報告。
- 已新增 `SPEED_RULES.md` 與 `scripts/fast_ci.ps1`，讓低風險小修可走 Fast Lane。
- 已新增 `AGENT_RUNTIME_RULES.md`、`PROJECT_PROFILE_RULES.md` 與 runtime / profile / deep security 腳本。
- 已新增 `.github/workflows/local-ci.yml`，未來上 GitHub 時可直接跑同一套本機 CI。
- v2.1 已新增本機自動開發控制台 MVP：`/dev-console`。

## Audit Gate 狀態

Audit 是使用者的糾察隊。
完成任何會修改工作區或狀態文件的 LOOP 前，必須：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\write_agent_audit_log.ps1 -Goal "..." -Classification small -Verification "..." -AuditResult "pass"
powershell -ExecutionPolicy Bypass -File scripts\check_audit_gate.ps1 -RequireLog
```

若 audit gate 未通過，本輪不得宣稱完成。

目前 audit gate 已包含 UI 內部註解規則：

- UI 主畫面不可直接顯示開發註解、Prompt、Agent 說明、TODO、debug、測試用、開發中等內部字樣。
- 必要說明需放入 tooltip、info icon、可點擊 help、預設收合 details 或 docs。

## 最近 LOOP 結果

已完成至少 5 個自動化基礎改善 LOOP：

1. 新增 `AUTO_DEV_LOOP.md`，定義自動開發每圈必問、狀態契約與禁止事項。
2. 新增 `write_agent_audit_log.ps1`，可寫入 JSONL audit log。
3. 新增 `check_automation_foundation.ps1`，檢查自動化文件與腳本完整性。
4. 將自動化腳本接回 `README.md`、`VERIFICATION_RULES.md`、`SECURITY_COMMANDS.md`、`START_NEXT.md`。
5. 完整驗證通過，並成功寫入 `logs/agent_loop_audit.jsonl` 測試紀錄。

最新驗證：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\fast_ci.ps1 -IncludePromptPack -IncludeAutomationFoundation
powershell -ExecutionPolicy Bypass -File scripts\fast_ci.ps1 -IncludeAuditGate -RequireAuditLog
powershell -ExecutionPolicy Bypass -File scripts\local_ci.ps1
powershell -ExecutionPolicy Bypass -File scripts\agent_runtime_once.ps1 -Goal "..." -Lane fast
powershell -ExecutionPolicy Bypass -File scripts\deep_security_check.ps1
```

結果：

- prompt pack check：PASS
- automation foundation check：PASS
- pytest -q：20 passed, 1 warning
- pytest tests -q：20 passed, 1 warning
- security_check：PASS without warnings
- audit gate：PASS
- one-key runtime：PASS
- deep_security_check：baseline PASS；optional tools missing warnings x3

## 仍有缺點

- 已新增 GitHub Actions workflow 範本，但尚未推上 GitHub 執行，不能宣稱雲端 CI 已實跑。
- `deep_security_check.ps1` 已提供 SAST / dependency / DAST 入口，但完整能力取決於 bandit、pip-audit、semgrep 等工具是否安裝。
- UI regression 需要 dev server 正在執行，尚未納入預設 `test_all`。
- audit summary 已可產生到 `logs/agent_loop_audit_summary.md`，但該報告位於 ignored logs 目錄，若要交付需另行輸出到 docs。

## 不可碰規則

- 不刪除 archive。
- 不搬移 archive。
- 不從 archive 複製主程式。
- 不碰正式資料、正式 DB、正式憑證。
- 不做不可逆 migration。
- 不把 AI 判斷直接寫入正式金額或正式狀態。
- 不做無關重構。

## 是否需要重啟 FastAPI

目前僅建立提示詞文件，不需要重啟 FastAPI。

若後續改 FastAPI route、schema、store 或 DB 初始化，需重新判斷是否重啟。

## archive 注意事項

`archive/old_api_local_web_20260704-135900` 只能作為歷史參考。

若 pytest 預設收集 archive 測試，應用 pytest 設定排除，不得刪除或搬移 archive。
