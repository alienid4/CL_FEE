# UI Regression Testing

This project includes a repeatable Playwright lifecycle regression for four UI modules:

- Cases
- Contracts
- Payments
- Documents

## Prerequisites

- FastAPI must already be running at `http://127.0.0.1:8888`.
- Install or update Python dependencies only when needed:

```powershell
.\scripts\test_ui_documents.ps1 -InstallDeps
```

- First-time Playwright browser setup:

```powershell
.\scripts\test_ui_documents.ps1 -InstallBrowsers
```

## Run

```powershell
.\scripts\test_ui_documents.ps1
```

The script name is kept for backward compatibility, but the runner now covers cases, contracts, payments, and documents.

Verify the non-local URL safety guard:

```powershell
.\scripts\test_ui_documents.ps1 -CheckNonLocalGuard
```

Run the standard Windows test gate with the full UI lifecycle regression included:

```powershell
.\scripts\test_windows.ps1 -IncludeUiLifecycle -CheckNonLocalGuard
```

The older switch remains valid as an alias:

```powershell
.\scripts\test_windows.ps1 -IncludeUiDocuments -CheckNonLocalGuard
```

## Runtime Freshness Smoke

Before trusting a browser or API session on port 8888, verify that the running FastAPI process is the current build and not a stale runtime:

```powershell
.\scripts\check_runtime_freshness.ps1 -BaseUrl "http://127.0.0.1:8888"
```

The smoke checks `/health` and confirms `/openapi.json` includes:

- `/api/audit-logs`
- `/api/import-batches`
- `/api/import-batches/{batch_id}/rows`

If any endpoint is missing, the script exits non-zero and prints the missing endpoint names. This check does not read from `archive/` and only inspects the live runtime.

You can include the freshness smoke in the standard Windows test gate when FastAPI is already running:

```powershell
.\scripts\test_windows.ps1 -IncludeRuntimeFreshness -RuntimeBaseUrl "http://127.0.0.1:8888"
```

Optional visible-browser mode:

```powershell
.\scripts\test_ui_documents.ps1 -Headed
```

By default, the script only allows local targets: `localhost`, `127.0.0.1`, or `::1`.
To run against a non-local environment, pass `-AllowNonLocal` explicitly:

```powershell
.\scripts\test_ui_documents.ps1 -BaseUrl "http://example-dev-host:8888" -AllowNonLocal
```

## Coverage

For each module, the script creates a temporary record through the API, then verifies through the UI:

- Edit loads the existing record into the correct form.
- Save sends `PATCH` to the same record instead of creating a duplicate.
- Disable changes status to `disabled`.
- Delete removes the record.
- Temporary test data is cleaned even when a check fails.

## Cleanup Prefix

Cleanup deletes temporary records with the `ui-regression-` prefix:

- Cases: `case_code`
- Contracts: `contract_code`
- Payments: records linked to prefixed contracts and carrying the test-only `payment_month=2099-07` / `payment_amount=34567` marker pair. Payment `invoice_status` and `status` use the production dictionaries and are not cleanup markers.
- Documents: `file_name`

Do not create manual dev records with that prefix unless they are disposable test data.

No FastAPI restart is needed for this test script. Browser refresh is enough for frontend-only changes.
