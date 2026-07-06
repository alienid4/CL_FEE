# Import Confirm Transaction Design

Status: design gate only. This document does not approve or implement formal writes.

## Scope

The first formal import-confirm implementation, when approved in a later high-risk slice, must be limited to:

- `cases` only.
- create-only.
- one import batch per request.
- one database transaction for the whole batch.
- no partial success.
- no updates, merges, disables, deletes, or relationship-table writes.
- no `contracts`, `payments`, or `documents` writes.
- no formal DB, MSSQL, AD, SSO, or production credential integration.

Current product behavior remains unchanged:

- `/api/import-batches/{batch_id}/confirm` supports `dry_run=true` only.
- `/api/import-batches/{batch_id}/confirm-preflight` is read-only.
- `accepted_warning_policy.status` is `disabled`.

## Proposed Request Contract

The future formal request may reuse the existing endpoint only after all gates below pass:

```json
{
  "dry_run": false,
  "target_tables": ["cases"],
  "confirmed_fields": [
    {"row_number": 1, "target_table": "cases", "target_field": "amount"}
  ],
  "accepted_warning_codes": [],
  "actor": "local-dev",
  "preview_token": "server-generated-preview-token"
}
```

`dry_run=false` must continue to return an error until the implementation slice adds the full transaction path and tests.

## Transaction Flow

The formal write path must run inside one explicit transaction:

1. Open database connection.
2. Begin transaction.
3. Load the import batch.
4. Load staged rows ordered by `row_number`, `id`.
5. Recompute mapping preview on the server.
6. Validate preview freshness with `preview_token` or a future row hash.
7. Validate `target_tables == ["cases"]`.
8. Validate `accepted_warning_policy.status == "disabled"` unless a separate allowlist design has passed.
9. Validate `summary.error_count == 0`.
10. Validate no duplicate `cases.case_code` inside the batch.
11. Requery existing `cases.case_code` inside the transaction and block conflicts.
12. Validate every `requires_confirmation=true` cases candidate is explicitly confirmed.
13. Build case records from source values only.
14. Insert every case row.
15. Insert one source-chain audit row per created case.
16. Optionally update the import batch status to `confirmed` only after all inserts and audits succeed.
17. Commit transaction.

Any exception before commit must roll back case inserts, audit rows, and batch-status changes.

## Source-Chain Audit Contract

Formal import audit must use an import-specific action such as `import_confirm_create`, not the generic UI `create` action.

The implementation must choose one explicit audit storage strategy before any write code is enabled:

- Store complete source-chain evidence in `audit_logs.after_json` for the MVP.
- Add dedicated audit columns or a dedicated import-confirm audit table in a separate schema-migration slice.

MVP recommendation: use `audit_logs.after_json` first, because it avoids a schema migration. This is acceptable only if tests can query the audit payload and recover the source batch, import row, row number, mapping version, target fields, and actor.

