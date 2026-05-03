#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${ROOT_DIR}"

ENV_FILE="${V20_ENV_FILE:-v20/.runtime/linux_0_13/service.env}"
if [[ -f "${ENV_FILE}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
fi

SERVICE_NAME="${V20_SYSTEMD_SERVICE:-${V20_SERVICE_NAME:-qiazhi-v20}}"
PORT="${V20_PORT:-9020}"
HEALTH_URL="${V20_HEALTH_URL:-http://127.0.0.1:${PORT}/health}"
DEPENDENCY_URL="${V20_DEPENDENCY_URL:-http://127.0.0.1:${PORT}/api/v20/runtime/dependencies}"
PYTHON_BIN="${PYTHON_BIN:-python3.12}"

sudo_cmd() {
  if [[ "${EUID}" -eq 0 ]]; then
    "$@"
  else
    sudo "$@"
  fi
}

usage() {
  cat <<EOF
Usage: $0 [restart|status|logs|health|dependencies]

Linux systemd-only control for the V20 service.

Defaults:
  service: ${SERVICE_NAME}
  env file: ${ENV_FILE}
  health: ${HEALTH_URL}

Examples:
  ./v20/scripts/restart_linux_systemd.sh
  ./v20/scripts/restart_linux_systemd.sh status
  ./v20/scripts/restart_linux_systemd.sh logs
EOF
}

require_linux_systemd() {
  if [[ "$(uname -s)" != "Linux" ]]; then
    echo "This script is Linux-only." >&2
    exit 2
  fi
  if ! command -v systemctl >/dev/null 2>&1; then
    echo "systemctl is required." >&2
    exit 2
  fi
}

wait_for_health() {
  local attempts="${V20_HEALTH_ATTEMPTS:-40}"
  local delay="${V20_HEALTH_DELAY_SECONDS:-0.5}"
  for _ in $(seq 1 "${attempts}"); do
    if curl -fsS "${HEALTH_URL}" >/tmp/qiazhi_v20_health.json 2>/dev/null; then
      cat /tmp/qiazhi_v20_health.json
      echo
      rm -f /tmp/qiazhi_v20_health.json
      return 0
    fi
    sleep "${delay}"
  done
  echo "V20 health check failed: ${HEALTH_URL}" >&2
  sudo_cmd journalctl -u "${SERVICE_NAME}" -n 80 --no-pager || true
  return 1
}

print_dependencies() {
  if ! command -v curl >/dev/null 2>&1; then
    return 0
  fi
  if curl -fsS "${DEPENDENCY_URL}" >/tmp/qiazhi_v20_dependencies.json 2>/dev/null; then
    if command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
      "${PYTHON_BIN}" - <<'PY' </tmp/qiazhi_v20_dependencies.json
import json, sys

p = json.load(sys.stdin)
llm = p.get("llm", {})
print(
    "dependencies",
    p.get("active_profile"),
    "postgres=" + str(p.get("postgres", {}).get("ready_for_connection")),
    "redis=" + str(p.get("redis", {}).get("ready_for_connection")),
    "llm=" + str(llm.get("model")),
    "llm_ready=" + str(llm.get("ready_for_connection")),
)
PY
    else
      cat /tmp/qiazhi_v20_dependencies.json
      echo
    fi
    rm -f /tmp/qiazhi_v20_dependencies.json
  else
    echo "Dependency endpoint not ready: ${DEPENDENCY_URL}" >&2
  fi
}

restart_service() {
  require_linux_systemd
  echo "Restarting ${SERVICE_NAME}..."
  sudo_cmd systemctl daemon-reload
  sudo_cmd systemctl restart "${SERVICE_NAME}"
  sudo_cmd systemctl --no-pager --lines=20 status "${SERVICE_NAME}" || true
  wait_for_health
  print_dependencies
}

case "${1:-restart}" in
  restart)
    restart_service
    ;;
  status)
    require_linux_systemd
    sudo_cmd systemctl --no-pager --lines=40 status "${SERVICE_NAME}"
    ;;
  logs)
    require_linux_systemd
    sudo_cmd journalctl -u "${SERVICE_NAME}" -n "${V20_LOG_LINES:-120}" --no-pager
    ;;
  health)
    wait_for_health
    ;;
  dependencies)
    print_dependencies
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    usage
    exit 2
    ;;
esac
