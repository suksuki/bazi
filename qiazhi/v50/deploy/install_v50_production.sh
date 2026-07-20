#!/usr/bin/env bash
set -euo pipefail

V50_ROOT=/home/hlsystem/bazi/qiazhi/v50
NGINX_TARGET=/etc/nginx/sites-enabled/dblife.com
SERVICE_TARGET=/etc/systemd/system/qiazhi-v50.service
STAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/home/hlsystem/qiazhi-sync-backups/v50-nginx
VENV_PIP=/home/hlsystem/bazi/qiazhi/.venv312/bin/pip
PRODUCT_REQUIREMENTS=$V50_ROOT/requirements-product.txt

if [[ ${EUID} -ne 0 ]]; then
  echo "Run with sudo: sudo $V50_ROOT/deploy/install_v50_production.sh" >&2
  exit 1
fi

test -f "$V50_ROOT/.env.v50.production"
test -f "$V50_ROOT/deploy/nginx_dblife_v50.conf"
test -f "$V50_ROOT/deploy/qiazhi-v50.service"
test -f "$PRODUCT_REQUIREMENTS"
test -x "$VENV_PIP"

sudo -u hlsystem "$VENV_PIP" install --disable-pip-version-check -q -r "$PRODUCT_REQUIREMENTS"

mkdir -p "$BACKUP_DIR"
if [[ -f "$NGINX_TARGET" ]]; then
  cp -a "$NGINX_TARGET" "$BACKUP_DIR/dblife.com.${STAMP}"
fi
find /etc/nginx/sites-enabled -maxdepth 1 -type f -name 'dblife.com.bak*' -exec mv -t "$BACKUP_DIR" {} +
chown -R hlsystem:hlsystem "$BACKUP_DIR"

install -m 0644 "$V50_ROOT/deploy/qiazhi-v50.service" "$SERVICE_TARGET"
install -m 0644 "$V50_ROOT/deploy/nginx_dblife_v50.conf" "$NGINX_TARGET"

if [[ -f "$V50_ROOT/.runtime/v50-product.pid" ]]; then
  TEMP_PID=$(cat "$V50_ROOT/.runtime/v50-product.pid" || true)
  if [[ -n "$TEMP_PID" ]] && kill -0 "$TEMP_PID" 2>/dev/null; then
    kill "$TEMP_PID"
    for _ in $(seq 1 20); do
      kill -0 "$TEMP_PID" 2>/dev/null || break
      sleep 0.25
    done
  fi
fi

systemctl daemon-reload
systemctl enable --now qiazhi-v50.service

for _ in $(seq 1 30); do
  curl -fsS http://127.0.0.1:9050/health >/dev/null && break
  sleep 1
done
curl -fsS http://127.0.0.1:9050/health >/dev/null

TTS_BASE_URL=$(sed -n 's/^V50_TTS_BASE_URL=//p' "$V50_ROOT/.env.v50.production" | tail -1 | tr -d '"')
if [[ -n "$TTS_BASE_URL" ]]; then
  curl -fsS --connect-timeout 5 --max-time 15 "$TTS_BASE_URL/health" >/dev/null
fi

nginx -t
systemctl reload nginx

echo "DeepBazi V50 is active at https://dblife.com/"
echo "DeepBazi V50 Next experience is active at https://dblife.com/experience"
echo "Qwen TTS is active through ${TTS_BASE_URL:-not-configured}"
echo "V40 remains available at https://dblife.com/v40/ui"
