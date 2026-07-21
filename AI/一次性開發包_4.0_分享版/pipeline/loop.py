#!/usr/bin/env python3
# C1 自主驅動器 (4.0) — 把 snapshot / checks / decisions 串成「按一次、走開」的迴圈。
# 規格來源：docs/一次性開發提示詞_4.0/一次性開發提示詞_4.0_FINAL.md（提示詞即規格）
#
# 這支就是 3.5 -> 4.0 缺的「引擎」。它「機制上」強制：
#   - 待辦自動拉：從 backlog.json 拉下一件，不用人派
#   - 預算煞車  ：到回合/時間上限就停下、出待續報告
#   - 卡住升級  ：同一件失敗 N 次 -> 標 blocked、寫進 decisions.json、停手不鬼打牆
#   - 自驗才過  ：每件先跑 .project/checks.py 全 PASS 才 commit
#   - 只在非保護分支跑（不碰 main/master）
#
# 用法：
#   python .project/loop.py --dry-run   # 只看計畫與煞車，不呼叫 AI、不改東西（先測骨架）
#   python .project/loop.py --once       # 只跑一件就停（第一次真的跑，建議先這個）
#   python .project/loop.py              # 一路跑到待辦清空或觸發煞車
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
PROJ = ROOT / ".project"
CONFIG = PROJ / "loop_config.json"
BACKLOG = PROJ / "backlog.json"
DECISIONS = PROJ / "decisions.json"
REPORT = PROJ / "run_report.md"
PROMPT_FILE = PROJ / ".loop_prompt.txt"

DEFAULT_CONFIG = {
    "max_rounds": 20,
    "max_minutes": 60,
    "max_fails_per_slice": 3,
    "protect_branches": ["main", "master"],
    # 驅動器怎麼呼叫 AI 做每一件切片。留空 = 不真的呼叫（只跑骨架，方便先測煞車/待辦）。
    #   codex 例：  "codex exec --full-auto"      + agent_prompt_via = "stdin"
    #   claude 例： "claude -p"                    + agent_prompt_via = "stdin"
    #   走檔案例：  "yourtool --file {prompt_file}" + agent_prompt_via = "file"
    "agent_cmd": "",
    "agent_prompt_via": "stdin",  # stdin | file
}

DRY = "--dry-run" in sys.argv
ONCE = "--once" in sys.argv


def log(msg: str) -> None:
    print(msg, flush=True)


def load_json(p: Path, default):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(p: Path, data) -> None:
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, encoding="utf-8", errors="replace")


def current_branch() -> str:
    return git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()


def run_checks() -> tuple[bool, str]:
    r = subprocess.run([sys.executable, str(PROJ / "checks.py")], cwd=ROOT,
                       capture_output=True, encoding="utf-8", errors="replace")
    tail = (r.stdout + r.stderr).strip().splitlines()
    return r.returncode == 0, (tail[-1] if tail else "")


def escalate(slice_: dict, reason: str) -> None:
    d = load_json(DECISIONS, {"decisions": [], "doc_scan_ignore": []})
    d.setdefault("loop_escalations", [])
    d["loop_escalations"].append({
        "id": slice_.get("id"), "desc": slice_.get("desc"),
        "reason": reason, "attempts": slice_.get("attempts", 0),
    })
    save_json(DECISIONS, d)


def build_prompt(slice_: dict) -> str:
    return (
        "以 4.0 自主模式，只實作『這一個切片』，不碰別的、不做無關重構。\n\n"
        f"切片：{slice_.get('desc','')}\n"
        f"完成的定義（怎樣算對）：{slice_.get('done_when','')}\n\n"
        "規則：\n"
        "- 只動這個切片需要的檔案。\n"
        "- 碰到金流/權限/刪資料/正式機/語意不明 -> 停手，不要自己決定。\n"
        "- 做完確認上面『完成的定義』達成。\n"
    )


def invoke_agent(cfg: dict, prompt: str) -> str:
    # 回傳 "skipped"（沒設定）/ "ok"（成功）/ "failed"（非 0 離開）
    cmd = (cfg.get("agent_cmd") or "").strip()
    if not cmd:
        return "skipped"
    import shlex
    via = cfg.get("agent_prompt_via", "stdin")
    if via == "file":
        PROMPT_FILE.write_text(prompt, encoding="utf-8")
        argv = shlex.split(cmd.replace("{prompt_file}", str(PROMPT_FILE)))
        r = subprocess.run(argv, cwd=ROOT)
    else:  # stdin
        argv = shlex.split(cmd)
        r = subprocess.run(argv, cwd=ROOT, input=prompt, encoding="utf-8")
    return "ok" if r.returncode == 0 else "failed"


