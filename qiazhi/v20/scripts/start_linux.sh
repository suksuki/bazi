#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/../.."

source "${SCRIPT_DIR}/_python.sh"
HOST="${V20_HOST:-0.0.0.0}"
PORT="${V20_PORT:-9020}"

export PYTHONPATH="${PWD}:${PYTHONPATH:-}"
export V20_ENV="${V20_ENV:-linux_0_13}"

exec "${PYTHON_BIN}" -m uvicorn v20.server:app --host "${HOST}" --port "${PORT}"
