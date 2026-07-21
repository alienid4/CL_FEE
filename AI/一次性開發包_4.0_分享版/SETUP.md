# SETUP — 3 步把這包裝進你的專案

假設你的專案在 `你的專案/`，把這包放旁邊。

## 1. 引擎放進 .project/

把本包 `pipeline/` 底下所有檔，複製到你專案的 `.project/`：

**Windows PowerShell**
```powershell
New-Item -ItemType Directory -Force 你的專案\.project | Out-Null
Copy-Item .\pipeline\* 你的專案\.project\ -Force
```
**Mac / Linux / Git Bash**
```bash
mkdir -p 你的專案/.project && cp pipeline/* 你的專案/.project/
```

## 2. 建立 git（自主開發的安全網）

```bash
cd 你的專案
git init            # 若還不是 git 專案
git add -A && git commit -m "init: 導入 4.0 開發包"
```

（建議也把 `.project/pre-commit` 掛成 git hook，讓每次 commit 自動跑 checks。若沒有，loop.py 也會在 commit 前先跑 checks。）

## 3. 填你的 AI CLI（loop.py 要靠它做每件事）

編輯 `.project/loop_config.json` 的 `agent_cmd`：

| 你用的工具 | 填法 |
|---|---|
| Claude Code | `"agent_cmd": "claude -p --permission-mode acceptEdits"` |
| OpenAI Codex | `"agent_cmd": "codex exec --full-auto"` |
| 先只測骨架 | 留空 `""`（loop 會跑但不真的呼叫 AI） |

若 AI 因權限改不了檔，Claude 可改用 `claude -p --dangerously-skip-permissions`（因為 loop 只在工作分支跑、又有 checks 擋）。

---

## 驗證它真的能自主跑

```bash
git checkout -b work/test-loop        # loop 拒絕在 main/master 跑
python .project/loop.py --dry-run     # ① 先看骨架：讀待辦、看煞車，不動東西
python .project/loop.py --once        # ② 真的跑一件：看它自己改檔→過 checks→commit
```

看到「你沒插手，它卻做完並 commit」= 自主成功。
再 `python .project/loop.py` 放它一路跑，你走開，回來看 `.project/run_report.md`。

## 常見卡關

| 症狀 | 解 |
|---|---|
| loop 說在保護分支拒跑 | 先 `git checkout -b work/xxx` |
| 認證 401 | 你的 AI CLI 沒登入，先登入一次 |
| AI 改不了檔 | agent_cmd 加 `--dangerously-skip-permissions`（Claude）|
| checks 一直 FAIL | 它會重試到上限→標 blocked、寫進 decisions.json（這是機制在運作）|
