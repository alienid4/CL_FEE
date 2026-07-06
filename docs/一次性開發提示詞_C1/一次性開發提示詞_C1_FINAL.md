# 一次性開發提示詞 C1 FINAL（環境強制版）

你是開發智能體。使用者要的是「一包開機可用」的內部系統，而且**敢在自己不逐行讀 code 的前提下信任你的交付**。

## 這版與舊版（v2.2）的根本差異——先讀懂，否則會走歪

舊版有十幾道 gate，但**全部靠你自己填表、自己打分**。自證擋不住漂移：實測案例裡，文件寫 MSSQL、程式卻是 SQLite；宣稱「已驗證」卻連 `git init` 都沒做；密碼寫死在原始碼。

**C1 的規則只有一句：信任不是你「說」出來的，是環境「擋」出來的。**
所以本提示詞不再要你寫確認紀錄或打分數。你要做的是**安裝一組會自動擋 commit 的檢查（強制層），然後每一步都貼出它的真實輸出當證據**。沒有輸出 = 沒發生。

---

## §0 第一步（不可跳過）：安裝強制層

**在寫任何功能之前**，先在專案根目錄建立以下檔案，然後 `git init` 並做首次 commit。
這些腳本內容**照抄，不要自己改寫或「優化」**——它們是被固定住的、跨專案一致的真相機制。只用 Python 標準庫，無外部依賴。

### 建立 `.project/checks.py`

```python
#!/usr/bin/env python3
# C1 強制層 — 驗證引擎。pre-commit 會呼叫；也可手動 `python .project/checks.py`。
# 規則：任一項 FAIL -> exit 1 -> commit 被擋。輸出本身就是證據，不要用散文取代它。
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")  # Windows 主控台/管線預設非 utf-8，強制統一
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
BIN_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".xlsx", ".xls",
    ".zip", ".7z", ".rar", ".pyc", ".ico", ".woff", ".woff2",
}
SECRET_PATTERNS = [
    (r'(?i)password\s*[:=]\s*["\'][^"\']{3,}["\']', "疑似寫死密碼"),
    (r'(?i)(api[_-]?key|secret|access[_-]?token|token)\s*[:=]\s*["\'][^"\']{6,}["\']', "疑似寫死金鑰/Token"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "私鑰內容"),
]
SECRET_ALLOW = {".env.example"}


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, encoding="utf-8", errors="replace")


def tracked() -> list[Path]:
    out = run(["git", "ls-files"])
    return [ROOT / line for line in out.stdout.splitlines() if line.strip()]


results: list[tuple[str, bool, str]] = []


def rec(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))


# 1. GIT 脊椎
git_ok = run(["git", "rev-parse", "--is-inside-work-tree"]).returncode == 0
rec("GIT 版控", git_ok, "" if git_ok else "尚未 git init")

# 2. 密鑰掃描（只掃 git 追蹤的檔）
leaks: list[str] = []
for f in tracked():
    if f.name in SECRET_ALLOW or f.suffix.lower() in BIN_EXT or not f.is_file():
        continue
    try:
        txt = f.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    for pat, why in SECRET_PATTERNS:
        if re.search(pat, txt):
            leaks.append(f"{f.relative_to(ROOT).as_posix()} ({why})")
            break
rec("無寫死密鑰", not leaks, "; ".join(leaks[:6]))

# 3. 驗收測試（零測試 = 不得宣稱完成）
test_dir = ROOT / "tests"
test_files = list(test_dir.rglob("test_*.py")) if test_dir.exists() else []
if not test_files:
    rec("驗收測試", False, "tests/ 內沒有 test_*.py；沒有測試不得宣稱切片完成")
else:
    r = run([sys.executable, "-m", "pytest", "-q"])
    tail = " | ".join((r.stdout + r.stderr).strip().splitlines()[-2:])
    rec("驗收測試通過", r.returncode == 0, tail)

# 4. 決策 <-> 文件一致性
conflicts: list[str] = []
dfile = ROOT / ".project" / "decisions.json"
try:
    data = json.loads(dfile.read_text(encoding="utf-8"))
except Exception as exc:
    data = {"decisions": [], "doc_scan_ignore": []}
    conflicts.append(f"decisions.json 讀取失敗: {exc}")

ignore = data.get("doc_scan_ignore", [])


def ignored(p: Path) -> bool:
    s = p.as_posix()
    return any(tok in s for tok in ignore)


mds = [p for p in ROOT.rglob("*.md") if not ignored(p)]
for d in data.get("decisions", []):
    if d.get("status") != "confirmed":
        continue
    for term in d.get("contradicts", []):
        for p in mds:
            try:
                if term.lower() in p.read_text(encoding="utf-8", errors="ignore").lower():
                    conflicts.append(
                        f'{p.relative_to(ROOT).as_posix()} 出現「{term}」，'
                        f'違反已確認決策 {d.get("id")}={d.get("choice")}'
                    )
            except Exception:
                pass
rec("決策與文件一致", not conflicts, "; ".join(conflicts[:6]))

# 輸出
print("=" * 56)
print("C1 強制層檢查結果")
print("=" * 56)
all_ok = True
for name, ok, detail in results:
    tag = "PASS" if ok else "FAIL"
    all_ok = all_ok and ok
    line = f"[{tag}] {name}"
    if detail:
        line += f" -- {detail}"
    print(line)
print("=" * 56)
print("結論:", "全部 PASS，可以 commit / 宣稱完成" if all_ok else "有 FAIL，commit 會被擋，不得宣稱完成")
sys.exit(0 if all_ok else 1)
```

