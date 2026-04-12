#!/usr/bin/env python3
"""
复现与修复验证：与 POST /api/admin/llm-models 使用同一套 _collect_llm_model_names 逻辑。

在 backend 根目录执行:
  cd qiazhi_bazi/backend && python3 scripts/smoke_llm_models_fetch.py
  QIAZHI_LLM_SMOKE_BASE_URL=http://127.0.0.1:11434/v1 python3 scripts/smoke_llm_models_fetch.py
  python3 scripts/smoke_llm_models_fetch.py --base-url http://127.0.0.1:11434/v1

若本脚本能列出模型而浏览器不能，多为：未重启后端、API_BASE 指错服务、或 Admin Token 与脚本环境不一致。
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from fastapi import HTTPException

# 与 pytest conftest 一致，避免 import app 时缺省
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))
os.environ.setdefault("DATABASE_URL", os.getenv("DATABASE_URL", "postgresql://test:test@127.0.0.1:5432/test"))


def _raw_probe(base_url: str) -> None:
    """不经过白名单，仅看网络层 Ollama/OpenAI 原始响应（用于区分 502 是连不上还是解析错）。"""
    import httpx

    url = base_url.strip().rstrip("/")
    root = url[:-3] if url.endswith("/v1") else url
    root = root.rstrip("/")
    _t = httpx.Timeout(10.0, connect=3.0)
    print("\n--- 原始探测（不经 validate / 不经业务解析）---", flush=True)
    for label, get_url in [
        ("Ollama GET /api/tags", f"{root}/api/tags"),
        ("OpenAI-compat GET /v1/models", f"{url}/models" if url.endswith("/v1") else f"{url}/v1/models"),
    ]:
        try:
            r = httpx.get(get_url, timeout=_t, follow_redirects=True)
            print(f"{label}: HTTP {r.status_code} len={len(r.content)}", flush=True)
            if r.headers.get("content-type", "").startswith("application/json"):
                data = r.json()
                print(json.dumps(data, ensure_ascii=False, indent=2)[:2000], flush=True)
                if isinstance(data, dict) and isinstance(data.get("models"), list) and data["models"]:
                    first = data["models"][0]
                    if isinstance(first, dict):
                        print(f"  首条 keys: {list(first.keys())}", flush=True)
                        print(f"  model= {first.get('model')!r} name= {first.get('name')!r}", flush=True)
            else:
                print(r.text[:500], flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"{label}: 异常 {type(e).__name__}: {e}", flush=True)


async def _run_collect(base_url: str, api_key: str | None) -> list[str]:
    from app.api.admin import _collect_llm_model_names

    return await _collect_llm_model_names(base_url, api_key)


def _validate_only(base_url: str) -> None:
    from app.api.admin_helpers import validate_target_url

    print("\n--- validate_target_url ---", flush=True)
    try:
        validate_target_url(base_url.strip().rstrip("/"), {"http", "https"})
        print("白名单: 通过", flush=True)
    except HTTPException as e:
        print(f"白名单: 失败 HTTP {e.status_code} {e.detail}", flush=True)
        raise SystemExit(2) from e


def main() -> None:
    p = argparse.ArgumentParser(description="Smoke test llm-models fetch (same as admin API).")
    p.add_argument(
        "--base-url",
        default=os.getenv("QIAZHI_LLM_SMOKE_BASE_URL") or "",
        help="与 Admin「有效 Base URL」一致，通常带 /v1；未传则须设置环境变量 QIAZHI_LLM_SMOKE_BASE_URL",
    )
    p.add_argument("--api-key", default=os.getenv("QIAZHI_LLM_SMOKE_API_KEY", "") or None, help="可选 Bearer")
    p.add_argument("--skip-raw", action="store_true", help="跳过原始 httpx 探测")
    args = p.parse_args()
    base_url = (args.base_url or "").strip()
    if not base_url:
        print("错误: 请传入 --base-url 或设置环境变量 QIAZHI_LLM_SMOKE_BASE_URL", flush=True)
        raise SystemExit(2)

    print("base_url:", base_url, flush=True)
    print("QIAZHI_ALLOWED_HOSTS:", os.getenv("QIAZHI_ALLOWED_HOSTS", "(未设置，使用代码默认 127.0.0.1,localhost)"), flush=True)

    if not args.skip_raw:
        _raw_probe(base_url)

    _validate_only(base_url)

    print("\n--- _collect_llm_model_names（与 /api/admin/llm-models 一致）---", flush=True)
    try:
        names = asyncio.run(_run_collect(base_url, args.api_key))
    except HTTPException as e:
        print(f"失败（与接口一致）: HTTP {e.status_code} detail={e.detail!r}", flush=True)
        raise SystemExit(1) from e
    except Exception as e:  # noqa: BLE001
        print(f"失败: {type(e).__name__}: {e}", flush=True)
        raise SystemExit(1) from e

    print("ok, models count:", len(names), flush=True)
    print(json.dumps(names, ensure_ascii=False, indent=2), flush=True)
    if not names:
        print("警告: 列表为空。若原始探测里 /api/tags 有模型，请检查后端是否已部署最新 admin.py。")
        raise SystemExit(3)


if __name__ == "__main__":
    main()
