#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
V19_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${V19_DIR}/.." && pwd)"

PYTHON_BIN="${PYTHON_BIN:-python3}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-9019}"
URL="http://${HOST}:${PORT}"

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

cd "${REPO_ROOT}"

"${PYTHON_BIN}" -m uvicorn v19.server:app --host "${HOST}" --port "${PORT}" &
SERVER_PID=$!

cleanup() {
  if kill -0 "${SERVER_PID}" >/dev/null 2>&1; then
    kill "${SERVER_PID}" >/dev/null 2>&1 || true
  fi
}

trap cleanup INT TERM EXIT

for _ in {1..40}; do
  if "${PYTHON_BIN}" - "${URL}/health" <<'PY' >/dev/null 2>&1
import sys
import urllib.request

urllib.request.urlopen(sys.argv[1], timeout=0.25).read()
PY
  then
    break
  fi
  sleep 0.25
done

echo "V19 backend API: ${URL}/api/agent/turn"
echo "V19 frontend:    ${URL}"

if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "${URL}" >/dev/null 2>&1 || true
fi

wait "${SERVER_PID}"
