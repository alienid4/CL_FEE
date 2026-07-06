param(
    [string]$BaseUrl = "http://127.0.0.1:8892",
    [string]$ScreenshotPath = "docs\ui_reference\current_8892_ui_checkpoint_gate.png"
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

$Uri = [Uri]$BaseUrl
if ($Uri.Host -notin @("127.0.0.1", "localhost", "::1")) {
    Write-Error "FAIL: UI checkpoint gate only allows local URLs by default: $BaseUrl"
    exit 2
}

$ScreenshotFullPath = Join-Path $Root $ScreenshotPath
$ScreenshotDir = Split-Path -Parent $ScreenshotFullPath
if (-not (Test-Path -LiteralPath $ScreenshotDir -PathType Container)) {
    New-Item -ItemType Directory -Path $ScreenshotDir | Out-Null
}

$PythonScript = @'
import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

base_url = sys.argv[1]
screenshot_path = Path(sys.argv[2])
module_ids = [
    "cases-module",
    "budget",
    "projects",
    "signoff",
    "contracts-module",
    "purchases",
    "payments-module",
    "data-review",
]

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1500, "height": 900})
    page.goto(base_url, wait_until="networkidle", timeout=30000)
    if page.locator("#login-form").count() and not page.locator("#login-form").is_hidden():
        page.locator('#login-form input[name="username"]').fill("ap01")
        page.locator('#login-form input[name="password"]').fill("1qaz@WSX")
        page.locator('#login-form button[type="submit"]').click()
        page.locator("#app-shell").wait_for(state="visible", timeout=10000)
    page.screenshot(path=str(screenshot_path), full_page=True)
    result = page.evaluate(
        """
        (moduleIds) => {
          const visibleText = document.body.innerText || "";
          const ids = Array.from(document.querySelectorAll("[id]")).map((el) => el.id);
          const duplicateIds = ids.filter((id, index) => ids.indexOf(id) !== index);
          return {
            viewportWidth: window.innerWidth,
            bodyScrollWidth: document.body.scrollWidth,
            bodyClientWidth: document.body.clientWidth,
            moduleSections: Object.fromEntries(moduleIds.map((id) => [id, !!document.getElementById(id)])),
            visibleModuleSections: moduleIds.filter((id) => {
              const el = document.getElementById(id);
              return !!el && !el.hidden;
            }),
            rowCounts: Object.fromEntries(moduleIds.map((id) => [id, document.querySelectorAll(`#${id} table tbody tr`).length])),
            duplicateIds,
            hasRoleSwitchText: visibleText.includes("檢視角色") || visibleText.includes("切換角色") || visibleText.includes("使用者："),
            hasDemoText: /Demo|DEMO/.test(visibleText),
            hasVisibleEnglishOperatorWords: /\\bDashboard\\b|\\bProject\\b|\\bBudget_ID\\b|\\bContract code\\b|\\bAmount\\b|\\balert\\b|\\bformal confirm\\b|\\bcommit\\b/.test(visibleText),
          };
        }
        """,
        module_ids,
    )
    browser.close()

failures = []
if result["viewportWidth"] != 1500:
    failures.append(f"viewport width expected 1500, got {result['viewportWidth']}")
if result["bodyScrollWidth"] != result["bodyClientWidth"]:
    failures.append(f"body has horizontal overflow: scrollWidth={result['bodyScrollWidth']} clientWidth={result['bodyClientWidth']}")
missing = [key for key, ok in result["moduleSections"].items() if not ok]
if missing:
    failures.append("missing module section(s): " + ", ".join(missing))
empty = [key for key, count in result["rowCounts"].items() if count <= 0]
if empty:
    failures.append("module section(s) have no table rows: " + ", ".join(empty))
if result["visibleModuleSections"] != ["cases-module"]:
    failures.append("default view must show only cases-module, got: " + ", ".join(result["visibleModuleSections"]))
if result["duplicateIds"]:
    failures.append("duplicate id(s): " + ", ".join(result["duplicateIds"]))
if result["hasRoleSwitchText"]:
    failures.append("visible role/user switch text found")
if result["hasDemoText"]:
    failures.append("visible Demo/DEMO text found")
if result["hasVisibleEnglishOperatorWords"]:
    failures.append("visible English operator wording found")

print(json.dumps(result, ensure_ascii=False, indent=2))
if failures:
    print("FAIL: " + " | ".join(failures))
    sys.exit(1)

print(f"PASS: UI checkpoint gate passed; screenshot saved to {screenshot_path}")
'@

$TempScript = Join-Path $env:TEMP "ai_fee_check_ui_checkpoint.py"
Set-Content -LiteralPath $TempScript -Value $PythonScript -Encoding UTF8
python $TempScript $BaseUrl $ScreenshotFullPath
