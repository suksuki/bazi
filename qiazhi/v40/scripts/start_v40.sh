#!/usr/bin/env bash
set -euo pipefail

if [ -f ".env.v40.local" ]; then
  set -a
  . ".env.v40.local"
  set +a
fi

export V40_HOST="${V40_HOST:-127.0.0.1}"
export V40_PORT="${V40_PORT:-9040}"
export V40_RUNTIME_DIR="${V40_RUNTIME_DIR:-.runtime}"
export V40_REDIS_PREFIX="${V40_REDIS_PREFIX:-v40}"
export V40_PYTHON="${V40_PYTHON:-python3}"

exec "${V40_PYTHON}" -m uvicorn v40.api.app:app --host "${V40_HOST}" --port "${V40_PORT}"
