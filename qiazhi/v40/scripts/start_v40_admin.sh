#!/usr/bin/env bash
set -euo pipefail

if [ -f ".env.v40.local" ]; then
  set -a
  . ".env.v40.local"
  set +a
fi

export V40_ADMIN_HOST="${V40_ADMIN_HOST:-127.0.0.1}"
export V40_ADMIN_PORT="${V40_ADMIN_PORT:-9041}"
export V40_API_BASE="${V40_API_BASE:-http://127.0.0.1:9040}"
export V40_PYTHON="${V40_PYTHON:-python3}"

exec "${V40_PYTHON}" -m uvicorn v40.admin.app:app --host "${V40_ADMIN_HOST}" --port "${V40_ADMIN_PORT}"
