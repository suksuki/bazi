"""Audit service layer for physics + LLM structured review."""
from __future__ import annotations

import json
from typing import Any, Dict, List

from app.api.contracts import AuditLlmStructuredResponse, AuditPhysicsWithLlmRequest
from app.api.router_helpers import (
    build_physics_audit_prompt,
    extract_first_json_object,
)
from app.core.runtime_config import get_runtime_config
from app.llm.client import QwenClient
from app.prompts.audit import AUDIT_JSON_REPAIR_SYSTEM
from app.plugins.blind_school.skill_prompt import format_blind_skill_registry_for_prompt
from app.services.helpers.audit_helpers import fallback_audit_response, normalize_audit_result


def _resolve_audit_prompt_tier(body: AuditPhysicsWithLlmRequest, cfg: Dict[str, Any]) -> str:
    raw = getattr(body, "audit_prompt_tier", None)
    if raw is not None:
        s = str(raw).strip().lower()
        if s in ("standard", "compact"):
            return s
    s = str((cfg or {}).get("audit_prompt_tier") or "compact").strip().lower()
    return s if s in ("standard", "compact") else "compact"


def ensure_physics_tensor(body: AuditPhysicsWithLlmRequest) -> Dict[str, Any]:
    physics_tensor = body.physics_tensor
    if physics_tensor:
        return physics_tensor
    from app.skills.physics_engine import PhysicsInferenceSkill

    physics_skill = PhysicsInferenceSkill.instance()
    consumed = physics_skill.consume(
        {"metadata": body.metadata, "solar_term": body.solar_term, "session_id": body.session_id}
    )
    return physics_skill.produce(consumed)


def build_audit_prompt_payload(
    body: AuditPhysicsWithLlmRequest,
    physics_tensor: Dict[str, Any],
) -> tuple[List[Dict[str, str]], Dict[str, Any], str]:
    cfg = get_runtime_config().get("llm", {}) or {}
    tier = _resolve_audit_prompt_tier(body, cfg)
    deity_scores = (physics_tensor or {}).get("deity_scores", {}) or {}
    audit_log = (physics_tensor or {}).get("audit_log", {}) or {}
    trace = (audit_log.get("trace", {}) if isinstance(audit_log, dict) else {}) or {}
    root_check = trace.get("root_check", {}) if isinstance(trace, dict) else {}
    seasonal_factors = {
        "solar_term": (physics_tensor or {}).get("meta", {}).get("solar_term", "derived_from_month_branch"),
        "params": (physics_tensor or {}).get("meta", {}).get("params", {}),
    }
    blind_skill_block = format_blind_skill_registry_for_prompt(physics_tensor, compact=(tier == "compact"))
    high_reasoning = bool((cfg or {}).get("is_high_reasoning_mode"))
    inf_trace: Dict[str, Any] | None = None
    try:
        md_dump = body.metadata.model_dump(mode="python") if hasattr(body.metadata, "model_dump") else {}
        raw_it = md_dump.get("inference_trace") if isinstance(md_dump, dict) else None
        inf_trace = raw_it if isinstance(raw_it, dict) else None
    except Exception:
        inf_trace = None
    prompt = build_physics_audit_prompt(
        deity_scores=deity_scores,
        root_check=root_check if isinstance(root_check, dict) else {},
        seasonal_factors=seasonal_factors,
        consensus_history=body.consensus_history or [],
        lang=body.lang,
        blind_skill_system_suffix=blind_skill_block,
        tier=tier,
        high_reasoning=high_reasoning,
        inference_trace=inf_trace,
    )
    return (
        prompt,
        {
            "deity_scores": deity_scores,
            "root_check": root_check,
            "seasonal_factors": seasonal_factors,
        },
        tier,
    )

async def audit_physics_with_llm_flow(body: AuditPhysicsWithLlmRequest) -> Dict[str, Any]:
    physics_tensor = ensure_physics_tensor(body)
    prompt, _context, audit_prompt_tier = build_audit_prompt_payload(body, physics_tensor)

    cfg = get_runtime_config().get("llm", {}) or {}
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
        raw, tel = await client.chat_with_telemetry(prompt, temperature=0.2, max_tokens=700, stop=None)
        llm_elapsed_ms = float(tel.get("elapsed_ms") or 0.0)
        llm_approx_tokens = float(tel.get("approx_tokens") or 0.0)
        parsed = AuditLlmStructuredResponse.model_validate(json.loads(extract_first_json_object(raw)))
        structured_hit = True
        repair_mode = "strict_json"
    except Exception:
        try:
            retry_prompt = [
                {"role": "system", "content": AUDIT_JSON_REPAIR_SYSTEM},
                {"role": "user", "content": f"基于上一轮分析，输出JSON：{raw[:1800]}"},
            ]
            retry_raw, tel2 = await client.chat_with_telemetry(retry_prompt, temperature=0.0, max_tokens=180, stop=None)
            llm_elapsed_ms = round((llm_elapsed_ms or 0.0) + float(tel2.get("elapsed_ms") or 0.0), 2)
            llm_approx_tokens = round((llm_approx_tokens or 0.0) + float(tel2.get("approx_tokens") or 0.0), 2)
            raw = retry_raw
            parsed = AuditLlmStructuredResponse.model_validate(json.loads(extract_first_json_object(retry_raw)))
            structured_hit = True
            repair_mode = "retry_json"
        except Exception:
            parsed = None

    parsed_obj = parsed or fallback_audit_response()
    result = normalize_audit_result(
        parsed_obj,
        raw,
        structured_hit,
        repair_mode,
        llm_elapsed_ms,
        llm_approx_tokens,
        prompt,
        physics_tensor,
    )
    result["audit_prompt_tier"] = audit_prompt_tier
    return result
