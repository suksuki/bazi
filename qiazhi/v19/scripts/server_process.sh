#!/usr/bin/env bash

v19_port_pids() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    lsof -tiTCP:"${port}" -sTCP:LISTEN 2>/dev/null || true
  elif command -v ss >/dev/null 2>&1; then
    ss -ltnp "( sport = :${port} )" 2>/dev/null | sed -n 's/.*pid=\([0-9][0-9]*\).*/\1/p' | sort -u
  elif command -v fuser >/dev/null 2>&1; then
    fuser "${port}/tcp" 2>/dev/null || true
  fi
}

v19_stop_existing_server() {
  local port="$1"
  local pid_file="$2"
  local pids=()
  local pid

  if [[ -f "${pid_file}" ]]; then
    pid="$(tr -cd '0-9' < "${pid_file}" || true)"
    if [[ -n "${pid}" ]]; then
      pids+=("${pid}")
    fi
  fi

  while IFS= read -r pid; do
    if [[ -n "${pid}" ]]; then
      pids+=("${pid}")
    fi
  done < <(v19_port_pids "${port}")

  if (( ${#pids[@]} == 0 )); then
    rm -f "${pid_file}"
    return 0
  fi

  pids=($(printf '%s\n' "${pids[@]}" | awk 'NF' | sort -u))
  echo "V19 server: stopping existing process(es) on port ${port}: ${pids[*]}"
  for pid in "${pids[@]}"; do
    kill "${pid}" >/dev/null 2>&1 || true
  done

  sleep 0.8
  for pid in "${pids[@]}"; do
    if kill -0 "${pid}" >/dev/null 2>&1; then
      echo "V19 server: force stopping ${pid}"
      kill -9 "${pid}" >/dev/null 2>&1 || true
    fi
  done
  rm -f "${pid_file}"
}

v19_wait_for_health() {
  local python_bin="$1"
  local url="$2"
  local pid="$3"
  local attempts="${4:-60}"
  local i

  for ((i = 0; i < attempts; i += 1)); do
    if "${python_bin}" - "${url}/health" <<'PY' >/dev/null 2>&1
import sys
import urllib.request

urllib.request.urlopen(sys.argv[1], timeout=0.25).read()
PY
    then
      return 0
    fi
    if ! kill -0 "${pid}" >/dev/null 2>&1; then
      return 1
    fi
    sleep 0.25
  done
  return 1
}

v19_start_server_detached() {
  local python_bin="$1"
  local repo_root="$2"
  local host="$3"
  local port="$4"
  local log_file="$5"
  local pid_file="$6"
  local url="http://${host}:${port}"
  local server_pid

  mkdir -p "$(dirname "${log_file}")"
  mkdir -p "$(dirname "${pid_file}")"
  cd "${repo_root}"

  echo "V19 server: starting detached at ${url}"
  {
    printf '\n[%s] starting v19.server:app on %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "${url}"
  } >> "${log_file}"

  server_pid="$("${python_bin}" - "${repo_root}" "${host}" "${port}" "${log_file}" <<'PY'
import os
import subprocess
import sys

repo_root, host, port, log_file = sys.argv[1:5]
env = os.environ.copy()
env["PYTHONPATH"] = repo_root + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
log = open(log_file, "ab", buffering=0)
process = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "v19.server:app", "--host", host, "--port", port],
    cwd=repo_root,
    stdin=subprocess.DEVNULL,
    stdout=log,
    stderr=subprocess.STDOUT,
    env=env,
    start_new_session=True,
)
print(process.pid)
PY
  )"
  echo "${server_pid}" > "${pid_file}"

  if ! v19_wait_for_health "${python_bin}" "${url}" "${server_pid}" 60; then
    echo "V19 server: health check failed at ${url}/health" >&2
    echo "V19 server: recent log ${log_file}" >&2
    tail -n 40 "${log_file}" >&2 || true
    kill "${server_pid}" >/dev/null 2>&1 || true
    rm -f "${pid_file}"
    return 1
  fi

  echo "V19 server: pid ${server_pid}"
  echo "V19 server: log ${log_file}"
  echo "V19 backend API: ${url}/api/agent/turn"
  echo "V19 frontend:    ${url}"
}
