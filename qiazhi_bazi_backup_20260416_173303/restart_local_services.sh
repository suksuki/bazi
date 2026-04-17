#!/usr/bin/env bash
set -euo pipefail

# Qiazhi-Bazi services restart (backend 8001, frontend 3001 by default)
#
# 若机房页 /api/admin 返回 503：多为未设置 QIAZHI_ADMIN_TOKEN。本脚本在未配置时会注入本机弱默认
# local-dev-qiazhi-admin，并导出 NEXT_PUBLIC_QIAZHI_ADMIN_TOKEN / NEXT_PUBLIC_QIAZHI_API 供前端 build/start。
#
# 不会重启 Nginx（仅本机 Node/Python）。改 Nginx 请自行 systemctl reload nginx。
#
# 若出现「首页 200 但 /_next/static 400」或 EADDRINUSE：多为旧 next-server 没被干掉。
# 非 root 时 lsof 常看不到别的用户监听的进程 → 仅 lsof 会杀不掉。本脚本在 lsof 之后会
# 始终再用 ss / fuser 扫 PID；仍杀不掉时可:
#   FORCE_SUDO_KILL=1 ./restart_local_services.sh
#
# Usage:
#   ./restart_local_services.sh
#   SKIP_BUILD=1 ./restart_local_services.sh    # 仅杀进程+起服务，不 pnpm build（要快）
#   FRONTEND_MODE=prod ./restart_local_services.sh
#   FRONTEND_MODE=dev BACKEND_PORT=8001 FRONTEND_PORT=3001 ./restart_local_services.sh
#   FORCE_SUDO_KILL=1 ./restart_local_services.sh   # 端口仍占用时用 sudo fuser/ss 强杀

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$SCRIPT_DIR"

BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
LOG_DIR="$ROOT_DIR/.runlogs"
BACKEND_ENV="$BACKEND_DIR/.env"

BACKEND_PORT="${BACKEND_PORT:-8001}"
FRONTEND_PORT="${FRONTEND_PORT:-3001}"
FRONTEND_MODE="${FRONTEND_MODE:-prod}" # dev | prod
# 生产模式下跳过前端 pnpm build（仅重启进程；需已有 frontend/.next）
SKIP_BUILD="${SKIP_BUILD:-0}"
FORCE_SUDO_KILL="${FORCE_SUDO_KILL:-0}"

mkdir -p "$LOG_DIR"

# 注意：须在「if 条件」里用 grep / lsof，不可写「ss|grep && return」在 then 里：
# 端口空闲时 grep 返回 1，在 set -e 下会直接退出整个脚本。
port_in_use() {
  local p="$1"
  if command -v ss >/dev/null 2>&1; then
    if ss -ltnp "sport = :$p" 2>/dev/null | grep -q LISTEN; then
      return 0
    fi
  fi
  if command -v lsof >/dev/null 2>&1; then
    if lsof -tiTCP:"$p" -sTCP:LISTEN >/dev/null 2>&1; then
      return 0
    fi
  fi
  return 1
}

# 从 ss 输出中提取监听该端口的所有 pid（不依赖 lsof 权限）
pids_listening_on_port() {
  local port="$1"
  if ! command -v ss >/dev/null 2>&1; then
    return 0
  fi
  ss -ltnp "sport = :$port" 2>/dev/null | grep -oE 'pid=[0-9]+' | cut -d= -f2 | sort -u || true
}

kill_pids_graceful_then_force() {
  local pids="$1"
  [ -z "$pids" ] && return 0
  # shellcheck disable=SC2086
  echo "$pids" | tr ' ' '\n' | grep -E '^[0-9]+$' | sort -u | xargs -r kill -15 2>/dev/null || true
  sleep 1
  # shellcheck disable=SC2086
  echo "$pids" | tr ' ' '\n' | grep -E '^[0-9]+$' | sort -u | xargs -r kill -9 2>/dev/null || true
}

