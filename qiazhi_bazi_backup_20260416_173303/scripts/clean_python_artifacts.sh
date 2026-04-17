#!/usr/bin/env bash
# V13.0：清理仓库内 Python 字节码与 pytest 缓存（不触碰 .venv）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
find "$ROOT/qiazhi_bazi/backend" -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
find "$ROOT/qiazhi_bazi/backend" -type f -name '*.pyc' -delete 2>/dev/null || true
find "$ROOT/qiazhi_bazi/backend" -type d -name .pytest_cache -prune -exec rm -rf {} + 2>/dev/null || true
echo "clean_python_artifacts: done under qiazhi_bazi/backend"
