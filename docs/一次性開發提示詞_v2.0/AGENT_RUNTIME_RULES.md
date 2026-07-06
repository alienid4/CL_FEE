# AGENT_RUNTIME_RULES

本檔定義 v2.0 的一鍵自動開發 runtime 入口。

目前採最小可執行 runtime，不假裝已是完整平台。

## 一鍵入口

低風險切片可執行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\agent_runtime_once.ps1 -Goal "..." -Lane fast
```

一般切片可執行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\agent_runtime_once.ps1 -Goal "..." -Lane standard
```

Release 前檢查可執行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\agent_runtime_once.ps1 -Goal "..." -Lane release
```

## Runtime 做什麼

1. 偵測專案 profile。
2. 依速度檔執行驗證。
3. 寫入 audit log。
4. 執行 audit gate。
5. 寫入 `logs\agent_runtime_state.json`。

## v2.1 本機控制台

本機控制台入口：

```text
http://127.0.0.1:8888/dev-console
```

API：

```text
GET /api/dev-console/status
POST /api/dev-console/run
```

控制台 MVP 只能執行白名單命令：

- Fast CI
- Local CI
- Deep Security
- Project Profile
- Runtime Fast
- Audit Summary

不得讓 UI 傳入任意 shell command。
不得新增正式部署、正式資料、憑證、不可逆 migration 按鈕。

## Runtime 不做什麼

- 不自動碰正式資料。
- 不自動部署。
- 不自動改憑證。
- 不自動做不可逆 migration。
- 不取代人類對重大業務規則的決策。

## 升級方向

下一階段可加入：

- retry policy。
- structured failure parser。
- code patch queue。
- sandbox execution。
- 多 agent 分工。
- 平台 CI status 回寫。
