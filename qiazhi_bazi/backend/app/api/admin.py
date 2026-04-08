"""Admin API：基础设施监控与联调工具。"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlmodel import select

from app.api.admin_helpers import (
    hard_compact_conclusion,
    parse_allowed_param_update,
    strip_reasoning,
    validate_target_url,
)
from app.api.contracts import (
    ApplyPhysicsSqlRequest,
    DbStatusRequest,
    LlmModelsRequest,
    LlmTestRequest,
    RuntimeConfigRequest,
)
from app.core.runtime_config import get_runtime_config, set_runtime_config
from app.db.models import PhysicsInteractionParam
from app.db.session import session_scope
from app.llm.client import QwenClient
from app.skills.physics_engine import PhysicsInferenceSkill
from app.services.admin_service import execute_llm_test, get_db_status_response, initialize_database

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)


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
    return strip_reasoning(result)


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
    return strip_reasoning(result)


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


def _admin_guard(x_admin_token: Optional[str] = Header(default=None)) -> None:
    expected = os.getenv("QIAZHI_ADMIN_TOKEN")
    # 未配置 token 时兼容本地开发；生产应配置
    if not expected:
        return
    if not x_admin_token or x_admin_token != expected:
        raise HTTPException(status_code=401, detail="admin token 无效")

@router.get("/db-status")
def db_status(_: None = Depends(_admin_guard)) -> Dict[str, Any]:
    return get_db_status_response(None)


@router.post("/db-status")
def db_status_with_override(body: DbStatusRequest, _: None = Depends(_admin_guard)) -> Dict[str, Any]:
    return get_db_status_response(body)


@router.post("/db-init")
def db_init(body: Optional[DbStatusRequest] = None, _: None = Depends(_admin_guard)) -> Dict[str, Any]:
    return initialize_database(body)


@router.post("/llm-test")
async def llm_test(body: LlmTestRequest, _: None = Depends(_admin_guard)) -> Dict[str, Any]:
    return await execute_llm_test(
        body,
        rewrite_final_only=_rewrite_final_only,
        compress_final_only=_compress_final_only,
        ollama_chat_no_think=_ollama_chat_no_think,
        logger=logger,
    )


@router.post("/llm-models")
async def llm_models(body: LlmModelsRequest, _: None = Depends(_admin_guard)) -> Dict[str, Any]:
    """
    拉取模型列表（优先 OpenAI `/models`，兼容 Ollama `/api/tags`）。
    """
    import httpx

    url = body.base_url.rstrip("/")
    validate_target_url(url, {"http", "https"})
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
        validate_target_url(base_url.strip(), {"http", "https"})
    updated = set_runtime_config({"llm": body.llm})
    return {"ok": True, "config": updated}


@router.post("/refresh-physics")
def refresh_physics(_: None = Depends(_admin_guard)) -> Dict[str, Any]:
    PhysicsInferenceSkill.instance().refresh_and_recalculate()
    return {"ok": True, "message": "physics cache refreshed"}
@router.post("/apply-physics-sql")
def apply_physics_sql(body: ApplyPhysicsSqlRequest, _: None = Depends(_admin_guard)) -> Dict[str, Any]:
    key, val = parse_allowed_param_update(body.sql_patch)
    with session_scope() as s:
        row = s.exec(select(PhysicsInteractionParam).where(PhysicsInteractionParam.param_key == key)).first()
        if row is None:
            row = PhysicsInteractionParam(param_key=key, param_value=val)
            s.add(row)
            old_val = None
        else:
            old_val = float(row.param_value)
            row.param_value = val
            s.add(row)
    if body.auto_refresh:
        PhysicsInferenceSkill.instance().refresh_and_recalculate()
    return {
        "ok": True,
        "updated": {"param_key": key, "old_value": old_val, "new_value": val},
        "auto_refresh": body.auto_refresh,
    }
