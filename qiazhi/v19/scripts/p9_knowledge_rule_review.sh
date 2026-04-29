#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BASE_URL="${BASE_URL:-http://127.0.0.1:9019}"
ROLE="${ROLE:-admin}"
SAVE_AUDIT="${SAVE_AUDIT:-1}"
INGEST_RULE_DB="${INGEST_RULE_DB:-1}"

cd "$PROJECT_ROOT"

echo "P9 seed/review: runtime knowledge + drafts + Rule DB"
BASE_URL="$BASE_URL" ROLE="$ROLE" SAVE_AUDIT="$SAVE_AUDIT" INGEST_RULE_DB="$INGEST_RULE_DB" "$PROJECT_ROOT/v19/scripts/p6_seed_and_audit.sh"

echo "P9 review: structural rule signals"
python3 "$PROJECT_ROOT/v19/scripts/p9_rule_signal_review.py" --base-url "$BASE_URL" --role "$ROLE"

echo "P9 review: knowledge -> Rule DB -> structural signal coverage"
python3 "$PROJECT_ROOT/v19/scripts/p9_knowledge_rule_coverage.py" --base-url "$BASE_URL" --role "$ROLE"

echo "P9 review: answer quality"
python3 "$PROJECT_ROOT/v19/scripts/p7_answer_quality_report.py" --base-url "$BASE_URL" --role "$ROLE"
