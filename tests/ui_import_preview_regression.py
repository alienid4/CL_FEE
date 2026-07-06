import argparse
import time
from urllib.parse import urlparse

import httpx
from playwright.sync_api import Page, sync_playwright


LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def api(client: httpx.Client, method: str, path: str, **kwargs):
    response = client.request(method, path, **kwargs)
    response.raise_for_status()
    return response.json()["data"]


def assert_local_base_url(base_url: str, allow_non_local: bool) -> None:
    host = urlparse(base_url).hostname
    if allow_non_local or host in LOCAL_HOSTS:
        return
    raise ValueError(f"Base URL {base_url} is not local. Use --allow-non-local only for explicit remote testing.")


def dashboard_counts(client: httpx.Client) -> dict[str, int]:
    return api(client, "GET", "/api/dashboard")["counts"]


def login_as_cio(page: Page) -> None:
    if page.locator("#login-form").count() == 0 or page.locator("#login-form").is_hidden():
        return
    page.locator('#login-form input[name="username"]').fill("ap01")
    page.locator('#login-form input[name="password"]').fill("1qaz@WSX")
    page.locator('#login-form button[type="submit"]').click()
    page.locator("#app-shell").wait_for(state="visible", timeout=10_000)


def run_regression(page: Page, client: httpx.Client, base_url: str) -> None:
    before_counts = dashboard_counts(client)
    source_name = f"ui-import-preview-{int(time.time())}.json"
    rows_json = """[
  {"case_code":"UI-DUP","amount":"abc","payment_month":"202607","payment_amount":"12000","free_text_note":"保留可見"},
  {"case_code":"UI-DUP","title":"重複案件","payment_month":"2026-13","payment_amount":"0"}
]"""

    page.goto(base_url, wait_until="networkidle")
    login_as_cio(page)
    for forbidden_button in ["Formal Confirm", "Commit Cases", "Import Confirm"]:
        if page.get_by_role("button", name=forbidden_button, exact=True).count() != 0:
            raise AssertionError(f"Formal write UI button must not be visible: {forbidden_button}")
    for forbidden_selector in ["#formal-confirm-cases", "#commit-import-cases"]:
        if page.locator(forbidden_selector).count() != 0:
            raise AssertionError(f"Formal write UI selector must not exist: {forbidden_selector}")
    page_text = page.locator("body").inner_text()
    for forbidden_text in ["檢視角色", "使用者：", "Dry run", "Warnings", "Rows", "Candidates", "Confirm", "Errors"]:
        if forbidden_text in page_text:
            raise AssertionError(f"Production UI must not show demo or English operator wording: {forbidden_text}")
    for tab_name, expected_text in [
        ("案件清單", "本月需要 CIO 看一眼"),
        ("主管儀表板", "預算歸屬結構"),
        ("流程圖", "Case 主檔與模組關聯"),
        ("線性進度圖", "IBM AIX/R6 維護"),
        ("處理優先矩陣", "處理優先序"),
        ("待確認", "待確認項目"),
    ]:
        page.get_by_role("button", name=tab_name, exact=True).click()
        if expected_text not in page.locator("body").inner_text():
            raise AssertionError(f"Expected tab {tab_name!r} to reveal {expected_text!r}.")
    page.get_by_role("button", name="案件清單", exact=True).click()
    for module_href, expected_text in [
        ("#budget", "年度預算編列"),
        ("#projects", "PROJ-2026-0001"),
        ("#signoff", "SIGN-2026-0001"),
        ("#contracts-module", "CON-2026-0001"),
        ("#purchases", "PR-2025-0001"),
        ("#payments-module", "PAY-2025-0001"),
        ("#data-review", "EVID-2026-0001"),
    ]:
        page.locator(f'a.module-card[href="{module_href}"]').last.click()
        if expected_text not in page.locator("body").inner_text():
            raise AssertionError(f"Expected module {module_href!r} to show {expected_text!r}.")
        if page.locator(f"{module_href} table tbody tr").count() == 0:
            raise AssertionError(f"Expected module {module_href!r} to include table rows.")
    page.locator('[data-drill-target="data-review-missing-row"]').click()
    if "drill-highlight" not in page.locator("#data-review-missing-row").get_attribute("class", timeout=3000):
        raise AssertionError("Expected data-review KPI click to highlight the matching detail row.")

    page.locator("[data-mapping-summary]").wait_for(timeout=10_000)
    catalog_text = page.locator("#mapping-catalog-result").inner_text()
    for expected in [
        "欄位",
        "需確認",
        "case_code",
        "案件.案件編號",
        "payment_amount",
        "付款.付款金額",
        "資料檢核.檔案名稱",
    ]:
        if expected not in catalog_text:
            raise AssertionError(f"Expected {expected!r} in mapping catalog result. Actual: {catalog_text}")

    page.locator("#import-preview-form input[name='source_name']").fill(source_name)
    page.locator("#import-preview-form textarea[name='rows_json']").fill(rows_json)
    page.locator("#import-preview-form button[type='submit']").click()
    page.locator("[data-import-summary]").wait_for(timeout=10_000)

    result_text = page.locator("#import-preview-result").inner_text()
    for expected in [
        "資料列",
        "檢核訊息",
        "錯誤",
        "嚴重度",
        "檢核項目",
        "必填欄位缺漏",
        "金額格式錯誤",
        "日期月份錯誤",
        "同批資料重複",
        "free_text_note",
    ]:
        if expected not in result_text:
            raise AssertionError(f"Expected {expected!r} in import preview result. Actual: {result_text}")

    page.locator("#warning-severity-filter").select_option("error")
    filtered_text = page.locator("#import-preview-result .import-warning-list").first.inner_text()
    if "同批資料重複" in filtered_text:
        raise AssertionError(f"Warning-level duplicate should be hidden by error filter. Actual: {filtered_text}")
    for expected in ["必填欄位缺漏", "金額格式錯誤", "日期月份錯誤"]:
        if expected not in filtered_text:
            raise AssertionError(f"Expected {expected!r} after error filter. Actual: {filtered_text}")

    page.locator("#warning-code-filter").select_option("missing_required")
    code_filtered_text = page.locator("#import-preview-result .import-warning-list").first.inner_text()
    if "必填欄位缺漏" not in code_filtered_text:
        raise AssertionError(f"Expected missing_required after code filter. Actual: {code_filtered_text}")
    for hidden in ["金額格式錯誤", "日期月份錯誤", "同批資料重複"]:
        if hidden in code_filtered_text:
            raise AssertionError(f"Expected {hidden!r} to be hidden by missing_required filter. Actual: {code_filtered_text}")

    page.locator("#preflight-cases").click()
    page.locator("[data-preflight-report]").wait_for(timeout=10_000)
    duplicate_gate = page.locator(".preflight-gate[data-gate-code='duplicate_in_batch']")
    duplicate_gate.wait_for(timeout=10_000)
    duplicate_gate_text = duplicate_gate.inner_text()
    for expected in ["已阻擋", "證據", "count: 2"]:
        if expected not in duplicate_gate_text:
            raise AssertionError(
                f"Expected {expected!r} in duplicate gate evidence. Actual: {duplicate_gate_text}"
            )

    valid_case_code = f"UI-DRY-RUN-{int(time.time())}"
    valid_rows_json = f"""[
  {{"case_code":"{valid_case_code}","title":"試算案件","owner":"業助","amount":"12345"}}
]"""
    page.locator("#import-preview-form input[name='source_name']").fill(f"{valid_case_code}.json")
    page.locator("#import-preview-form textarea[name='rows_json']").fill(valid_rows_json)
    page.locator("#import-preview-form button[type='submit']").click()
    page.locator("[data-import-summary]").wait_for(timeout=10_000)
    page.locator("#dry-run-cases").click()
    page.locator("[data-dry-run-plan]").wait_for(timeout=10_000)
    dry_run_text = page.locator("#dry-run-result").inner_text()
    for expected in [
        "試算",
        "案件",
        "預計新增",
        "正式寫入",
        "總金額",
        "12,345 元",
        "批次",
        "對應版本",
        "draft-v1",
        "來源列",
        valid_case_code,
        "試算案件",
        "負責人 業助",
        "金額 12,345 元",
    ]:
        if expected not in dry_run_text:
            raise AssertionError(f"Expected {expected!r} in dry-run result. Actual: {dry_run_text}")

    page.locator("#preflight-cases").click()
    page.locator("[data-preflight-report]").wait_for(timeout=10_000)
    preflight_text = page.locator("#preflight-result").inner_text()
    for expected in [
        "正式寫入前檢核",
        "正式寫入",
        "阻擋",
        "寫入筆數",
        "阻擋項目",
        "對應版本",
        "資料列",
        "錯誤",
        "版本新鮮度",
        "伺服器預覽指紋",
        "伺服器重新檢核：是",
        "指紋",
        "正式寫入尚未開放",
        "警示接受規則",
        "來源舉證鏈",
        "預覽版本檢查",
        "伺服器重新檢核",
    ]:
        if expected not in preflight_text:
            raise AssertionError(f"Expected {expected!r} in preflight result. Actual: {preflight_text}")
    requires_confirmation_gate = page.locator(".preflight-gate[data-gate-code='requires_confirmation']")
    requires_confirmation_gate.wait_for(timeout=10_000)
    if requires_confirmation_gate.get_attribute("data-gate-status") != "pass":
        raise AssertionError(
            "Preflight UI must send the same confirmed cases fields as dry run so requires_confirmation passes. "
            f"Actual gate: {requires_confirmation_gate.inner_text()}"
        )

    after_counts = dashboard_counts(client)
    if after_counts != before_counts:
        raise AssertionError(f"Import preview or mapping catalog changed domain counts: before={before_counts}, after={after_counts}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8888")
    parser.add_argument("--allow-non-local", action="store_true")
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args()

    assert_local_base_url(args.base_url, args.allow_non_local)
    with httpx.Client(base_url=args.base_url, timeout=10) as client:
        client.get("/health").raise_for_status()
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=not args.headed)
            try:
                page = browser.new_page()
                run_regression(page, client, args.base_url)
            finally:
                browser.close()

    print("UI import preview regression passed: warnings render and domain counts remain unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
