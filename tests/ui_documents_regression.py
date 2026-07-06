import argparse
import sys
import time
from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import urlparse

import httpx
from playwright.sync_api import Page, sync_playwright


LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


@dataclass(frozen=True)
class UiModule:
    name: str
    api_path: str
    list_selector: str
    form_selector: str
    row_attr: str
    match_field: str
    patch_field: str
    patch_value: Any
    create_payload: Callable[[dict[str, int], str], dict[str, Any]]


def api(client: httpx.Client, method: str, path: str, **kwargs: Any) -> Any:
    response = client.request(method, path, **kwargs)
    response.raise_for_status()
    if response.status_code == 204:
        return None
    return response.json()["data"]


def safe_delete(client: httpx.Client, path: str) -> None:
    try:
        client.delete(path).raise_for_status()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code != 404:
            raise


def cleanup_regression_data(client: httpx.Client, prefix: str) -> None:
    contracts = api(client, "GET", "/api/contracts")
    regression_contract_ids = {
        int(item["id"])
        for item in contracts
        if str(item.get("contract_code", "")).startswith(prefix)
    }

    payments = api(client, "GET", "/api/payments")
    for item in payments:
        contract_id = item.get("contract_id")
        is_regression_payment_value = item.get("payment_month") == "2099-07" and item.get("payment_amount") == 34567
        if contract_id in regression_contract_ids and is_regression_payment_value:
            safe_delete(client, f"/api/payments/{item['id']}")

    documents = api(client, "GET", "/api/documents")
    for item in documents:
        if str(item.get("file_name", "")).startswith(prefix):
            safe_delete(client, f"/api/documents/{item['id']}")

    for item in contracts:
        if str(item.get("contract_code", "")).startswith(prefix):
            safe_delete(client, f"/api/contracts/{item['id']}")

    cases = api(client, "GET", "/api/cases")
    for item in cases:
        if str(item.get("case_code", "")).startswith(prefix):
            safe_delete(client, f"/api/cases/{item['id']}")


def text_value(page: Page, selector: str) -> str:
    return page.locator(selector).input_value()


def assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def fill_form_field(page: Page, form_selector: str, field_name: str, value: Any) -> None:
    field = page.locator(f'{form_selector} [name="{field_name}"]')
    field.evaluate("(element, value) => { element.value = String(value); }", value)


def login_as_cio(page: Page) -> None:
    if page.locator("#login-form").count() == 0 or page.locator("#login-form").is_hidden():
        return
    page.locator('#login-form input[name="username"]').fill("ap01")
    page.locator('#login-form input[name="password"]').fill("1qaz@WSX")
    page.locator('#login-form button[type="submit"]').click()
    page.locator("#app-shell").wait_for(state="visible", timeout=10_000)


def run_module_lifecycle(
    page: Page,
    client: httpx.Client,
    module: UiModule,
    context: dict[str, int],
    prefix: str,
) -> int:
    created = api(client, "POST", module.api_path, json=module.create_payload(context, prefix))
    created_id = int(created["id"])
    context[f"{module.name}_id"] = created_id

    page.goto(client.base_url.join("/").__str__(), wait_until="networkidle")
    login_as_cio(page)
    module_href = MODULE_VIEW_HREFS[module.name]
    page.locator(f'a.module-card[href="{module_href}"]').last.click()
    row = page.locator(f'{module.list_selector} article[data-{module.row_attr}="{created_id}"]')
    row.wait_for(state="visible", timeout=10_000)

    row.locator('button[data-action="edit"]').click()
    form = page.locator(module.form_selector)
    form.locator('button[type="submit"]').wait_for(state="visible")

    assert_equal(text_value(page, f'{module.form_selector} input[name="id"]'), str(created_id), f"{module.name} edit id")
    assert_equal(
        text_value(page, f'{module.form_selector} [name="{module.match_field}"]'),
        str(created[module.match_field]),
        f"{module.name} edit {module.match_field}",
    )
    assert_equal(form.locator('button[type="submit"]').inner_text(), "儲存", f"{module.name} submit mode")

    fill_form_field(page, module.form_selector, module.patch_field, module.patch_value)
    with page.expect_response(
        lambda response: f"{module.api_path}/{created_id}" in response.url
        and response.request.method == "PATCH"
        and response.ok
    ):
        form.locator('button[type="submit"]').click()

    rows_after_save = api(client, "GET", module.api_path)
    matches = [item for item in rows_after_save if item[module.match_field] == created[module.match_field]]
    assert_equal(len(matches), 1, f"{module.name} save should update the existing record")
    assert_equal(matches[0]["id"], created_id, f"{module.name} updated id")
    assert_equal(matches[0][module.patch_field], module.patch_value, f"{module.name} updated {module.patch_field}")

    row = page.locator(f'{module.list_selector} article[data-{module.row_attr}="{created_id}"]')
    row.wait_for(state="visible", timeout=10_000)
    with page.expect_response(
        lambda response: f"{module.api_path}/{created_id}/disable" in response.url
        and response.request.method == "POST"
        and response.ok
    ):
        row.locator('button[data-action="disable"]').click()

    disabled = next(item for item in api(client, "GET", module.api_path) if item["id"] == created_id)
    assert_equal(disabled["status"], "disabled", f"{module.name} disabled status")

    row = page.locator(f'{module.list_selector} article[data-{module.row_attr}="{created_id}"]')
    row.wait_for(state="visible", timeout=10_000)
    with page.expect_response(
        lambda response: f"{module.api_path}/{created_id}" in response.url
        and response.request.method == "DELETE"
        and response.status == 204
    ):
        row.locator('button[data-action="delete"]').click()

    remaining = [item for item in api(client, "GET", module.api_path) if item["id"] == created_id]
    assert_equal(remaining, [], f"{module.name} deleted record")
    return created_id


