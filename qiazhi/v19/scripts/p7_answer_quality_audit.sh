#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BASE_URL="${BASE_URL:-http://127.0.0.1:9019}"
ROLE="${ROLE:-admin}"
SAVE_AUDIT="${SAVE_AUDIT:-1}"

cd "$PROJECT_ROOT"

echo "P7 audit: guided question answer matrix"
if [[ "$SAVE_AUDIT" == "1" ]]; then
  python3 "$PROJECT_ROOT/v19/scripts/guided_question_audit_matrix.py" --base-url "$BASE_URL" --role "$ROLE" --save
else
  python3 "$PROJECT_ROOT/v19/scripts/guided_question_audit_matrix.py" --base-url "$BASE_URL" --role "$ROLE"
fi

echo "P7 report: answer quality ledger"
python3 "$PROJECT_ROOT/v19/scripts/p7_answer_quality_report.py" --base-url "$BASE_URL" --role "$ROLE"
