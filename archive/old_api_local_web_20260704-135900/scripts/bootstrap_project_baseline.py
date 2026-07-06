#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = ROOT / "templates"


def copy_file(src: Path, dst: Path, force: bool) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and not force:
        return f"skip existing: {dst}"
    shutil.copy2(src, dst)
    return f"write: {dst}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Copy baseline templates into a project.")
    parser.add_argument("--target", required=True, help="Target project directory")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    target = Path(args.target).resolve()
    target.mkdir(parents=True, exist_ok=True)

    results: list[str] = []
    for src in TEMPLATE_ROOT.rglob("*"):
        if src.is_dir():
            continue
        rel = src.relative_to(TEMPLATE_ROOT)
        results.append(copy_file(src, target / rel, args.force))

    for line in results:
        print(line)
    print(f"done target={target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

