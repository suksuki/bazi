#!/usr/bin/env bash
set -euo pipefail

# Clean runtime/build artifacts without touching source files.
# Usage:
#   ./scripts/clean-runtime-artifacts.sh
#   DRY_RUN=1 ./scripts/clean-runtime-artifacts.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DRY_RUN="${DRY_RUN:-0}"

log() {
  printf "%s\n" "$*"
}

run() {
  if [ "$DRY_RUN" = "1" ]; then
    log "[dry-run] $*"
  else
    eval "$*"
  fi
}

log "Cleaning runtime artifacts under: $ROOT_DIR"

run "find '$ROOT_DIR/backend' -type d -name '__pycache__' -prune -exec rm -rf {} +"
run "find '$ROOT_DIR/backend' -type d -name '.pytest_cache' -prune -exec rm -rf {} +"
run "rm -rf '$ROOT_DIR/frontend/.next'"
run "find '$ROOT_DIR/frontend' -type f -name 'tsconfig.tsbuildinfo' -delete"
run "find '$ROOT_DIR/.runlogs' -type f -name '*.log' -delete 2>/dev/null || true"

log "Done."