Minimum `after_json` shape:

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
    "preview_token": "server-generated-preview-token"
  },
  "confirm": {
    "confirmed_fields": [],
    "accepted_warning_codes": [],
    "accepted_warning_policy": "disabled",
    "server_preview_rerun": true,
    "actor": "local-dev"
  }
}
```

Audit logs must not contain secrets, credentials, cookies, session data, or entire uploaded source files.

## Freshness Strategy

The formal implementation needs one of these before writes are enabled:

- `preview_token`: server-generated digest over batch id, row ids, row numbers, raw JSON, mapping version, and warning summary.
- row hash: persisted hash per staged row.
- batch lock: status transition preventing row changes after preview.

MVP recommendation: implement `preview_token` first because it does not require a schema migration. A later schema migration can persist hashes or lock state if needed.

## Idempotency And Replay

MVP policy is block replay:

- If any planned `case_code` already exists, return conflict.
- Re-submitting the same batch after success must create no additional cases.
- Replaying with the same `preview_token` must fail once domain rows exist.
- No update or merge behavior is allowed in MVP.

The later implementation must define an idempotency key before enabling writes. Suggested key inputs:

- `batch_id`
- `mapping_version`
- `target_tables`
- ordered import row ids and raw-row fingerprints
- actor
- action nonce or server-issued `preview_token`

The implementation must not rely only on SQLite `UNIQUE(cases.case_code)`. The transaction should gate conflicts before insert, while the unique constraint remains the final defense.

## Accepted Warning Policy

Current policy remains disabled:

- `accepted_warning_codes` cannot bypass `preview_errors`.
- It cannot bypass duplicate checks.
- It cannot bypass existing-case conflicts.
- It cannot bypass required confirmations.
- It cannot bypass source-chain or stale-preview gates.

Any future allowlist requires a separate high-risk design for severity limits, actor permission, audit evidence, rollback, and UI wording.

## Actor And Authorization

MVP local actor may remain `local-dev` only for local development.

Formal write implementation must make actor explicit in the request or server context and record it in audit logs. Production authorization, AD, SSO, or role mapping is out of scope until a separate high-risk auth slice.

## Response Contract

On success, future formal confirm should return:

```json
{
  "dry_run": false,
  "target_tables": ["cases"],
  "created": {
    "cases": [
      {"id": 1, "case_code": "CASE-001", "source_row_id": 10}
    ]
  },
  "summary": {
    "created_count": 1,
    "skipped_count": 0,
    "audit_log_count": 1,
    "server_preview_rerun": true
  },
  "audit_log_ids": [100],
  "accepted_warning_policy": {
    "status": "disabled",
    "allowed_warning_codes": []
  }
}
```

Partial success is not allowed. `skipped_count` must be zero for the MVP.

## Required Tests Before Implementation Approval

- `dry_run=false` remains blocked until the formal slice intentionally changes it.
- Unsupported target tables return `400`.
- Preview errors block formal confirm.
- Missing explicit confirmations block formal confirm.
- Duplicate `case_code` inside staged rows blocks formal confirm.
- Existing domain `case_code` blocks formal confirm inside the transaction.
- Replaying a successful batch creates no extra cases.
- Success creates all planned cases and matching `import_confirm_create` audit rows.
- Forced mid-transaction failure rolls back all cases, audit logs, and batch status.
- Stale preview token blocks formal confirm.
- `accepted_warning_codes` cannot bypass disabled policy.
- Actor is recorded and unsupported actor policy is explicit.
- UI exposes no formal confirm button until all API gates pass.
- Case insert failure rolls back import audit rows.
- Audit insert failure rolls back created cases.
- Audit query can recover batch id, import row id, row number, mapping version, source fields, target fields, and actor for each created case.
- Mapping-version mismatch blocks formal confirm.
- Missing source-chain evidence blocks formal confirm.

## Release Gates Before Any Formal Write

- Architect gate: transaction boundary, rollback behavior, stale-preview strategy, idempotency key, audit storage strategy, and target-table scope are approved.
- Reviewer/Security gate: actor/authorization, accepted-warning policy, source-chain audit, and no-production-data boundaries are approved.
- Tester gate: automated success, rollback, replay, stale-preview, authorization, and UI no-formal-button tests are green.
- Runtime gate: `pytest -q`, `pytest tests -q`, UI import regression, local CI, runtime freshness, and audit gate are green on a fresh runtime.
- Product gate: UI still does not expose a formal confirm button until the API gates are complete.

## Still Forbidden

- Do not enable `dry_run=false` in this design slice.
- Do not add a formal confirm UI button.
- Do not write domain rows from import confirm.
- Do not modify DB schema.
- Do not write contracts, payments, or documents.
- Do not connect to formal DB, MSSQL, AD, SSO, or production systems.
- Do not use `archive/old_api_local_web_20260704-135900` as source code.

## Next Safe Slice

Recommended next slice: transaction readiness tests that still keep `dry_run=false` blocked, plus a preview-token design test or helper if it can remain read-only.
