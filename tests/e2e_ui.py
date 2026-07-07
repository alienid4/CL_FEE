"""端到端 UI 自動測試（真瀏覽器）：登入 → 建案 → 出現在待辦/清單 → CIO 唯讀。

跑法：python tests/e2e_ui.py
自帶臨時 DB 與伺服器，不污染正式資料。需 Playwright 瀏覽器（playwright install chromium）。
"""
import os
import subprocess
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8")  # Windows 主控台預設非 utf-8
except Exception:
    pass

DB = "./data/_e2e.db"
PORT = 8011
BASE = f"http://127.0.0.1:{PORT}"


def main() -> int:
    for f in (DB,):
        try:
            os.remove(f)
        except OSError:
            pass
    env = {
        **os.environ,
        "SQLITE_PATH": DB,
        "AP01_PASSWORD": "e2e-pass",
        "AP02_PASSWORD": "e2e-pass",
        "AP03_PASSWORD": "e2e-pass",
        "SESSION_SECRET": "e2e-secret-fixed",
    }
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(PORT), "--log-level", "warning"],
        env=env,
    )
    results: list[tuple[str, bool]] = []
    try:
        import httpx
        from playwright.sync_api import sync_playwright

        for _ in range(60):
            try:
                httpx.get(BASE + "/health", timeout=1)
                break
            except Exception:
                time.sleep(0.3)

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()

            # 1) 登入 ap02（主管）
            page.goto(BASE + "/")
            page.fill('#login-form input[name="username"]', "ap02")
            page.fill('#login-form input[name="password"]', "e2e-pass")
            page.click('#login-form button[type="submit"]')
            page.wait_for_selector("#app-shell", state="visible", timeout=10000)
            results.append(("登入 ap02 並保持登入", True))

            # 2) 新增案件（審核中 + 下一步 + 備註）
            page.fill('#case-form input[name="case_code"]', "E2E-001")
            page.fill('#case-form input[name="title"]', "E2E 測試案")
            page.select_option('#case-form select[name="status"]', "reviewing")
            page.fill('#case-form input[name="note"]', "E2E 備註")
            page.fill('#case-form input[name="next_step"]', "E2E 下一步")
            page.click("#submit-case")
            page.wait_for_timeout(700)

            # 3) 驗證出現在案件清單與待辦
            cases_text = page.inner_text("#cases")
            results.append(("新增案件出現在案件清單", "E2E-001" in cases_text))
            todo_text = page.inner_text("#todo-list")
            results.append(("審核中案件出現在待辦", "E2E-001" in todo_text))
            results.append(("待辦帶出備註/下一步", "E2E 下一步" in todo_text))

            # 3.5) 合約模組：靜態假表已移除，真清單可即時新增
            page.click('a.module-card[href="#contracts-module"]')
            page.wait_for_timeout(400)
            results.append(("合約模組已無假表(CON-2026-0001)", "CON-2026-0001" not in page.content()))
            page.fill('#contract-form input[name="contract_code"]', "E2E-CON-1")
            page.fill('#contract-form input[name="contract_name"]', "E2E 合約")
            page.click('#contract-form button[type="submit"]')
            page.wait_for_timeout(700)
            results.append(("新增合約出現在真清單", "E2E-CON-1" in page.inner_text("#contracts")))

            # 3.7) 示範資料：主管在主管儀表板可一鍵載入（DEMO- 標示）
            page.click('a.module-card[href="#cases-module"]')
            page.wait_for_timeout(300)
            page.click('button[data-case-tab="dashboard"]')
            page.wait_for_timeout(300)
            demo_visible = page.is_visible("#demo-controls")
            results.append(("主管可見示範資料工具", demo_visible))
            page.click("#demo-seed")
            page.wait_for_selector("#demo-status:has-text('已載入')", timeout=8000)
            results.append(("載入示範資料後狀態回饋", "已載入" in page.inner_text("#demo-status")))
            page.click('button[data-case-tab="list"]')
            page.wait_for_timeout(600)
            results.append(("示範案件進入案件清單(DEMO-)", "DEMO-" in page.inner_text("#cio-cases-body")))

            # 4) 換 CIO（唯讀）→ 建案應失敗（案件數不增）
            page.click('a.module-card[href="#cases-module"]')
            page.wait_for_timeout(300)
            page.click("#logout" if page.query_selector("#logout") else "text=登出")
            page.wait_for_selector("#login-form", state="visible", timeout=10000)
            page.fill('#login-form input[name="username"]', "ap01")
            page.fill('#login-form input[name="password"]', "e2e-pass")
            page.click('#login-form button[type="submit"]')
            page.wait_for_selector("#app-shell", state="visible", timeout=10000)
            before = page.inner_text("#cases")
            page.fill('#case-form input[name="case_code"]', "CIO-BLOCK")
            page.fill('#case-form input[name="title"]', "CIO 不該能建")
            page.click("#submit-case")
            page.wait_for_timeout(500)
            after = page.inner_text("#cases")
            results.append(("CIO 唯讀：建案被擋（清單無 CIO-BLOCK）", "CIO-BLOCK" not in after))

            browser.close()

        print("=" * 44)
        for name, ok in results:
            print(("[PASS]" if ok else "[FAIL]"), name)
        print("=" * 44)
        all_ok = all(ok for _, ok in results)
        print("E2E UI 結果:", "全部通過" if all_ok else "有失敗")
        return 0 if all_ok else 1
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
        try:
            os.remove(DB)
        except OSError:
            pass


if __name__ == "__main__":
    sys.exit(main())
