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
