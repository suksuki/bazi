#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/../.."

source "${SCRIPT_DIR}/_python.sh"
HOST="${V20_HOST:-0.0.0.0}"
PORT="${V20_PORT:-9020}"

export PYTHONPATH="${PWD}:${PYTHONPATH:-}"
export V20_ENV="${V20_ENV:-linux_0_13}"

port_pid() {
  if command -v lsof >/dev/null 2>&1; then
    lsof -tiTCP:"${PORT}" -sTCP:LISTEN 2>/dev/null | head -n 1
    return 0
  fi
  if command -v ss >/dev/null 2>&1; then
    ss -ltnp "sport = :${PORT}" 2>/dev/null | sed -n 's/.*pid=\([0-9][0-9]*\).*/\1/p' | head -n 1
    return 0
  fi
  return 1
}

if pid="$(port_pid)" && [[ -n "${pid}" ]]; then
  echo "V20 Linux service is already listening on ${HOST}:${PORT} pid=${pid}."
  echo "Use ./v20/scripts/service_linux.sh status | logs | restart, or set V20_PORT to start another instance."
  exit 0
fi

exec "${PYTHON_BIN}" -m uvicorn v20.server:app --host "${HOST}" --port "${PORT}"
