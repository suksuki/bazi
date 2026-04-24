#!/usr/bin/env bash
set -euo pipefail

DOMAIN="${V17_DOMAIN:-https://dblife.com}"
BACKEND_URL="${V17_BACKEND_HEALTH_URL:-http://127.0.0.1:8017/health}"
FRONTEND_URL="${V17_FRONTEND_LOGIN_URL:-http://127.0.0.1:3001/login}"
ADMIN_API_URL="${V17_ADMIN_API_URL:-${DOMAIN%/}/api/v17-admin/db-bridge?v17_origin=v17_rebirth}"
LOGIN_URL="${V17_LOGIN_URL:-${DOMAIN%/}/login}"

GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m"

failures=0

check_code() {
  local label="$1"
  local url="$2"
  local allowed_regex="$3"
  local code
  code="$(curl -sS -m 10 -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || true)"
  if [[ "$code" =~ $allowed_regex ]]; then
    echo -e "${GREEN}ok${NC} ${label}: HTTP ${code}"
  else
    echo -e "${RED}fail${NC} ${label}: HTTP ${code} (${url})"
    failures=$((failures + 1))
  fi
}

check_json_contains() {
  local label="$1"
  local url="$2"
  local needle="$3"
  local body
  body="$(curl -sS -m 10 "$url" 2>/dev/null || true)"
  if [[ "$body" == *"$needle"* ]]; then
    echo -e "${GREEN}ok${NC} ${label}: ${needle}"
  else
    echo -e "${RED}fail${NC} ${label}: missing ${needle}"
    echo -e "${YELLOW}${body:0:240}${NC}"
    failures=$((failures + 1))
  fi
}

echo "V17 deploy check"
echo "domain: ${DOMAIN}"

check_json_contains "backend health" "$BACKEND_URL" '"ok":true'
check_code "frontend login" "$FRONTEND_URL" '^(200|30[1278])$'
check_code "domain login" "$LOGIN_URL" '^(200|30[1278])$'

# Unauthenticated admin API should usually be 401. 200 is accepted for an already-authenticated curl jar.
# 404 is not accepted because it means Nginx routed /api/v17-admin/ to the wrong upstream.
check_code "admin API route" "$ADMIN_API_URL" '^(200|401|403)$'

if [[ -n "${V17_ADMIN_IDENTIFIER:-}" && -n "${V17_ADMIN_PASSWORD:-}" ]]; then
  login_code="$(curl -sS -m 10 -o /dev/null -w "%{http_code}" \
    -H "Content-Type: application/json" \
    --data "{\"identifier\":\"${V17_ADMIN_IDENTIFIER}\",\"password\":\"${V17_ADMIN_PASSWORD}\"}" \
    "${DOMAIN%/}/api/auth/login" 2>/dev/null || true)"
  if [[ "$login_code" =~ ^200$ ]]; then
    echo -e "${GREEN}ok${NC} admin login API: HTTP ${login_code}"
  else
    echo -e "${RED}fail${NC} admin login API: HTTP ${login_code}"
    failures=$((failures + 1))
  fi
else
  echo -e "${YELLOW}skip${NC} admin login API: set V17_ADMIN_IDENTIFIER and V17_ADMIN_PASSWORD to test credentials"
fi

if (( failures > 0 )); then
  echo -e "${RED}V17 deploy check failed: ${failures}${NC}"
  exit 1
fi

echo -e "${GREEN}V17 deploy check passed.${NC}"
