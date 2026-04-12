#!/usr/bin/env bash
# 按端口杀监听进程（解决 pkill 匹配不到 next-server 导致旧进程占坑）
_free_tcp_port() {
  local port="$1"
  command -v ss >/dev/null 2>&1 || return 0
  local p
  p="$(ss -ltnp "sport = :$port" 2>/dev/null | grep -oE 'pid=[0-9]+' | cut -d= -f2 | sort -u | tr '\n' ' ')"
  [ -z "${p// /}" ] && return 0
  echo "[free] :$port -> $p" >&2
  # shellcheck disable=SC2086
  echo "$p" | tr ' ' '\n' | grep -E '^[0-9]+$' | sort -u | xargs -r kill -15 2>/dev/null || true
  sleep 1
  # shellcheck disable=SC2086
  echo "$p" | tr ' ' '\n' | grep -E '^[0-9]+$' | sort -u | xargs -r kill -9 2>/dev/null || true
  sleep 1
  local i
  for i in $(seq 1 40); do
    ss -ltn "sport = :$port" 2>/dev/null | grep -q LISTEN || return 0
    sleep 0.1
  done
  echo "[free] WARN: :$port 仍被占用" >&2
  return 1
}
