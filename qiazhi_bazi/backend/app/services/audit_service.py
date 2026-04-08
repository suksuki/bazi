"""Audit service layer for physics + LLM structured review."""
from __future__ import annotations

import json
import time
from typing import Any, Dict, List

from app.api.contracts import AuditLlmStructuredResponse, AuditPhysicsWithLlmRequest
from app.api.router_helpers import (
    build_physics_audit_prompt,
    extract_first_json_object,
)
from app.core.runtime_config import get_runtime_config
from app.llm.client import QwenClient
from app.services.helpers.audit_helpers import fallback_audit_response, normalize_audit_result
from app.skills.physics_engine import PhysicsInferenceSkill


def ensure_physics_tensor(body: AuditPhysicsWithLlmRequest) -> Dict[str, Any]:
    physics_tensor = body.physics_tensor
    if physics_tensor:
        return physics_tensor
    physics_skill = PhysicsInferenceSkill.instance()
    consumed = physics_skill.consume(
        {"metadata": body.metadata, "solar_term": body.solar_term, "session_id": body.session_id}
    )
    return physics_skill.produce(consumed)


def build_audit_prompt_payload(
    body: AuditPhysicsWithLlmRequest,
    physics_tensor: Dict[str, Any],
) -> tuple[List[Dict[str, str]], Dict[str, Any]]:
    deity_scores = (physics_tensor or {}).get("deity_scores", {}) or {}
    audit_log = (physics_tensor or {}).get("audit_log", {}) or {}
    trace = (audit_log.get("trace", {}) if isinstance(audit_log, dict) else {}) or {}
    root_check = trace.get("root_check", {}) if isinstance(trace, dict) else {}
    seasonal_factors = {
        "solar_term": (physics_tensor or {}).get("meta", {}).get("solar_term", "derived_from_month_branch"),
        "params": (physics_tensor or {}).get("meta", {}).get("params", {}),
    }
    prompt = build_physics_audit_prompt(
        deity_scores=deity_scores,
        root_check=root_check if isinstance(root_check, dict) else {},
        seasonal_factors=seasonal_factors,
        consensus_history=body.consensus_history or [],
        lang=body.lang,
    )
    return prompt, {
        "deity_scores": deity_scores,
        "root_check": root_check,
        "seasonal_factors": seasonal_factors,
    }

async def audit_physics_with_llm_flow(body: AuditPhysicsWithLlmRequest) -> Dict[str, Any]:
    physics_tensor = ensure_physics_tensor(body)
    prompt, _context = build_audit_prompt_payload(body, physics_tensor)

    cfg = get_runtime_config().get("llm", {})
    client = QwenClient(
        base_url=cfg.get("base_url"),
        api_key=cfg.get("api_key"),
        model=cfg.get("model") or None,
    )
    raw = ""
    parsed: AuditLlmStructuredResponse | None = None
    structured_hit = False
    repair_mode = "fallback"
    llm_elapsed_ms = 0.0
    llm_approx_tokens = 0.0
    try:
        t0 = time.perf_counter()
        raw = await client.chat(prompt, temperature=0.2, max_tokens=700, stop=None)
        llm_elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        llm_approx_tokens = round(len(raw) / 1.8, 2)
        parsed = AuditLlmStructuredResponse.model_validate(json.loads(extract_first_json_object(raw)))
        structured_hit = True
        repair_mode = "strict_json"
    except Exception:
        try:
            retry_prompt = [
                {"role": "system", "content": "Only output strict JSON object. No prose."},
                {"role": "user", "content": f"基于上一轮分析，输出JSON：{raw[:1800]}"},
            ]
            t1 = time.perf_counter()
            retry_raw = await client.chat(retry_prompt, temperature=0.0, max_tokens=180, stop=None)
            llm_elapsed_ms = round((llm_elapsed_ms or 0.0) + (time.perf_counter() - t1) * 1000, 2)
            llm_approx_tokens = round((llm_approx_tokens or 0.0) + len(retry_raw) / 1.8, 2)
            raw = retry_raw
            parsed = AuditLlmStructuredResponse.model_validate(json.loads(extract_first_json_object(retry_raw)))
            structured_hit = True
            repair_mode = "retry_json"
        except Exception:
            parsed = None

    parsed_obj = parsed or fallback_audit_response()
    return normalize_audit_result(
        parsed_obj,
        raw,
        structured_hit,
        repair_mode,
        llm_elapsed_ms,
        llm_approx_tokens,
        prompt,
        physics_tensor,
    )
