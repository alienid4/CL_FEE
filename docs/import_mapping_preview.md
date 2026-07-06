# Import Mapping Preview Draft

This draft is read-only. It previews how staged `import_rows.raw_json` fields may map into formal tables before any confirmed import flow exists.

| source_field | target_table | target_field | confidence | mode | requires_confirmation | notes |
| --- | --- | --- | --- | --- | --- | --- |
| case_code | cases | case_code | 0.86 | exact | false | Case identifier from staged source row. |
| title | cases | title | 0.78 | exact | false | Case title or short description. |
| owner | cases | owner | 0.72 | exact | false | Business owner or responsible team. |
| amount | cases | amount | 0.62 | manual-confirm | true | Money fields must be confirmed before any formal import. |
| contract_code | contracts | contract_code | 0.84 | exact | false | Contract identifier from source row. |
| contract_name | contracts | contract_name | 0.80 | exact | false | Contract display name. |
| vendor_name | contracts | vendor_name | 0.74 | exact | false | Vendor or supplier name. |
| contract_amount | contracts | amount | 0.68 | manual-confirm | true | Contract amount requires confirmation. |
| case_id | contracts | case_id | 0.58 | manual-confirm | true | Relationship fields must be confirmed against existing cases. |
| contract_id | payments | contract_id | 0.58 | manual-confirm | true | Relationship fields must be confirmed against existing contracts. |
| payment_month | payments | payment_month | 0.70 | manual-confirm | true | Payment month requires confirmation. |
| payment_amount | payments | payment_amount | 0.70 | manual-confirm | true | Payment amount requires confirmation. |
| file_name | documents | file_name | 0.66 | manual-confirm | true | Document and PDF fields require confirmation. |
| document_type | documents | document_type | 0.60 | manual-confirm | true | Document category requires confirmation. |

Preview API:

```http
GET /api/import-batches/{batch_id}/mapping-preview
```

The response returns one preview item per staged row:

- `candidates`: mapped source fields with `target_table`, `target_field`, `source_field`, `value`, and `requires_confirmation`.
- `unmapped_fields`: source fields that have no current mapping and must remain visible for review.
- `warnings`: row-level validation hints with `code`, `severity`, `message`, `source_field`, `target_table`, `target_field`, and `row_number`.

The response `summary` includes:

- `candidate_count`: total mapped candidates across staged rows.
- `unmapped_field_count`: total source fields without a mapping.
- `requires_confirmation_count`: mapped candidates that must be confirmed before formal import.
- `warning_count`: row warnings with `severity=warning`.
- `error_count`: row warnings with `severity=error`.
- `warning_by_code`: counts by warning code.

Current warning codes:

- `missing_required`: a staged row maps to a target table but lacks a required target field.
- `invalid_amount`: an amount-like field is non-numeric, zero, or negative.
- `invalid_month`: `payments.payment_month` is not valid `YYYY-MM`; `YYYYMM` is accepted only as a warning-level hint when the month is valid.
- `duplicate_in_batch`: `cases.case_code` or `contracts.contract_code` duplicates another staged row in the same batch.

The endpoint does not insert, update, or delete `cases`, `contracts`, `payments`, or `documents`.

Mapping draft catalog API:

```http
GET /api/import-mapping-draft
```

The response is read-only and returns the current mapping draft rules:

- `field_count`: number of configured source-field mappings.
- `requires_confirmation_count`: number of mappings that must be confirmed before formal import.
- `target_tables`: mapping counts grouped by target table.
- `fields`: source field rules with target table/field, confidence, mode, confirmation flag, notes, and aliases.

This endpoint is intended for UI review and handoff documentation. It does not create import batches, stage rows, insert domain records, or write audit logs.
