#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

PY=python3
command -v python3 >/dev/null 2>&1 || PY=python

echo "==> synthetic lab =="
"$PY" -m pytest v17_rebirth/tests -m synthetic -q

