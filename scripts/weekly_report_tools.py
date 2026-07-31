"""週進度報告工具：抓數字、比對流程圖、產出前檢查。

用法（在專案根目錄執行；中文路徑用 py 跑，不要用 PowerShell 的 Get-Content 改檔）：

    py scripts\\weekly_report_tools.py stats  <舊報告.html> <新報告.html>
        兩份報告的整體％、各階段％、四態統計並排，寫信要的數字一次拿到。

    py scripts\\weekly_report_tools.py flow-diff <舊報告.html> <新報告.html>
        流程圖上「這次新完成」的節點編號與行號（用來標橘框）。

    py scripts\\weekly_report_tools.py mark <報告.html> <行號,行號,...>
        把指定行的已完成節點框改成橘色（本次新完成）。行號由 flow-diff 給。

    py scripts\\weekly_report_tools.py verify <報告.html>
        產出前檢查：HTML 標籤閉合、無 BOM、橘框數、舊版號有沒有殘留。

舊報告＝上次寄出那份，放在 docs\\報告存檔\\。改報告前一定要先備份一份帶日期的，
否則下次沒有東西可以對比（規則見 AI\\週報告_TEMPLATE.md）。
"""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

# 自閉合或 SVG 內不需要成對計算的標籤
VOID = {"meta", "link", "br", "hr", "img", "input", "path", "rect", "circle",
        "polygon", "text", "line", "marker", "use", "tspan"}

NODE_LINE = re.compile(r'^<(rect|polygon)\s')
NODE_CODE = re.compile(r'>([A-E]\d)</text>')
ORANGE = "#d9860b"          # 本次新完成
GREEN = "#1b6b4a"           # 先前已完成


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def stats(path: str) -> dict:
    s = read(path)
    return {
        "overall": (re.findall(r'class="pct">(\d+)%', s) or ["?"])[0],
        "stages": re.findall(
            r'stage-tag">([^<]+)</span><span class="stage-title">([^<]+)</span>\s*'
            r'<span class="stage-pct"><span class="mini-bar"><i style="width:(\d+)%', s),
        "tiles": re.findall(r'class="num">(\d+)</div><div class="lbl">([^<]+)<', s),
    }


def cmd_stats(old: str, new: str) -> None:
    a, b = stats(old), stats(new)
    print(f"整體：{a['overall']}% → {b['overall']}%")
    print("\n各階段：")
    bmap = {name: pct for _tag, name, pct in b["stages"]}
    for _tag, name, pct in a["stages"]:
        after = bmap.get(name, "?")
        delta = f"+{int(after) - int(pct)}" if after.isdigit() else "?"
        print(f"  {name:　<16} {pct:>3}% → {after:>3}%  ({delta})")
    print("\n四態統計：")
    bt = dict((lbl, n) for n, lbl in b["tiles"])
    for n, lbl in a["tiles"]:
        print(f"  {lbl:　<12} {n:>3} → {bt.get(lbl, '?'):>3}")


def flow_states(path: str) -> dict[str, tuple[str, int]]:
    """{節點編號: (done|todo, 行號)}；節點框後第一個編號文字就是它的編號。"""
    out: dict[str, tuple[str, int]] = {}
    pending = None
    for i, line in enumerate(read(path).split("\n"), 1):
        if NODE_LINE.match(line) and ('rx="10"' in line or line.startswith("<polygon")):
            if "stroke-dasharray" in line:
                pending = ("todo", i)
            elif GREEN in line or ORANGE in line:
                pending = ("done", i)
            else:
                pending = None
        m = NODE_CODE.search(line)
        if m and pending:
            out[m.group(1)] = pending
            pending = None
    return out


def cmd_flow_diff(old: str, new: str) -> None:
    a, b = flow_states(old), flow_states(new)
    newly = sorted(k for k in b if b[k][0] == "done" and a.get(k, ("todo", 0))[0] == "todo")
    print("本次新完成（標橘框）：", ", ".join(newly) or "（無）")
    print("行號：", ",".join(str(b[k][1]) for k in newly))
    print("仍未開發：", ", ".join(sorted(k for k in b if b[k][0] == "todo")) or "（無）")
    print("先前就完成：", ", ".join(sorted(k for k in b if b[k][0] == "done" and k not in newly)))


def cmd_mark(path: str, rows: str) -> None:
    p = Path(path)
    lines = p.read_text(encoding="utf-8").split("\n")
    targets = [int(x) for x in rows.replace(" ", "").split(",") if x]
    for n in targets:
        i = n - 1
        s = lines[i]
        if ORANGE in s:
            continue                      # 已經標過，重跑不會壞
        assert f'stroke="{GREEN}"' in s, f"第 {n} 行不是已完成節點：{s[:90]}"
        lines[i] = s.replace(f'stroke="{GREEN}"', f'stroke="{ORANGE}"').replace(
            'stroke-width="2.5"', 'stroke-width="3"')
    p.write_text("\n".join(lines), encoding="utf-8", newline="")
    print(f"已標記 {len(targets)} 個節點為本次新完成")


class _Balance(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.stack: list[str] = []
        self.bad: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        else:
            self.bad.append(tag)


def cmd_verify(path: str) -> None:
    s = read(path)
    h = _Balance()
    h.feed(s)
    tabs = re.findall(r'class="tab[^"]*"[^>]*>([^<]+)</button>', s)
    orange = len(re.findall(r'<(?:rect|polygon)[^>]*stroke="' + ORANGE + r'"', s))
    old_versions = sorted(set(re.findall(r'v0\.\d+\.\d+', s)))
    print(f"[{'OK  ' if not h.stack and not h.bad else 'FAIL'}] 標籤閉合 未閉合={h.stack} 錯配={h.bad[:5]}")
    print(f"[{'OK  ' if not s.startswith(chr(0xFEFF)) else 'FAIL'}] 無 BOM")
    print(f"[{'OK  ' if len(tabs) >= 6 else 'FAIL'}] 頁籤 {len(tabs)} 個：{' / '.join(tabs)}")
    print(f"[{'OK  ' if orange else 'WARN'}] 流程圖橘框（本次新完成）{orange} 個")
    head = re.search(r'class="eyebrow">.*?<span>(v0\.\d+\.\d+)</span>.*?<span>(\d{4}-\d{2}-\d{2})</span>', s, re.S)
    foot = re.search(r'產生於 (\d{4}-\d{2}-\d{2}) · (v0\.\d+\.\d+)', s)
    print(f"[INFO] 頁首：{head.group(1) if head else '?'} / {head.group(2) if head else '?'}"
          f"　頁尾：{foot.group(2) if foot else '?'} / {foot.group(1) if foot else '?'}　←這兩處要一致且是最新")
    print(f"[INFO] 內文提到的版號（更新紀錄會有舊的，正常）：{', '.join(old_versions)}")


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    cmd, args = sys.argv[1], sys.argv[2:]
    table = {"stats": cmd_stats, "flow-diff": cmd_flow_diff, "mark": cmd_mark, "verify": cmd_verify}
    if cmd not in table:
        print(__doc__)
        return 1
    table[cmd](*args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
