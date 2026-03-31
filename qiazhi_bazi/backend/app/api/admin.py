"""Admin API：基础设施监控与联调工具。"""
from __future__ import annotations

import ipaddress
import os
import re
import time
import logging
from urllib.parse import urlparse, urlunparse
from typing import Any, Dict, List, Optional

from app.core.runtime_config import get_runtime_config, set_runtime_config
from app.db.session import DB_URL, _engine, init_db
from app.llm.client import QwenClient
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlmodel import SQLModel, create_engine

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)


class LlmTestRequest(BaseModel):
    system_prompt: str = Field(default="你是严谨的命理分析助手。")
    user_prompt: str = Field(default="请用中文简要说明‘寅申冲’的核心矛盾。")
    language: str = Field(default="ZH", description="ZH/EN/KO")
    temperature: float = 0.3
    max_tokens: int = 256
    base_url: Optional[str] = Field(default=None, description="可覆盖 LLM 地址，如 http://192.168.0.10:8000/v1")
    api_key: Optional[str] = Field(default=None, description="可覆盖 API Key")
    model: Optional[str] = Field(default=None, description="可覆盖模型名")


class DbStatusRequest(BaseModel):
    db_url: Optional[str] = Field(default=None, description="可覆盖数据库连接串")


class LlmModelsRequest(BaseModel):
    base_url: str = Field(..., description="LLM OpenAI 兼容地址")
    api_key: Optional[str] = Field(default=None, description="可选 API Key")


class RuntimeConfigRequest(BaseModel):
    llm: Dict[str, Any] = Field(default_factory=dict)


def _strip_reasoning(raw: str) -> str:
    text = (raw or "").strip()
    if not text:
        logger.warning("strip_reasoning empty_input")
        return ""
    # 常见“最终回答”锚点（含韩语常见变体）
    anchors = [
        "Final Answer:",
        "Answer:",
        "최종 결론:",
        "최종 답변:",
        "결론:",
        "판정:",
        "요약:",
        "最终回答：",
        "最终结论：",
        "结论：",
    ]
    for a in anchors:
        idx = text.rfind(a)
        if idx >= 0:
            return text[idx + len(a) :].strip()
    lower = text.lower()
    # 纯推理/思维链场景：直接判空，触发二次改写
    if (
        text.startswith("Thinking Process:")
        or text.startswith("思考过程")
        or "thinking process" in lower
        or "reasoning" in lower
        or "사고 과정" in text
    ):
        logger.warning("strip_reasoning blocked_reasoning_keywords")
        return ""
    # 终极容错：短文本且不含思考关键词，直接视为结论
    if "thinking" not in lower and "reasoning" not in lower and len(text) < 200:
        return text
    # 尝试剥离英文推理标题块
    cleaned = re.sub(r"^Thinking Process:\s*", "", text, flags=re.IGNORECASE)
    compact = cleaned.strip()
    if not compact:
        logger.warning("strip_reasoning empty_after_cleanup")
    return compact


async def _rewrite_final_only(client: QwenClient, source_text: str, language: str) -> str:
    if not source_text.strip():
        return ""
    lang_hint = {"ZH": "用中文", "EN": "Use English", "KO": "한국어로"}
    messages = [
        {
            "role": "system",
            "content": "你是结果整理器。只输出最终结论，不展示推理过程，不使用标题。",
        },
        {
            "role": "user",
            "content": (
                f"{lang_hint.get(language, '用中文')}把下面内容改写成 80 字以内的最终结论：\n"
                f"{source_text}"
            ),
        },
    ]
    result = await client.chat(messages=messages, temperature=0.1, max_tokens=128)
    return _strip_reasoning(result)


async def _compress_final_only(client: QwenClient, source_text: str, language: str) -> str:
    if not source_text.strip():
        return ""
    lang_hint = {"ZH": "中文", "EN": "English", "KO": "한국어"}
    messages = [
        {"role": "system", "content": "你是结论压缩器。只输出最终结论，不要过程，不要标题，不要列表。"},
        {
            "role": "user",
            "content": f"请用{lang_hint.get(language, '中文')}把下文压缩为120字以内结论：\n{source_text}",
        },
    ]
    result = await client.chat(messages=messages, temperature=0.1, max_tokens=96)
    return _strip_reasoning(result)


