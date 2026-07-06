from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LOGS_DIR = ROOT / "logs"


def find_prompt_pack() -> Path:
    pinned = ROOT / "docs" / "一次性開發提示詞_v2.1"
    if pinned.exists() and pinned.is_dir():
        return pinned

    candidates = []
    for path in (ROOT / "docs").iterdir():
        if not path.is_dir():
            continue
        name = path.name
        if "_v2." not in name:
            continue
        try:
            version = tuple(int(part) for part in name.rsplit("_v", 1)[1].split("."))
        except (IndexError, ValueError):
            continue
        candidates.append((version, path))
    if not candidates:
        return ROOT / "docs" / "一次性開發提示詞_v2.1"
    return sorted(candidates, key=lambda item: item[0])[-1][1]


@dataclass(frozen=True)
class ConsoleCommand:
    command_id: str
    label: str
    lane: str
    args: tuple[str, ...]
    timeout_seconds: int
    requires_approval: bool = False


COMMANDS: dict[str, ConsoleCommand] = {
    "fast_ci": ConsoleCommand(
        command_id="fast_ci",
        label="Fast CI",
        lane="fast",
        args=(
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            "scripts\\fast_ci.ps1",
            "-IncludePromptPack",
            "-IncludeAutomationFoundation",
        ),
        timeout_seconds=120,
    ),
    "local_ci": ConsoleCommand(
        command_id="local_ci",
        label="Local CI",
        lane="standard",
        args=("powershell", "-ExecutionPolicy", "Bypass", "-File", "scripts\\local_ci.ps1"),
        timeout_seconds=240,
    ),
    "deep_security": ConsoleCommand(
        command_id="deep_security",
        label="Deep Security",
        lane="release",
        args=("powershell", "-ExecutionPolicy", "Bypass", "-File", "scripts\\deep_security_check.ps1"),
        timeout_seconds=240,
    ),
    "profile": ConsoleCommand(
        command_id="profile",
        label="Project Profile",
        lane="fast",
        args=("powershell", "-ExecutionPolicy", "Bypass", "-File", "scripts\\detect_project_profile.ps1"),
        timeout_seconds=60,
    ),
    "runtime_fast": ConsoleCommand(
        command_id="runtime_fast",
        label="Runtime Fast",
        lane="fast",
        args=(
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            "scripts\\agent_runtime_once.ps1",
            "-Goal",
            "Run v2.1 local control panel fast loop",
            "-Lane",
            "fast",
        ),
        timeout_seconds=180,
    ),
    "audit_summary": ConsoleCommand(
        command_id="audit_summary",
        label="Audit Summary",
        lane="fast",
        args=("powershell", "-ExecutionPolicy", "Bypass", "-File", "scripts\\summarize_agent_audit_log.ps1"),
        timeout_seconds=60,
    ),
}


def read_text_file(path: Path, limit: int = 6000) -> str:
    if not path.exists() or not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > limit:
        return text[:limit] + "\n..."
    return text


def read_json_file(path: Path) -> Any:
    if not path.exists() or not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"error": "invalid json", "path": str(path.relative_to(ROOT))}


def read_audit_entries(limit: int = 8) -> list[dict[str, Any]]:
    path = LOGS_DIR / "agent_loop_audit.jsonl"
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            rows.append({"audit_result": "invalid", "goal": "Invalid JSONL entry"})
    return rows[-limit:]


def command_catalog() -> list[dict[str, Any]]:
    return [
        {
            "command_id": command.command_id,
            "label": command.label,
            "lane": command.lane,
            "timeout_seconds": command.timeout_seconds,
            "requires_approval": command.requires_approval,
        }
        for command in COMMANDS.values()
    ]


def console_status() -> dict[str, Any]:
    prompt_pack = find_prompt_pack()
    return {
        "version": "v2.1-local-control-panel-mvp",
        "prompt_pack": str(prompt_pack.relative_to(ROOT)),
        "current_status": read_text_file(prompt_pack / "CURRENT_STATUS.md", limit=5000),
        "start_next": read_text_file(prompt_pack / "START_NEXT.md", limit=2500),
        "commands": command_catalog(),
        "audit_entries": read_audit_entries(),
        "project_profile": read_json_file(LOGS_DIR / "project_profile.json"),
        "runtime_state": read_json_file(LOGS_DIR / "agent_runtime_state.json"),
        "safety": {
            "production_data": "blocked",
            "deployment": "blocked",
            "credentials": "blocked",
            "command_mode": "allowlist",
        },
    }


def run_console_command(command_id: str, dry_run: bool = False) -> dict[str, Any]:
    if command_id not in COMMANDS:
        raise KeyError(command_id)
    command = COMMANDS[command_id]
    if dry_run:
        return {
            "command_id": command.command_id,
            "label": command.label,
            "lane": command.lane,
            "dry_run": True,
            "args": list(command.args),
        }

    completed = subprocess.run(
        command.args,
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=command.timeout_seconds,
        check=False,
    )
    return {
        "command_id": command.command_id,
        "label": command.label,
        "lane": command.lane,
        "exit_code": completed.returncode,
        "ok": completed.returncode == 0,
        "stdout": completed.stdout[-8000:],
        "stderr": completed.stderr[-8000:],
    }
