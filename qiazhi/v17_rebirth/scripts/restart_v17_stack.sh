#!/usr/bin/env bash
set -euo pipefail

echo "[1/3] Restart backend + frontend services..."
sudo systemctl restart v17-backend.service v17-frontend.service

echo "[2/3] Health checks..."
sleep 2

check_http_code() {
  local url="$1"
  local retries="${2:-8}"
  local delay="${3:-1}"
  local code="000"
  local i

  for ((i = 1; i <= retries; i++)); do
    code="$(curl -sS -m 5 -o /dev/null -w "%{http_code}" "$url" || true)"
    if [[ "$code" != "000" ]]; then
      break
    fi
    sleep "$delay"
  done

  echo "$code"
}

BACKEND_CODE="$(check_http_code "http://127.0.0.1:8017/health" 10 1)"
FRONTEND_CODE="$(check_http_code "http://127.0.0.1:3001/" 10 1)"

echo "backend(8017): ${BACKEND_CODE:-N/A}"
echo "frontend(3001): ${FRONTEND_CODE:-N/A}"

echo "[3/3] Quick service status..."
sudo systemctl --no-pager --full status v17-backend.service | sed -n '1,12p'
sudo systemctl --no-pager --full status v17-frontend.service | sed -n '1,12p'
