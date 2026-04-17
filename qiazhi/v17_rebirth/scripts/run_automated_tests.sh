#!/usr/bin/env bash
set -euo pipefail
# scripts → v17_rebirth → qiazhi → 仓库根 bazi
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

PY=python3
command -v python3 >/dev/null 2>&1 || PY=python

echo "==> pytest V17 (exclude integration) =="
"$PY" -m pytest qiazhi/v17_rebirth/tests -m "not integration" -q

echo "==> pytest V17 integration =="
"$PY" -m pytest qiazhi/v17_rebirth/tests -m integration -q

FRONT="$ROOT/qiazhi/v17_rebirth/frontend"
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
