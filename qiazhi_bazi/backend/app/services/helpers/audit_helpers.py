"""Pure helpers for audit service normalization."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from app.api.contracts import AuditLlmStructuredResponse
from app.api.router_helpers import coerce_alignment_score, patch_audit_json_from_text, sql_filter

DEFAULT_SQL_PATCH = "UPDATE physics_interaction_params SET param_value=0.20 WHERE param_key='CF_FLOATING_DECAY';"

# 物理引擎 interaction_params 白名单：禁止 LLM 发明 param_key（如「印星系数」）
ALLOWED_LOGIC_PROPOSAL_PARAM_KEYS = frozenset(
    {
        "CF_FLOATING_DECAY",
        "THROUGH_STEM_BOOST",
        "CONFLICT_PENALTY_GAMMA",
        "A_PROTRUSION",
        "OFFICER_RESTRAINT_ALPHA",
        "POWER_DISTRIBUTION_GAMMA",
    }
)
DEFAULT_LOGIC_PROPOSAL_PARAM_KEY = "CF_FLOATING_DECAY"
_PARAM_KEY_FROM_SQL = re.compile(
    r"WHERE\s+param_key\s*=\s*['\"]([A-Za-z0-9_]+)['\"]",
    re.IGNORECASE,
)


def _param_key_from_sql(sql: str) -> Optional[str]:
    m = _PARAM_KEY_FROM_SQL.search(sql or "")
    if not m:
        return None
    k = m.group(1)
    return k if k in ALLOWED_LOGIC_PROPOSAL_PARAM_KEYS else None


def coerce_logic_proposal_param_key(logic_proposal: Dict[str, Any], sql_patch: str) -> None:
    """将 logic_proposal.param_key 限制在白名单；非法键则从合法 sql 提取，否则回退默认键。"""
    raw = str(logic_proposal.get("param_key") or "").strip()
    if raw in ALLOWED_LOGIC_PROPOSAL_PARAM_KEYS:
        return
    extracted = _param_key_from_sql(str(logic_proposal.get("sql_patch") or "")) or _param_key_from_sql(sql_patch or "")
    logic_proposal["param_key"] = extracted or DEFAULT_LOGIC_PROPOSAL_PARAM_KEY


def fallback_audit_response() -> AuditLlmStructuredResponse:
    return AuditLlmStructuredResponse(
        diagnosis="结构化审计回退：LLM 未返回可解析 JSON，已启用默认评分策略。",
        alignment_score=35.0,
        top_anomaly="未拿到结构化审计结论，请检查 LLM 返回格式。",
        causal_reasoning="建议检查根气与季节系数是否同步进入模型。",
        tuning_suggestions=[DEFAULT_SQL_PATCH],
        sql_patch=DEFAULT_SQL_PATCH,
        refresh_hint="POST /api/admin/refresh-physics",
        logic_proposal={
            "title": "[系统逻辑校准] 抑制比肩虚浮能量",
            "param_key": "CF_FLOATING_DECAY",
            "suggested_value": 0.20,
            "reason": "乙木无根且比肩偏高，需要增强虚浮衰减。",
            "expected_impact": "比肩分值下降并与根气现实对齐。",
            "sql_patch": DEFAULT_SQL_PATCH,
            "source_role": "LLM",
        },
    )


def normalize_audit_result(
    parsed_obj: AuditLlmStructuredResponse,
    raw: str,
    structured_hit: bool,
    repair_mode: str,
    llm_elapsed_ms: float,
    llm_approx_tokens: float,
    prompt: List[Dict[str, str]],
    physics_tensor: Dict[str, Any],
    audit_prompt_tier: str = "standard",
) -> Dict[str, Any]:
    needs_semantic_heal = (
        (not structured_hit)
        or float(getattr(parsed_obj, "alignment_score", 0.0) or 0.0) <= 0.0
        or not (parsed_obj.sql_patch or "").strip()
        or not (isinstance(parsed_obj.logic_proposal, dict) and parsed_obj.logic_proposal.get("sql_patch"))
    )
    if needs_semantic_heal:
        patched_obj, patched = patch_audit_json_from_text(raw, parsed_obj)
        parsed_obj = patched_obj
        if patched:
            structured_hit = True
            repair_mode = "semantic_patch"

    top_anomaly = parsed_obj.top_anomaly.strip()
    diagnosis = parsed_obj.diagnosis.strip()
    if not diagnosis:
        diagnosis = (top_anomaly or "审计链路未产出 diagnosis：已根据物理张量与共识差分做结构化回退，请人工复核。")[:800]
    alignment_score = coerce_alignment_score(parsed_obj.alignment_score, top_anomaly)
    causal_reasoning = parsed_obj.causal_reasoning.strip()
    tuning_suggestions = [str(item) for item in (parsed_obj.tuning_suggestions or []) if str(item).strip()]
    sql_patch = sql_filter(parsed_obj.sql_patch.strip())
    if not sql_patch and tuning_suggestions:
        sql_patch = sql_filter(str(tuning_suggestions[0]))
    if not sql_patch:
        sql_patch = DEFAULT_SQL_PATCH
    logic_proposal = parsed_obj.logic_proposal if isinstance(parsed_obj.logic_proposal, dict) else {}
    if not logic_proposal:
        logic_proposal = {
            "title": "[系统逻辑校准] 抑制比肩虚浮能量",
            "param_key": "CF_FLOATING_DECAY",
            "suggested_value": 0.20,
            "reason": "结构化回退场景，建议先收敛虚浮系数。",
            "expected_impact": "重算后比肩下降，结构稳定性提升。",
            "sql_patch": sql_patch,
            "source_role": "LLM",
        }
    logic_proposal["sql_patch"] = sql_filter(str(logic_proposal.get("sql_patch", ""))) or sql_patch
    logic_proposal["source_role"] = str(logic_proposal.get("source_role") or "LLM")
    coerce_logic_proposal_param_key(logic_proposal, sql_patch)
    refresh_hint = parsed_obj.refresh_hint.strip()
    return {
        "ok": True,
        "diagnosis": diagnosis,
        "alignment_score": alignment_score,
        "top_anomaly": top_anomaly,
        "causal_reasoning": causal_reasoning,
        "tuning_suggestions": tuning_suggestions,
        "sql_patch": sql_patch,
        "refresh_hint": refresh_hint,
        "structured_hit": structured_hit,
        "repair_mode": repair_mode,
        "logic_proposal": logic_proposal,
        "llm_meta": {
            "elapsed_ms": llm_elapsed_ms,
            "approx_tokens": llm_approx_tokens,
            "prompt_scenario": "physics_audit",
            "audit_prompt_tier": str(audit_prompt_tier or "standard"),
        },
        "llm_raw": raw,
        "prompt": prompt,
        "physics_tensor": physics_tensor,
    }