free_tcp_port() {
  local port="$1"
  local name="${2:-port}"

  # 1) lsof（当前用户可见的监听进程）
  if command -v lsof >/dev/null 2>&1; then
    if lsof -tiTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
      lsof -tiTCP:"$port" -sTCP:LISTEN | sort -u | xargs -r kill -15 2>/dev/null || true
      sleep 1
      lsof -tiTCP:"$port" -sTCP:LISTEN | sort -u | xargs -r kill -9 2>/dev/null || true
      sleep 1
    fi
  fi

  # 2) ss：补齐 lsof 看不到的监听方（多行里多个 pid=）
  local ss_pids
  ss_pids="$(pids_listening_on_port "$port" | tr '\n' ' ')"
  if [ -n "${ss_pids// /}" ]; then
    echo "  → $name :$port 发现 PID（ss）: $ss_pids"
    kill_pids_graceful_then_force "$ss_pids"
    sleep 1
  fi

  # 3) fuser（部分系统可直接按端口杀）
  if command -v fuser >/dev/null 2>&1; then
    fuser -k -TERM "${port}/tcp" 2>/dev/null || true
    sleep 1
    fuser -k -KILL "${port}/tcp" 2>/dev/null || true
    sleep 1
  fi

  # 4) 仍占用且允许 sudo：用 root 视角再 fuser / ss 杀一次
  if [ "$FORCE_SUDO_KILL" = "1" ] && command -v sudo >/dev/null 2>&1; then
    if port_in_use "$port"; then
      echo "  → FORCE_SUDO_KILL: 尝试 sudo 释放 :$port …"
      sudo fuser -k -KILL "${port}/tcp" 2>/dev/null || true
      sleep 1
      ss_pids="$(sudo ss -ltnp "sport = :$port" 2>/dev/null | grep -oE 'pid=[0-9]+' | cut -d= -f2 | sort -u | tr '\n' ' ')"
      if [ -n "${ss_pids// /}" ]; then
        # shellcheck disable=SC2086
        echo "$ss_pids" | tr ' ' '\n' | grep -E '^[0-9]+$' | sort -u | xargs -r sudo kill -9 2>/dev/null || true
      fi
      sleep 1
    fi
  fi
}

echo "[1/5] Stop old processes (ports $FRONTEND_PORT/$BACKEND_PORT)..."
free_tcp_port "$FRONTEND_PORT" "frontend"
free_tcp_port "$BACKEND_PORT" "backend"

# 若端口仍被占用，说明当前用户没能杀掉监听进程（常见于 root/systemd 起的旧 next）
if port_in_use "$FRONTEND_PORT"; then
  echo "ERROR: 端口 $FRONTEND_PORT 在 kill 后仍被占用，新 next start 会失败或留下旧进程导致静态资源 400。" >&2
  echo "可尝试: FORCE_SUDO_KILL=1 $0" >&2
  echo "或手动: sudo ss -ltnp 'sport = :$FRONTEND_PORT'  然后: sudo kill -9 <pid>" >&2
  exit 1
fi
if port_in_use "$BACKEND_PORT"; then
  echo "ERROR: 端口 $BACKEND_PORT 在 kill 后仍被占用。" >&2
  echo "可尝试: FORCE_SUDO_KILL=1 $0" >&2
  echo "或手动: sudo ss -ltnp 'sport = :$BACKEND_PORT'  然后: sudo kill -9 <pid>" >&2
  exit 1
fi

echo "[2/5] Load env for frontend build + runtime..."
if [ -f "$BACKEND_ENV" ]; then
  set -a && source "$BACKEND_ENV" && set +a
fi
# Admin API 未配置时 FastAPI 对 /api/admin/* 一律返回 503；本脚本为本地开发注入弱默认（公网部署必须在 backend/.env 设置强 token）。
if [ -z "${QIAZHI_ADMIN_TOKEN:-}" ]; then
  export QIAZHI_ADMIN_TOKEN="local-dev-qiazhi-admin"
  echo "[restart] 提示: 未设置非空 QIAZHI_ADMIN_TOKEN，本次已使用本机默认（勿用于公网）。"
fi
# 前端 prod build 需在同一 shell 内可见 NEXT_PUBLIC_*（勿依赖未创建的 .env.local）
export NEXT_PUBLIC_QIAZHI_ADMIN_TOKEN="${NEXT_PUBLIC_QIAZHI_ADMIN_TOKEN:-$QIAZHI_ADMIN_TOKEN}"
export NEXT_PUBLIC_QIAZHI_API="${NEXT_PUBLIC_QIAZHI_API:-http://127.0.0.1:${BACKEND_PORT}}"

FRONTEND_LOG="$LOG_DIR/frontend-$FRONTEND_PORT.log"

echo "[3/5] Prepare frontend ($FRONTEND_MODE)..."
if [ "$FRONTEND_MODE" = "prod" ]; then
  if [ "$SKIP_BUILD" = "1" ]; then
    echo "SKIP_BUILD=1 → 跳过 pnpm build（使用现有 .next）"
  elif command -v pnpm >/dev/null 2>&1; then
    (cd "$FRONTEND_DIR" && pnpm build)
  else
    (cd "$FRONTEND_DIR" && npm run build)
  fi
fi

echo "[4/5] Start backend ($BACKEND_PORT)..."
nohup bash -lc "cd \"$BACKEND_DIR\" && set -a && source \"$BACKEND_ENV\" 2>/dev/null && set +a && if [ -z \"\${QIAZHI_ADMIN_TOKEN:-}\" ]; then export QIAZHI_ADMIN_TOKEN=local-dev-qiazhi-admin; fi && PYTHONPATH=. python3 -m uvicorn main:app --host 0.0.0.0 --port $BACKEND_PORT" \
  > "$LOG_DIR/backend-$BACKEND_PORT.log" 2>&1 &
