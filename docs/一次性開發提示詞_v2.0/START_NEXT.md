# START_NEXT

## 2026-07-05 23:08 Asia/Taipei - Next Slice

Next recommended slice: formal confirm preflight hardening tests.

Mode: Coder + Tester. Formal writes remain forbidden.

Read first:

1. `CURRENT_STATUS.md`
2. `docs/import_confirm_write_mvp_design.md`
3. `docs/import_confirm_reviewer_security_checklist.md`
4. `app/main.py`
5. `app/store.py`
6. `app/import_mapping.py`
7. `tests/test_fresh_app.py`

Allowed work:

- Add or strengthen tests proving `dry_run=false` remains blocked.
- Add tests for existing `cases.case_code` conflict in dry-run confirm.
- Add tests proving `accepted_warning_codes` does not bypass errors or confirmation gates.
- Add tests documenting replay/idempotency policy as blocked for MVP.
- Add read-only preflight helpers only if they do not write domain tables or audit domain create records.

Forbidden:

- Do not insert cases from import confirm.
- Do not add a formal confirm UI button.
- Do not write contracts, payments, or documents.
- Do not change schema without a separate high-risk approval slice.
- Do not use archive code.

Required validation:

```powershell
pytest -q
pytest tests -q
powershell -ExecutionPolicy Bypass -File scripts\local_ci.ps1
powershell -ExecutionPolicy Bypass -File scripts\check_audit_gate.ps1 -RequireLog
```

本檔定義下一輪開發指令，必須保持短小明確。

## 請先讀

1. `CURRENT_STATUS.md`
2. 本檔
3. 當前切片相關程式碼與測試

## 本輪目標

下一輪建議：formal confirm 前的 Reviewer/Security 設計切片。

目前 v2.1 本機自動開發控制台 MVP 已新增；下一輪回到產品 backlog。
v2.1 已改為 All-in-One Build Pack；新系統從 0 到 MVP 時先讀 `ALL_IN_ONE_BUILD_PACK.md`。

建議先跑：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\local_ci.ps1
pytest tests -q
```

此切片是 formal import confirm 前的高風險設計 review，速度檔至少是 Release Lane。只做 Reviewer/Security 設計，不直接寫正式資料。

若暫時不做 Reviewer/Security 設計，下一個安全切片是：audit/source-chain display，先顯示既有暫存來源資訊，不寫正式表。

## 不可碰

- 不刪除 archive。
- 不搬移 archive。
- 不從 archive 複製主程式。
- 不做無關重構。
- 不碰正式部署 credential。
- 不推送遠端 repository，除非使用者明確要求。

## 預期做法

審查 `docs/import_confirm_write_mvp_design.md` 與現有 dry-run API，產出 formal confirm 前的 Reviewer/Security checklist。
要求：

- 明確列出正式寫入前仍缺哪些 gate。
- 明確列出 transaction、audit/source-chain、rollback/disable、duplicate/update policy。
- 明確列出哪些 endpoint/UI 仍不得出現正式 confirm。
- 不改 DB schema、不寫正式表。

## 驗證

完成後必須跑：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\local_ci.ps1
pytest -q
pytest tests -q
powershell -ExecutionPolicy Bypass -File scripts\check_prompt_pack.ps1
```

## 完成回報

- 本次完成項目
- 速度檔
- 跟上次差異
- 變更檔案
- 驗證命令與結果
- 是否需要重啟 FastAPI
- 下一個建議切片
