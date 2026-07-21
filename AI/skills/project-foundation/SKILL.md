---
name: project-foundation
description: Use when starting or rescuing any software project and Codex must establish basic engineering foundations before coding: project purpose, users, terms, data model, workflow status, sensitive data, risks, acceptance cases, handoff files, and minimum implementation scope.
---

# Project Foundation

Use this skill before writing code for a new project or before stabilizing an existing project.

## Workflow

1. Inspect existing files, docs, config, tests, and deployment notes.
2. Identify system purpose, users, data, workflow, status, and risk.
3. Produce or update foundation docs:
   - `docs/project_overview.md`
   - `docs/data_dictionary.md`
   - `docs/workflow_state.md`
   - `docs/risk_register.md`
   - `docs/test_plan.md`
   - `docs/security_data_handling.md`
   - `docs/ai_truth_and_evidence.md`
   - `docs/ai_work_quality_rules.md`
   - `docs/company_codex_enterprise_profile.md`
   - `docs/product_ui_rules.md`
   - `docs/module_management_rules.md`
   - `docs/security_scanning_rules.md`
4. Define the smallest safe implementation scope.
5. Only then start coding.

## Required Output

Always summarize:

- What the system does.
- The main domain terms.
- The core data entities.
- The main workflow and state transitions.
- Sensitive data and high-risk actions.
- Company defaults such as MSSQL, AD login, and email configuration when relevant.
- UI rules such as search, sorting, drill-down metrics, tabs, and module settings.
- Acceptance cases.
- What is intentionally out of scope.
- What evidence is known, missing, or assumed.

## Guardrail

Do not begin implementation if core terms, status rules, or safety boundaries are still ambiguous. State assumptions, request or generate safe diagnostics, and keep the change small.
