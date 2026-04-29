#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
V19_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${V19_DIR}/.." && pwd)"

PYTHON_BIN="${PYTHON_BIN:-python3}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-9019}"
URL="http://${HOST}:${PORT}"
REMOTE="${REMOTE:-origin}"
BRANCH="${BRANCH:-main}"
FORCE_SYNC="${FORCE_SYNC:-0}"
STOP_EXISTING="${STOP_EXISTING:-1}"
RUN_P6="${RUN_P6:-0}"
RUN_P7="${RUN_P7:-0}"
ROLE="${ROLE:-admin}"
SAVE_AUDIT="${SAVE_AUDIT:-1}"
INGEST_RULE_DB="${INGEST_RULE_DB:-0}"

export PYTHONPATH="${REPO_ROOT}:${PYTHONPATH:-}"

cd "${REPO_ROOT}"

echo "V19 deploy: repo=${REPO_ROOT} branch=${BRANCH} port=${PORT}"

if [[ -d .git ]]; then
  echo "V19 deploy: fetching ${REMOTE}/${BRANCH}"
  git fetch --prune "${REMOTE}"
  if [[ "${FORCE_SYNC}" == "1" ]]; then
    echo "V19 deploy: FORCE_SYNC=1, resetting to ${REMOTE}/${BRANCH}"
    git reset --hard "${REMOTE}/${BRANCH}"
    git clean -fd -e "v19/.runtime/" -e ".venv/" -e "v19/.venv/"
  else
    echo "V19 deploy: fast-forward pull"
    git pull --ff-only "${REMOTE}" "${BRANCH}"
  fi
else
  echo "V19 deploy: ${REPO_ROOT} is not a git repository; skipping sync" >&2
fi

if [[ "${STOP_EXISTING}" == "1" ]]; then
  if command -v ss >/dev/null 2>&1; then
    mapfile -t PIDS < <(ss -ltnp "( sport = :${PORT} )" 2>/dev/null | sed -n 's/.*pid=\([0-9][0-9]*\).*/\1/p' | sort -u)
    if (( ${#PIDS[@]} > 0 )); then
      echo "V19 deploy: stopping existing process(es) on port ${PORT}: ${PIDS[*]}"
      for pid in "${PIDS[@]}"; do
        kill "${pid}" >/dev/null 2>&1 || true
      done
      sleep 1
      for pid in "${PIDS[@]}"; do
        if kill -0 "${pid}" >/dev/null 2>&1; then
          kill -9 "${pid}" >/dev/null 2>&1 || true
        fi
      done
    fi
  else
    echo "V19 deploy: ss not found; skipping port cleanup" >&2
  fi
fi

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "python3 not found. Install Python 3 or set PYTHON_BIN=/path/to/python3." >&2
  exit 1
fi

if ! "${PYTHON_BIN}" - <<'PY' >/dev/null 2>&1
import fastapi
import uvicorn
PY
then
  echo "Missing Python dependencies. Install fastapi and uvicorn for this Python." >&2
  echo "Example: ${PYTHON_BIN} -m pip install fastapi uvicorn" >&2
  exit 1
fi

echo "V19 deploy: starting server at ${URL}"
"${PYTHON_BIN}" -m uvicorn v19.server:app --host "${HOST}" --port "${PORT}" &
SERVER_PID=$!

cleanup() {
  if kill -0 "${SERVER_PID}" >/dev/null 2>&1; then
    kill "${SERVER_PID}" >/dev/null 2>&1 || true
  fi
}

trap cleanup INT TERM EXIT

for _ in {1..60}; do
  if "${PYTHON_BIN}" - "${URL}/health" <<'PY' >/dev/null 2>&1
import sys
import urllib.request
urllib.request.urlopen(sys.argv[1], timeout=0.25).read()
PY
  then
    break
  fi
  if ! kill -0 "${SERVER_PID}" >/dev/null 2>&1; then
    echo "V19 deploy: server exited before health check passed" >&2
    wait "${SERVER_PID}"
    exit 1
  fi
  sleep 0.25
done

if ! "${PYTHON_BIN}" - "${URL}/health" <<'PY' >/dev/null 2>&1
import sys
import urllib.request
urllib.request.urlopen(sys.argv[1], timeout=1).read()
PY
then
  echo "V19 deploy: health check failed at ${URL}/health" >&2
  exit 1
fi

echo "V19 backend API: ${URL}/api/agent/turn"
echo "V19 frontend:    ${URL}"

if [[ "${RUN_P6}" == "1" ]]; then
  echo "V19 deploy: running P6 seed/audit"
  if ! BASE_URL="${URL}" ROLE="${ROLE}" SAVE_AUDIT="${SAVE_AUDIT}" INGEST_RULE_DB="${INGEST_RULE_DB}" "${SCRIPT_DIR}/p6_seed_and_audit.sh"; then
    echo "V19 deploy warning: P6 seed/audit failed; server remains running" >&2
  fi
fi

if [[ "${RUN_P7}" == "1" ]]; then
  echo "V19 deploy: running P7 answer quality audit"
  if ! BASE_URL="${URL}" ROLE="${ROLE}" SAVE_AUDIT="${SAVE_AUDIT}" "${SCRIPT_DIR}/p7_answer_quality_audit.sh"; then
    echo "V19 deploy warning: P7 quality audit reported issues; server remains running" >&2
  fi
fi

if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "${URL}" >/dev/null 2>&1 || true
fi

wait "${SERVER_PID}"
