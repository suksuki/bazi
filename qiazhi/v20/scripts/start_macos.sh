#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

PYTHON_BIN="${PYTHON_BIN:-python3}"
HOST="${V20_HOST:-127.0.0.1}"
PORT="${V20_PORT:-9020}"

export PYTHONPATH="${PWD}:${PYTHONPATH:-}"
export V20_ENV="${V20_ENV:-local_macos}"

"${PYTHON_BIN}" -m uvicorn v20.server:app --host "${HOST}" --port "${PORT}"