def write_report(cfg: dict, rounds: int, elapsed_min: float, backlog: list, note: str) -> None:
    done = [s for s in backlog if s.get("status") == "done"]
    blocked = [s for s in backlog if s.get("status") == "blocked"]
    todo = [s for s in backlog if s.get("status") in (None, "todo", "doing")]
    def sec(title: str, items: list) -> list:
        body = items if items else ["- （無）"]
        return [f"## {title}", *body, ""]

    lines = [
        "# Run Report（自主迴圈）", "",
        f"- 狀態：{note}",
        f"- 回合：{rounds} / {cfg['max_rounds']}　時間：{elapsed_min:.1f} / {cfg['max_minutes']} 分",
        f"- 完成 {len(done)}　卡住 {len(blocked)}　待辦剩 {len(todo)}", "",
    ]
    lines += sec("完成", [f"- ✅ {s['id']} {s['desc']}" for s in done])
    lines += sec("卡住（已升級給人）", [f"- 🛑 {s['id']} {s['desc']}（試 {s.get('attempts',0)} 次）" for s in blocked])
    lines += sec("還沒做", [f"- ▢ {s['id']} {s['desc']}" for s in todo])
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    cfg = {**DEFAULT_CONFIG, **load_json(CONFIG, {})}
    if not CONFIG.exists():
        save_json(CONFIG, DEFAULT_CONFIG)
        log(f"已建立預設 {CONFIG.name}。")

    # 分支護欄：不在保護分支上跑
    br = current_branch()
    if br in cfg["protect_branches"]:
        log(f"⛔ 目前在保護分支「{br}」，拒絕自主跑。請先切到工作分支：")
        log(f'   git checkout -b work/auto-loop')
        return 2

    backlog = load_json(BACKLOG, None)
    if not isinstance(backlog, list) or not backlog:
        log(f"⛔ 找不到有效的 {BACKLOG.name}（要是一個切片陣列）。範例：")
        log('   [{ "id":"S1", "desc":"...", "done_when":"...", "status":"todo", "attempts":0 }]')
        return 2

    log(f"分支：{br}｜待辦 {len(backlog)} 件｜煞車：{cfg['max_rounds']} 回合 / {cfg['max_minutes']} 分 / 每件 {cfg['max_fails_per_slice']} 次"
        + ("　[DRY-RUN]" if DRY else ""))

    start = time.monotonic()
    rounds = 0

    def elapsed_min() -> float:
        return (time.monotonic() - start) / 60.0

    while True:
        # 煞車：預算檢查
        if rounds >= cfg["max_rounds"]:
            write_report(cfg, rounds, elapsed_min(), backlog, "到回合上限，停下（待續）")
            log("⛽ 到回合上限，停下，出待續報告。"); return 0
        if elapsed_min() >= cfg["max_minutes"]:
            write_report(cfg, rounds, elapsed_min(), backlog, "到時間上限，停下（待續）")
            log("⛽ 到時間上限，停下，出待續報告。"); return 0

        # 拉下一件
        nxt = next((s for s in backlog if s.get("status") in (None, "todo", "doing")), None)
        if nxt is None:
            write_report(cfg, rounds, elapsed_min(), backlog, "待辦清空，全部處理完")
            log("✅ 待辦清空，收工。"); return 0

        rounds += 1
        log(f"\n── 回合 {rounds}：{nxt['id']} {nxt.get('desc','')}")

        if DRY:
            log(f"  [dry-run] 會做這件；完成定義：{nxt.get('done_when','')}")
            nxt["status"] = "done"  # 只在記憶體標記，dry-run 不存檔
            if ONCE:
                log("  [dry-run] --once，停。"); return 0
            continue

        nxt["status"] = "doing"; save_json(BACKLOG, backlog)

        # 呼叫 AI 實作這件
        status = invoke_agent(cfg, build_prompt(nxt))
        if status == "skipped":
            log("  ⚠ loop_config.json 沒填 agent_cmd，無法實作切片。停。（見 SETUP.md）")
            nxt["status"] = "todo"; save_json(BACKLOG, backlog); return 3
        if status == "failed":
            nxt["attempts"] = nxt.get("attempts", 0) + 1
            if nxt["attempts"] >= cfg["max_fails_per_slice"]:
                nxt["status"] = "blocked"; escalate(nxt, "AI 執行失敗（非 0 離開）")
                log(f"  🛑 AI 連續失敗 {nxt['attempts']} 次 → blocked、寫進 decisions.json。")
            else:
                nxt["status"] = "todo"
                log(f"  ✗ AI 執行失敗（第 {nxt['attempts']} 次），稍後重試。")
            save_json(BACKLOG, backlog); write_report(cfg, rounds, elapsed_min(), backlog, "進行中")
            if ONCE:
                log("\n--once，停。"); return 0
            continue

        # 自驗：跑 checks.py
        ok, summary = run_checks()
        log(f"  checks：{'PASS' if ok else 'FAIL'} — {summary}")

        if ok:
            add = git("add", "-A")
            commit = git("commit", "-m", nxt.get("desc", nxt["id"]))
            committed = commit.returncode == 0
            log("  commit：" + ("已存檔" if committed else "無變更可存（可能 AI 未產生改動）"))
            nxt["status"] = "done"; nxt["attempts"] = 0
        else:
            nxt["attempts"] = nxt.get("attempts", 0) + 1
            if nxt["attempts"] >= cfg["max_fails_per_slice"]:
                nxt["status"] = "blocked"
                escalate(nxt, f"連續 {nxt['attempts']} 次沒過 checks：{summary}")
                log(f"  🛑 卡住 {nxt['attempts']} 次 → 標 blocked、寫進 decisions.json，跳下一件。")
            else:
                nxt["status"] = "todo"
                log(f"  ✗ 沒過（第 {nxt['attempts']} 次），稍後重試。")

        save_json(BACKLOG, backlog)
        write_report(cfg, rounds, elapsed_min(), backlog, "進行中")

        if ONCE:
            log("\n--once，停。"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
