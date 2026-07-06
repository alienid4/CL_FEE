---
name: project-rescue-audit
description: Use when an existing project has already been developed and needs stabilization: architecture inventory, data model cleanup, status rules, smoke tests, runbook, diagnostics, risk register, regression test plan, and handoff preparation without rewriting from scratch.
---

# Project Rescue Audit

Use this for existing systems. Do not start with a rewrite.

## Audit Order

1. Inventory stack, entry points, config, data stores, routes, jobs, and deployment path.
2. Identify core domain entities and status rules.
3. Identify duplicated logic across UI, routes, services, and scripts.
4. Identify missing tests and risky operations.
5. Add or update baseline docs.
6. Add safe diagnostics.
7. Add the smallest smoke test.
8. Recommend phased stabilization work.

## Output Format

```text
Current state:
Top risks:
Quick wins:
Must not change yet:
Recommended phases:
Evidence collected:
Missing evidence:
```

## Risk Focus

- Data loss
- Broken workflow
- Hidden business rules in UI
- Unclear status transitions
- Missing rollback
- Missing tests
- Sensitive data leakage
- Hardcoded deployment assumptions
- Package layout drift
