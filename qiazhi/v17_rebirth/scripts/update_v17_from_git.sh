#!/usr/bin/env bash
set -euo pipefail

GREEN="\033[0;32m"
YELLOW="\033[1;33m"
BLUE="\033[0;34m"
RED="\033[0;31m"
NC="\033[0m"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
QIAZHI_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
REPO_ROOT="$(cd "${QIAZHI_ROOT}/.." && pwd)"
BRANCH="${V17_GIT_BRANCH:-chore/same-origin-api}"
REMOTE="${V17_GIT_REMOTE:-origin}"
FRONTEND_DIR="${QIAZHI_ROOT}/v17_rebirth/frontend"
I18N_FILE="qiazhi/v17_rebirth/frontend/lib/i18n.ts"

print_step() {
  echo -e "${BLUE}$1${NC}"
}

fail() {
  echo -e "${RED}$1${NC}" >&2
  exit 1
}

cd "${REPO_ROOT}"

current_branch="$(git branch --show-current)"
if [[ "${current_branch}" != "${BRANCH}" ]]; then
  fail "当前分支是 ${current_branch:-detached}，预期 ${BRANCH}。请先切换分支，避免部署错版本。"
fi

print_step "[1/5] Prepare local runtime directories..."
mkdir -p "${QIAZHI_ROOT}/v17_rebirth/.runlogs" "${QIAZHI_ROOT}/v17_rebirth/.runtime"

if [[ -f "${I18N_FILE}" ]] && ! git ls-files --error-unmatch "${I18N_FILE}" >/dev/null 2>&1; then
  backup="${I18N_FILE}.pretrack.$(date +%Y%m%d_%H%M%S).bak"
  echo -e "${YELLOW}Found untracked ${I18N_FILE}; moving to ${backup} before pull.${NC}"
  mv "${I18N_FILE}" "${backup}"
fi

dirty_non_runtime="$(
  git status --porcelain \
    | grep -vE '^(.. )?qiazhi/\\.venv/|^(.. )?qiazhi/\\.pnpm-store/|^(.. )?qiazhi/v17_rebirth/\\.runlogs/|^(.. )?qiazhi/v17_rebirth/\\.runtime/|^\\?\\? db_backups/' \
    || true
)"
if [[ -n "${dirty_non_runtime}" ]]; then
  echo -e "${RED}工作区存在非运行时改动，先处理后再部署:${NC}" >&2
  echo "${dirty_non_runtime}" >&2
  exit 1
fi

print_step "[2/5] Pull latest ${REMOTE}/${BRANCH}..."
git fetch "${REMOTE}" "${BRANCH}"
git pull --ff-only "${REMOTE}" "${BRANCH}"

print_step "[3/5] Install frontend dependencies if needed..."
if command -v pnpm >/dev/null 2>&1; then
  pnpm --dir "${FRONTEND_DIR}" install --no-frozen-lockfile
else
  fail "pnpm not found. 请先执行 source ~/.nvm/nvm.sh && corepack enable。"
fi

print_step "[4/5] Restart V17 stack..."
"${QIAZHI_ROOT}/v17_rebirth/scripts/restart_v17_stack.sh"

print_step "[5/5] Deployment health check..."
"${QIAZHI_ROOT}/v17_rebirth/scripts/check_v17_deploy.sh"

echo -e "${GREEN}V17 update completed.${NC}"
