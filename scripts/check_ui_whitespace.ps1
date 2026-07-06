param(
    [string]$BaseUrl = "http://127.0.0.1:8892"
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

$Uri = [Uri]$BaseUrl
if ($Uri.Host -notin @("127.0.0.1", "localhost", "::1")) {
    Write-Error "FAIL: whitespace gate only allows local URLs by default: $BaseUrl"
    exit 2
}

$PythonScript = @'
import json
import sys

from playwright.sync_api import sync_playwright

base_url = sys.argv[1]
modules = [
    ("cases-module", 0),
    ("budget", 0),
    ("projects", 0),
    ("signoff", 0),
    ("contracts-module", 0),
    ("purchases", 0),
    ("payments-module", 0),
    ("data-review", -1),
]

results = []
failures = []
warnings = []

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1500, "height": 900})
    page.goto(base_url, wait_until="networkidle", timeout=30000)
    if page.locator("#login-form").count() and not page.locator("#login-form").is_hidden():
        page.locator('#login-form input[name="username"]').fill("ap01")
        page.locator('#login-form input[name="password"]').fill("1qaz@WSX")
        page.locator('#login-form button[type="submit"]').click()
        page.locator("#app-shell").wait_for(state="visible", timeout=10000)

    for module_id, index in modules:
        page.evaluate("window.scrollTo(0, 260)")
        locator = page.locator(f'.module-card[href="#{module_id}"]')
        locator = locator.last if index == -1 else locator.nth(index)
        locator.click()
        page.wait_for_timeout(100)
        result = page.evaluate(
            """
            (moduleId) => {
              const panel = document.getElementById(moduleId);
              const activePanels = Array.from(document.querySelectorAll(".module-panel"))
                .filter((el) => !el.hidden)
                .map((el) => el.id);
              const panelRect = panel ? panel.getBoundingClientRect() : null;
              const visible = Array.from(document.querySelectorAll("main *")).filter((el) => {
                const rect = el.getBoundingClientRect();
                const style = getComputedStyle(el);
                return rect.width > 0 && rect.height > 0 && style.visibility !== "hidden" && style.display !== "none";
              });
              let firstVisibleTop = 99999;
              let contentBottom = 0;
              for (const el of visible) {
                const rect = el.getBoundingClientRect();
                firstVisibleTop = Math.min(firstVisibleTop, rect.top);
                contentBottom = Math.max(contentBottom, rect.bottom);
              }
              return {
                module: moduleId,
                scrollY: Math.round(window.scrollY),
                activePanels,
                panelTop: panelRect ? Math.round(panelRect.top) : null,
                panelHeight: panelRect ? Math.round(panelRect.height) : null,
                firstVisibleTop: Math.round(firstVisibleTop),
                contentBottom: Math.round(contentBottom),
                bottomBlank: Math.round(window.innerHeight - contentBottom),
                bodyScrollHeight: document.body.scrollHeight,
                bodyClientHeight: document.documentElement.clientHeight,
              };
            }
            """,
            module_id,
        )
        results.append(result)

    browser.close()

for result in results:
    module_id = result["module"]
    if result["activePanels"] != [module_id]:
        failures.append(f"{module_id}: active panel mismatch {result['activePanels']}")
    if result["scrollY"] != 0:
        failures.append(f"{module_id}: did not reset to top, scrollY={result['scrollY']}")
    if result["panelTop"] is None or result["panelTop"] > 24:
        failures.append(f"{module_id}: panel starts too low, panelTop={result['panelTop']}")
    if result["firstVisibleTop"] > 24:
        failures.append(f"{module_id}: first visible content starts too low, top={result['firstVisibleTop']}")
    if module_id != "data-review" and result["panelHeight"] and result["panelHeight"] >= 820:
        failures.append(f"{module_id}: panel appears stretched to viewport, height={result['panelHeight']}")
    if result["bottomBlank"] > 380:
        warnings.append(f"{module_id}: bottom blank {result['bottomBlank']}px because current fixture content is short")

print(json.dumps({"results": results, "warnings": warnings}, ensure_ascii=False, indent=2))
if failures:
    print("FAIL: " + " | ".join(failures))
    sys.exit(1)

print("PASS: whitespace gate passed")
'@

$TempScript = Join-Path $env:TEMP "ai_fee_check_ui_whitespace.py"
Set-Content -LiteralPath $TempScript -Value $PythonScript -Encoding UTF8
python $TempScript $BaseUrl
