# Import Confirm Write MVP Design

Status: Architect design only. Do not implement formal writes from this document without a separate Coder + Tester + Reviewer slice.

## Scope

The MVP import-confirm path must stay conservative:

- First implement dry-run only.
- First target table is `cases` only.
- Do not write `contracts`, `payments`, or `documents` in the first Coder slice.
- Do not change DB schema in the design slice.
- Do not use `archive/old_api_local_web_20260704-135900` as source code.

## Data Flow

1. User creates an import batch in `import_batches`.
2. User stages source rows in `import_rows`.
3. Server recomputes `mapping-preview`.
4. User reviews warnings, unmapped fields, and mapping candidates.
5. User submits a confirm request.
6. Server reruns mapping preview and validation; it must not trust a frontend plan.
7. In dry-run mode, server returns a create plan without writing domain tables.
8. Later formal confirm writes in one transaction only after gates are stable.

## MVP Target Tables

Phase 1:

- `cases` only.

Later phases:

- `contracts`, after `case_id` relationship handling is explicit.
- `payments`, after `contract_id`, amount, month, and invoice rules are stable.
- `documents`, after file/source evidence handling is designed.

## Required Gates Before Any Formal Write

- `summary.error_count == 0`.
- Every `requires_confirmation=true` candidate must be explicitly confirmed in the request.
- Required fields must be present.
- Batch duplicates must block writing unless a future merge/update policy exists.
- Relationship ids must exist before writing relationship tables.
- AI must not auto-fix amount, status, date, or approval state into formal records.

## Rollback And Failure Strategy

MVP does not implement delete rollback.

Formal confirm, when added later, should be a single transaction:

- All selected rows succeed, or none are written.
- Partial success is not allowed in MVP.
- Batch rollback and batch disable are later high-risk slices.

## Audit And Source Chain

Without schema changes, the MVP should use `audit_logs` for source evidence when formal write is eventually enabled.

Suggested `after_json` shape:

```json
{
  "record": {"id": 1, "case_code": "CASE-001"},
  "source": {
    "batch_id": 1,
    "import_row_id": 10,
    "row_number": 2,
    "source_fields": {"case_code": "CASE-001"},
    "mapping_version": "draft-v1"
  }
}
```

Adding permanent source columns such as `import_batch_id`, `import_row_id`, or `source_hash` to domain tables is a later schema migration and must go through a high-risk review slice.

## API Draft

```http
POST /api/import-batches/{batch_id}/confirm
```

Request:

```json
{
  "dry_run": true,
  "target_tables": ["cases"],
  "confirmed_fields": [
    {"row_number": 1, "target_table": "cases", "target_field": "amount"}
  ],
  "accepted_warning_codes": []
}
```

Initial behavior:

- `dry_run=true` is required.
- `target_tables` must be exactly `["cases"]`.
- The server returns a plan and does not write `cases`, `contracts`, `payments`, or `documents`.
- The server reruns preview and validation for the current batch.

Suggested errors:

- `404`: batch not found.
- `400`: unsupported target table or dry_run is false.
- `409`: duplicate or stale conflict.
- `422`: validation gate failed.

## Test Checklist

- Dry-run does not change dashboard domain counts.
- Dry-run does not create domain audit entries.
- Rows with error warnings return 422.
- Missing confirmation for `requires_confirmation` fields returns 422.
- Duplicate `case_code` returns 409 or 422.
- Cases-only dry-run returns a deterministic create plan.
- Unsupported tables return 400.
- Future formal confirm must be transaction-only and disallow partial success.

## Still Forbidden

- Do not connect to formal DB.
- Do not touch formal data.
- Do not write AI-derived amount, date, status, or approval result into formal records.
- Do not copy source code from archive.
- Do not implement batch delete rollback in the MVP.
- Do not write `payments` or `documents` in the first import-confirm implementation.

## Next Coder Slice

Implement cases-only dry-run confirm API:

- Add `POST /api/import-batches/{batch_id}/confirm`.
- Require `dry_run=true`.
- Require `target_tables=["cases"]`.
- Return a create plan only.
- Add API tests for read-only behavior, error gate, requires-confirmation gate, and unsupported target tables.
