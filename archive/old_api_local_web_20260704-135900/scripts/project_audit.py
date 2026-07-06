#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path


IGNORE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
}

SECRET_PATTERNS = [
    re.compile(r"api[_-]?key", re.I),
    re.compile(r"token", re.I),
    re.compile(r"password", re.I),
    re.compile(r"private[_-]?key", re.I),
    re.compile(r"secret", re.I),
]

LANG_BY_EXT = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".jsx": "javascript",
    ".cs": "csharp",
    ".java": "java",
    ".go": "go",
    ".ps1": "powershell",
    ".sh": "shell",
    ".html": "html",
    ".css": "css",
}


def should_skip(path: Path) -> bool:
    return any(part in IGNORE_DIRS for part in path.parts)


def safe_scan_file(path: Path) -> dict[str, int]:
    result = {"secret_keyword_hits": 0}
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return result
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            result["secret_keyword_hits"] += 1
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe project audit without printing secrets.")
    parser.add_argument("--target", required=True, help="Project directory")
    parser.add_argument("--output", help="Write JSON output")
    args = parser.parse_args()

    target = Path(args.target).resolve()
    files = [p for p in target.rglob("*") if p.is_file() and not should_skip(p)]
    ext_counts = Counter(p.suffix.lower() or "<no_ext>" for p in files)
    lang_counts = Counter(LANG_BY_EXT.get(p.suffix.lower(), "other") for p in files)

    markers = {
        "has_git": (target / ".git").exists(),
        "has_agents": (target / "AGENTS.md").exists(),
        "has_memory": (target / "Memory.md").exists(),
        "has_tests_dir": (target / "tests").exists(),
        "has_package_json": (target / "package.json").exists(),
        "has_requirements": (target / "requirements.txt").exists(),
        "has_pyproject": (target / "pyproject.toml").exists(),
        "has_dockerfile": any(p.name.lower() == "dockerfile" for p in files),
        "has_env_example": (target / ".env.example").exists(),
    }

    secret_hits = 0
    scanned_text_files = 0
    for path in files:
        if path.suffix.lower() in {".py", ".js", ".ts", ".json", ".yaml", ".yml", ".md", ".txt", ".env", ".ps1", ".sh"}:
            scanned_text_files += 1
            secret_hits += safe_scan_file(path)["secret_keyword_hits"]

    result = {
        "target": str(target),
        "file_count": len(files),
        "extension_counts": dict(ext_counts.most_common(20)),
        "language_counts": dict(lang_counts.most_common()),
        "markers": markers,
        "safe_security_summary": {
            "scanned_text_files": scanned_text_files,
            "secret_keyword_hits": secret_hits,
            "note": "This reports keyword hits only; it does not print secret values."
        },
        "recommended_next_steps": [
            "Fill baseline docs if missing.",
            "Add at least one smoke test.",
            "Add safe diagnostics script.",
            "Move business rules out of UI when found.",
            "Add regression tests for known bugs."
        ]
    }

    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

