#!/usr/bin/env bash

resolve_v20_python() {
  if [[ -n "${PYTHON_BIN:-}" ]]; then
    printf '%s\n' "${PYTHON_BIN}"
    return 0
  fi
  local venv_python="${V20_PYTHON_VENV:-${PWD}/.venv312}/bin/python"
  if [[ -x "${venv_python}" ]]; then
    printf '%s\n' "${venv_python}"
    return 0
  fi
  if command -v python3.12 >/dev/null 2>&1; then
    command -v python3.12
    return 0
  fi
  printf 'V20 requires Python 3.12. Create .venv312 or set PYTHON_BIN=/path/to/python3.12.\n' >&2
  return 2
}

PYTHON_BIN="$(resolve_v20_python)"
PYTHON_VERSION="$("${PYTHON_BIN}" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")')"
case "${PYTHON_VERSION}" in
  3.12.*) ;;
  *)
    printf 'V20 requires Python 3.12, got %s from %s.\n' "${PYTHON_VERSION}" "${PYTHON_BIN}" >&2
    return 2
    ;;
esac

export PYTHON_BIN
