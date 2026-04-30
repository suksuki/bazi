#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
V19_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
APP_ROOT="$(cd "${V19_DIR}/.." && pwd)"
GIT_ROOT="$(git -C "${APP_ROOT}" rev-parse --show-toplevel 2>/dev/null || true)"
source "${SCRIPT_DIR}/server_process.sh"

PYTHON_BIN="${PYTHON_BIN:-python3}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-9019}"
URL="http://${HOST}:${PORT}"
RUNTIME_DIR="${RUNTIME_DIR:-${V19_DIR}/.runtime}"
LOG_FILE="${LOG_FILE:-${RUNTIME_DIR}/server_${PORT}.log}"
PID_FILE="${PID_FILE:-${RUNTIME_DIR}/server_${PORT}.pid}"
REMOTE="${REMOTE:-origin}"
BRANCH="${BRANCH:-main}"
FORCE_SYNC="${FORCE_SYNC:-0}"
STOP_EXISTING="${STOP_EXISTING:-1}"
USE_SYSTEMD="${USE_SYSTEMD:-0}"
SERVICE_NAME="${SERVICE_NAME:-qiazhi-v19}"
RUN_P6="${RUN_P6:-0}"
RUN_P7="${RUN_P7:-0}"
RUN_P9="${RUN_P9:-0}"
ROLE="${ROLE:-admin}"
SAVE_AUDIT="${SAVE_AUDIT:-1}"
INGEST_RULE_DB="${INGEST_RULE_DB:-0}"

export PYTHONPATH="${APP_ROOT}:${PYTHONPATH:-}"

cd "${APP_ROOT}"

echo "V19 deploy: app=${APP_ROOT} branch=${BRANCH} port=${PORT}"

if [[ -n "${GIT_ROOT}" && -d "${GIT_ROOT}/.git" ]]; then
  echo "V19 deploy: git=${GIT_ROOT}"
  cd "${GIT_ROOT}"
  echo "V19 deploy: fetching ${REMOTE}/${BRANCH}"
  git fetch --prune "${REMOTE}"
  if [[ "${FORCE_SYNC}" == "1" ]]; then
    echo "V19 deploy: FORCE_SYNC=1, resetting to ${REMOTE}/${BRANCH}"
    git reset --hard "${REMOTE}/${BRANCH}"
    git clean -fd \
      -e "v19/.runtime/" \
      -e ".venv/" \
      -e "v19/.venv/" \
      -e "qiazhi/v19/.runtime/" \
      -e "qiazhi/.venv/" \
      -e "qiazhi/v19/.venv/" \
      -e "db_backups/"
  else
    echo "V19 deploy: fast-forward pull"
    git pull --ff-only "${REMOTE}" "${BRANCH}"
  fi
  cd "${APP_ROOT}"
else
  echo "V19 deploy: no git repository found from ${APP_ROOT}; skipping sync" >&2
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

if [[ "${USE_SYSTEMD}" == "1" ]]; then
  if ! command -v systemctl >/dev/null 2>&1; then
    echo "USE_SYSTEMD=1 requires systemctl on the server." >&2
    exit 1
  fi
  if ! systemctl cat "${SERVICE_NAME}.service" >/dev/null 2>&1; then
    echo "Systemd service ${SERVICE_NAME}.service is not installed." >&2
    echo "Run: HOST=${HOST} PORT=${PORT} SERVICE_NAME=${SERVICE_NAME} ${SCRIPT_DIR}/install_systemd_service.sh" >&2
    exit 1
  fi

  echo "V19 deploy: restarting systemd service ${SERVICE_NAME}"
  sudo systemctl stop "${SERVICE_NAME}.service" >/dev/null 2>&1 || true
  if [[ "${STOP_EXISTING}" == "1" ]]; then
    v19_stop_existing_server "${PORT}" "${PID_FILE}"
  fi
  sudo systemctl start "${SERVICE_NAME}.service"
  if ! v19_wait_for_url "${PYTHON_BIN}" "${URL}" 80; then
    echo "V19 deploy: health check failed at ${URL}/health" >&2
    sudo systemctl status "${SERVICE_NAME}.service" --no-pager >&2 || true
    journalctl -u "${SERVICE_NAME}.service" -n 60 --no-pager >&2 || true
    exit 1
  fi
  echo "V19 systemd service: ${SERVICE_NAME}"
  echo "V19 backend API: ${URL}/api/agent/turn"
  echo "V19 frontend:    ${URL}"
else
  if [[ "${STOP_EXISTING}" == "1" ]]; then
    v19_stop_existing_server "${PORT}" "${PID_FILE}"
  fi
  echo "V19 deploy: starting server at ${URL}"
  v19_start_server_detached "${PYTHON_BIN}" "${APP_ROOT}" "${HOST}" "${PORT}" "${LOG_FILE}" "${PID_FILE}"
fi

if [[ "${RUN_P9}" == "1" ]]; then
  echo "V19 deploy: running P9 knowledge/rule-signal review"
  if ! BASE_URL="${URL}" ROLE="${ROLE}" SAVE_AUDIT="${SAVE_AUDIT}" INGEST_RULE_DB="${INGEST_RULE_DB:-1}" "${SCRIPT_DIR}/p9_knowledge_rule_review.sh"; then
    echo "V19 deploy warning: P9 knowledge/rule-signal review reported issues; server remains running" >&2
  fi
elif [[ "${RUN_P6}" == "1" ]]; then
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
