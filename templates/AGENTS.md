# AI Collaboration Rules

This project allows AI-assisted development, but the AI must work inside these
guardrails.

## Before Coding

- Read existing code, docs, config, and tests first.
- Identify the domain terms, data model, workflow, and status rules.
- State the smallest safe change.
- Do not rewrite architecture unless the request explicitly requires it.
- If the requirement is unreasonable or incomplete, do not simply agree. State the recommended option, pros and cons, then ask for confirmation only when needed.

## Coding Rules

- Keep changes scoped to the requested behavior.
- Put business rules in services or domain modules, not UI templates.
- Keep UI responsible for display and interaction only.
- Preserve existing user workflows unless the request asks to change them.
- Do not commit secrets, tokens, real credentials, private keys, or personal data.
- Do not upload sensitive production data to external tools.
- For company formal systems, default to Microsoft SQL Server when no database is specified.
- If an Add action exists, provide a matching Edit and Delete/Disable path unless explicitly out of scope.

## Debug Rules

- Do not guess when production or company data is involved.
- Provide a safe diagnostics command or script when more evidence is needed.
- Diagnostics must mask or hash sensitive values.
- Prefer JSON or text output stored under `/tmp` or a local temp directory.
- Separate facts, assumptions, and recommendations.
- If evidence is missing, say what is unknown and request or generate a safe evidence bundle.
- Never claim a root cause from screenshots alone when a safe diagnostic command can be provided.

## Testing Rules

- Run the narrowest useful test first.
- Add a regression test for every bug fixed.
- If tests cannot run, explain why and provide an alternate verification.
- Small fixes may use quick smoke verification. Data, auth, security, install, schema, release, or cross-module changes require broader verification.

## UI Rules

- Avoid excessive blank space in operational screens.
- Use tabs to separate subfunctions.
- Keep one primary function per page when practical.
- Tables must support sorting.
- Provide full-text search for searchable data.
- Metric cards with numbers must drill down to detail.
- Large tables should not open by default; show them after search, filter, metric-card click, or explicit "show all".

## Module Management Rules

- Every module must have an admin/settings surface.
- Every module must support enable/disable or a documented reason why it cannot.
- Module-specific settings belong under that module's admin area.
- AD login and email settings must be configurable and testable for company systems.

## Release Rules

- Small fix: smoke test and concise release note.
- Medium fix: unit/API test plus smoke test.
- Large fix: full test, security scan, rollback note, and manual approval.
- Preserve existing package layout and install commands unless a migration is explicitly approved.

## Handoff Rules

- Update `Memory.md` after meaningful changes.
- Update `HANDOFF_INDEX.md` and `docs/current_state_snapshot.md` before a handoff.
- The next agent must read the handoff files before editing.
- For company or production issues, do not conclude root cause without evidence.

## Definition Of Done

- Change scope is clear.
- Tests or verification evidence are attached.
- Risks and manual checks are listed.
- Related docs are updated when behavior changes.
- No sensitive data is added.
