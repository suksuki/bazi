#!/usr/bin/env bash
set -euo pipefail

GREEN="\033[0;32m"
YELLOW="\033[1;33m"
BLUE="\033[0;34m"
RED="\033[0;31m"
NC="\033[0m"

# V17.23-Red: Redis 状态后端配置
# 若已设置 QIAZHI_REDIS_URL 环境变量则使用现有值；否则默认本机 Redis
export QIAZHI_REDIS_URL="${QIAZHI_REDIS_URL:-redis://127.0.0.1:6379/0}"

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
    # 轮询期 stderr 静音：避免「首包未就绪」时刷屏 curl: (7) Couldn't connect
    code="$(curl -sS -m 5 -o /dev/null -w "%{http_code}" "${url}" 2>/dev/null || true)"
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

# 固定使用 qiazhi/.venv（Python 3.12），避免误用全局旧版解释器
VENV_DIR="${QIAZHI_ROOT}/.venv"
VENV_PY="${VENV_DIR}/bin/python"

_venv_python_ok() {
  [[ -x "${VENV_PY}" ]] || return 1
  "${VENV_PY}" -c "import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 12) else 1)" 2>/dev/null
}

_venv_has_uvicorn() {
  "${VENV_PY}" -c "import uvicorn" 2>/dev/null
}

if [[ -x "${VENV_PY}" ]] && _venv_python_ok && _venv_has_uvicorn; then
  UVICORN_LAUNCH=("${VENV_PY}" "-m" "uvicorn")
  echo -e "${BLUE}Backend Python:${NC} $("${VENV_PY}" -V) (${VENV_PY})"
elif [[ -x "${VENV_PY}" ]] && ! _venv_python_ok; then
  echo -e "${RED}发现 ${VENV_DIR} 但不是 Python 3.12+。请删除后重建:${NC}" >&2
  echo -e "  rm -rf \"${VENV_DIR}\"" >&2
  echo -e "  ./qiazhi/v17_rebirth/scripts/bootstrap_qiazhi_venv_312.sh" >&2
  exit 1
elif [[ -x "${VENV_PY}" ]] && _venv_python_ok && ! _venv_has_uvicorn; then
  echo -e "${RED}${VENV_PY} 为 3.12 但未安装 uvicorn。请执行:${NC}" >&2
  echo -e "  \"${VENV_PY}\" -m pip install 'uvicorn[standard]'" >&2
  echo -e "  或重新跑: ./qiazhi/v17_rebirth/scripts/bootstrap_qiazhi_venv_312.sh" >&2
  exit 1
else
  echo -e "${RED}未找到 ${VENV_DIR}（需 Python 3.12 venv）。请先执行:${NC}" >&2
  echo -e "  ./qiazhi/v17_rebirth/scripts/bootstrap_qiazhi_venv_312.sh" >&2
  exit 1
fi

print_step "[1/5] Prepare process state..."
# V17.16：清理可能占用 8017 或挂死的 gunicorn / 旧 worker（无进程时静默成功）
pkill -f gunicorn 2>/dev/null || true
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
# V17.16：Uvicorn 无 Gunicorn 式 --no-buffer；有 stdbuf 时行缓冲 stdout/stderr（否则仅 PYTHONUNBUFFERED）。
# 注意：set -u 下勿展开空数组 "${arr[@]}"（macOS bash 3.2 会报 unbound variable），改用分支调用。
(
  cd "${PROJECT_DIR}"
  export PYTHONPATH="${PROJECT_DIR%/v17_rebirth}"
  export PYTHONUNBUFFERED=1
  export QIAZHI_REDIS_URL="${QIAZHI_REDIS_URL:-redis://127.0.0.1:6379/0}"
  if command -v stdbuf >/dev/null 2>&1; then
    stdbuf -oL -eL "${UVICORN_LAUNCH[@]}" v17_rebirth.backend.api.app:app --host "${BACKEND_HOST}" --port "${BACKEND_PORT}" \
      --proxy-headers --timeout-keep-alive 75 \
      >> "${BACKEND_LOG}" 2>&1
  else
    "${UVICORN_LAUNCH[@]}" v17_rebirth.backend.api.app:app --host "${BACKEND_HOST}" --port "${BACKEND_PORT}" \
      --proxy-headers --timeout-keep-alive 75 \
      >> "${BACKEND_LOG}" 2>&1
  fi
) &
echo $! > "${BACKEND_PID_FILE}"

(
  cd "${FRONTEND_DIR}"
  "${FRONTEND_START_CMD[@]}" >> "${FRONTEND_LOG}" 2>&1
) &
echo $! > "${FRONTEND_PID_FILE}"

# 给 uvicorn / Next 一点时间 bind 端口，减少首轮 curl 失败
sleep 0.6

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
