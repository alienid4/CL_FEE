# Import Confirm Accepted Warning Policy

Status: disabled.

This policy is intentionally read-only and conservative. It documents what the current product exposes in preflight responses before any formal import-confirm write path exists.

## Current Contract

- `accepted_warning_codes` is accepted by the API as input for future compatibility.
- It does not enable formal writes.
- It does not bypass errors, duplicate checks, existing-case conflicts, required confirmations, source-chain requirements, or stale-preview guards.
- The preflight response must return `accepted_warning_policy.status = "disabled"`.
- The preflight response must return an empty `allowed_warning_codes` list.

## Non-Bypassable Gates

- `preview_errors`
- `duplicate_in_batch`
- `existing_case_code`
- `requires_confirmation`
- `source_chain_contract`
- `stale_preview_guard`

## Next Design Requirement

Before any warning can become allowlisted, a separate high-risk design slice must define actor authorization, warning severity limits, audit evidence, stale-preview protection, and rollback behavior.
