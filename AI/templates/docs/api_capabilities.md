# API Capabilities

Use this page to describe what this system can expose to an AI control center or
cross-system dashboard.

## Capability Matrix

| Capability | Available | Endpoint | Notes |
| --- | --- | --- | --- |
| Health | no | `/health` | |
| Ready | no | `/ready` | |
| Version | no | `/api/version` | |
| Status | no | `/api/status` | |
| Capabilities | no | `/api/capabilities` | |
| Safe Diagnostics | no | `/api/diagnostics/safe` | read-only and masked |
| Assets / Records | no | | |
| Capacity | no | | |
| Workflow | no | | |

## Recommended Response Format

Success:

```json
{
  "ok": true,
  "data": {}
}
```

Failure:

```json
{
  "ok": false,
  "error": "safe error message"
}
```

