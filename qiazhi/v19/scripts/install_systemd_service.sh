#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
V19_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
APP_ROOT="$(cd "${V19_DIR}/.." && pwd)"
source "${SCRIPT_DIR}/server_process.sh"

PYTHON_BIN="${PYTHON_BIN:-python3}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-9019}"
URL="http://${HOST}:${PORT}"
SERVICE_NAME="${SERVICE_NAME:-qiazhi-v19}"
SERVICE_USER="${SERVICE_USER:-$(id -un)}"
SERVICE_GROUP="${SERVICE_GROUP:-$(id -gn)}"
RUNTIME_DIR="${RUNTIME_DIR:-${V19_DIR}/.runtime}"
ENV_FILE="${ENV_FILE:-${RUNTIME_DIR}/${SERVICE_NAME}.env}"
PID_FILE="${PID_FILE:-${RUNTIME_DIR}/server_${PORT}.pid}"
UNIT_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

if ! command -v systemctl >/dev/null 2>&1; then
  echo "systemctl not found; this installer requires a systemd-based Linux server." >&2
  exit 1
fi

if ! command -v sudo >/dev/null 2>&1; then
  echo "sudo not found; install the service as root or install sudo first." >&2
  exit 1
fi

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "python3 not found. Install Python 3 or set PYTHON_BIN=/path/to/python3." >&2
  exit 1
fi
PYTHON_EXEC="$(command -v "${PYTHON_BIN}")"

if ! "${PYTHON_BIN}" - <<'PY' >/dev/null 2>&1
import fastapi
import lunar_python
import uvicorn
PY
then
  echo "Missing Python dependencies. Install fastapi, uvicorn, and lunar-python for this Python." >&2
  echo "Example: ${PYTHON_BIN} -m pip install fastapi uvicorn lunar-python" >&2
  exit 1
fi

mkdir -p "${RUNTIME_DIR}"
touch "${ENV_FILE}"
chmod 600 "${ENV_FILE}"

if ! grep -q '^V19_ALLOW_ROLE_QUERY_FALLBACK=' "${ENV_FILE}"; then
  echo "V19_ALLOW_ROLE_QUERY_FALLBACK=${V19_ALLOW_ROLE_QUERY_FALLBACK:-1}" >> "${ENV_FILE}"
fi

tmp_unit="$(mktemp)"
cat > "${tmp_unit}" <<EOF
[Unit]
Description=Qiazhi V19 Bazi API
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${SERVICE_USER}
Group=${SERVICE_GROUP}
WorkingDirectory=${APP_ROOT}
Environment=PYTHONPATH=${APP_ROOT}
EnvironmentFile=-${ENV_FILE}
ExecStart=${PYTHON_EXEC} -m uvicorn v19.server:app --host ${HOST} --port ${PORT}
Restart=always
RestartSec=3
KillSignal=SIGINT
TimeoutStopSec=20

[Install]
WantedBy=multi-user.target
EOF

echo "V19 systemd: installing ${UNIT_FILE}"
sudo install -m 0644 "${tmp_unit}" "${UNIT_FILE}"
rm -f "${tmp_unit}"

echo "V19 systemd: enabling and restarting ${SERVICE_NAME}"
sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}.service" >/dev/null
sudo systemctl stop "${SERVICE_NAME}.service" >/dev/null 2>&1 || true
v19_stop_existing_server "${PORT}" "${PID_FILE}"
sudo systemctl start "${SERVICE_NAME}.service"
if ! v19_wait_for_url "${PYTHON_BIN}" "${URL}" 80; then
  echo "V19 systemd: health check failed at ${URL}/health" >&2
  sudo systemctl status "${SERVICE_NAME}.service" --no-pager >&2 || true
  journalctl -u "${SERVICE_NAME}.service" -n 60 --no-pager >&2 || true
  exit 1
fi

echo "V19 systemd: installed"
echo "  service: sudo systemctl status ${SERVICE_NAME} --no-pager"
echo "  logs:    journalctl -u ${SERVICE_NAME} -f"
echo "  url:     ${URL}"
