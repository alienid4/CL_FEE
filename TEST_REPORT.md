# CL_FEE 測試報告

基準：HEAD。**119 pytest 全過 + 25 項 Playwright E2E 全過。**

## 怎麼跑
```bash
python -m pytest -q          # 119 passed
python tests/e2e_ui.py       # 25 項真瀏覽器 E2E 全部通過
python .project/checks.py    # C1 關卡：git/密鑰/測試/決策一致 全 PASS
```

## 單元/整合測試涵蓋（tests/）
| 檔案 | 涵蓋 |
|---|---|
| test_fresh_app | 首頁/OpenAPI/登入帳號/狀態字典驗證/稽核 |
| test_row_scope | 承辦 owner 隔離（讀+寫） |
| test_case_approval | 雙人複核：送出/核准/不能自核/另一助理可核/承辦-CIO 不能核/擋直接設已核准 |
| test_cio_overview | 決策總覽：只算已核准/下探完整鏈/預算外/CIO 模組極簡/承辦範圍 |
| test_new_modules | 預算/專案/簽呈/請購 CRUD+狀態驗證+需登入+關聯/隔離/FK 檢查/搜尋 |
| test_reminders | 逾期催辦：案件/合約/專案、已完成排除、承辦範圍 |
| test_review_fixes | 多月預測/超支/未歸戶付款/待我複核/CSV 匯出/催辦通知預覽 |
| test_seed_data | 示範資料載入/清空/只刪 DEMO-/不碰真資料/權限 |
| test_monthly_spending / test_expiring_contracts / test_export_cases | 月度支出/到期合約/案件匯出 |
| test_session_expiry / test_env_loader | session 過期/.env 載入 |
| test_case_note_fields / test_contract_amount_optional / test_todo | 備註下一步/合約金額可空/待辦 |
| test_c1_review_findings | 前兩輪多 agent 審查發現項的回歸鎖 |
| ui_documents_regression / ui_import_preview_regression | 前端結構回歸 |

## 端到端（tests/e2e_ui.py，真 Chromium）
登入 → 建案 → 待辦 → 合約模組假→真 → 預算模組啟用+新增 → 示範資料載入 →
催辦逾期 → 主管圖表 → 雙人複核（送出→待複核→建立者無核准鈕→ap04 核准→已核准）→
CIO 極簡（只見決策總覽、其他隱藏、無建案表單、資金看板+圖表+預算外卡片）。

## 誠實原則
- 不以「測試通過」為唯一證據；每次 commit 均經 C1 checks（git 版控 + 密鑰掃描 +
  pytest + 決策↔文件一致）全 PASS 才放行，並留 commit 軌跡。
- E2E 用真瀏覽器，非嵌入式預覽（後者因第三方 cookie 限制無法保持登入）。
