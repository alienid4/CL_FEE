# Change Size Policy

用來判斷這次修改要走快速流程還是完整流程。

## Small

範圍：

- 文案。
- 小型 UI 呈現。
- 單一欄位排序或標籤。
- 不改資料模型、不改部署。

最低要求：

- Smoke test。
- 截圖或簡短驗證。
- release note。

## Medium

範圍：

- API 行為。
- 資料轉換。
- 狀態流程。
- 多個畫面連動。

最低要求：

- Targeted tests。
- Smoke test。
- 影響面說明。
- rollback note。

## Large

範圍：

- 資料庫 migration。
- 權限或帳號。
- 部署方式。
- 批次寫入正式資料。
- 安全或敏感資料處理。

最低要求：

- Full test 或合理替代驗證。
- 備份與 rollback。
- 人工核准。
- 安全檢查。
- 交接文件更新。
