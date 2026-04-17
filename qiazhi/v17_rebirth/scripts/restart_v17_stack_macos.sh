#!/usr/bin/env bash
set -euo pipefail

GREEN="\033[0;32m"
YELLOW="\033[1;33m"
BLUE="\033[0;34m"
RED="\033[0;31m"
NC="\033[0m"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
QIAZHI_ROOT="${PROJECT_DIR%/v17_rebirth}"
FRONTEND_DIR="${PROJECT_DIR}/frontend"
BACKEND_HOST="127.0.0.1"
BACKEND_PORT="8017"
FRONTEND_PORT="3001"
RUNLOG_DIR="${PROJECT_DIR}/.runlogs"
BACKEND_LOG="${RUNLOG_DIR}/backend-${BACKEND_PORT}.log"
FRONTEND_LOG="${RUNLOG_DIR}/frontend-${FRONTEND_PORT}.log"
BACKEND_PID_FILE="${RUNLOG_DIR}/backend-${BACKEND_PORT}.pid"
FRONTEND_PID_FILE="${RUNLOG_DIR}/frontend-${FRONTEND_PORT}.pid"

mkdir -p "${RUNLOG_DIR}"

print_step() {
  echo -e "${BLUE}$1${NC}"
}

kill_pid_file_if_alive() {
  local pid_file="$1"
  if [[ -f "${pid_file}" ]]; then
    local pid
    pid="$(cat "${pid_file}" 2>/dev/null || true)"
    if [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null; then
      kill "${pid}" 2>/dev/null || true
      sleep 1
      if kill -0 "${pid}" 2>/dev/null; then
        kill -9 "${pid}" 2>/dev/null || true
      fi
    fi
    rm -f "${pid_file}"
  fi
}

kill_port_listener() {
  local port="$1"
  local pids
  pids="$(lsof -ti tcp:"${port}" 2>/dev/null || true)"
  if [[ -n "${pids}" ]]; then
    echo -e "${YELLOW}Killing processes on port ${port}: ${pids}${NC}"
    echo "${pids}" | xargs kill 2>/dev/null || true
    sleep 1
    pids="$(lsof -ti tcp:"${port}" 2>/dev/null || true)"
    if [[ -n "${pids}" ]]; then
      echo "${pids}" | xargs kill -9 2>/dev/null || true
    fi
  fi
}

check_http_code() {
  local label="$1"
  local url="$2"
  local retries="${3:-10}"
  local delay="${4:-1}"
  local code="000"
  local i

  for ((i = 1; i <= retries; i++)); do
    code="$(curl -sS -m 5 -o /dev/null -w "%{http_code}" "${url}" || true)"
    if [[ "${code}" =~ ^2|^3 ]]; then
      echo -e "${GREEN}${label} ready: HTTP ${code}${NC}"
      CHECK_HTTP_CODE_RESULT="${code}"
      return 0
    fi
    sleep "${delay}"
  done

  echo -e "${RED}${label} not ready: HTTP ${code}${NC}"
  CHECK_HTTP_CODE_RESULT="${code}"
  return 1
}

if ! command -v node >/dev/null 2>&1; then
  echo -e "${RED}node not found. Please install Node.js >= 20.9 first.${NC}"
  exit 1
fi

node_major="$(node -p 'Number(process.versions.node.split(".")[0])' 2>/dev/null || echo 0)"
echo -e "${BLUE}Node in use:${NC} $(node -v) ($(command -v node))"
if (( node_major < 20 )); then
  echo -e "${RED}Node version too old for Next.js build. Need >= 20.9.0${NC}"
  exit 1
fi

if ! command -v uvicorn >/dev/null 2>&1; then
  if [[ -x "${QIAZHI_ROOT}/.venv/bin/uvicorn" ]]; then
    UVICORN_CMD="${QIAZHI_ROOT}/.venv/bin/uvicorn"
  else
    echo -e "${RED}uvicorn not found. Please activate python env or install uvicorn.${NC}"
    exit 1
  fi
else
  UVICORN_CMD="$(command -v uvicorn)"
fi

print_step "[1/5] Prepare process state..."
kill_pid_file_if_alive "${BACKEND_PID_FILE}"
kill_pid_file_if_alive "${FRONTEND_PID_FILE}"
kill_port_listener "${BACKEND_PORT}"
kill_port_listener "${FRONTEND_PORT}"

print_step "[2/5] Build frontend (production)..."
if command -v pnpm >/dev/null 2>&1; then
  if [[ -f "${FRONTEND_DIR}/pnpm-lock.yaml" ]]; then
    pnpm --dir "${FRONTEND_DIR}" install --frozen-lockfile
  else
    pnpm --dir "${FRONTEND_DIR}" install
  fi
  pnpm --dir "${FRONTEND_DIR}" build
  FRONTEND_START_CMD=(pnpm start -p "${FRONTEND_PORT}")
elif command -v npm >/dev/null 2>&1; then
  npm --prefix "${FRONTEND_DIR}" install
  npm --prefix "${FRONTEND_DIR}" run build
  FRONTEND_START_CMD=(npm --prefix "${FRONTEND_DIR}" run start -- -p "${FRONTEND_PORT}")
else
  echo -e "${RED}Neither pnpm nor npm found. Install one package manager first.${NC}"
  exit 1
fi

print_step "[3/5] Start backend + frontend..."
(
  cd "${PROJECT_DIR}"
  PYTHONPATH="${PROJECT_DIR%/v17_rebirth}" \
  "${UVICORN_CMD}" v17_rebirth.backend.api.app:app --host "${BACKEND_HOST}" --port "${BACKEND_PORT}" \
    >> "${BACKEND_LOG}" 2>&1
) &
echo $! > "${BACKEND_PID_FILE}"

(
  cd "${FRONTEND_DIR}"
  "${FRONTEND_START_CMD[@]}" >> "${FRONTEND_LOG}" 2>&1
) &
echo $! > "${FRONTEND_PID_FILE}"

print_step "[4/5] Health checks..."
BACKEND_URL="http://${BACKEND_HOST}:${BACKEND_PORT}/health"
FRONTEND_URL="http://${BACKEND_HOST}:${FRONTEND_PORT}/v17/oracle"

check_http_code "backend" "${BACKEND_URL}" 15 1 || true
BACKEND_CODE="${CHECK_HTTP_CODE_RESULT:-000}"
check_http_code "frontend" "${FRONTEND_URL}" 20 1 || true
FRONTEND_CODE="${CHECK_HTTP_CODE_RESULT:-000}"

print_step "[5/5] Final status..."
echo -e "${BLUE}backend(${BACKEND_PORT}):${NC} ${BACKEND_CODE}"
echo -e "${BLUE}frontend(${FRONTEND_PORT}):${NC} ${FRONTEND_CODE}"
echo -e "${BLUE}backend pid:${NC} $(cat "${BACKEND_PID_FILE}")"
echo -e "${BLUE}frontend pid:${NC} $(cat "${FRONTEND_PID_FILE}")"
echo -e "${BLUE}backend log:${NC} ${BACKEND_LOG}"
echo -e "${BLUE}frontend log:${NC} ${FRONTEND_LOG}"

if [[ ! "${BACKEND_CODE}" =~ ^2|^3 ]] || [[ ! "${FRONTEND_CODE}" =~ ^2|^3 ]]; then
  echo -e "${YELLOW}One or more checks failed. Inspect logs above.${NC}"
  exit 1
fi

echo -e "${GREEN}V17 stack restarted successfully on macOS.${NC}"
