#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
V19_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${V19_DIR}/.." && pwd)"
source "${SCRIPT_DIR}/server_process.sh"

PYTHON_BIN="${PYTHON_BIN:-python3}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-9019}"
URL="http://${HOST}:${PORT}"
RUNTIME_DIR="${RUNTIME_DIR:-${V19_DIR}/.runtime}"
LOG_FILE="${LOG_FILE:-${RUNTIME_DIR}/server_${PORT}.log}"
PID_FILE="${PID_FILE:-${RUNTIME_DIR}/server_${PORT}.pid}"

export PYTHONPATH="${REPO_ROOT}:${PYTHONPATH:-}"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "python3 not found. Install Python 3 or set PYTHON_BIN=/path/to/python3." >&2
  exit 1
fi

if ! "${PYTHON_BIN}" - <<'PY' >/dev/null 2>&1
import fastapi
import lunar_python
import uvicorn
PY
then
  echo "Missing Python dependencies. Install fastapi, uvicorn, and lunar-python for this Python." >&2
  echo "Example: ${PYTHON_BIN} -m pip install fastapi uvicorn lunar-python" >&2
  exit 1
fi

v19_stop_existing_server "${PORT}" "${PID_FILE}"
v19_start_server_detached "${PYTHON_BIN}" "${REPO_ROOT}" "${HOST}" "${PORT}" "${LOG_FILE}" "${PID_FILE}"

if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "${URL}" >/dev/null 2>&1 || true
fi
