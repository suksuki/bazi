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

export V40_ADMIN_HOST="${V40_ADMIN_HOST:-127.0.0.1}"
export V40_ADMIN_PORT="${V40_ADMIN_PORT:-9041}"
export V40_API_BASE="${V40_API_BASE:-http://127.0.0.1:9040}"
if [ -z "${V40_PYTHON:-}" ] && [ -x "${DEFAULT_V40_PYTHON}" ]; then
  export V40_PYTHON="${DEFAULT_V40_PYTHON}"
else
  export V40_PYTHON="${V40_PYTHON:-python3.12}"
fi

exec "${V40_PYTHON}" -m uvicorn v40.admin.app:app --host "${V40_ADMIN_HOST}" --port "${V40_ADMIN_PORT}"
