# SECURITY_SCAN_RULES

本檔定義 AI_FEE 的漏洞掃描與白箱 / 黑箱安全檢查。

日常資安底線請看 `SECURITY_RULES.md`。

## 掃描分級

### 小修

適用：

- 文件小修
- 測試設定修正
- 明確 UI bug
- 不碰資料模型、權限、DB、部署

檢查：

- 確認未新增敏感資料。
- 確認未誤用 archive。
- 一般不需要完整白箱 / 黑箱掃描。

### 中型功能

適用：

- 新增 API
- 新增 UI 表單
- 修改資料寫入流程
- 新增匯出或查詢能力

白箱檢查：

- secret scan：檢查是否新增 key、token、密碼、`.env`。
- dependency check：檢查新依賴是否有已知漏洞。
- SAST / code review：檢查 SQL injection、command injection、path traversal、unsafe deserialization。
- 錯誤訊息：不得洩漏 stack trace、DB path、憑證、內部路徑。

### 大型 / 高風險功能

適用：

- 登入 / 權限 / AD / SSO
- MSSQL adapter
- Excel 匯入 / 回匯
- 部署流程
- 對外服務
- 正式資料路徑

白箱檢查：

- secret scan
- dependency vulnerability scan
- SAST
- 權限與角色邏輯審查
- audit log 完整性檢查
- 匯入 / 回匯防覆蓋檢查
- DB query 與 migration 風險檢查

黑箱檢查：

- DAST 或等效 HTTP 探測
- 未授權 API 探測
- 登入 / session / role bypass 檢查
- HTTP security headers 檢查
- CORS 檢查
- TLS 檢查，若是 HTTPS 環境
- error leakage 檢查
- rate limit / brute force 風險評估

## Release 前最低檢查

release 或部署前至少確認：

- 沒有敏感資料進 Git。
- `.env`、DB、log、Excel、PDF 未被 commit。
- archive 未被主程式引用。
- 測試已通過。
- FastAPI debug / reload / error 設定符合目標環境。
- 權限未只靠前端控制。
- rollback 或恢復方式已記錄。

## 建議命令與方式

可依專案環境選用：

```powershell
git status --short
git diff --check
pytest -q
pytest tests -q
```

敏感字串檢查可用 `rg`：

```powershell
rg -n "password|passwd|secret|token|api[_-]?key|private key|BEGIN RSA|BEGIN OPENSSH|connection string|Trusted_Connection|User ID|UID=|PWD=" .
```

若新增 Python 依賴，需檢查 dependency 風險。
若工具不可用，回報「未能執行」與替代檢查方式，不得假裝已掃描。

## 回報格式

```text
資安掃描：
- 分級：小修 / 中型 / 大型 / 高風險
- 白箱檢查：已執行 / 未執行，證據
- 黑箱檢查：已執行 / 未執行，原因
- 敏感資料：未發現 / 發現並處理
- 剩餘風險：
```