def _hard_compact_conclusion(text: str, max_len: int = 120) -> str:
    t = (text or "").strip()
    if not t:
        return ""
    # 去掉 markdown 标题与列表，取第一句
    lines = [ln.strip() for ln in t.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    plain = " ".join(lines)
    for sep in ["。", "！", "?", "？", "."]:
        idx = plain.find(sep)
        if 0 < idx < max_len:
            return plain[: idx + 1]
    return plain[:max_len]


async def _ollama_chat_no_think(
    base_url: str,
    model: str,
    messages: List[Dict[str, str]],
    temperature: float,
    max_tokens: int,
) -> str:
    import httpx

    root = base_url.rstrip("/")
    if root.endswith("/v1"):
        root = root[:-3]
    url = f"{root}/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "think": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
    return (data.get("message") or {}).get("content", "").strip()


def _allowed_hosts() -> set[str]:
    raw = os.getenv("QIAZHI_ALLOWED_HOSTS", "127.0.0.1,localhost,192.168.0.10,192.168.0.13")
    return {x.strip().lower() for x in raw.split(",") if x.strip()}


def _validate_target_url(raw_url: str, scheme_allow: set[str]) -> None:
    parsed = urlparse(raw_url)
    if parsed.scheme not in scheme_allow:
        raise HTTPException(status_code=400, detail=f"不允许的 URL 协议: {parsed.scheme}")
    if parsed.scheme == "sqlite":
        raise HTTPException(status_code=400, detail="禁止 SQLite。仅允许 PostgreSQL。")
    if not parsed.hostname:
        raise HTTPException(status_code=400, detail="URL 缺少主机名")
    host = parsed.hostname.lower()
    allowed = _allowed_hosts()
    if host in allowed:
        return
    try:
        ip = ipaddress.ip_address(host)
        if str(ip) in allowed:
            return
    except ValueError:
        pass
    raise HTTPException(status_code=403, detail=f"目标主机未在白名单内: {host}")


def _masked_db_url(raw_url: str) -> str:
    try:
        p = urlparse(raw_url)
        if p.password:
            netloc = p.netloc.replace(p.password, "***")
            return urlunparse((p.scheme, netloc, p.path, p.params, p.query, p.fragment))
    except Exception:
        pass
    return raw_url


def _admin_guard(x_admin_token: Optional[str] = Header(default=None)) -> None:
    expected = os.getenv("QIAZHI_ADMIN_TOKEN")
    # 未配置 token 时兼容本地开发；生产应配置
    if not expected:
        return
    if not x_admin_token or x_admin_token != expected:
        raise HTTPException(status_code=401, detail="admin token 无效")


def _get_db_status_with_url(target_db_url: Optional[str]) -> Dict[str, Any]:
    url = target_db_url or DB_URL
    _validate_target_url(url, {"postgresql", "postgresql+psycopg2", "postgresql+psycopg"})
    p = urlparse(url)
    if p.hostname != "192.168.0.13" or (p.port not in (None, 5432)):
        raise HTTPException(status_code=403, detail="数据库地址必须为 192.168.0.13:5432")
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
                recent_raw_data = [r[0] for r in rows]
                jsonb_rows = conn.execute(
                    text(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_schema='public' AND table_name='decision_step' "
                        "AND column_name IN ('raw_data','human_choice') AND udt_name='jsonb'"
                    )
                ).fetchall()
                jsonb_columns = [r[0] for r in jsonb_rows]
            except Exception:  # noqa: BLE001
                pass
    return {
        "ok": True,
        "db_url": _masked_db_url(url),
        "latency_ms": latency_ms,
        "counts": counts,
        "recent_raw_data": recent_raw_data,
        "jsonb_check": {
            "decision_step_jsonb_columns": jsonb_columns,
            "ok": set(jsonb_columns) == {"raw_data", "human_choice"},
        },
    }


@router.get("/db-status")
def db_status(_: None = Depends(_admin_guard)) -> Dict[str, Any]:
    try:
        return _get_db_status_with_url(target_db_url=None)
    except Exception as e:  # noqa: BLE001
        return {
            "ok": False,
            "db_url": _masked_db_url(DB_URL),
            "error": str(e),
            "hint": "连接失败。请检查账号密码、网络可达性，并确认 0.13 的 pg_hba.conf 已允许该客户端与用户。",
        }


@router.post("/db-status")
def db_status_with_override(body: DbStatusRequest, _: None = Depends(_admin_guard)) -> Dict[str, Any]:
    try:
        return _get_db_status_with_url(target_db_url=body.db_url)
    except Exception as e:  # noqa: BLE001
        return {
            "ok": False,
            "db_url": _masked_db_url(body.db_url or DB_URL),
            "error": str(e),
            "hint": "连接失败。请检查账号密码、网络可达性，并确认 0.13 的 pg_hba.conf 已允许该客户端与用户。",
        }


@router.post("/db-init")
def db_init(body: Optional[DbStatusRequest] = None, _: None = Depends(_admin_guard)) -> Dict[str, Any]:
    try:
        target = body.db_url if body else None
        if target:
            _validate_target_url(target, {"postgresql", "postgresql+psycopg2", "postgresql+psycopg"})
            from app.db import models  # noqa: F401

            engine = create_engine(target, echo=False)
            SQLModel.metadata.create_all(engine)
            status = _get_db_status_with_url(target)
            return {
                "ok": True,
                "message": "create_all 执行成功",
                "db_url": _masked_db_url(target),
                "jsonb_check": status.get("jsonb_check"),
            }
        init_db()
        status = _get_db_status_with_url(DB_URL)
        return {
            "ok": True,
            "message": "create_all 执行成功",
            "db_url": _masked_db_url(DB_URL),
            "jsonb_check": status.get("jsonb_check"),
        }
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/llm-test")
async def llm_test(body: LlmTestRequest, _: None = Depends(_admin_guard)) -> Dict[str, Any]:
    stop_words = ["Thinking Process:", "Reasoning:", "思考过程", "推理过程"]
    language_hint = {"ZH": "请用中文回答。", "EN": "Please answer in English.", "KO": "한국어로 답변해 주세요."}
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": body.system_prompt},
        {"role": "user", "content": f"{body.user_prompt}\n{language_hint.get(body.language, '')}".strip()},
    ]
    if body.base_url:
        _validate_target_url(body.base_url, {"http", "https"})
    client = QwenClient(base_url=body.base_url, api_key=body.api_key, model=body.model)
    start = time.perf_counter()
    try:
        raw_content = ""
        # 对 Ollama 推理模型优先走原生接口，显式关闭思考输出
        if body.base_url and body.model and "11434" in body.base_url:
            try:
                raw_content = await _ollama_chat_no_think(
                    base_url=body.base_url,
                    model=body.model,
                    messages=messages,
                    temperature=body.temperature,
                    max_tokens=body.max_tokens,
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
        content = _strip_reasoning(raw_content)
        if not content:
            logger.warning("llm_test strip_empty reason=no_anchor_or_blocked_keywords")
            content = await _rewrite_final_only(client, raw_content, body.language)
        if not content:
            content = "已隐藏模型推理过程。该模型当前未返回可提取的最终结论，建议切换非推理模型或在 Prompt 中明确“仅输出最终结论”。"
        elif len(content) > 220 or "###" in content or "一、" in content:
            concise = await _compress_final_only(client, content, body.language)
            if concise:
                content = concise
        if len(content) > 160 or "###" in content or "一、" in content:
            content = _hard_compact_conclusion(content, max_len=120)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"LLM 调用失败: {e}") from e
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


