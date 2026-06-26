#!/usr/bin/env bash
set -euo pipefail

if [[ -f ".env.v30.real" ]]; then
  set -a
  # shellcheck disable=SC1091
  source ".env.v30.real"
  set +a
fi

export V30_HOST="${V30_HOST:-0.0.0.0}"
export V30_PORT="${V30_PORT:-9030}"
export V30_REPOSITORY="${V30_REPOSITORY:-postgres}"
export V30_REDIS_PREFIX="${V30_REDIS_PREFIX:-v30}"
export V30_RUNTIME_DIR="${V30_RUNTIME_DIR:-/home/hlsystem/bazi/qiazhi/v30/.runtime}"

python3 -m uvicorn v30.api.app:app --host "${V30_HOST}" --port "${V30_PORT}"