MODULES = [
    UiModule(
        name="case",
        api_path="/api/cases",
        list_selector="#cases",
        form_selector="#case-form",
        row_attr="case-id",
        match_field="case_code",
        patch_field="owner",
        patch_value="UI Regression Owner",
        create_payload=lambda _context, prefix: {
            "case_code": f"{prefix}case",
            "title": "UI regression case",
            "owner": "Created by UI regression",
            "amount": 12345,
            "status": "draft",
        },
    ),
    UiModule(
        name="contract",
        api_path="/api/contracts",
        list_selector="#contracts",
        form_selector="#contract-form",
        row_attr="contract-id",
        match_field="contract_code",
        patch_field="vendor_name",
        patch_value="UI Regression Vendor",
        create_payload=lambda context, prefix: {
            "contract_code": f"{prefix}contract",
            "contract_name": "UI regression contract",
            "vendor_name": "Created by UI regression",
            "amount": 23456,
            "case_id": context["case_id"],
            "status": "active",
        },
    ),
    UiModule(
        name="payment",
        api_path="/api/payments",
        list_selector="#payments",
        form_selector="#payment-form",
        row_attr="payment-id",
        match_field="contract_id",
        patch_field="invoice_status",
        patch_value="received",
        create_payload=lambda context, prefix: {
            "contract_id": context["contract_id"],
            "payment_month": "2099-07",
            "payment_amount": 34567,
            "invoice_status": "not_received",
            "status": "pending",
        },
    ),
    UiModule(
        name="document",
        api_path="/api/documents",
        list_selector="#documents",
        form_selector="#document-form",
        row_attr="document-id",
        match_field="file_name",
        patch_field="source_note",
        patch_value="updated by ui regression",
        create_payload=lambda context, prefix: {
            "file_name": f"{prefix}document.pdf",
            "document_type": "contract",
            "source_note": "created by ui regression",
            "status": "active",
            "case_id": context["case_id"],
            "contract_id": context["contract_id"],
        },
    ),
]

MODULE_VIEW_HREFS = {
    "case": "#cases-module",
    "contract": "#contracts-module",
    "payment": "#payments-module",
    "document": "#data-review",
}


def run_ui_lifecycle_regression(base_url: str, headless: bool) -> None:
    prefix = f"ui-regression-{int(time.time())}-"
    context: dict[str, int] = {}

    with httpx.Client(base_url=base_url, timeout=10.0) as client:
        health = client.get("/health")
        health.raise_for_status()
        cleanup_regression_data(client, "ui-regression-")

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=headless)
                try:
                    page = browser.new_page()
                    for module in MODULES:
                        run_module_lifecycle(page, client, module, context, prefix)
                finally:
                    browser.close()
        finally:
            cleanup_regression_data(client, "ui-regression-")


def validate_base_url(base_url: str, allow_non_local: bool) -> str:
    normalized = base_url.rstrip("/")
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("base-url must be an absolute http(s) URL")
    if not allow_non_local and parsed.hostname not in LOCAL_HOSTS:
        allowed = ", ".join(sorted(LOCAL_HOSTS))
        raise ValueError(
            f"base-url host {parsed.hostname!r} is not local. "
            f"Allowed hosts are {allowed}; pass --allow-non-local to run against another environment."
        )
    return normalized


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run cases/contracts/payments/documents UI lifecycle regression against a running AI_FEE server."
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8888")
    parser.add_argument(
        "--allow-non-local",
        action="store_true",
        help="Allow destructive regression cleanup against a non-local base URL.",
    )
    parser.add_argument("--headed", action="store_true", help="Show the browser while running.")
    args = parser.parse_args()

    try:
        base_url = validate_base_url(args.base_url, allow_non_local=args.allow_non_local)
        run_ui_lifecycle_regression(base_url, headless=not args.headed)
    except Exception as exc:
        print(f"UI lifecycle regression failed: {exc}", file=sys.stderr)
        return 1

    print(
        "UI lifecycle regression passed: cases, contracts, payments, and documents "
        "edit/save, disable, delete, and cleanup verified."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
