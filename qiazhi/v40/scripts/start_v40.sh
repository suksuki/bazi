#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
V40_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${V40_ROOT}/../.." && pwd)"
DEFAULT_V40_PYTHON="${REPO_ROOT}/qiazhi/.venv312/bin/python"

cd "${V40_ROOT}"

if [ -f "${V40_ROOT}/.env.v40.local" ]; then
  set -a
  . "${V40_ROOT}/.env.v40.local"
  set +a
fi

export V40_HOST="${V40_HOST:-127.0.0.1}"
export V40_PORT="${V40_PORT:-9040}"
export V40_RUNTIME_DIR="${V40_RUNTIME_DIR:-.runtime}"
export V40_REDIS_PREFIX="${V40_REDIS_PREFIX:-v40}"
if [ -z "${V40_PYTHON:-}" ] && [ -x "${DEFAULT_V40_PYTHON}" ]; then
  export V40_PYTHON="${DEFAULT_V40_PYTHON}"
else
  export V40_PYTHON="${V40_PYTHON:-python3.12}"
fi

exec "${V40_PYTHON}" -m uvicorn v40.api.app:app --host "${V40_HOST}" --port "${V40_PORT}"
