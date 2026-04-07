"""基础设施握手脚本：检测本地 DB + LLM(0.10) 连通性。"""
from __future__ import annotations

import asyncio
import json
import os
import sys

import httpx
from sqlalchemy import text

from app.db.session import DB_URL, _engine, init_db


async def check_llm() -> tuple[bool, str]:
    base_url = os.getenv("QIAZHI_BAZI_LLM_BASE_URL", "http://192.168.0.10:8000/v1").rstrip("/")
    api_key = os.getenv("QIAZHI_BAZI_LLM_API_KEY", "empty")
    model = os.getenv("QIAZHI_BAZI_LLM_MODEL", "qwen")
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "请用韩语说一句“你好”。"}],
        "temperature": 0.2,
        "max_tokens": 64,
        "stream": False,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return True, content.strip() or "<empty>"
    except Exception as e:  # noqa: BLE001
        return False, str(e)


def check_db() -> tuple[bool, str]:
    try:
        # 1) 连接可用
        with _engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        # 2) 尝试自动建表
        init_db()
        return True, "连接成功，可执行 create_all。"
    except Exception as e:  # noqa: BLE001
        return False, str(e)


async def main() -> int:
    print("=== Qiazhi-Bazi Infra Handshake ===")
    print(f"DATABASE_URL: {DB_URL}")
    print(f"LLM_BASE_URL: {os.getenv('QIAZHI_BAZI_LLM_BASE_URL', 'http://192.168.0.10:8000/v1')}")

    db_ok, db_msg = check_db()
    print(f"[DB] {'OK' if db_ok else 'FAIL'}: {db_msg}")

    llm_ok, llm_msg = await check_llm()
    if llm_ok:
        print("[LLM] OK: /v1/chat/completions 有响应")
        print(f"[LLM-KR] {llm_msg}")
    else:
        print(f"[LLM] FAIL: {llm_msg}")

    summary = {
        "db_ok": db_ok,
        "llm_ok": llm_ok,
        "llm_korean_preview": llm_msg if llm_ok else None,
    }
    print("[SUMMARY]", json.dumps(summary, ensure_ascii=False))
    return 0 if db_ok and llm_ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
