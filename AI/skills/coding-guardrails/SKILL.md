---
name: coding-guardrails
description: Use for every code change in any project to prevent broad refactors, UI-embedded business rules, sensitive data leaks, untested bug fixes, and fixes that break other workflows.
---

# Coding Guardrails

Use this skill whenever changing code.

## Before Editing

- Read relevant files first.
- Identify the exact behavior being changed.
- Identify related screens, APIs, services, tests, and data rules.
- Check for user or uncommitted changes and do not overwrite them.
- Separate confirmed facts from assumptions.
- If evidence is missing, collect read-only diagnostics before changing code.
- If the requirement is unreasonable, recommend a safer answer with pros and cons before asking for confirmation.

## Edit Rules

- Keep changes scoped.
- Put business rules in service/domain modules, not UI files.
- Avoid unrelated refactors.
- Add a regression test for every bug fix.
- Keep user workflows clear: current state, next action, and failure reason.
- Do not commit secrets or sensitive data.
- Preserve existing package layout and install commands unless explicitly changed.
- For company formal systems, default to Microsoft SQL Server when no database is specified.
- Enterprise UI tables must be sortable, searchable, and drill-down friendly when they display metrics or large data.
- If a feature adds records, provide edit and delete/disable behavior or document why it is out of scope.

## Verification

Choose verification by risk:

- Small: smoke test.
- Medium: targeted unit/API test plus smoke.
- Large: full test, security scan, rollback note.

## Final Report

Report:

- Changed behavior.
- Changed files.
- Tests or verification evidence.
- Risks and manual checks.
- Known assumptions and missing evidence.