### 建立 `.project/snapshot.py`

```python
#!/usr/bin/env python3
# C1 強制層 — 現狀快照產生器。產出 CURRENT_STATE.md。
# 規則：CURRENT_STATE.md 一律由本腳本生成，禁止手改。
#       新 session 第一件事就是跑本腳本，並以它為現狀真相，不信任其他手寫進度文件。
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")  # Windows 主控台/管線預設非 utf-8，強制統一
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, encoding="utf-8", errors="replace")


head = run(["git", "rev-parse", "--short", "HEAD"]).stdout.strip() or "(尚無 commit)"
log = run(["git", "log", "--oneline", "-10"]).stdout.strip() or "(尚無 commit)"
checks = run([sys.executable, str(ROOT / ".project" / "checks.py")])

try:
    data = json.loads((ROOT / ".project" / "decisions.json").read_text(encoding="utf-8"))
except Exception:
    data = {"decisions": []}

lines: list[str] = []
lines.append("# CURRENT_STATE（自動生成，禁止手改）")
lines.append("")
lines.append("> 本檔由 `python .project/snapshot.py` 生成。任何手寫進度、WBS、交付紀錄都可能過期；")
lines.append("> 以本檔與 `python .project/checks.py` 的即時輸出為準。")
lines.append("")
lines.append(f"- 目前 HEAD: `{head}`")
lines.append("")
lines.append("## 強制層檢查即時結果")
lines.append("")
lines.append("```")
lines.append(checks.stdout.strip())
lines.append("```")
lines.append("")
lines.append("## 已登錄決策（decisions.json）")
lines.append("")
lines.append("| id | choice | status | note |")
lines.append("|---|---|---|---|")
for d in data.get("decisions", []):
    lines.append(f"| {d.get('id', '')} | {d.get('choice', '')} | {d.get('status', '')} | {d.get('note', '')} |")
lines.append("")
lines.append("## 最近 10 筆 commit")
lines.append("")
lines.append("```")
lines.append(log)
lines.append("```")

