#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${ROOT_DIR}"

DEFAULT_RUNTIME_DIR="${V20_RUNTIME_DIR:-v20/.runtime/linux_0_13}"
SERVICE_ENV_FILE="${V20_ENV_FILE:-${DEFAULT_RUNTIME_DIR}/service.env}"
if [[ -f "${SERVICE_ENV_FILE}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${SERVICE_ENV_FILE}"
  set +a
fi

export V20_ENV="${V20_ENV:-linux_0_13}"
export V20_HOST="${V20_HOST:-0.0.0.0}"
export V20_PORT="${V20_PORT:-9020}"
export V20_RUNTIME_DIR="${V20_RUNTIME_DIR:-${DEFAULT_RUNTIME_DIR}}"
export V20_SERVICE_NAME="${V20_SERVICE_NAME:-qiazhi-v20}"

PID_FILE="${V20_PID_FILE:-${V20_RUNTIME_DIR}/service_${V20_PORT}.pid}"
LOG_FILE="${V20_LOG_FILE:-${V20_RUNTIME_DIR}/service_${V20_PORT}.log}"
HEALTH_URL="${V20_HEALTH_URL:-http://127.0.0.1:${V20_PORT}/health}"
SCREEN_NAME="${V20_SCREEN_NAME:-${V20_SERVICE_NAME}}"

usage() {
  cat <<EOF
Usage: $0 {start|stop|restart|status|logs|systemd-unit}

Environment:
  V20_DATABASE_URL, V20_REDIS_URL, V20_LLM_* are passed through from the shell.
  V20_RUNTIME_DIR=${V20_RUNTIME_DIR}
  V20_ENV_FILE=${SERVICE_ENV_FILE}
  V20_PID_FILE=${PID_FILE}
  V20_LOG_FILE=${LOG_FILE}
  V20_SCREEN_NAME=${SCREEN_NAME}
EOF
}

running_pid() {
  local pid=""
  [[ -f "${PID_FILE}" ]] || return 1
  pid="$(cat "${PID_FILE}" 2>/dev/null || true)"
  [[ "${pid}" =~ ^[0-9]+$ ]] || return 1
  kill -0 "${pid}" 2>/dev/null || return 1
  printf '%s\n' "${pid}"
}

port_pid() {
  if command -v lsof >/dev/null 2>&1; then
    lsof -tiTCP:"${V20_PORT}" -sTCP:LISTEN 2>/dev/null | head -n 1
    return 0
  fi
  if command -v ss >/dev/null 2>&1; then
    ss -ltnp "sport = :${V20_PORT}" 2>/dev/null | sed -n 's/.*pid=\([0-9][0-9]*\).*/\1/p' | head -n 1
    return 0
  fi
  return 1
}

start_service() {
  mkdir -p "${V20_RUNTIME_DIR}"
  if pid="$(running_pid)"; then
    echo "V20 Linux service already running pid=${pid}"
    return 0
  fi
  if pid="$(port_pid)" && [[ -n "${pid}" ]]; then
    echo "V20 port ${V20_PORT} already has a listener pid=${pid}; not starting a duplicate."
    return 0
  fi
  rm -f "${PID_FILE}"
  touch "${LOG_FILE}"
  echo "Starting V20 Linux service on ${V20_HOST}:${V20_PORT}"
  if command -v screen >/dev/null 2>&1; then
    screen -S "${SCREEN_NAME}" -X quit >/dev/null 2>&1 || true
    screen -dmS "${SCREEN_NAME}" bash -lc "cd '${ROOT_DIR}' && exec '${SCRIPT_DIR}/start_linux.sh' >> '${LOG_FILE}' 2>&1"
  else
    nohup "${SCRIPT_DIR}/start_linux.sh" >>"${LOG_FILE}" 2>&1 &
  fi
  for _ in {1..40}; do
    if pid="$(port_pid)" && [[ -n "${pid}" ]]; then
      echo "${pid}" >"${PID_FILE}"
      break
    fi
    sleep 0.25
  done
  if pid="$(running_pid)"; then
    echo "V20 Linux service running pid=${pid}"
    echo "Log: ${LOG_FILE}"
    return 0
  fi
  echo "V20 Linux service failed to start. Last log lines:"
  tail -n 40 "${LOG_FILE}" || true
  return 1
}

stop_service() {
  local pid=""
  if ! pid="$(running_pid)"; then
    rm -f "${PID_FILE}"
    if pid="$(port_pid)" && [[ -n "${pid}" ]]; then
      echo "Stopping unmanaged V20 Linux listener on port ${V20_PORT} pid=${pid}"
      kill "${pid}" 2>/dev/null || true
      for _ in {1..20}; do
        kill -0 "${pid}" 2>/dev/null || break
        sleep 0.25
      done
      if kill -0 "${pid}" 2>/dev/null; then
        echo "Force stopping unmanaged pid=${pid}"
        kill -KILL "${pid}" 2>/dev/null || true
      fi
      echo "Stopped unmanaged V20 Linux listener"
      screen -S "${SCREEN_NAME}" -X quit >/dev/null 2>&1 || true
      return 0
    fi
    screen -S "${SCREEN_NAME}" -X quit >/dev/null 2>&1 || true
    echo "V20 Linux service is not running"
    return 0
  fi
  echo "Stopping V20 Linux service pid=${pid}"
  kill "${pid}" 2>/dev/null || true
  for _ in {1..20}; do
    kill -0 "${pid}" 2>/dev/null || break
    sleep 0.25
  done
  if kill -0 "${pid}" 2>/dev/null; then
    echo "Force stopping pid=${pid}"
    kill -KILL "${pid}" 2>/dev/null || true
  fi
  rm -f "${PID_FILE}"
  screen -S "${SCREEN_NAME}" -X quit >/dev/null 2>&1 || true
  echo "Stopped V20 Linux service"
}

status_service() {
  local pid=""
  if pid="$(running_pid)"; then
    echo "running pid=${pid}"
    if command -v curl >/dev/null 2>&1; then
      curl -fsS "${HEALTH_URL}" || true
      echo
    fi
    return 0
  fi
  if pid="$(port_pid)" && [[ -n "${pid}" ]]; then
    echo "port ${V20_PORT} listening pid=${pid} (not managed by ${PID_FILE})"
    return 0
  fi
  echo "stopped"
  return 1
}

show_logs() {
  mkdir -p "${V20_RUNTIME_DIR}"
  touch "${LOG_FILE}"
  if [[ "${1:-}" == "--follow" || "${1:-}" == "-f" ]]; then
    tail -n "${V20_LOG_LINES:-80}" -F "${LOG_FILE}"
  else
    tail -n "${V20_LOG_LINES:-80}" "${LOG_FILE}"
  fi
}

systemd_unit() {
  cat <<EOF
[Unit]
Description=Qiazhi V20 Bazi Measurement Service
After=network.target

[Service]
Type=simple
WorkingDirectory=${ROOT_DIR}
Environment=V20_ENV=linux_0_13
Environment=V20_HOST=0.0.0.0
Environment=V20_PORT=${V20_PORT}
Environment=PYTHONPATH=${ROOT_DIR}
ExecStart=${SCRIPT_DIR}/start_linux.sh
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
}

case "${1:-}" in
  start) start_service ;;
  stop) stop_service ;;
  restart) stop_service; start_service ;;
  status) status_service ;;
  logs) shift; show_logs "$@" ;;
  systemd-unit) systemd_unit ;;
  -h|--help|help|"") usage ;;
  *) usage; exit 2 ;;
esac
