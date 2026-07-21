# Debug Intake

Use this when AI needs evidence.

## Rules

- Do not paste secrets.
- Do not paste raw personal data.
- Prefer safe diagnostics scripts.
- Output to `/tmp` or local temp directory.
- Send only masked JSON/text output.

## Minimum Debug Bundle

| Item | Required |
| --- | --- |
| Version | yes |
| Environment | yes |
| Error message | yes |
| Steps to reproduce | yes |
| Relevant safe logs | yes |
| Screenshot | optional |

## Safe Command Pattern

```text
run diagnostics -> output masked file -> send file path or masked output
```

