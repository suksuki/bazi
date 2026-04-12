"""Service helpers for admin infrastructure and LLM diagnostics."""
from __future__ import annotations

import ipaddress
import os
import time
from typing import Any, Awaitable, Callable, Dict, List, Optional
from urllib.parse import urlparse

from fastapi import HTTPException
from sqlalchemy import text
from sqlmodel import SQLModel, create_engine

from app.api.admin_helpers import (
    hard_compact_conclusion,
    jsonb_check_payload,
    masked_db_url,
    strip_reasoning,
    trust_any_host,
    validate_target_url,
)
from app.api.contracts import DbStatusRequest, LlmTestRequest
from app.core.llm_ollama import looks_like_native_ollama_base_url
from app.db.session import DB_URL, _engine, init_db
from app.llm.client import QwenClient

RewriteFn = Callable[[QwenClient, str, str], Awaitable[str]]
CompressFn = Callable[[QwenClient, str, str], Awaitable[str]]
OllamaFn = Callable[[str, str, List[Dict[str, str]], float, int], Awaitable[str]]


def _admin_db_host_allowed(hostname: str, allowed_db_hosts: set[str]) -> bool:
    if trust_any_host():
        return True
    h = (hostname or "").lower()
    if h in allowed_db_hosts:
        return True
    try:
        ip = ipaddress.ip_address(h)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return not (os.getenv("QIAZHI_STRICT_DB_HOSTS", "").lower() in ("1", "true", "yes"))
    except ValueError:
        pass
    return False


def get_db_status_payload(target_db_url: Optional[str]) -> Dict[str, Any]:
    url = target_db_url or DB_URL
    validate_target_url(url, {"postgresql", "postgresql+psycopg2", "postgresql+psycopg"})
    parsed = urlparse(url)
    allowed_db_hosts = {"127.0.0.1", "localhost", "::1", "host.docker.internal"}
    extra_hosts = os.getenv("QIAZHI_ALLOWED_DB_HOSTS", "").strip()
    if extra_hosts:
        allowed_db_hosts.update({host.strip().lower() for host in extra_hosts.split(",") if host.strip()})
    host = (parsed.hostname or "").lower()
    if not _admin_db_host_allowed(host, allowed_db_hosts):
        allowed_str = ", ".join(sorted(allowed_db_hosts))
        raise HTTPException(
            status_code=403,
            detail=f"数据库主机未放行：{host}。默认可用 127.0.0.1/localhost 及私网 IP；域名请写入 QIAZHI_ALLOWED_DB_HOSTS。",
        )

    engine = _engine if not target_db_url else create_engine(url, echo=False)
    start = time.perf_counter()
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        table_count = conn.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema='public' AND table_name IN ('consultation', 'decision_step')"
            )
        ).scalar_one()
        counts = {"consultation": None, "decision_step": None}
        recent_raw_data: List[Any] = []
        jsonb_columns: List[str] = []
        if table_count:
            try:
                counts["consultation"] = conn.execute(text("SELECT COUNT(*) FROM consultation")).scalar_one()
                counts["decision_step"] = conn.execute(text("SELECT COUNT(*) FROM decision_step")).scalar_one()
                rows = conn.execute(text("SELECT raw_data FROM decision_step ORDER BY id DESC LIMIT 5")).fetchall()
                recent_raw_data = [row[0] for row in rows]
                jsonb_rows = conn.execute(
                    text(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_schema='public' AND table_name='decision_step' "
                        "AND column_name IN ('raw_data','human_choice') AND udt_name='jsonb'"
                    )
                ).fetchall()
                jsonb_columns = [row[0] for row in jsonb_rows]
            except Exception:
                pass
    return jsonb_check_payload(
        latency_ms=latency_ms,
        url=url,
        counts=counts,
        recent_raw_data=recent_raw_data,
        jsonb_columns=jsonb_columns,
    )


