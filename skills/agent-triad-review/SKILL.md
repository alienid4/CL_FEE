---
name: agent-triad-review
description: Use when the user wants multiple agents or role-based checks for code changes: Code Agent, Test Agent, and Review Agent coordination, with one editor and two reviewers to avoid agents overwriting each other.
---

# Agent Triad Review

Use three roles, but only one role edits code.

## Roles

| Role | Responsibility | Can Edit |
| --- | --- | --- |
| Code Agent | Implement bounded change | yes |
| Test Agent | Reproduce, run tests, collect evidence | no |
| Review Agent | Check risk, security, architecture, scope | no |

## Workflow

```text
goal -> Code Agent patch -> Test Agent evidence -> Review Agent risks
     -> pass: summarize
     -> fail: Code Agent retry
```

## Shared State

Record:

- goal
- files changed
- test commands
- failures
- review findings
- retry count
- final decision
- assumptions
- missing evidence
- rollback notes

## Guardrail

Never let multiple agents edit the same files at the same time. Review agents
must provide findings and evidence, not patches, unless explicitly asked.
