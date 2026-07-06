#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


CHECKS = [
    ("AGENTS.md", 8, "AI collaboration rules exist."),
    ("HANDOFF_INDEX.md", 8, "Handoff entry point exists."),
    ("Memory.md", 8, "Session memory exists."),
    ("docs/project_overview.md", 6, "Project overview exists."),
    ("docs/data_dictionary.md", 6, "Data dictionary exists."),
    ("docs/workflow_state.md", 6, "Workflow state rules exist."),
    ("docs/test_plan.md", 8, "Test plan exists."),
    ("docs/security_data_handling.md", 8, "Security data rules exist."),
    ("docs/ai_truth_and_evidence.md", 8, "AI evidence rules exist."),
    ("docs/ai_work_quality_rules.md", 8, "AI anti-laziness rules exist."),
    ("docs/company_codex_enterprise_profile.md", 6, "Company Codex Enterprise defaults exist."),
    ("docs/product_ui_rules.md", 6, "Enterprise UI rules exist."),
    ("docs/module_management_rules.md", 6, "Module management rules exist."),
    ("docs/security_scanning_rules.md", 6, "Security scanning rules exist."),
    ("docs/current_state_snapshot.md", 6, "Current state snapshot exists."),
    ("docs/release_checklist.md", 5, "Release checklist exists."),
    ("docs/regression_catalog.md", 5, "Regression catalog exists."),
    ("docs/runbook.md", 6, "Runbook exists."),
]

TEST_MARKERS = [
    "tests",
    "test",
    "pytest.ini",
    "package.json",
    "pyproject.toml",
]


def has_test_marker(target: Path) -> bool:
    for marker in TEST_MARKERS:
        path = target / marker
        if path.exists():
            return True
    return False


def score_target(target: Path) -> dict[str, object]:
    details = []
    score = 0
    max_score = sum(weight for _, weight, _ in CHECKS) + 10

    for rel, weight, description in CHECKS:
        exists = (target / rel).exists()
        if exists:
            score += weight
        details.append({
            "file": rel,
            "exists": exists,
            "weight": weight,
            "description": description,
        })

    tests_present = has_test_marker(target)
    if tests_present:
        score += 10
    details.append({
        "file": "<test marker>",
        "exists": tests_present,
        "weight": 10,
        "description": "At least one test marker exists.",
    })

    percent = round(score / max_score * 100, 1) if max_score else 0
    if percent >= 85:
        level = "strong"
    elif percent >= 65:
        level = "usable"
    elif percent >= 45:
        level = "needs_work"
    else:
        level = "fragile"

    return {
        "target": str(target),
        "score": score,
        "max_score": max_score,
        "percent": percent,
        "level": level,
        "details": details,
        "guidance": [
            "Fill missing high-weight files first.",
            "Add one smoke test before large refactoring.",
            "Update handoff files before another AI or engineer takes over.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Score project baseline readiness.")
    parser.add_argument("--target", required=True, help="Project directory")
    parser.add_argument("--output", help="Write JSON output")
    args = parser.parse_args()

    target = Path(args.target).resolve()
    result = score_target(target)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
