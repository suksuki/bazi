#!/usr/bin/env bash
set -euo pipefail
# scripts → v17_rebirth/scripts → 仓库根 qiazhi（当前工作区）
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

PY=python3
command -v python3 >/dev/null 2>&1 || PY=python

echo "==> pytest V17 (exclude integration) =="
"$PY" -m pytest v17_rebirth/tests -m "not integration" -q

echo "==> pytest V17 integration =="
"$PY" -m pytest v17_rebirth/tests -m integration -q

echo "==> relation origin trend gate =="
TREND_REPORT="$(mktemp)"
trap 'rm -f "$TREND_REPORT"' EXIT
"$PY" v17_rebirth/scripts/relation_origin_trend_report.py > "$TREND_REPORT"
TREND_REPORT_PATH="$TREND_REPORT" "$PY" - <<'PY'
import json
import os
import sys

path = os.environ.get("TREND_REPORT_PATH", "")
with open(path, "r", encoding="utf-8") as fp:
    payload = json.load(fp)

violations = int((payload.get("summary") or {}).get("compliance", {}).get("violation_count", 0))
if violations:
    print(f"[FAIL] relation origin trend violations: {violations}")
    sys.exit(1)
print("[OK] relation origin trend compliance passed: 0 violations")
PY

FRONT="$ROOT/v17_rebirth/frontend"
if [[ -d "$FRONT" ]]; then
  echo "==> frontend test:ci =="
  cd "$FRONT"
  if command -v pnpm >/dev/null 2>&1; then
    pnpm install --frozen-lockfile 2>/dev/null || pnpm install
    pnpm run test:ci
  else
    npm install
    npm run test:ci
  fi
fi

echo "OK: automated tests finished."
