#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/hlsystem/bazi/qiazhi/v17_rebirth"
UNIT_SRC="$ROOT/deploy/systemd"

echo "[1/5] Prepare runtime directories..."
mkdir -p "$ROOT/.runlogs" "$ROOT/.runtime"

echo "[2/5] Install unit files to /etc/systemd/system ..."
sudo cp "$UNIT_SRC/v17-backend.service" /etc/systemd/system/v17-backend.service
sudo cp "$UNIT_SRC/v17-frontend.service" /etc/systemd/system/v17-frontend.service

echo "[3/5] Reload systemd daemon..."
sudo systemctl daemon-reload

echo "[4/5] Enable services on boot..."
sudo systemctl enable v17-backend.service v17-frontend.service

echo "[5/5] Start services..."
sudo systemctl restart v17-backend.service v17-frontend.service

echo
echo "=== Service Status ==="
sudo systemctl --no-pager --full status v17-backend.service | sed -n '1,20p'
sudo systemctl --no-pager --full status v17-frontend.service | sed -n '1,20p'
echo "======================"
