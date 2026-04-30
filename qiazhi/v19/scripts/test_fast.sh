#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

PYTHON_BIN="${PYTHON_BIN:-python3}"

"${PYTHON_BIN}" -m py_compile \
  v19/server.py \
  v19/bazi_guided_questions.py \
  v19/agent/renderers.py \
  v19/rule_graph_orchestrator.py \
  v19/synthetic_validation/mainline_completion_audit.py

"${PYTHON_BIN}" -m json.tool docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json >/dev/null

"${PYTHON_BIN}" -m pytest -q v19/tests/test_p67_p68_multilingual_and_test_tiers.py
