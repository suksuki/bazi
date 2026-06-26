#!/usr/bin/env bash
set -euo pipefail

export V30_HOST="${V30_HOST:-127.0.0.1}"
export V30_PORT="${V30_PORT:-9030}"
export V30_RUNTIME_DIR="${V30_RUNTIME_DIR:-.runtime}"
export V30_REDIS_PREFIX="${V30_REDIS_PREFIX:-v30}"

exec python3 -m uvicorn v30.api.app:app --host "${V30_HOST}" --port "${V30_PORT}"
