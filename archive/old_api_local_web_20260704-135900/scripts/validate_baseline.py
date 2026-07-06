#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_FILES = [
    "AGENTS.md",
    "HANDOFF_INDEX.md",
    "Memory.md",
    "docs/project_overview.md",
    "docs/data_dictionary.md",
    "docs/workflow_state.md",
    "docs/ai_truth_and_evidence.md",
    "docs/ai_work_quality_rules.md",
    "docs/current_state_snapshot.md",
    "docs/handoff_checklist.md",
    "docs/company_codex_enterprise_profile.md",
    "docs/product_ui_rules.md",
    "docs/module_management_rules.md",
    "docs/security_scanning_rules.md",
    "docs/runbook.md",
    "docs/test_plan.md",
    "docs/security_data_handling.md",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate baseline project files.")
    parser.add_argument("--target", required=True, help="Target project directory")
    parser.add_argument("--json", action="store_true", help="Print JSON")
    args = parser.parse_args()

    target = Path(args.target).resolve()
    missing = [item for item in REQUIRED_FILES if not (target / item).exists()]
    result = {
        "ok": not missing,
        "target": str(target),
        "required_count": len(REQUIRED_FILES),
        "missing_count": len(missing),
        "missing": missing,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"target={target}")
        print(f"ok={result['ok']}")
        if missing:
            print("missing:")
            for item in missing:
                print(f"- {item}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
