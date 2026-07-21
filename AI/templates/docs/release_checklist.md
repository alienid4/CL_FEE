# Release Checklist

## Change Size

| Size | Examples | Required Verification |
| --- | --- | --- |
| Small | text, label, simple UI | smoke test |
| Medium | filters, import rule, API behavior | unit/API test + smoke |
| Large | data model, auth, deployment, migration | full test + rollback |

## Before Release

- [ ] Version updated
- [ ] Release note written
- [ ] Tests run
- [ ] UI regression run when web workflows changed
- [ ] Non-local destructive-test guard verified when regression runner changed
- [ ] Sensitive data scan done
- [ ] Package layout verified
- [ ] Install / patch command verified
- [ ] Rollback path documented

## Release Evidence

| Item | Evidence |
| --- | --- |
| Commit | |
| Package | |
| SHA256 | |
| Test output | |
| UI regression output | |
| Guard output | |
| Known risk | |
