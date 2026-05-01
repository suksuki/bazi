#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/../.."

source "${SCRIPT_DIR}/_python.sh"
HOST="${V20_HOST:-127.0.0.1}"
PORT="${V20_PORT:-9020}"

export PYTHONPATH="${PWD}:${PYTHONPATH:-}"
export V20_ENV="${V20_ENV:-local_macos}"

port_pid() {
  command -v lsof >/dev/null 2>&1 || return 1
  lsof -tiTCP:"${PORT}" -sTCP:LISTEN 2>/dev/null | head -n 1
}

if pid="$(port_pid)" && [[ -n "${pid}" ]]; then
  echo "V20 macOS service is already listening on ${HOST}:${PORT} pid=${pid}."
  echo "Use ./v20/scripts/service_macos.sh status | logs | restart, or set V20_PORT to start another instance."
  exit 0
fi

exec "${PYTHON_BIN}" -m uvicorn v20.server:app --host "${HOST}" --port "${PORT}"
