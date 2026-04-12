#!/usr/bin/env bash
# 本机直连 Next：非 200 → 进程 cwd 不对或需重新 pnpm build；域名异常而此处 200 → 查 Nginx
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO/frontend"
if [ ! -f .next/BUILD_ID ]; then
  echo "缺少 .next/BUILD_ID — 请在 $(pwd) 执行 pnpm build" >&2
  exit 1
fi
# 优先 main-app（每 build 必有），避免抽到边缘 chunk
f="$(ls .next/static/chunks/main-app-*.js 2>/dev/null | head -1 || true)"
if [ -z "$f" ]; then
  f="$(ls .next/static/chunks/webpack-*.js 2>/dev/null | head -1 || true)"
fi
if [ -z "$f" ]; then
  echo "未找到 main-app / webpack chunk — 请 pnpm build" >&2
  exit 1
fi
rel="_next/static/chunks/$(basename "$f")"
echo "PWD=$(pwd) BUILD_ID=$(cat .next/BUILD_ID)"
echo "GET http://127.0.0.1:3001/$rel"
curl -sS -o /dev/null -w "HTTP %{http_code}\n" "http://127.0.0.1:3001/$rel"
