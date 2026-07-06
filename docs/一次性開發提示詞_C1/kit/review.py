#!/usr/bin/env python3
"""C1 覆蓋層 — 可攜式多 agent 審查（跨工具、跨模型）。

不綁任何 IDE / agent 工具：純 Python 標準庫，直接呼叫 LLM API。
在 Claude 用、回 Codex 用、cron 排程用，都是同一支 `python .project/review.py`。

- 真獨立：每個審查視角是一次「全新 context」的 API 呼叫，彼此看不到對方推理。
- 對抗性驗證：每個發現再開一次獨立呼叫，預設「不成立，除非證明得了」。
- 程式彙總：由本腳本用死板規則決定留哪些，不讓模型互相打分。
- 產出住在 repo（REVIEW_REPORT.md / .project/review_findings.json），跨工具、永久。

用法：
    set ANTHROPIC_API_KEY=...             (或 OPENAI_API_KEY)
    python .project/review.py             # 真的審查（會呼叫 API、計費到你的 key）
    python .project/review.py --dry-run   # 只組 prompt、不呼叫 API、不花錢

環境變數：
    REVIEW_PROVIDER = anthropic | openai   (預設 anthropic；回 Codex 就設 openai)
    REVIEW_MODEL    = 覆寫模型 id
    REVIEW_TARGET   = 要審的資料夾（預設 app）
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")  # Windows 主控台/管線預設非 utf-8，強制統一
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = {"anthropic": "claude-sonnet-5", "openai": "gpt-4o"}


def env(name: str, default: str | None = None) -> str | None:
    v = os.environ.get(name)
    return v if v not in (None, "") else default


PROVIDER = (env("REVIEW_PROVIDER", "anthropic") or "anthropic").lower()
MODEL = env("REVIEW_MODEL", DEFAULT_MODEL.get(PROVIDER, "claude-sonnet-5"))
TARGET = env("REVIEW_TARGET", "app")


# ---- 收集要審查的原始碼 ----
def gather_sources(target: str, max_chars: int = 60000) -> tuple[str, list[str]]:
    base = ROOT / target
    files = [f for f in sorted(base.rglob("*.py")) if "__pycache__" not in f.parts] if base.exists() else []
    chunks: list[str] = []
    total = 0
    used: list[str] = []
    for f in files:
        try:
            txt = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        piece = f"\n===== FILE: {f.relative_to(ROOT).as_posix()} =====\n" + txt
        if total + len(piece) > max_chars:
            piece = piece[: max(0, max_chars - total)] + "\n...(截斷)...\n"
        chunks.append(piece)
        used.append(f.relative_to(ROOT).as_posix())
        total += len(piece)
        if total >= max_chars:
            break
    return "".join(chunks), used


# ---- LLM 呼叫（provider 抽象，這是「跨工具」的關鍵）----
def call_llm(system: str, user: str, model: str | None = None, max_tokens: int = 2000) -> str:
    model = model or MODEL
    if PROVIDER == "anthropic":
        key = env("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("缺 ANTHROPIC_API_KEY")
        body = {"model": model, "max_tokens": max_tokens, "system": system,
                "messages": [{"role": "user", "content": user}]}
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(body).encode("utf-8"),
            headers={"content-type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01"},
        )
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read())
        return "".join(b.get("text", "") for b in data.get("content", []))
    if PROVIDER == "openai":
        key = env("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("缺 OPENAI_API_KEY")
        body = {"model": model, "max_tokens": max_tokens,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={"content-type": "application/json", "authorization": f"Bearer {key}"},
        )
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read())
        return data["choices"][0]["message"]["content"]
    raise RuntimeError(f"未知 REVIEW_PROVIDER: {PROVIDER}（只支援 anthropic / openai）")


def extract_json(text: str) -> dict | None:
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text.strip())
    text = re.sub(r"```$", "", text.strip())
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except Exception:
                    return None
    return None


# ---- 三個獨立審查視角 ----
LENSES = [
    {"key": "security", "system": "你是獨立的資安審查員，只看使用者提供的原始碼，不臆測。",
     "focus": "寫死密鑰/密碼、認證與 session/cookie 缺陷、權限繞過、注入、subprocess 命令執行風險。"},
    {"key": "correctness", "system": "你是獨立的正確性審查員，只看使用者提供的原始碼。",
     "focus": "錯誤處理漏洞、狀態轉換錯誤、邊界條件、會拋未捕捉例外的路徑、API 契約不一致。"},
    {"key": "data-integrity", "system": "你是獨立的資料一致性審查員，只看使用者提供的原始碼。",
     "focus": "暫存污染正式資料、稽核遺漏、回匯/更新覆蓋、金額/狀態驗證缺口、作廢 vs 刪除的破壞性。"},
]

FIND_INSTRUCT = (
    '找出真實、可在程式碼指到 file:line 的問題。只輸出 JSON：\n'
    '{"findings":[{"title":"","file":"","line":0,"severity":"high|medium|low","detail":"","failing_input":""}]}\n'
    '沒有問題就回 {"findings":[]}。不要輸出 JSON 以外的任何字。'
)
VERIFY_SYSTEM = ("你是獨立的對抗性驗證員，之前沒看過任何人的推理。"
                 "預設疑似問題『不成立』，除非你能在程式碼指出具體會出錯的輸入或執行路徑。")
VERIFY_INSTRUCT = '只輸出 JSON：{"is_real":true/false,"reason":"","proposed_test":"pytest 測試名"}。不要其他字。'


def find_worker(lens: dict, source: str) -> list[dict]:
    try:
        raw = call_llm(lens["system"], f"{lens['focus']}\n\n{FIND_INSTRUCT}\n\n以下是要審查的原始碼：\n{source}")
        data = extract_json(raw) or {"findings": []}
        return [{**f, "lens": lens["key"]} for f in data.get("findings", [])]
    except Exception as exc:
        print(f"  [warn] finder {lens['key']} 失敗：{exc}")
        return []


def verify_worker(finding: dict, source: str) -> dict:
    try:
        user = f"疑似問題：{json.dumps(finding, ensure_ascii=False)}\n\n{VERIFY_INSTRUCT}\n\n相關原始碼：\n{source}"
        return extract_json(call_llm(VERIFY_SYSTEM, user)) or {"is_real": False, "reason": "無法解析驗證回應", "proposed_test": ""}
    except Exception as exc:
        return {"is_real": False, "reason": f"驗證失敗：{exc}", "proposed_test": ""}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="只組 prompt、不呼叫 API、不花錢")
    args = ap.parse_args()

    source, files = gather_sources(TARGET)
    print(f"[C1 review] provider={PROVIDER} model={MODEL} target={TARGET} 檔案={len(files)} 字元={len(source)}")
    if not source:
        print("沒有找到要審查的 .py 檔（檢查 REVIEW_TARGET）")
        sys.exit(1)

    if args.dry_run:
        print("--- DRY RUN：不呼叫 API、不計費 ---")
        print(f"會開 {len(LENSES)} 個獨立 finder（各自全新 context、互不相見）：")
        for l in LENSES:
            print(f"  · {l['key']}：{l['focus']}")
        print("每個發現會再各開一個獨立 verifier 做對抗性驗證；通過的才留下。")
        print("plumbing OK。設好 API key 後拿掉 --dry-run 即真的執行。")
        return

    with ThreadPoolExecutor(max_workers=3) as ex:
        found = list(ex.map(lambda l: find_worker(l, source), LENSES))

    rank = {"high": 0, "medium": 1, "low": 2}
    seen: set[str] = set()
    all_f: list[dict] = []
    for lst in found:
        for f in lst:
            k = f"{f.get('file', '').lower()}::{f.get('title', '').lower()[:40]}"
            if k in seen:
                continue
            seen.add(k)
            all_f.append(f)
    all_f.sort(key=lambda f: rank.get(f.get("severity"), 3))
    shortlist = all_f[:10]
    print(f"[Find] 3 視角共 {len(all_f)} 項，取前 {len(shortlist)} 送對抗性驗證")

    with ThreadPoolExecutor(max_workers=4) as ex:
        verdicts = list(ex.map(lambda f: verify_worker(f, source), shortlist))

    confirmed = [{**f, "reason": v.get("reason", ""), "proposed_test": v.get("proposed_test", "")}
                 for f, v in zip(shortlist, verdicts) if v.get("is_real")]
    print(f"[Verify] {len(shortlist)} 送驗，{len(confirmed)} 通過對抗性驗證")

    (ROOT / ".project" / "review_findings.json").write_text(
        json.dumps({"confirmed": confirmed}, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# C1 多 agent 審查報告（可攜式）", "",
             f"- provider / model：{PROVIDER} / {MODEL}",
             f"- 確認問題：{len(confirmed)} 項", "",
             "| 嚴重度 | 視角 | 問題 | 檔案:行 | 建議測試 |", "|---|---|---|---|---|"]
    for c in confirmed:
        lines.append(f"| {c.get('severity', '')} | {c.get('lens', '')} | {c.get('title', '')} | "
                     f"{c.get('file', '')}:{c.get('line', '')} | `{c.get('proposed_test', '')}` |")
    (ROOT / "REVIEW_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("已寫出 REVIEW_REPORT.md 與 .project/review_findings.json")
    print("下一步：把 proposed_test 落成 tests/，讓發現變成永久、跨工具的測試。")


if __name__ == "__main__":
    main()
