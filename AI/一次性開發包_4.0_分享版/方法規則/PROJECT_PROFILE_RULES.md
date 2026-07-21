# PROJECT_PROFILE_RULES

本檔定義如何把 v2.1 All-in-One Build Pack 套用到不同專案。

## 自動偵測

先跑：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\detect_project_profile.ps1
```

輸出：

```text
logs\project_profile.json
```

## Profile 用途

Profile 會記錄：

- 語言。
- framework。
- 可用測試命令。
- 可用 CI 命令。
- 預設風險邊界。

## 非 Python / 非 Web 專案

若偵測到不是 Python / Web：

- 保留 v2.1 的切片、audit、資安與正式資料規則。
- 替換測試命令。
- 替換 build / lint / package 命令。
- 保留 Fast / Standard / Release Lane 概念。

不得因為專案類型不同就跳過 audit 或安全邊界。