@router.post("/llm-models")
async def llm_models(body: LlmModelsRequest, _: None = Depends(_admin_guard)) -> Dict[str, Any]:
    """
    拉取模型列表（优先 OpenAI `/models`，兼容 Ollama `/api/tags`）。
    """
    import httpx

    url = body.base_url.rstrip("/")
    _validate_target_url(url, {"http", "https"})
    headers = {}
    if body.api_key:
        headers["Authorization"] = f"Bearer {body.api_key}"

    async with httpx.AsyncClient(timeout=20.0) as client:
        # OpenAI compatible: /v1/models
        try:
            r = await client.get(f"{url}/models", headers=headers)
            r.raise_for_status()
            data = r.json()
            items = data.get("data", [])
            names = [x.get("id") for x in items if x.get("id")]
            return {"ok": True, "models": names}
        except Exception:
            pass

        # Ollama native: /api/tags (when base url without /v1)
        try:
            fallback = url[:-3] if url.endswith("/v1") else url
            r2 = await client.get(f"{fallback}/api/tags")
            r2.raise_for_status()
            data2 = r2.json()
            models = data2.get("models", [])
            names = [x.get("model") for x in models if x.get("model")]
            return {"ok": True, "models": names}
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=f"模型列表获取失败: {e}") from e


@router.get("/runtime-config")
def runtime_config_get(_: None = Depends(_admin_guard)) -> Dict[str, Any]:
    return {"ok": True, "config": get_runtime_config()}


@router.put("/runtime-config")
def runtime_config_put(body: RuntimeConfigRequest, _: None = Depends(_admin_guard)) -> Dict[str, Any]:
    llm = body.llm or {}
    base_url = llm.get("base_url")
    if isinstance(base_url, str) and base_url.strip():
        _validate_target_url(base_url.strip(), {"http", "https"})
    updated = set_runtime_config({"llm": body.llm})
    return {"ok": True, "config": updated}
