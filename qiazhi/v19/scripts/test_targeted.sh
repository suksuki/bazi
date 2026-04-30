#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

PYTHON_BIN="${PYTHON_BIN:-python3}"
TARGET_EXPR="${1:-p69 or p68 or p67 or p66 or p65 or p64 or p63 or p62 or p61 or p60 or p59 or p52 or p51 or p50 or p49 or p48 or p47 or p46 or p10_review}"

"${PYTHON_BIN}" -m pytest -q \
  v19/tests/test_p67_p68_multilingual_and_test_tiers.py \
  v19/tests/test_p69_mainline_p1_safe_wrappers.py \
  v19/tests/test_guided_question_p10_review.py \
  v19/tests/test_guided_synthetic_collision.py \
  -k "${TARGET_EXPR}"
