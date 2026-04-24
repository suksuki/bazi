#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKUP_DIR="${V17_BACKUP_DIR:-/home/hlsystem/bazi/db_backups}"
STAMP="$(date +%Y%m%d_%H%M%S)"

mkdir -p "$BACKUP_DIR"

copied=0
for name in v17_auth.db v17_evolution.db; do
  src="${PROJECT_DIR}/.runtime/${name}"
  if [[ -f "$src" ]]; then
    cp "$src" "${BACKUP_DIR}/${name%.db}_${STAMP}.db"
    copied=$((copied + 1))
    echo "backup: ${BACKUP_DIR}/${name%.db}_${STAMP}.db"
  else
    echo "skip: ${src} not found"
  fi
done

if (( copied == 0 )); then
  echo "no runtime DBs were backed up"
  exit 1
fi
