# Security Scanning Rules

弱點掃描分成白箱與黑箱，兩者用途不同。

## 白箱

白箱從程式碼、套件與設定檢查：

- SAST。
- Dependency vulnerability。
- Secret scan。
- License scan。
- Config / IaC scan。
- SQL injection pattern。
- 權限與資料流檢查。

## 黑箱

黑箱從外部使用者視角檢查：

- TLS / certificate。
- HTTP security headers。
- Auth / session。
- Rate limit。
- Error leakage。
- Port exposure。
- DAST。

## 發版要求

小修：

- Secret scan。
- 受影響功能 smoke test。

中修：

- Secret scan。
- Dependency scan。
- API / UI regression。

大修：

- Secret scan。
- Dependency scan。
- SAST 或替代檢查。
- 黑箱 smoke 或 DAST。
- Rollback note。

