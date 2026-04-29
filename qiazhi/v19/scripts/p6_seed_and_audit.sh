#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:9019}"
ROLE="${ROLE:-admin}"
SAVE_AUDIT="${SAVE_AUDIT:-1}"
INGEST_RULE_DB="${INGEST_RULE_DB:-0}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

post_json() {
  local path="$1"
  local body="$2"
  curl -sS -X POST "${BASE_URL}${path}?role=${ROLE}" \
    -H "Content-Type: application/json" \
    -d "$body"
  printf '\n'
}

echo "P6 seed: runtime knowledge units"
post_json "/api/admin/knowledge/seed" '{"force": true}'

echo "P6 seed: current knowledge draft seeds"
post_json "/api/admin/bazi-source-archive/knowledge-drafts/seed-current" '{"force": true}'

if [[ "$INGEST_RULE_DB" == "1" ]]; then
  echo "P6 optional: ingest current knowledge drafts into Bazi Rule DB"
  post_json "/api/admin/bazi-rule-db/ingest-current" '{"force": false, "enable_engine": true}'
else
  echo "P6 optional Rule DB ingestion skipped. Set INGEST_RULE_DB=1 to run it."
fi

echo "P6 audit: guided question matrix"
if [[ "$SAVE_AUDIT" == "1" ]]; then
  python3 "$PROJECT_ROOT/v19/scripts/guided_question_audit_matrix.py" --base-url "$BASE_URL" --role "$ROLE" --save
else
  python3 "$PROJECT_ROOT/v19/scripts/guided_question_audit_matrix.py" --base-url "$BASE_URL" --role "$ROLE"
fi
