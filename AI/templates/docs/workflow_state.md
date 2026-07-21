# Workflow And State

## Main Workflow

```text
draft -> review -> active -> retired
          |
          -> rejected
```

## State Machine

| From | Action | To | Who Can Do It | Required Evidence |
| --- | --- | --- | --- | --- |
| draft | submit | review | owner | required fields complete |
| review | approve | active | approver | audit note |
| active | retire | retired | admin | reason |

## User Guidance

Every workflow screen should answer:

- What is the current state?
- What can I do now?
- Why is an action disabled?
- Who owns the next step?
- What evidence is needed?

## Batch Workflow

```text
import -> precheck -> staging -> apply -> verify -> rollback if needed
```

