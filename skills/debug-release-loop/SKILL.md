---
name: debug-release-loop
description: Use when fixing bugs, collecting evidence, preparing patches, releases, install packages, rollback notes, or when the user says not to guess and asks for diagnostics, proof, or release-ready output.
---

# Debug Release Loop

Use a controlled loop:

```text
reproduce -> collect evidence -> diagnose -> patch -> test -> package -> report
```

## Evidence First

If data is missing, provide a safe diagnostics command or script. Do not guess.

Diagnostics must:

- Be read-only.
- Mask or hash sensitive values.
- Output to `/tmp` or a local temp directory.
- Avoid tokens, passwords, raw personal data, and private keys.
- Prefer counts, status values, stable hashes, and short masked samples.

## Patch Rules

- Fix the smallest confirmed cause.
- Add regression coverage when possible.
- Preserve package layout and install commands.
- Keep rollback notes.
- Do not declare a root cause until evidence supports it.

## Release Report

Include:

- Version or patch id.
- Package path.
- SHA256 if packaged.
- Install command.
- Verification command and result.
- Known risks.
- Whether this was a small, medium, or large change.
