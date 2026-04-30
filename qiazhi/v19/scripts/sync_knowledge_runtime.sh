#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
V19_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_ROOT="$(cd "${V19_DIR}/.." && pwd)"

BASE_URL="${BASE_URL:-http://127.0.0.1:9019}"
ROLE="${ROLE:-admin}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
RUNTIME_DIR="${RUNTIME_DIR:-${V19_DIR}/.runtime}"
BACKUP_RUNTIME="${BACKUP_RUNTIME:-1}"
BACKUP_DIR="${BACKUP_DIR:-${HOME:-${PROJECT_ROOT}}}"
INGEST_RULE_DB="${INGEST_RULE_DB:-1}"
ENABLE_ENGINE="${ENABLE_ENGINE:-1}"
RUN_AUDIT="${RUN_AUDIT:-1}"
SAVE_AUDIT="${SAVE_AUDIT:-1}"

cd "${PROJECT_ROOT}"

get_json() {
  local path="$1"
  curl -sS "${BASE_URL}${path}?role=${ROLE}"
  printf '\n'
}

post_json() {
  local path="$1"
  local body="$2"
  curl -sS -X POST "${BASE_URL}${path}?role=${ROLE}" \
    -H "Content-Type: application/json" \
    -d "$body"
  printf '\n'
}

echo "V19 knowledge sync: base=${BASE_URL} role=${ROLE}"

if ! "${PYTHON_BIN}" - "${BASE_URL}/health" <<'PY' >/dev/null 2>&1
import sys
import urllib.request

urllib.request.urlopen(sys.argv[1], timeout=1).read()
PY
then
  echo "V19 knowledge sync: server health check failed at ${BASE_URL}/health" >&2
  echo "Start or deploy the service first, then rerun this script." >&2
  exit 1
fi

if [[ "${BACKUP_RUNTIME}" == "1" && -d "${RUNTIME_DIR}" ]]; then
  mkdir -p "${BACKUP_DIR}"
  backup_file="${BACKUP_DIR}/qiazhi-v19-runtime-sync-$(date +%Y%m%d-%H%M%S).tgz"
  echo "V19 knowledge sync: backing up runtime to ${backup_file}"
  tar -czf "${backup_file}" -C "${PROJECT_ROOT}" "v19/.runtime"
fi

echo "V19 knowledge sync: seed reviewed knowledge units"
post_json "/api/admin/knowledge/seed" '{"force": true}'

echo "V19 knowledge sync: seed source archive catalog"
post_json "/api/admin/bazi-source-archive/seed" '{"force": false}'

echo "V19 knowledge sync: seed current knowledge drafts"
post_json "/api/admin/bazi-source-archive/knowledge-drafts/seed-current" '{"force": true}'

if [[ "${INGEST_RULE_DB}" == "1" ]]; then
  echo "V19 knowledge sync: ingest current drafts into Rule DB"
  if [[ "${ENABLE_ENGINE}" == "1" ]]; then
    post_json "/api/admin/bazi-rule-db/ingest-current" '{"force": false, "enable_engine": true}'
  else
    post_json "/api/admin/bazi-rule-db/ingest-current" '{"force": false, "enable_engine": false}'
  fi
else
  echo "V19 knowledge sync: Rule DB ingestion skipped. Set INGEST_RULE_DB=1 to run it."
fi

echo "V19 knowledge sync: status snapshot"
get_json "/api/admin/knowledge/status"
get_json "/api/admin/bazi-source-archive/status"
get_json "/api/admin/bazi-rule-db/status"

if [[ "${RUN_AUDIT}" == "1" ]]; then
  echo "V19 knowledge sync: structural rule signal audit"
  "${PYTHON_BIN}" "${SCRIPT_DIR}/p9_rule_signal_review.py" --base-url "${BASE_URL}" --role "${ROLE}"

  echo "V19 knowledge sync: knowledge -> Rule DB coverage audit"
  "${PYTHON_BIN}" "${SCRIPT_DIR}/p9_knowledge_rule_coverage.py" --base-url "${BASE_URL}" --role "${ROLE}"

  echo "V19 knowledge sync: guided answer quality audit"
  BASE_URL="${BASE_URL}" ROLE="${ROLE}" SAVE_AUDIT="${SAVE_AUDIT}" "${SCRIPT_DIR}/p7_answer_quality_audit.sh"
fi

echo "V19 knowledge sync: done"
