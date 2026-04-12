"""Audit service layer for physics + LLM structured review."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

from app.api.contracts import AuditLlmStructuredResponse, AuditPhysicsWithLlmRequest
from app.api.router_helpers import (
    build_physics_audit_prompt,
    extract_first_json_object,
)
from app.core.runtime_config import get_runtime_config
from app.llm.client import QwenClient
from app.prompts.audit import AUDIT_JSON_REPAIR_SYSTEM
from app.utils.semantic_firewall import strip_float_literals
from app.plugins.blind_school.skill_prompt import format_blind_skill_registry_for_prompt
from app.services.helpers.audit_helpers import fallback_audit_response, normalize_audit_result
from app.services.helpers.tensor_adapters import collect_conflict_matrix_points_for_llm


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
    conflict_points = collect_conflict_matrix_points_for_llm(body.metadata, physics_tensor)
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
    duel_ctx = str(getattr(body, "will_conflict_duel_context", None) or "").strip()
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
        conflict_points=conflict_points,
        will_conflict_duel_context=duel_ctx,
    )
    label_lines: List[str] = []
    meta_pt = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    bud = meta_pt.get("semantic_label_bundle_v1") if isinstance(meta_pt.get("semantic_label_bundle_v1"), dict) else {}
    for line in (bud.get("verified_fact_lines") or [])[:28]:
        s = str(line or "").strip()
        if s:
            label_lines.append(s)
    if label_lines and len(prompt) > 1 and isinstance(prompt[1], dict):
        prefix = "[Verified Facts·语义标签工厂]\n" + "\n".join(label_lines) + "\n\n"
        prompt = [
            prompt[0],
            {**prompt[1], "content": prefix + str(prompt[1].get("content") or "")},
        ]
    prompt = [{"role": m["role"], "content": strip_float_literals(str(m.get("content") or ""))} for m in prompt]
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
    retry_raw = ""
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
    except Exception as exc_primary:
        logger.warning(
            "audit_physics_llm primary_json_parse_failed tier=%s err=%s detail=%s raw_prefix=%r",
            audit_prompt_tier,
            type(exc_primary).__name__,
            str(exc_primary)[:400],
            (raw or "")[:400],
        )
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
        except Exception as exc_retry:
            logger.warning(
                "audit_physics_llm retry_json_failed tier=%s err=%s detail=%s retry_raw_prefix=%r",
                audit_prompt_tier,
                type(exc_retry).__name__,
                str(exc_retry)[:400],
                str(retry_raw or "")[:400],
            )
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
        audit_prompt_tier,
    )
    result["audit_prompt_tier"] = audit_prompt_tier
    lm = result.get("llm_meta") if isinstance(result.get("llm_meta"), dict) else {}
    logger.info(
        "audit_physics_llm done tier=%s structured_hit=%s repair_mode=%s elapsed_ms=%.1f approx_tokens=%.1f",
        audit_prompt_tier,
        bool(result.get("structured_hit")),
        result.get("repair_mode"),
        float(lm.get("elapsed_ms") or 0.0),
        float(lm.get("approx_tokens") or 0.0),
    )
    return result
