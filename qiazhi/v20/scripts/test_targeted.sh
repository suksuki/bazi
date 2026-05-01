#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

PYTHON_BIN="${PYTHON_BIN:-python3}"
"${PYTHON_BIN}" -m v20.testing.runner targeted "$@"
