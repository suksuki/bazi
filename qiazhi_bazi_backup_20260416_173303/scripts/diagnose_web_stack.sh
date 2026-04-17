#!/usr/bin/env bash
# 泛型 500 / 白屏时：本机端口、关键 URL、日志里 Error 片段
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$REPO/.runlogs"

echo "=== 监听 ==="
ss -ltnp 2>/dev/null | grep -E ':3001|:8001' || true

echo ""
echo "=== 本机 HTTP ==="
curl -sS -o /dev/null -w "GET /        3001 -> %{http_code}\n" http://127.0.0.1:3001/ || echo "3001 不可达"
curl -sS -o /dev/null -w "GET /health  8001 -> %{http_code}\n" http://127.0.0.1:8001/health || echo "8001 不可达"
curl -sS -o /dev/null -w "GET /ready   8001 -> %{http_code}\n" http://127.0.0.1:8001/ready || true

echo ""
echo "=== frontend-3001.log 近期 Error / EADDRINUSE / Server Action（各至多 12 行）==="
if [ -f "$LOG/frontend-3001.log" ]; then
  grep -E "Error|EADDRINUSE|Server Action|⨯|FATAL" "$LOG/frontend-3001.log" 2>/dev/null | tail -12 || echo "(无匹配)"
else
  echo "(无日志文件)"
fi

echo ""
echo "=== backend-8001.log 近期 Error / OperationalError（至多 12 行）==="
if [ -f "$LOG/backend-8001.log" ]; then
  grep -E "Error|OperationalError|Traceback|FATAL|Exception" "$LOG/backend-8001.log" 2>/dev/null | tail -12 || echo "(无匹配)"
else
  echo "(无日志文件)"
fi

echo ""
echo "=== 下一步（浏览器）==="
echo "F12 → Network → Preserve log → 刷新；点红条 500，看 Request URL。"
echo "若是 /_next/static → 再跑: $REPO/scripts/check_next_static.sh"
echo "若是 RSC/Flight 或 Server Action → 对站点「清空缓存并硬性重新加载」或无痕窗口。"
echo "若是 /api/* → 看上面 backend 日志与 DATABASE_URL。"