def get_db_status_response(body: Optional[DbStatusRequest]) -> Dict[str, Any]:
    target = body.db_url if body else None
    try:
        return get_db_status_payload(target_db_url=target)
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "db_url": masked_db_url(target or DB_URL),
            "error": str(exc),
            "hint": "连接失败。请检查账号密码、数据库服务状态与目标地址是否在白名单内。",
        }


def initialize_database(body: Optional[DbStatusRequest]) -> Dict[str, Any]:
    target = body.db_url if body else None
    try:
        if target:
            validate_target_url(target, {"postgresql", "postgresql+psycopg2", "postgresql+psycopg"})
            from app.db import models  # noqa: F401

            engine = create_engine(target, echo=False)
            SQLModel.metadata.create_all(engine)
            status = get_db_status_payload(target)
            return {
                "ok": True,
                "message": "create_all 执行成功",
                "db_url": masked_db_url(target),
                "jsonb_check": status.get("jsonb_check"),
            }

        init_db()
        status = get_db_status_payload(DB_URL)
        return {
            "ok": True,
            "message": "create_all 执行成功",
            "db_url": masked_db_url(DB_URL),
            "jsonb_check": status.get("jsonb_check"),
        }
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


async def execute_llm_test(
    body: LlmTestRequest,
    *,
    rewrite_final_only: RewriteFn,
    compress_final_only: CompressFn,
    ollama_chat_no_think: OllamaFn,
    logger: Any,
) -> Dict[str, Any]:
    stop_words = ["Thinking Process:", "Reasoning:", "思考过程", "推理过程"]
    language_hint = {"ZH": "请用中文回答。", "EN": "Please answer in English.", "KO": "한국어로 답변해 주세요."}
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": body.system_prompt},
        {"role": "user", "content": f"{body.user_prompt}\n{language_hint.get(body.language, '')}".strip()},
    ]
    if body.base_url:
        validate_target_url(body.base_url, {"http", "https"})

    client = QwenClient(base_url=body.base_url, api_key=body.api_key, model=body.model)
    start = time.perf_counter()
    try:
        raw_content = ""
        if body.base_url and body.model and looks_like_native_ollama_base_url(body.base_url):
            try:
                raw_content = await ollama_chat_no_think(
                    body.base_url,
                    body.model,
                    messages,
                    body.temperature,
                    body.max_tokens,
                )
            except Exception:
                raw_content = ""
        if not raw_content:
            raw_content = await client.chat(
                messages=messages,
                temperature=body.temperature,
                max_tokens=body.max_tokens,
                stop=stop_words,
            )

        logger.info("llm_test raw_content: %s", raw_content)
        content = strip_reasoning(raw_content)
        if not content:
            logger.warning("llm_test strip_empty reason=no_anchor_or_blocked_keywords")
            if body.fast_path:
                content = "已隐藏模型推理过程。该模型当前未返回可提取的最终结论，建议切换非推理模型或在 Prompt 中明确“仅输出最终结论”。"
            else:
                content = await rewrite_final_only(client, raw_content, body.language)
        if not content:
            content = "已隐藏模型推理过程。该模型当前未返回可提取的最终结论，建议切换非推理模型或在 Prompt 中明确“仅输出最终结论”。"
        elif not body.fast_path and (len(content) > 220 or "###" in content or "一、" in content):
            concise = await compress_final_only(client, content, body.language)
            if concise:
                content = concise
        if len(content) > 160 or "###" in content or "一、" in content:
            content = hard_compact_conclusion(content, max_len=120)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"LLM 调用失败: {exc}") from exc

    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    token_per_sec: Optional[float] = None
    approx_tokens = len(content) / 1.8 if content else 0
    if elapsed_ms > 0 and approx_tokens > 0:
        token_per_sec = round(approx_tokens / (elapsed_ms / 1000), 2)
    return {
        "ok": True,
        "language": body.language,
        "elapsed_ms": elapsed_ms,
        "approx_tokens_per_sec": token_per_sec,
        "content": content,
    }