BACKEND_PID=$!

# 给 uvicorn 绑定端口留时间（慢盘/首次 import 时 1s 不够）
sleep 2

echo "[5/5] Start frontend ($FRONTEND_PORT, mode=$FRONTEND_MODE)..."
if [ "$FRONTEND_MODE" = "dev" ]; then
  if command -v pnpm >/dev/null 2>&1; then
    nohup bash -lc "cd \"$FRONTEND_DIR\" && export NEXT_PUBLIC_QIAZHI_API=\"$NEXT_PUBLIC_QIAZHI_API\" NEXT_PUBLIC_QIAZHI_ADMIN_TOKEN=\"$NEXT_PUBLIC_QIAZHI_ADMIN_TOKEN\" && pnpm dev -- -p $FRONTEND_PORT" > "$FRONTEND_LOG" 2>&1 &
  else
    nohup bash -lc "cd \"$FRONTEND_DIR\" && export NEXT_PUBLIC_QIAZHI_API=\"$NEXT_PUBLIC_QIAZHI_API\" NEXT_PUBLIC_QIAZHI_ADMIN_TOKEN=\"$NEXT_PUBLIC_QIAZHI_ADMIN_TOKEN\" && npm run dev -- -p $FRONTEND_PORT" > "$FRONTEND_LOG" 2>&1 &
  fi
else
  if command -v pnpm >/dev/null 2>&1; then
    nohup bash -lc "cd \"$FRONTEND_DIR\" && export NEXT_PUBLIC_QIAZHI_API=\"$NEXT_PUBLIC_QIAZHI_API\" NEXT_PUBLIC_QIAZHI_ADMIN_TOKEN=\"$NEXT_PUBLIC_QIAZHI_ADMIN_TOKEN\" && pnpm start -p $FRONTEND_PORT" > "$FRONTEND_LOG" 2>&1 &
  else
    nohup bash -lc "cd \"$FRONTEND_DIR\" && export NEXT_PUBLIC_QIAZHI_API=\"$NEXT_PUBLIC_QIAZHI_API\" NEXT_PUBLIC_QIAZHI_ADMIN_TOKEN=\"$NEXT_PUBLIC_QIAZHI_ADMIN_TOKEN\" && npm run start -- -p $FRONTEND_PORT" > "$FRONTEND_LOG" 2>&1 &
  fi
fi
FRONTEND_PID=$!

sleep 2

echo "Health checks..."
BACKEND_HEALTH="FAIL"
FRONTEND_HEALTH="FAIL"
BACKEND_HTTP_CODE=""
FRONTEND_HTTP_CODE=""
for _ in $(seq 1 20); do
  BACKEND_HTTP_CODE="$(curl -sS -m 3 -o /dev/null -w "%{http_code}" "http://127.0.0.1:$BACKEND_PORT/health" || true)"
  FRONTEND_HTTP_CODE="$(curl -sS -m 3 -o /dev/null -w "%{http_code}" "http://127.0.0.1:$FRONTEND_PORT/" || true)"
  if [ "$BACKEND_HTTP_CODE" = "200" ] && [ "$FRONTEND_HTTP_CODE" = "200" ]; then
    BACKEND_HEALTH="OK"
    FRONTEND_HEALTH="OK"
    break
  fi
  sleep 1
done

echo ""
echo "====== Local Dev Services ======"
echo "Backend PID : $BACKEND_PID (health: $BACKEND_HEALTH, http: ${BACKEND_HTTP_CODE:-N/A})"
echo "Frontend PID: $FRONTEND_PID (health: $FRONTEND_HEALTH, http: ${FRONTEND_HTTP_CODE:-N/A})"
echo "Backend URL : http://127.0.0.1:$BACKEND_PORT/health"
echo "Frontend URL: http://127.0.0.1:$FRONTEND_PORT/"
echo "FrontendMode: $FRONTEND_MODE"
echo "Backend Log : $LOG_DIR/backend-$BACKEND_PORT.log"
echo "Frontend Log: $FRONTEND_LOG"
echo "=================================="

if [ "$BACKEND_HEALTH" != "OK" ]; then
  echo "" >&2
  echo "后端未通过 /health（常见：旧逻辑下 init_db 失败会直接退出；已在新版 main 中改为降级启动）。最近日志：" >&2
  tail -n 30 "$LOG_DIR/backend-$BACKEND_PORT.log" 2>/dev/null >&2 || true
fi
if [ "$FRONTEND_HEALTH" != "OK" ]; then
  echo "" >&2
  echo "前端未返回 200。最近日志：" >&2
  tail -n 25 "$FRONTEND_LOG" 2>/dev/null >&2 || true
fi

