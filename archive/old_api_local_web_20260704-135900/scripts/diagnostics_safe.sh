#!/usr/bin/env bash
set -eu

TARGET="${1:-.}"
OUTPUT_DIR="${2:-/tmp}"
STAMP="$(date +%Y%m%d%H%M%S)"
OUT="${OUTPUT_DIR}/project_diagnostics_safe_${STAMP}.json"

hash_short() {
  printf '%s' "$1" | sha256sum | awk '{print substr($1,1,12)}'
}

TARGET_ABS="$(cd "$TARGET" && pwd)"
FILE_COUNT="$(find "$TARGET_ABS" -type f \
  -not -path '*/.git/*' \
  -not -path '*/node_modules/*' \
  -not -path '*/venv/*' \
  -not -path '*/.venv/*' \
  -not -path '*/__pycache__/*' | wc -l | tr -d ' ')"

cat > "$OUT" <<JSON
{
  "generated_at": "$(date -Iseconds)",
  "target_hash": "$(hash_short "$TARGET_ABS")",
  "host_hash": "$(hostname | sha256sum | awk '{print substr($1,1,12)}')",
  "user_hash": "$(id -un | sha256sum | awk '{print substr($1,1,12)}')",
  "file_count": $FILE_COUNT,
  "markers": {
    "has_git": $(test -d "$TARGET_ABS/.git" && echo true || echo false),
    "has_agents": $(test -f "$TARGET_ABS/AGENTS.md" && echo true || echo false),
    "has_memory": $(test -f "$TARGET_ABS/Memory.md" && echo true || echo false),
    "has_tests": $(test -d "$TARGET_ABS/tests" && echo true || echo false),
    "has_package_json": $(test -f "$TARGET_ABS/package.json" && echo true || echo false),
    "has_requirements": $(test -f "$TARGET_ABS/requirements.txt" && echo true || echo false),
    "has_env_example": $(test -f "$TARGET_ABS/.env.example" && echo true || echo false)
  }
}
JSON

echo "output=$OUT"

