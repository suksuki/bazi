#!/usr/bin/env bash
set -euo pipefail

# Force modern Node first in PATH for pnpm/next.
export PATH="/usr/local/bin:${PATH}"

GREEN="\033[0;32m"
YELLOW="\033[1;33m"
BLUE="\033[0;34m"
RED="\033[0;31m"
NC="\033[0m"
FRONTEND_DIR="/home/hlsystem/bazi/qiazhi/v17_rebirth/frontend"
FRONTEND_LOG="/home/hlsystem/bazi/qiazhi/v17_rebirth/.runlogs/frontend-3001.log"

node_major="$(node -p 'Number(process.versions.node.split(".")[0])' 2>/dev/null || echo 0)"
echo -e "${BLUE}Node in use:${NC} $(node -v 2>/dev/null || echo 'missing') ($(command -v node || echo 'not found'))"
if (( node_major < 20 )); then
  echo -e "${RED}Node version too old for Next.js build. Need >= 20.9.0${NC}"
  echo -e "${YELLOW}Tip:${NC} ensure '/usr/local/bin/node' is available and ahead in PATH."
  exit 1
fi

echo -e "${BLUE}[1/4] Build frontend (production)...${NC}"
if ! pnpm --dir "$FRONTEND_DIR" build; then
  echo -e "${RED}Frontend build failed.${NC}"
  if [[ -f "$FRONTEND_LOG" ]]; then
    echo -e "${YELLOW}Recent frontend log:${NC}"
    total_lines="$(wc -l < "$FRONTEND_LOG" 2>/dev/null || echo 0)"
    start_line=1
    if (( total_lines > 40 )); then
      start_line=$((total_lines - 39))
    fi
    sed -n "${start_line},${total_lines}p" "$FRONTEND_LOG" 2>/dev/null || true
  fi
  exit 1
fi

echo -e "${BLUE}[2/4] Restart backend + frontend services...${NC}"
sudo systemctl restart v17-backend.service v17-frontend.service

echo -e "${BLUE}[3/4] Health checks...${NC}"
sleep 2

render_progress() {
  local label="$1"
  local current="$2"
  local total="$3"
  local width=24
  local filled=$(( current * width / total ))
  local empty=$(( width - filled ))
  local bar_fill bar_empty
  bar_fill="$(printf "%0.s#" $(seq 1 "$filled"))"
  bar_empty="$(printf "%0.s-" $(seq 1 "$empty"))"
  printf "\r${YELLOW}%-10s${NC} [${GREEN}%s${NC}%s] %d/%d" "$label" "$bar_fill" "$bar_empty" "$current" "$total"
}

check_http_code() {
  local label="$1"
  local url="$2"
  local retries="${3:-8}"
  local delay="${4:-1}"
  local code="000"
  local i

  echo -e "${YELLOW}${label}${NC}"
  for ((i = 1; i <= retries; i++)); do
    render_progress "$label" "$i" "$retries"
    code="$(curl -sS -m 5 -o /dev/null -w "%{http_code}" "$url" || true)"
    if [[ "$code" =~ ^2|^3 ]]; then
      render_progress "$label" "$retries" "$retries"
      printf "\n"
      break
    fi
    sleep "$delay"
  done
  if [[ ! "$code" =~ ^2|^3 ]]; then
    printf "\n"
  fi
  if [[ "$code" =~ ^2|^3 ]]; then
    echo -e "${GREEN}${label} ready: HTTP ${code}${NC}"
  else
    echo -e "${RED}${label} not ready: HTTP ${code}${NC}"
  fi

  CHECK_HTTP_CODE_RESULT="$code"
}

check_http_code "backend" "http://127.0.0.1:8017/health" 10 1
BACKEND_CODE="$CHECK_HTTP_CODE_RESULT"
check_http_code "frontend" "http://127.0.0.1:3001/v17/oracle" 10 1
FRONTEND_CODE="$CHECK_HTTP_CODE_RESULT"

echo -e "${BLUE}backend(8017):${NC} ${BACKEND_CODE:-N/A}"
echo -e "${BLUE}frontend(3001):${NC} ${FRONTEND_CODE:-N/A}"

echo -e "${BLUE}[4/4] Quick service status...${NC}"
sudo systemctl --no-pager --full status v17-backend.service | sed -n '1,12p'
sudo systemctl --no-pager --full status v17-frontend.service | sed -n '1,12p'

echo -e "${BLUE}Final page probe (with redirect follow):${NC}"
curl -sS -m 10 -L -o /dev/null -w "local_root => code=%{http_code} final=%{url_effective}\n" "http://127.0.0.1:3001/" || true
curl -sS -m 10 -L -o /dev/null -w "local_oracle => code=%{http_code} final=%{url_effective}\n" "http://127.0.0.1:3001/v17/oracle" || true
