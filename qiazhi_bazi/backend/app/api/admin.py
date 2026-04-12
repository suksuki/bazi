"""Admin API：基础设施监控与联调工具。"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from app.api.admin_auth import admin_token_guard
from app.api.admin_helpers import (
    hard_compact_conclusion,
    parse_allowed_param_update,
    redact_runtime_config_for_api_response,
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
from app.core.llm_ollama import looks_like_native_ollama_base_url
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
    *,
    request_options: Optional[Dict[str, Any]] = None,
    runtime_options: Optional[Dict[str, Any]] = None,
) -> str:
    import httpx

    from app.core.llm_ollama import merge_ollama_chat_options

    root = base_url.rstrip("/")
    if root.endswith("/v1"):
        root = root[:-3]
    url = f"{root}/api/chat"
    opts = merge_ollama_chat_options(
        temperature=temperature,
        num_predict=max_tokens,
        request_options=request_options,
        runtime_options=runtime_options,
    )
    base_payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": opts,
    }
    # 常见指令小模型无 think；推理模型需压思考链时设 QIAZHI_OLLAMA_CHAT_THINK_FALSE=1。
    if os.getenv("QIAZHI_OLLAMA_CHAT_THINK_FALSE", "").lower() in ("1", "true", "yes"):
        base_payload = {**base_payload, "think": False}
    timeout_sec = float(os.getenv("QIAZHI_ADMIN_OLLAMA_TIMEOUT_SEC", "240") or "240")
    async with httpx.AsyncClient(timeout=timeout_sec) as client:
        r = await client.post(url, json=base_payload)
        r.raise_for_status()
        data = r.json()
        return (data.get("message") or {}).get("content", "").strip()


@router.get("/db-status")
def db_status(_: None = Depends(admin_token_guard)) -> Dict[str, Any]:
    return get_db_status_response(None)


@router.post("/db-status")
def db_status_with_override(body: DbStatusRequest, _: None = Depends(admin_token_guard)) -> Dict[str, Any]:
    return get_db_status_response(body)


@router.post("/db-init")
def db_init(body: Optional[DbStatusRequest] = None, _: None = Depends(admin_token_guard)) -> Dict[str, Any]:
    return initialize_database(body)


@router.post("/llm-test")
async def llm_test(body: LlmTestRequest, _: None = Depends(admin_token_guard)) -> Dict[str, Any]:
    return await execute_llm_test(
        body,
        rewrite_final_only=_rewrite_final_only,
        compress_final_only=_compress_final_only,
        ollama_chat_no_think=_ollama_chat_no_think,
        logger=logger,
    )


async def _collect_llm_model_names(base_url: str, api_key: Optional[str]) -> List[str]:
    """
    兼容 OpenAI 风格 /v1/models 与 Ollama /api/tags。
    - base_url 未带 /v1 时补试 /v1/models（修复仅填 https://api.openai.com 导致 502）。
    - URL 命中 QIAZHI_OLLAMA_NATIVE_PORTS 所列端口时优先走 Ollama 原生接口（部分环境下 /v1/models 不可用）。
    """
    import httpx

    url = (base_url or "").strip().rstrip("/")
    if not url:
        raise HTTPException(status_code=400, detail="base_url 不能为空")
    validate_target_url(url, {"http", "https"})

    headers: Dict[str, str] = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try_ollama_first = looks_like_native_ollama_base_url(url)

    def ollama_root(u: str) -> str:
        return u[:-3] if u.endswith("/v1") else u

    root = ollama_root(url).rstrip("/")
    errs: List[str] = []

    def _err_msg(exc: BaseException) -> str:
        s = str(exc).strip()
        return f"{type(exc).__name__}: {s}" if s else type(exc).__name__

    openai_endpoints: List[str] = []
    if url.endswith("/v1"):
        openai_endpoints.append(f"{url}/models")
    else:
        openai_endpoints.append(f"{url}/v1/models")
        openai_endpoints.append(f"{url}/models")

    async def get_ollama_tags(client: httpx.AsyncClient) -> Optional[List[str]]:
        ep = f"{root}/api/tags"
        try:
            r = await client.get(ep)
            r.raise_for_status()
            data = r.json()
        except Exception as e:  # noqa: BLE001
            errs.append(f"{ep}: {_err_msg(e)}")
            return None
        if not isinstance(data, dict):
            errs.append(f"{ep}: 响应非 JSON 对象")
            return None
        models = data.get("models")
        if not isinstance(models, list):
            errs.append(f"{ep}: 缺少 models 数组")
            return None
        # Ollama 文档：ModelSummary 含 name / model（部分版本仅返回其一）
        out: List[str] = []
        for m in models:
            if not isinstance(m, dict):
                continue
            mid = m.get("model") or m.get("name")
            if mid:
                out.append(str(mid).strip())
        return out

    async def get_openai_ids(client: httpx.AsyncClient, endpoint: str) -> Optional[List[str]]:
        try:
            r = await client.get(endpoint, headers=headers)
            r.raise_for_status()
            data = r.json()
        except Exception as e:  # noqa: BLE001
            errs.append(f"{endpoint}: {_err_msg(e)}")
            return None
        if not isinstance(data, dict):
            errs.append(f"{endpoint}: 响应非 JSON 对象")
            return None
        items = data.get("data")
        if items is None:
            errs.append(f"{endpoint}: 缺少 data 字段")
            return None
        if not isinstance(items, list):
            errs.append(f"{endpoint}: data 非数组")
            return None
        return [str(x["id"]) for x in items if isinstance(x, dict) and x.get("id")]

    # 串行尝试多个端点，总超时过长会导致网关 502 / 前端一直「连接中」；收紧单次连接与读超时
    _httpx_timeout = httpx.Timeout(12.0, connect=4.0)
    async with httpx.AsyncClient(timeout=_httpx_timeout, follow_redirects=True) as client:
        if try_ollama_first:
            names = await get_ollama_tags(client)
            # 仅当解析到至少一个模型名时才短路；[] 可能是未装模型，也可能是旧字段遗漏，继续试 OpenAI 兼容路径
            if names:
                return names

        for ep in openai_endpoints:
            names = await get_openai_ids(client, ep)
            if names is not None:
                return names

        if not try_ollama_first:
            names = await get_ollama_tags(client)
            if names is not None:
                return names

    raise HTTPException(status_code=502, detail="模型列表获取失败: " + " | ".join(errs[:10]))


@router.post("/llm-models")
async def llm_models(body: LlmModelsRequest, _: None = Depends(admin_token_guard)) -> Dict[str, Any]:
    """拉取模型列表（OpenAI 兼容 /v1/models 与 Ollama /api/tags，多路径容错）。"""
    names = await _collect_llm_model_names(body.base_url, body.api_key)
    return {"ok": True, "models": names}


@router.get("/runtime-config")
def runtime_config_get(_: None = Depends(admin_token_guard)) -> Dict[str, Any]:
    return {"ok": True, "config": redact_runtime_config_for_api_response(get_runtime_config())}


@router.put("/runtime-config")
def runtime_config_put(body: RuntimeConfigRequest, _: None = Depends(admin_token_guard)) -> Dict[str, Any]:
    """合并写入 ``runtime_config.json``。

    ``llm`` 可选字段 ``is_high_reasoning_mode``（bool）：为 true 时终判 ``prompt_builder`` 使用全量插件
    evidence 溯源档位，不做短句碎片化截断（强模型切换前可预置）。
    """
    llm = body.llm or {}
    base_url = llm.get("base_url")
    if isinstance(base_url, str) and base_url.strip():
        validate_target_url(base_url.strip(), {"http", "https"})
    patch: Dict[str, Any] = {}
    if body.llm:
        patch["llm"] = body.llm
    if body.causal_routing is not None:
        patch["causal_routing"] = body.causal_routing
    updated = set_runtime_config(patch)
    return {"ok": True, "config": redact_runtime_config_for_api_response(updated)}


@router.post("/refresh-physics")
def refresh_physics(_: None = Depends(admin_token_guard)) -> Dict[str, Any]:
    PhysicsInferenceSkill.instance().refresh_and_recalculate()
    return {"ok": True, "message": "physics cache refreshed"}
@router.post("/apply-physics-sql")
def apply_physics_sql(body: ApplyPhysicsSqlRequest, _: None = Depends(admin_token_guard)) -> Dict[str, Any]:
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
