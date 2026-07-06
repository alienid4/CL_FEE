#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json


FIELDS = [
    "code_size",
    "data_complexity",
    "test_gap",
    "deploy_risk",
    "security_risk",
    "ui_flow_risk",
]


def level(total: int) -> tuple[str, str]:
    if total <= 10:
        return "small", "0.5-1 day"
    if total <= 18:
        return "medium", "2-4 days"
    if total <= 25:
        return "large", "1-2 weeks"
    return "high_risk", "stabilize first; do not rush coding"


def main() -> int:
    parser = argparse.ArgumentParser(description="Estimate project change difficulty.")
    for field in FIELDS:
        parser.add_argument(f"--{field.replace('_', '-')}", type=int, required=True)
    args = parser.parse_args()

    scores = {field: getattr(args, field) for field in FIELDS}
    invalid = {key: value for key, value in scores.items() if value < 1 or value > 5}
    if invalid:
        raise SystemExit(f"scores must be 1-5: {invalid}")

    total = sum(scores.values())
    level_name, estimate = level(total)
    result = {
        "scores": scores,
        "total": total,
        "level": level_name,
        "estimated_time": estimate,
        "guidance": "Use small scoped changes and require stronger verification as the score rises."
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

