# Import Confirm Reviewer/Security Checklist

Status: Reviewer/Security design gate. This document does not authorize formal writes.

## Scope

This checklist controls the transition from the existing cases-only dry-run import confirm path to any future formal write path.

Current allowed behavior:

- `POST /api/import-batches/{batch_id}/confirm` supports `dry_run=true` only.
- `target_tables` must be exactly `["cases"]`.
- The endpoint returns a plan and must not write `cases`, `contracts`, `payments`, `documents`, or case create audit logs.

Still forbidden:

- Do not connect to formal DB.
- Do not write formal data.
- Do not change DB schema in this checklist slice.
- Do not use `archive/old_api_local_web_20260704-135900` as source code.
- Do not add a formal confirm button or formal write endpoint until every blocking gate below has automated evidence.

## Reviewer Decision

Formal write is not approved yet.

Reason: the dry-run path is correctly read-only, but the formal write safety shell is incomplete. The next safe slice is `formal confirm preflight hardening`, not formal data insertion.

## Blocking Gates Before Formal Write

| Gate | Minimum requirement | Current status |
| --- | --- | --- |
| Transaction gate | Re-read batch and rows, recompute preview, validate, insert case rows, and write audit logs inside one explicit transaction. Any failure rolls back all rows and audit logs. | Blocked: no formal transaction path exists. |
| Source-chain gate | Every formal write audit entry must include `batch_id`, `import_row_id`, `row_number`, source fields, target fields, and mapping/plan version. | Blocked: dry-run plan has source row id, but no formal audit source-chain write exists. |
| Duplicate gate | Block duplicate `cases.case_code` inside the batch and block existing domain `case_code` again inside the formal transaction. | Partially ready in dry-run; missing formal transaction recheck evidence. |
| Create-only gate | MVP formal import must create cases only. Existing `case_code` must return conflict; no update, merge, disable, or overwrite. | Policy documented here; not implemented as formal write behavior. |
| Confirmation gate | Every `requires_confirmation=true` cases candidate must be explicitly confirmed by the user. Formal UI must not auto-confirm fields from preview. | Dry-run validates confirmations; formal UI policy still missing. |
| Warning policy gate | `accepted_warning_codes` must have a documented allowlist or remain unsupported. Error warnings must always block. | Blocked: schema exists, policy not defined. |
| Stale preview gate | Confirm request must detect batch/row changes after user preview, using a plan version, source hash, or batch lock. | Blocked: no preview version/hash/lock exists. |
| Rollback evidence gate | Tests must prove mid-write failure leaves no partial `cases` rows and no partial audit logs. | Blocked: no formal write tests exist. |
| AI-derived value gate | AI must not auto-fix or infer amount, date, status, approval, or relationship fields into formal records. Only confirmed source values may be written. | Policy documented here; requires formal tests before approval. |
| Actor/authorization gate | Formal writes require an explicit actor and role/permission policy. `local-dev` is acceptable only for local testing and must not imply production authorization. | Blocked: current audit actor defaults to `local-dev`; no role gate exists. |
| Idempotency/replay gate | Re-submitting the same batch must not create duplicate cases. MVP policy is block replay and block existing `case_code`. | Blocked: existing conflict is tested in dry-run logic only; no formal replay evidence exists. |
| UI release gate | No formal confirm UI control may be exposed until transaction, duplicate, source-chain, rollback, stale, and human-confirm tests pass. | Currently safe: UI has dry-run only. |

## Required Formal Write Contract

The first formal implementation, when approved later, must be limited to:

- `cases` only.
- create-only.
- one import batch at a time.
- one transaction for the entire selected batch.
- no partial success.
- no update or merge.
- no relationship table writes.
- no DB schema migration.

The response should include:

- created case ids.
- skipped count, expected to be zero for MVP.
- source-chain summary.
- audit log ids.
- validation summary matching the server recomputed preview.
- idempotency/replay result.

## Audit Source-Chain Minimum

For each created case, the formal write audit entry should use `table_name="cases"` and `action="import_confirm_create"` or another explicit import action, not a generic UI create action.

The `after_json` payload must include:

```json
{
  "record": {
    "id": 1,
    "case_code": "CASE-001"
  },
  "source": {
    "batch_id": 1,
    "import_row_id": 10,
    "row_number": 2,
    "source_fields": {
      "case_code": "CASE-001",
      "title": "Example",
      "amount": "12000"
    },
    "target_fields": {
      "case_code": "CASE-001",
      "title": "Example",
      "amount": "12000"
    },
    "mapping_version": "draft-v1",
    "plan_version": "server-generated"
  },
  "confirm": {
    "confirmed_fields": [],
    "accepted_warning_codes": [],
    "server_preview_rerun": true,
    "actor": "local-dev"
  }
}
```

Do not write secrets, formal credentials, cookies, session data, private personal data, or complete source files into audit logs.

## Required Tests Before Formal Write Approval

- `dry_run=false` remains blocked until the formal slice intentionally changes it.
- Unsupported target tables still return `400`.
- Missing required fields return `422`.
- Missing explicit confirmation returns `422`.
- Preview error warnings return `422`.
- Duplicate `case_code` in the staged batch returns conflict or validation error.
- Existing `cases.case_code` returns conflict.
- Replaying the same batch returns conflict and creates no additional case or audit log.
- Formal write transaction success creates all expected cases and matching source-chain audit logs.
- Forced mid-transaction failure rolls back every created case and every audit log.
- Stale preview or changed staged rows block confirm.
- `accepted_warning_codes` is rejected or ignored by explicit policy until an allowlist exists.
- Actor/authorization gate blocks unsupported actors or records a local-only actor policy.
- Formal UI cannot auto-confirm `requires_confirmation` fields.
- Formal UI is absent or disabled until the API gates pass.

Minimum command set for the first formal write Coder slice:

```powershell
pytest -q
pytest tests -q
powershell -ExecutionPolicy Bypass -File scripts\test_ui_import_preview.ps1
powershell -ExecutionPolicy Bypass -File scripts\test_ui_documents.ps1
powershell -ExecutionPolicy Bypass -File scripts\local_ci.ps1
powershell -ExecutionPolicy Bypass -File scripts\check_audit_gate.ps1 -RequireLog
```

## Security Review Notes

- Formal DB, AD, MSSQL, production credentials, and real production data remain out of scope.
- Any future MSSQL adapter must go through a separate high-risk Architect + Coder + Tester + Reviewer slice.
- Security reports must separate white-box checks from black-box checks.
- Intrusive scans are not allowed against production without explicit approval.

## Next Safe Slice

Recommended next Coder slice: `formal confirm preflight hardening`.

Allowed work:

- Add tests proving formal confirm remains blocked.
- Add a non-writing preflight/check endpoint only if it improves evidence and remains read-only.
- Define `accepted_warning_codes` policy as rejected/unsupported for MVP.
- Add plan/version/hash design or tests without enabling formal writes.

Not allowed in the next slice:

- Do not insert cases from import confirm.
- Do not add a formal confirm UI button.
- Do not write contracts, payments, or documents.
- Do not change schema unless separately approved.
