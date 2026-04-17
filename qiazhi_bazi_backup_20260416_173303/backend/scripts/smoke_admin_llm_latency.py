#!/usr/bin/env python3
"""
测量管理页「Test LLM」等价路径的耗时：直连 Ollama /api/chat vs 经 FastAPI POST /api/admin/llm-test。

用法（在 backend 目录）:
  python3 scripts/smoke_admin_llm_latency.py --model <你的0.5B模型名>
  python3 scripts/smoke_admin_llm_latency.py --model qwen2.5:0.5b --backend http://127.0.0.1:8001
  QIAZHI_ADMIN_TOKEN=xxx python3 scripts/smoke_admin_llm_latency.py --model qwen2.5:0.5b

环境变量:
  QIAZHI_ADMIN_TOKEN   调用 /api/admin/llm-test 时默认 X-Admin-Token（未设且连本机 8001 时用 local-dev-qiazhi-admin）
  OLLAMA_ROOT          默认 http://127.0.0.1:11434
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import httpx

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))
os.environ.setdefault("DATABASE_URL", os.getenv("DATABASE_URL", "postgresql://test:test@127.0.0.1:5432/test"))


def _ollama_chat_direct(
    *,
    root: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
    temperature: float,
) -> tuple[float, str]:
    root = root.rstrip("/")
    url = f"{root}/api/chat"
    payload: dict = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "options": {"temperature": temperature, "num_predict": max_tokens},
    }
    timeout = float(os.getenv("QIAZHI_ADMIN_OLLAMA_TIMEOUT_SEC", "240") or "240")
    t0 = time.perf_counter()
    with httpx.Client(timeout=timeout) as client:
        r = client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    text = ((data.get("message") or {}).get("content") or "").strip()
    return elapsed_ms, text


def _admin_llm_test(
    *,
    backend: str,
    admin_token: str,
    base_url: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
    temperature: float,
    fast_path: bool,
) -> tuple[float, dict]:
    backend = backend.rstrip("/")
    url = f"{backend}/api/admin/llm-test"
    body = {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "language": "ZH",
        "temperature": temperature,
        "max_tokens": max_tokens,
        "base_url": base_url,
        "model": model,
        "fast_path": fast_path,
    }
    headers = {"Content-Type": "application/json", "X-Admin-Token": admin_token}
    t0 = time.perf_counter()
    with httpx.Client(timeout=300.0) as client:
        r = client.post(url, json=body, headers=headers)
        r.raise_for_status()
        data = r.json()
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return elapsed_ms, data


def main() -> int:
    ap = argparse.ArgumentParser(description="Smoke: Ollama direct vs FastAPI admin llm-test latency.")
    ap.add_argument("--model", default=os.getenv("QIAZHI_BAZI_LLM_MODEL", ""), help="Ollama 模型名，如 qwen2.5:0.5b")
    ap.add_argument("--ollama-root", default=os.getenv("OLLAMA_ROOT", "http://127.0.0.1:11434"), help="Ollama 根地址（无 /v1）")
    ap.add_argument(
        "--openai-base",
        default="",
        help="传给后端的 base_url（须含 /v1），默认由 --ollama-root 推导为 {root}/v1",
    )
    ap.add_argument("--backend", default=os.getenv("QIAZHI_SMOKE_BACKEND", "http://127.0.0.1:8001"), help="FastAPI 根；设为空字符串则跳过 llm-test")
    ap.add_argument(
        "--admin-token",
        default=os.getenv("QIAZHI_ADMIN_TOKEN", "local-dev-qiazhi-admin"),
        help="X-Admin-Token",
    )
    ap.add_argument("--max-tokens", type=int, default=256)
    ap.add_argument("--temperature", type=float, default=0.3)
    ap.add_argument("--no-fast-path", action="store_true", help="llm-test 传 fast_path=false（会可能多一轮压缩）")
    args = ap.parse_args()
    if not (args.model or "").strip():
        print("请指定 --model 或环境变量 QIAZHI_BAZI_LLM_MODEL", file=sys.stderr)
        return 2

    system_prompt = "你是严谨的命理分析助手。"
    user_prompt = "请评估‘墓库开闭’对命盘稳定性的影响。"
    openai_base = (args.openai_base or "").strip() or f"{args.ollama_root.rstrip('/')}/v1"

    print("=== smoke_admin_llm_latency ===", flush=True)
    print(f"model={args.model!r} ollama_root={args.ollama_root!r}", flush=True)
    print(f"prompt user (len={len(user_prompt)}): {user_prompt}", flush=True)

    # 0) Ollama 是否在线
    try:
        r = httpx.get(f"{args.ollama_root.rstrip('/')}/api/tags", timeout=5.0)
        print(f"GET /api/tags -> HTTP {r.status_code}", flush=True)
    except Exception as exc:  # noqa: BLE001
        print(f"WARN: 无法连接 Ollama ({args.ollama_root}): {exc}", flush=True)

    # 1) 直连 Ollama
    try:
        ms, text = _ollama_chat_direct(
            root=args.ollama_root,
            model=args.model.strip(),
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
        )
        approx_tok = max(len(text), 1) / 1.8
        tps = round(approx_tok / (ms / 1000.0), 3) if ms > 0 else 0.0
        print(f"\n[1] 直连 Ollama /api/chat  wall_ms={ms:.2f}  approx_tok/s={tps}", flush=True)
        print(f"    reply_len={len(text)} preview: {text[:200]!r}{'…' if len(text) > 200 else ''}", flush=True)
    except Exception as exc:  # noqa: BLE001
        print(f"\n[1] 直连 Ollama 失败: {exc}", file=sys.stderr, flush=True)
        return 1

    # 2) 经 FastAPI（可选）
    backend = (args.backend or "").strip()
    if not backend:
        print("\n[2] 跳过（未指定 --backend）", flush=True)
        return 0

    try:
        ms2, data = _admin_llm_test(
            backend=backend,
            admin_token=args.admin_token,
            base_url=openai_base,
            model=args.model.strip(),
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            fast_path=not args.no_fast_path,
        )
        api_elapsed = data.get("elapsed_ms")
        content = str(data.get("content") or "")
        approx2 = max(len(content), 1) / 1.8
        tps2 = round(approx2 / (ms2 / 1000.0), 3) if ms2 > 0 else 0.0
        print(f"\n[2] POST {backend}/api/admin/llm-test  wall_ms={ms2:.2f}  body.elapsed_ms={api_elapsed}", flush=True)
        print(f"    fast_path={not args.no_fast_path} approx_tok/s(按墙钟)={tps2}", flush=True)
        print(f"    reply_len={len(content)} preview: {content[:200]!r}{'…' if len(content) > 200 else ''}", flush=True)
        overhead = ms2 - float(ms)
        print(f"\n墙钟差 (llm-test - 直连) ≈ {overhead:.2f} ms（含 FastAPI+httpx 与后端计时口径差异）", flush=True)
    except httpx.HTTPStatusError as exc:
        print(f"\n[2] llm-test HTTP {exc.response.status_code}: {exc.response.text[:500]}", file=sys.stderr, flush=True)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"\n[2] llm-test 失败: {exc}", file=sys.stderr, flush=True)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
