#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${ROOT_DIR}"

export V20_ENV="${V20_ENV:-local_macos}"
export V20_HOST="${V20_HOST:-127.0.0.1}"
export V20_PORT="${V20_PORT:-9020}"
export V20_RUNTIME_DIR="${V20_RUNTIME_DIR:-v20/.runtime/local}"
export V20_SERVICE_NAME="${V20_SERVICE_NAME:-qiazhi-v20-local}"

PID_FILE="${V20_PID_FILE:-${V20_RUNTIME_DIR}/service_${V20_PORT}.pid}"
LOG_FILE="${V20_LOG_FILE:-${V20_RUNTIME_DIR}/service_${V20_PORT}.log}"
HEALTH_URL="${V20_HEALTH_URL:-http://127.0.0.1:${V20_PORT}/health}"

usage() {
  cat <<EOF
Usage: $0 {start|stop|restart|status|logs|launchd-plist}

Environment:
  V20_DATABASE_URL, V20_REDIS_URL, V20_LLM_* are passed through from the shell.
  V20_RUNTIME_DIR=${V20_RUNTIME_DIR}
  V20_PID_FILE=${PID_FILE}
  V20_LOG_FILE=${LOG_FILE}
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
  command -v lsof >/dev/null 2>&1 || return 1
  lsof -tiTCP:"${V20_PORT}" -sTCP:LISTEN 2>/dev/null | head -n 1
}

start_service() {
  mkdir -p "${V20_RUNTIME_DIR}"
  if pid="$(running_pid)"; then
    echo "V20 macOS service already running pid=${pid}"
    return 0
  fi
  if pid="$(port_pid)" && [[ -n "${pid}" ]]; then
    echo "V20 port ${V20_PORT} already has a listener pid=${pid}; not starting a duplicate."
    return 0
  fi
  rm -f "${PID_FILE}"
  touch "${LOG_FILE}"
  echo "Starting V20 macOS service on ${V20_HOST}:${V20_PORT}"
  nohup "${SCRIPT_DIR}/start_macos.sh" >>"${LOG_FILE}" 2>&1 &
  echo "$!" >"${PID_FILE}"
  sleep 1
  if pid="$(running_pid)"; then
    echo "V20 macOS service running pid=${pid}"
    echo "Log: ${LOG_FILE}"
    return 0
  fi
  echo "V20 macOS service failed to start. Last log lines:"
  tail -n 40 "${LOG_FILE}" || true
  return 1
}

stop_service() {
  local pid=""
  if ! pid="$(running_pid)"; then
    rm -f "${PID_FILE}"
    echo "V20 macOS service is not managed by ${PID_FILE}"
    return 0
  fi
  echo "Stopping V20 macOS service pid=${pid}"
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
  echo "Stopped V20 macOS service"
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

launchd_plist() {
  cat <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.qiazhi.v20.local</string>
  <key>WorkingDirectory</key><string>${ROOT_DIR}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${SCRIPT_DIR}/start_macos.sh</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>V20_ENV</key><string>local_macos</string>
    <key>V20_HOST</key><string>127.0.0.1</string>
    <key>V20_PORT</key><string>${V20_PORT}</string>
  </dict>
  <key>StandardOutPath</key><string>${ROOT_DIR}/${LOG_FILE}</string>
  <key>StandardErrorPath</key><string>${ROOT_DIR}/${LOG_FILE}</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
</dict>
</plist>
EOF
}

case "${1:-}" in
  start) start_service ;;
  stop) stop_service ;;
  restart) stop_service; start_service ;;
  status) status_service ;;
  logs) shift; show_logs "$@" ;;
  launchd-plist) launchd_plist ;;
  -h|--help|help|"") usage ;;
  *) usage; exit 2 ;;
esac
