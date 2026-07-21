# AI Read-Only API Contract

Use read-only APIs first. Do not give AI write APIs until audit, approval, and
rollback are designed.

## Required Endpoints

```text
GET /health
GET /ready
GET /api/version
GET /api/capabilities
GET /api/status
GET /api/diagnostics/safe
```

## `/api/capabilities` Example

```json
{
  "ok": true,
  "data": {
    "health": true,
    "data_quality": false,
    "capacity": false,
    "workflow": true,
    "reports": true,
    "write_actions": false
  }
}
```

## `/api/diagnostics/safe` Rules

- Must be read-only.
- Must mask or hash sensitive values.
- Must not include tokens, passwords, private keys, personal data, or raw logs
  containing secrets.
- Must include timestamps, version, configured capabilities, and high-level
  health counts.

