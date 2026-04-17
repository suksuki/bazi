#!/usr/bin/env bash
# 在「能访问 Ollama 的局域网机器」上执行（例如 0.13 应用服务器），检测指定主机 Ollama 是否可拉模型。
#
# 用法:
#   ./scripts/check_ollama_lan.sh
#   OLLAMA_HOST=127.0.0.1 OLLAMA_PORT=11434 ./scripts/check_ollama_lan.sh
#
# 依赖: curl（无则退出 2）

set -euo pipefail
HOST="${OLLAMA_HOST:-127.0.0.1}"
PORT="${OLLAMA_PORT:-11434}"
BASE="http://${HOST}:${PORT}"

echo "== Ollama 局域网探测 =="
echo "目标: ${BASE}"
echo ""

if ! command -v curl >/dev/null 2>&1; then
  echo "错误: 未找到 curl" >&2
  exit 2
fi

echo "--- GET ${BASE}/api/tags (Ollama 原生) ---"
code_tags=$(curl -sS -o /tmp/ollama_tags.json -w "%{http_code}" --connect-timeout 5 --max-time 15 "${BASE}/api/tags" || true)
echo "HTTP ${code_tags}"
if [[ "${code_tags}" == "200" ]] && [[ -s /tmp/ollama_tags.json ]]; then
  head -c 1200 /tmp/ollama_tags.json
  echo ""
  if command -v python3 >/dev/null 2>&1; then
    python3 - <<'PY'
import json, sys
try:
    d = json.load(open("/tmp/ollama_tags.json"))
    m = d.get("models") or []
    names = []
    for x in m:
        if isinstance(x, dict):
            n = x.get("model") or x.get("name")
            if n:
                names.append(str(n))
    print("解析到模型数:", len(names))
    for n in names[:20]:
        print(" ", n)
    if not names:
        print("(models 数组为空或缺少 name/model 字段)")
except Exception as e:
    print("JSON 解析失败:", e)
PY
  fi
else
  echo "(未拿到 200 或 body 为空，请检查 Ollama 是否监听 0.0.0.0:${PORT}、防火墙、本机路由)"
fi

echo ""
echo "--- GET ${BASE}/v1/models (OpenAI 兼容) ---"
code_v1=$(curl -sS -o /tmp/ollama_v1_models.json -w "%{http_code}" --connect-timeout 5 --max-time 15 "${BASE}/v1/models" || true)
echo "HTTP ${code_v1}"
if [[ "${code_v1}" == "200" ]] && [[ -s /tmp/ollama_v1_models.json ]]; then
  head -c 1200 /tmp/ollama_v1_models.json
  echo ""
fi

echo ""
echo "== 与后端一致的自检（需本仓库 backend 路径、Python 依赖）=="
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
BACKEND_ROOT=$(cd "${SCRIPT_DIR}/.." && pwd)
if [[ -f "${BACKEND_ROOT}/scripts/smoke_llm_models_fetch.py" ]]; then
  (cd "${BACKEND_ROOT}" && python3 scripts/smoke_llm_models_fetch.py --base-url "${BASE}/v1" --skip-raw) || true
else
  echo "跳过: 未找到 smoke_llm_models_fetch.py"
fi

echo ""
echo "完成。若本机在局域网仍超时，问题在网络层，不是前端解析。"
