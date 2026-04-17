#!/usr/bin/env bash
# 在 qiazhi/.venv 下创建 Python 3.12 虚拟环境并安装仓库根目录 requirements.txt
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
QIAZHI_ROOT="${PROJECT_DIR%/v17_rebirth}"
BAZI_ROOT="$(cd "${QIAZHI_ROOT}/.." && pwd)"
REQ="${BAZI_ROOT}/requirements.txt"
VENV="${QIAZHI_ROOT}/.venv"

if [[ ! -f "${REQ}" ]]; then
  echo "找不到依赖清单: ${REQ}" >&2
  exit 1
fi

if ! command -v python3.12 >/dev/null 2>&1; then
  echo "未找到 python3.12。请先安装（例: brew install python@3.12），并确保 PATH 中有 python3.12。" >&2
  exit 1
fi

echo "使用: $(command -v python3.12) — $(python3.12 -V)"
echo "目标 venv: ${VENV}"

rm -rf "${VENV}"
python3.12 -m venv "${VENV}"
"${VENV}/bin/pip" install -U pip
"${VENV}/bin/pip" install -r "${REQ}"

echo ""
echo "完成。当前解释器:"
"${VENV}/bin/python" -V
"${VENV}/bin/python" -m uvicorn --version || true
