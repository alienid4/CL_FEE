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


def login(page, username, password):
    """登入頁角色欄現為下拉選單（非文字輸入），選項由 /api/auth/options 非同步載入。"""
    page.wait_for_selector("#login-role option", state="attached", timeout=10000)
    page.select_option("#login-role", username)
    if page.is_visible("#login-pass-wrap"):
        page.fill('#login-form input[name="password"]', password)
    page.click('#login-form button[type="submit"]')
    page.wait_for_selector("#app-shell", state="visible", timeout=10000)


def logout(page):
    page.click("#logout" if page.query_selector("#logout") else "text=登出")
    page.wait_for_selector("#login-form", state="visible", timeout=10000)


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
        "AP04_PASSWORD": "e2e-pass",
        "ADMIN_PASSWORD": "e2e-pass",
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
            page.on("dialog", lambda d: d.accept())  # 自動接受 confirm（正式匯入）

            # 1) 登入 ap02（主管）
            page.goto(BASE + "/")
            login(page, "ap02", "e2e-pass")
            results.append(("登入 ap02 並保持登入", True))

            # 2) 新增案件（審核中 + 下一步 + 備註）：表單平常收合，先點「＋ 新增」展開
            page.click('[data-form-toggle="case-form"]')
            page.wait_for_timeout(200)
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
            page.click('[data-form-toggle="contract-form"]')
            page.wait_for_timeout(200)
            page.fill('#contract-form input[name="contract_code"]', "E2E-CON-1")
            page.fill('#contract-form input[name="contract_name"]', "E2E 合約")
            page.click('#contract-form button[type="submit"]')
            page.wait_for_timeout(700)
            results.append(("新增合約出現在真清單", "E2E-CON-1" in page.inner_text("#contracts")))

            # 3.6) 八大功能之一「預算」：模組已啟用（非「尚未啟用」），可新增
            page.click('a.module-card[href="#budget"]')
            page.wait_for_timeout(400)
            results.append(("預算模組已啟用(非尚未啟用)", not page.is_visible("#module-unbuilt")))
            page.click('[data-form-toggle="budget-form"]')
            page.wait_for_timeout(200)
            page.fill('#budget-form input[name="budget_code"]', "E2E-BUD-1")
            page.fill('#budget-form input[name="category"]', "基礎建設")
            page.fill('#budget-form input[name="amount"]', "26742000")
            page.click('#budget-form button[type="submit"]')
            page.wait_for_timeout(700)
            results.append(("新增預算出現在真清單", "E2E-BUD-1" in page.inner_text("#budgets")))

            # 3.65) Excel 正式匯入：資料管理 → 資料檢核磚塊 → 預覽 → 試算 → 正式匯入 → 案件寫入
            page.click('a.module-card[href="#data-admin"]')
            page.wait_for_timeout(300)
            page.click('.admin-tile[data-open-panel="data-review"]')
            page.wait_for_timeout(400)
            page.click('#import-preview-form button[type="submit"]')
            page.wait_for_timeout(700)
            page.click("#dry-run-cases")
            page.wait_for_timeout(700)
            page.click("#formal-import-cases")
            page.wait_for_timeout(900)
            results.append(("正式匯入完成回饋", "正式匯入完成" in page.inner_text("#formal-import-result")))
            page.click('a.module-card[href="#cases-module"]')
            page.wait_for_timeout(500)
            results.append(("匯入的案件進入清單(CASE-SAMPLE-001)", "CASE-SAMPLE-001" in page.inner_text("#cio-cases-body")))

            # 3.66) CSV 匯出：資料管理 → 匯入／匯出 → 下載案件 CSV，驗證真的觸發下載且內容含剛建的案件
            page.click('a.module-card[href="#data-admin"]')
            page.wait_for_timeout(300)
            page.click('.admin-tile[data-open-panel="io-center"]')
            page.wait_for_timeout(400)
            with page.expect_download() as dl_info:
                page.click('[data-export="/api/cases.csv"]')
            download = dl_info.value
            results.append(("匯出 CSV 觸發下載且檔名正確", download.suggested_filename == "cases.csv"))
            csv_path = download.path()
            csv_text = csv_path.read_text(encoding="utf-8-sig") if csv_path else ""
            results.append(("匯出的 CSV 含剛建立的案件", "E2E-001" in csv_text))
            results.append(("匯出的 CSV 含正確表頭", "案件編號" in csv_text))

            # 3.67) 單位主檔：主動新增單位（撞名擋下）→ 出現在預算單位下拉
            page.click('a.module-card[href="#data-admin"]')
            page.wait_for_timeout(300)
            page.click('.admin-tile[data-open-panel="unit-admin"]')
            page.wait_for_timeout(400)
            page.fill('#unit-create-form input[name="canonical_code"]', "E2E-U1")
            page.fill('#unit-create-form input[name="canonical_name"]', "E2E驗證單位")
            page.click('#unit-create-form button[type="submit"]')
            page.wait_for_timeout(600)
            results.append(("新增單位成功回饋", "已新增" in page.inner_text("#unit-create-status")))
            results.append(("新增單位出現在單位主檔清單", "E2E驗證單位" in page.inner_text("#unitmaster-result")))
            # 撞名應被擋下
            page.fill('#unit-create-form input[name="canonical_name"]', "E2E驗證單位")
            page.click('#unit-create-form button[type="submit"]')
            page.wait_for_timeout(600)
            results.append(("撞名新增被擋下", "已存在" in page.inner_text("#unit-create-status")))
            # 預算表單的單位下拉應該吃得到新單位
            page.click('a.module-card[href="#budget"]')
            page.wait_for_timeout(300)
            page.click('[data-form-toggle="budget-form"]')
            page.wait_for_timeout(200)
            unit_options = page.locator('#budget-form select[name="unit_name"] option').all_inner_texts()
            results.append(("預算單位下拉含新單位", "E2E驗證單位" in unit_options))

            # 3.68) 人員主檔：主動新增人員（撞名擋下）→ 出現在案件負責人下拉
            page.click('a.module-card[href="#data-admin"]')
            page.wait_for_timeout(300)
            page.click('.admin-tile[data-open-panel="personnel-admin"]')
            page.wait_for_timeout(400)
            page.fill('#personnel-create-form input[name="name"]', "E2E驗證人員")
            page.click('#personnel-create-form button[type="submit"]')
            page.wait_for_timeout(600)
            results.append(("新增人員成功回饋", "已新增" in page.inner_text("#personnel-create-status")))
            results.append(("新增人員出現在人員名單", "E2E驗證人員" in page.inner_text("#personnelmaster-result")))
            page.fill('#personnel-create-form input[name="name"]', "E2E驗證人員")
            page.click('#personnel-create-form button[type="submit"]')
            page.wait_for_timeout(600)
            results.append(("撞名新增人員被擋下", "已存在" in page.inner_text("#personnel-create-status")))
            page.click('a.module-card[href="#cases-module"]')
            page.wait_for_timeout(300)
            page.click('[data-form-toggle="case-form"]')
            page.wait_for_timeout(200)
            owner_options = page.locator('#case-form select[name="owner"] option').all_inner_texts()
            results.append(("案件負責人下拉含新人員", "E2E驗證人員" in owner_options))
            # 下拉第一個選項要保留各表單自己的欄位標籤（負責人），不能被灌選項時整批蓋成同一句「（未選擇）」
            results.append(("負責人下拉第一項保留欄位標籤", owner_options[0] == "（未選擇）負責人"))
            # 所屬年度也要能用下拉選（不是自由輸入）
            year_options = page.locator('#case-form select[name="fiscal_year"] option').all_inner_texts()
            results.append(("所屬年度改成下拉且有多個年度可選", len(year_options) >= 4))

            # 3.69) 案名沿用：合約表單選了案子、名稱欄位是空的 → 自動帶入案名（仍可改）
            page.fill('#case-form input[name="case_code"]', "E2E-NAMEFILL")
            page.fill('#case-form input[name="title"]', "案名沿用驗證案")
            page.click("#submit-case")
            page.wait_for_timeout(700)
            page.click('a.module-card[href="#contracts-module"]')
            page.wait_for_timeout(300)
            page.click('[data-form-toggle="contract-form"]')
            page.wait_for_timeout(200)
            page.select_option('#contract-form select[name="case_id"]', label="E2E-NAMEFILL｜案名沿用驗證案")
            page.wait_for_timeout(200)
            results.append(("選案後合約名稱自動帶入案名", page.input_value('#contract-form input[name="contract_name"]') == "案名沿用驗證案"))

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
            # 催辦清單：demo 有一筆逾期案件（DEMO-C01）；等 refresh 載入完成
            page.wait_for_timeout(1000)
            results.append(("催辦清單出現逾期項目", "已逾期" in page.inner_text("#reminders-list")))
            results.append(("主管儀表板出現圖表(SVG)", page.locator("#manager-charts svg").count() >= 1))
            # 側欄全文搜尋（接了 /api/search）：搜 DEMO 有結果
            page.fill("#global-search", "DEMO")
            page.wait_for_timeout(600)
            results.append(("全文搜尋有結果", "DEMO-" in page.inner_text("#search-results-main")))
            page.fill("#global-search", "")
            page.click('button[data-case-tab="list"]')
            page.wait_for_timeout(600)
            results.append(("示範案件進入案件清單(DEMO-)", "DEMO-" in page.inner_text("#cio-cases-body")))

            # 3.75) 未歸戶付款：合約 E2E-CON-1 沒關聯案件，替它建一筆付款 → 主管儀表板「未歸戶付款」面板要看得到
            contract_id = page.evaluate(
                """async () => {
                    const r = await fetch('/api/contracts');
                    const d = await r.json();
                    const c = (d.data || []).find(x => x.contract_code === 'E2E-CON-1');
                    return c ? c.id : null;
                }"""
            )
            results.append(("取得未關聯案件的合約 ID(E2E-CON-1)", contract_id is not None))
            page.click('a.module-card[href="#payments-module"]')
            page.wait_for_timeout(300)
            page.click('[data-form-toggle="payment-form"]')
            page.wait_for_timeout(200)
            page.fill('#payment-form input[name="contract_id"]', str(contract_id))
            page.fill('#payment-form input[name="payment_month"]', "2026-08")
            page.fill('#payment-form input[name="payment_amount"]', "1000")
            page.click('#payment-form button[type="submit"]')
            page.wait_for_timeout(700)
            page.click('a.module-card[href="#cases-module"]')
            page.wait_for_timeout(300)
            page.click('button[data-case-tab="dashboard"]')
            page.wait_for_timeout(400)
            results.append(("未歸戶付款面板出現", page.is_visible("#orphan-payments")))
            results.append(("未歸戶付款徽章顯示筆數", page.is_visible("#orphan-payments-count")))
            results.append(("未歸戶付款列出無案合約", "E2E-CON-1" in page.inner_text("#orphan-payments-list")))

            # 3.76) 催辦通知按鈕：點「產生催辦通知」→ 站內預覽出現內容（未設 SMTP，只預覽不真寄）
            page.click("#notify-reminders")
            page.wait_for_timeout(600)
            results.append(("催辦通知按鈕產生預覽內容", len(page.inner_text("#notify-preview").strip()) > 0))
            page.click('button[data-case-tab="list"]')
            page.wait_for_timeout(300)

            # 3.77) 一條龍新案精靈：單頁多步驟，勾④合約才能勾⑤付款；送出後自動串 case_id/contract_id
            page.click('button[data-case-tab="wizard"]')
            page.wait_for_timeout(300)
            wiz = page.locator('[data-case-panel="wizard"]')
            results.append(("付款開關預設鎖定(未勾合約)", wiz.locator('[data-wizard-toggle="payment"]').is_disabled()))
            wiz.locator('[data-wizard-step="case"] input[name="case_code"]').fill("E2E-WIZ")
            wiz.locator('[data-wizard-step="case"] input[name="title"]').fill("精靈E2E驗證案")
            wiz.locator('[data-wizard-toggle="contract"]').check()
            results.append(("勾⑤合約後付款開關解鎖", not wiz.locator('[data-wizard-toggle="payment"]').is_disabled()))
            wiz.locator('[data-wizard-step="contract"] input[name="contract_code"]').fill("K-E2E-WIZ")
            wiz.locator('[data-wizard-step="contract"] input[name="contract_name"]').fill("精靈E2E合約")
            wiz.locator('[data-wizard-toggle="payment"]').check()
            wiz.locator('[data-wizard-step="payment"] input[name="payment_month"]').fill("2026-09")
            wiz.locator('[data-wizard-step="payment"] input[name="payment_amount"]').fill("8000")
            page.click('#wizard-form button[type="submit"]')
            page.wait_for_timeout(900)
            results.append(("精靈送出成功", "全部建立成功" in page.inner_text("#wizard-status")))
            results.append(("精靈結果顯示合約與付款", "K-E2E-WIZ" in page.inner_text("#wizard-result") and "2026-09" in page.inner_text("#wizard-result")))
            results.append(("精靈送出後表單重置(收合)", wiz.locator('[data-wizard-step="contract"] .wizard-step-body').is_hidden()))
            page.click('button[data-case-tab="list"]')
            page.wait_for_timeout(400)
            results.append(("精靈建立的案件出現在案件清單", "E2E-WIZ" in page.inner_text("#cio-cases-body")))

            # 3.8) 待我複核佇列（主管儀表板小面板）：ap03 建案送出 → ap02 在面板核准（非案件列核准鈕）
            logout(page)
            login(page, "ap03", "e2e-pass")
            page.click('[data-form-toggle="case-form"]')
            page.wait_for_timeout(200)
            page.fill('#case-form input[name="case_code"]', "E2E-Q1")
            page.fill('#case-form input[name="title"]', "待複核佇列測試")
            page.click("#submit-case")
            page.wait_for_timeout(700)
            q1 = page.locator("#cases .row", has_text="E2E-Q1")
            q1.get_by_role("button", name="送出複核").click()
            page.wait_for_timeout(600)
            logout(page)
            login(page, "ap02", "e2e-pass")
            page.click('button[data-case-tab="dashboard"]')
            page.wait_for_timeout(400)
            results.append(("待我複核佇列出現他人送出的案件", "E2E-Q1" in page.inner_text("#pending-approvals-list")))
            results.append(("待我複核徽章顯示筆數", page.is_visible("#pending-approvals-count")))
            page.locator("#pending-approvals-list li", has_text="E2E-Q1").get_by_role("button", name="核准").click()
            page.wait_for_timeout(700)
            results.append(("面板核准後從待複核佇列移除", "E2E-Q1" not in page.inner_text("#pending-approvals-list")))
            page.click('button[data-case-tab="list"]')
            page.wait_for_timeout(400)
            results.append(("面板核准後案件狀態為已核准", "已核准" in page.locator("#cases .row", has_text="E2E-Q1").inner_text()))

            # 3.91) 追溯鏈：案件列「追溯鏈」按鈕 → 整條控管鏈(含預算/專案，先前漏接、這次補上)
            row_wiz = page.locator("#cases .row", has_text="E2E-WIZ")
            row_wiz.get_by_role("button", name="追溯鏈").click()
            page.wait_for_timeout(500)
            trace_text = page.inner_text("#case-trace")
            results.append(("追溯鏈顯示預算節點", "預算" in trace_text))
            results.append(("追溯鏈顯示專案節點", "專案" in trace_text))
            results.append(("追溯鏈顯示精靈建立的合約", "K-E2E-WIZ" in trace_text))

            # 3.9) 雙人複核（案件列按鈕路徑）：ap02 送出 E2E-001 → 待複核；建立者不能自己核；ap04 核准 → 已核准
            row = page.locator("#cases .row", has_text="E2E-001")
            row.get_by_role("button", name="送出複核").click()
            page.wait_for_timeout(600)
            row = page.locator("#cases .row", has_text="E2E-001")
            results.append(("送出後狀態為待複核", "待複核" in row.inner_text()))
            results.append(("建立者看不到自己案件的核准鈕", row.get_by_role("button", name="核准").count() == 0))
            logout(page)
            login(page, "ap04", "e2e-pass")
            page.wait_for_timeout(500)
            row4 = page.locator("#cases .row", has_text="E2E-001")
            row4.get_by_role("button", name="核准").click()
            page.wait_for_timeout(600)
            results.append(("另一助理核准後狀態為已核准", "已核准" in page.locator("#cases .row", has_text="E2E-001").inner_text()))

            # 4) 換 CIO（極簡）：只看到決策總覽，其他模組與建案表單完全隱藏
            page.click('a.module-card[href="#cases-module"]')
            page.wait_for_timeout(300)
            logout(page)
            login(page, "ap01", "e2e-pass")
            page.wait_for_timeout(500)
            results.append(("CIO 看得到決策總覽", page.is_visible('a.module-card[href="#cio-overview"]')))
            results.append(("CIO 看不到合約模組(完全隱藏)", not page.is_visible('a.module-card[href="#contracts-module"]')))
            results.append(("CIO 落在決策總覽面板", page.is_visible("#cio-overview")))
            results.append(("CIO 沒有建案表單(唯讀+隱藏)", not page.is_visible("#case-form")))
            results.append(("CIO 資金看板顯示要準備的資金", "要準備的資金" in page.inner_text("#cio-metrics")))
            page.wait_for_timeout(500)
            results.append(("CIO 決策總覽出現圖表(SVG)", page.locator("#cio-charts svg").count() >= 1))
            results.append(("CIO 看板有預算外卡片", "下月預算外" in page.inner_text("#cio-metrics")))

            # 5) 系統管理後台：admin 登入 → 見系統管理 → 存 SMTP 設定 → 持久
            logout(page)
            login(page, "admin", "e2e-pass")
            page.wait_for_timeout(500)
            results.append(("admin 看得到系統管理", page.is_visible('a.module-card[href="#admin-console"]')))
            results.append(("admin 落在系統管理面板", page.is_visible("#admin-console")))
            results.append(("admin 看不到案件管理", not page.is_visible('a.module-card[href="#cases-module"]')))
            page.fill('#admin-settings-form input[name="smtp_host"]', "mail.e2e.local")
            page.click('#admin-settings-form button[type="submit"]')
            page.wait_for_timeout(600)
            results.append(("儲存 SMTP 設定成功", "已儲存" in page.inner_text("#admin-settings-status")))
            results.append(("系統狀態顯示 SMTP 已設定", "已設定" in page.inner_text("#admin-status")))
            # 帳號管理：新增一個承辦帳號
            page.fill('#admin-user-form input[name="username"]', "e2euser")
            page.select_option('#admin-user-role', "handler")
            page.fill('#admin-user-form input[name="password"]', "E2e!pass1")
            page.click('#admin-user-form button[type="submit"]')
            page.wait_for_timeout(600)
            results.append(("新增帳號出現在清單", "e2euser" in page.inner_text("#admin-users-body")))
            results.append(("備份按鈕存在", page.is_visible("#admin-backup")))

            try:
                browser.close()
            except Exception as exc:
                print(f"(browser.close 警告，不影響結果判定: {exc})")

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