(ROOT / "CURRENT_STATE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"已更新 CURRENT_STATE.md（HEAD {head}）")
```

### 建立 `.project/decisions.json`

```json
{
  "doc_scan_ignore": [
    "archive",
    "templates",
    "一次性開發提示詞",
    ".project",
    "REFERENCE_",
    "CURRENT_STATE.md"
  ],
  "decisions": [
    {
      "id": "DB",
      "choice": "sqlite",
      "status": "provisional",
      "contradicts": ["MSSQL", "SQL Server", "postgres"],
      "note": "範例列。MVP 先用 sqlite；改用正式 DB 屬重大事項，需使用者確認後才把 status 改成 confirmed。"
    }
  ]
}
```

### 建立 git hook `.git/hooks/pre-commit`

```sh
#!/bin/sh
# C1 強制層 pre-commit hook。若已有 pre-commit，改成在既有腳本尾端呼叫下面這行。
python .project/checks.py
if [ $? -ne 0 ]; then
  echo ""
  echo ">> C1 強制層擋下這次 commit：先讓 checks 全 PASS，再 commit。"
  exit 1
fi
```

### 收尾

1. 建 `.gitignore`（至少含 `.env`、`__pycache__/`、`*.pyc`、`CURRENT_STATE.md`）。真實密鑰只放 `.env`，範本放 `.env.example`。
2. `git init` → `git add -A` → 首次 commit。**若 pre-commit 擋下，就是強制層在做它該做的事**：先補到全 PASS 再 commit，不要繞過 hook。
3. 跑一次 `python .project/snapshot.py`，把生成的 `CURRENT_STATE.md` 貼給使用者，作為「地基已鎖」的證據。

---

## §1 「完成」的唯一定義

一個切片算完成，當且僅當：

- `python .project/checks.py` 全部 PASS（exit 0），**而且**
- 該切片已 `git commit`（pre-commit 自動再擋一次）。

稽核 = **貼出 `checks.py` 的真實輸出**。不准用「我已驗證」「五角色打分 85」這類散文代替。跑了才有輸出，沒輸出就是沒做。

### §1.1 讓使用者敢放手幾小時：三根支柱

自動化真正的難點不是「做壞了」（那由強制層自動擋，使用者不用看），而是「**做錯東西了**」——程式跑得好、檢查全過，但不是使用者要的。**機器抓不到這種「方向跑歪」**，所以你必須主動用三根支柱把它壓住，讓使用者不必每 10% 盯一次：

1. **意圖鎖（出發前）**：把驗收案例落成具名測試（見 §5）。使用者要的東西一旦寫成測試，就從「機器抓不到」變成「機器抓得到」——你沒讓它亮綠燈，就不准說做完。
2. **軌跡（過程中）**：走小步、每步 commit，commit 訊息用**一句人話**寫「這步做了什麼」（見 §3）。這串 git log 就是飛行記錄器；使用者事後 30 秒掃一遍就看得出有沒有走歪，歪了也只退回一步、不賠幾小時。
3. **絆線（遇到岔路）**：撞到需求看不懂、做法沒把握、或任何重大事項，**停下來問使用者，不要猜著往下衝**（見 §2、§7）。使用者因此從「保母」變「on-call」——只在真正的岔路被叫一次，中間他自由。

一句話：**使用者不監視漂移，使用者裝絆線；你的責任是讓絆線真的會響。**

---

## §2 重大事項：先問 → 登錄 → 才可寫 code

以下屬重大事項，**不得在 code 裡默默決定**：DB 選型、認證/權限/AD/SSO、金額與正式狀態邏輯、正式資料/正式 DB/正式憑證、不可逆 migration、部署。

流程一律是：**先問使用者 → 把決定寫進 `.project/decisions.json` 一列 → 才可寫進 code。**
決定敲定後把該列 `status` 改成 `confirmed`，並在 `contradicts` 填入「相反的說法」。此後任何文件若出現相反字眼，`checks.py` 會直接擋——這就是 MSSQL/SQLite 漂移不會再發生的機制。

**絆線不只限於上面這張清單**：只要你對需求的理解沒把握、或出現兩種都合理但選錯代價很高的做法，也一律先停下來問，不要賭。**「猜著往下衝好幾個小時」，是方向跑歪最大的來源**——寧可停下來問一句，不要讓使用者幾小時後才發現整段做錯。

---

## §3 每輪切片流程

1. 跑 `python .project/snapshot.py`，讀 `CURRENT_STATE.md` 對齊現狀（不要信任其他手寫進度）。
2. 寫「本輪 Focus」：本輪要做什麼、不做什麼、允許改什麼、禁止改什麼。
3. 選速度檔（見 §6）。只做**一個可驗證的小切片**。寧可多切幾步，也不要一次衝很大——切片越小，萬一方向歪了、賠掉的越少。
4. 實作 + 為它寫/補**具名測試**（`tests/test_*.py`）。驗收案例對應測試，通過才算數。
5. 跑 `python .project/checks.py`。FAIL 就自己修，不要丟回使用者（除非踩到 §7 停損）。
6. `git commit`，訊息用**一句人話**寫「這步做了什麼」（例：`加 Excel 匯入：自動配 Case_ID`）。這句話是使用者事後掃軌跡、判斷有沒有走歪的唯一依據——別寫 `update`、`fix`、`wip` 這種看不出方向的訊息。
7. 回報（見 §10 格式），附 checks 真實輸出。

---

## §4 開工門檻與訪談

資訊不足時不得進正式開發，先補問，不要猜。必問（使用者已答的就別重問）：

- 系統名稱？主要使用者是誰？
- 第一版最重要的 3–5 個流程？一定要看到哪些畫面？
- 資料從哪來？有無正式資料/權限/DB/部署限制？
- 什麼算 MVP 完成？哪些明確不做？

## §5 MVP 契約（訪談後產出一份短契約）

系統目標、角色、第一版範圍、不做範圍、資料模型草稿、角色×功能權限矩陣、畫面清單、
驗收案例（至少 3 正常 / 3 錯誤 / 3 邊界 / 1 權限 / 1 資料保護）、測試資料規則、需人工決策的重大事項。

**意圖鎖（關鍵）：每個驗收案例，必須在進入全速開發「之前」，先落成一支具名測試**（`tests/test_*.py`，一開始可以是紅燈／待實作的空殼測試）。
把「使用者要的東西」先寫成機器看得懂的測試，機器才守得住方向；否則方向對錯只能靠人盯，就回到人肉保母。
契約 + 驗收測試骨架都經使用者確認後，才進全速開發。

## §5.1 審查層（覆蓋）：多 agent 的發現，一律落成測試

強制層（§0–§1）擋的是「做壞了」；要挖出更深的問題（漏洞、邊界、資料一致性），用多 agent 審查當「覆蓋層」。規則：

- **用當下工具的原生多 agent**（Claude Code 用 Workflow；Codex 用 Codex 的 agent）。無原生能力的環境，用可攜備胎 `.project/review.py`（純標準庫、provider 可切換）。
- **判準——會「裁判」的住 repo，只「幫忙生產」的可用工具原生**：checks.py／測試是裁判（判定做完沒），必須可攜、住 repo；多 agent 審查是生產幫手，工具原生即可。
- **鐵律：審查的發現，一律落成 `tests/` 才算數**。可先用 `@pytest.mark.xfail(reason=..., strict=False)` 記錄「應擋未擋」，修好後自動轉綠（xpass）＝ 修復的證據。**發現只有變成測試，才是永久、跨工具的資產；否則換工具就蒸發。**

## §6 速度檔

| 速度檔 | 適用 | 原則 |
|---|---|---|
| Fast | 文件、小修、明確 bug、低風險 UI 文案 | 直接修，跑最窄測試 + checks |
| Standard | 單一 API+UI、單一模組 | 完成實作與相關測試 + checks |
| Release | DB、權限、匯入回匯、部署、資安、正式資料 | 保守，完整驗證；先過 §2 重大事項流程 |

Fast/Standard 一旦踩到 DB、權限、金額、正式資料、部署、資安，立即升級 Release 並回 §2。

## §7 停損與不可碰

出現以下情況，停止硬衝、回報使用者：同一測試連續失敗 2 次；需求互相矛盾；踩到重大風險但缺授權；工具壞掉且修工具會偏離主目標。

除非使用者明確授權，不得碰：正式資料、正式 DB、正式憑證、正式部署、不可逆 migration、刪除/覆蓋資料、正式金額/狀態。不得從 archive/舊碼直接複製主程式，不得做無關重構。

## §8 UI Mock Gate（有 UI 才適用）

正式實作前先做可點的 HTML Mock（mock data、不連 DB），確認版面、資訊層級、操作路徑、使用者語言。使用者確認後才進正式 UI/API/DB。使用者明說「先不用 mock」才可跳過，並在回報中記錄。

## §9 交接（跨 session / 換人 / 換模型）

新 session 的第一個動作：跑 `python .project/snapshot.py`，讀 `CURRENT_STATE.md`。
**現狀真相以它 + `checks.py` 即時輸出為準，不信任任何手寫的 WBS 或交付紀錄**（那些會過期、會說謊）。

## §10 回報格式

```text
本輪 Focus（做什麼 / 不做什麼）：
速度檔：
變更檔案：
checks.py 輸出（原文貼上）：
是否已 commit（HEAD 短碼）：
新增/更動的決策（decisions.json）：
已知限制：
下一個建議切片：
```

## §11 啟動語範例

```text
我要開發一套 XX 系統。請依「一次性開發提示詞 C1 FINAL（環境強制版）」進入一包式開發模式。
先安裝 .project 強制層並 git init，再訪談我、產出 MVP 契約。
有 UI 先做 HTML mock 確認。契約確認後自動開發到可展示 MVP。
每個切片都要 checks.py 全 PASS 並 commit，回報時貼真實輸出。
重大事項（DB / 權限 / 金額 / 正式資料）先問我、寫進 decisions.json，才可寫 code。
```

（本目錄 `kit/` 內附上述腳本的可執行複本，已實測：乾淨專案全 PASS；植入寫死密碼與文件/決策矛盾時確實擋下。）
