# Security And Data Handling

## Never Commit

- API tokens
- Passwords
- Private keys
- Real personal data
- Production database dumps
- Raw internal host lists unless approved
- Screenshots containing sensitive values

## Debug Masking

Mask or hash:

- IP addresses when external sharing is possible
- Hostnames
- User names
- Email addresses
- Phone numbers
- Token values
- Internal paths if sensitive

## External AI Rule

When using external AI, provide structure and masked samples. Do not provide raw
company data unless approved by policy.

## Company GPT Rule

Internal GPT may receive internal architecture details only when company policy
allows it. Secrets are still never allowed.

## Safe Debug Output

Prefer:

- Counts
- Status values
- Stable hashes
- Short samples with sensitive fields masked
- Output files stored under `/tmp` or local temp

Avoid:

- Full host lists
- Full personal data
- Raw credentials
- Private paths when external sharing is possible
