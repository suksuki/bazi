"""Pure helpers for audit service normalization."""
from __future__ import annotations

import re
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.api.contracts import AuditLlmStructuredResponse
from app.api.router_helpers import coerce_alignment_score, patch_audit_json_from_text, sql_filter
from app.skills.physics_rules import DEFAULT_INTERACTION_PARAMS

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
_DIAGNOSIS_ALIAS_MAP = {
    "CF_FLOATING_DECAY": "[虚浮衰减系数]",
    "THROUGH_STEM_BOOST": "[透干增益系数]",
    "CONFLICT_PENALTY_GAMMA": "[冲突惩罚强度]",
    "A_PROTRUSION": "[透出系数]",
    "OFFICER_RESTRAINT_ALPHA": "[官杀约束强度]",
    "POWER_DISTRIBUTION_GAMMA": "[功率分配指数]",
}


def _param_key_from_sql(sql: str) -> Optional[str]:
    m = _PARAM_KEY_FROM_SQL.search(sql or "")
    if not m:
        return None
    k = m.group(1)
    return k if k in ALLOWED_LOGIC_PROPOSAL_PARAM_KEYS else None


def _alias_diagnosis_param_keys(text: str) -> str:
    out = str(text or "")
    for key, alias in _DIAGNOSIS_ALIAS_MAP.items():
        out = out.replace(key, alias)
    return out


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
    diagnosis = _alias_diagnosis_param_keys(diagnosis)
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


_SQL_PATCH_KV_RE = re.compile(
    r"^UPDATE\s+physics_interaction_params\s+SET\s+param_value\s*=\s*([0-9]*\.?[0-9]+)\s+WHERE\s+param_key\s*=\s*'([A-Za-z0-9_]+)'\s*;?$",
    re.IGNORECASE,
)


def parse_interaction_sql_patch_kv(sql_patch: str) -> Optional[Tuple[str, float]]:
    """解析单条 ``physics_interaction_params`` UPDATE，供 Inbox PATCH 与二次刷新使用（与 ``sql_filter`` 白名单一致）。"""
    s = sql_filter(str(sql_patch or "").strip())
    if not s:
        return None
    m = _SQL_PATCH_KV_RE.match(s.strip())
    if not m:
        return None
    return str(m.group(2)), float(m.group(1))


def _canonical_interaction_param_key(raw: str) -> str:
    """将审计侧大写键对齐到 ``DEFAULT_INTERACTION_PARAMS`` 中的规范键名。"""
    s = str(raw or "").strip()
    if not s:
        return ""
    for k in DEFAULT_INTERACTION_PARAMS.keys():
        if k.upper() == s.upper():
            return k
    upper_alias = {
        "CONFLICT_PENALTY_GAMMA": "conflict_penalty_gamma",
        "THROUGH_STEM_BOOST": "through_stem_boost",
    }
    if s in upper_alias:
        return upper_alias[s]
    return s


def secondary_refresh_physics_tensor_before_final_verdict_v14_01(
    metadata: Dict[str, Any],
    physics_tensor: Dict[str, Any],
) -> Dict[str, Any]:
    """
    V14.01：若 Decision Inbox 写入 ``pending_sql_patches``，在终判前静默合并参数并重跑 ``evaluate_interactions``，
    使 LLM 所见 ``physics_tensor`` 与用户意志一致（不经 LLM 审计调用）。
    """
    reg = metadata.get("decision_impact_registry_v14_01") if isinstance(metadata.get("decision_impact_registry_v14_01"), dict) else {}
    pending = [str(x).strip() for x in (reg.get("pending_sql_patches") or []) if str(x).strip()]
    if not pending:
        return {"applied": False, "reason": "no_pending_sql_patch"}

    from app.services.helpers.interaction_pipeline import evaluate_interactions
    from app.skills.physics_engine import PhysicsInferenceSkill

    skill = PhysicsInferenceSkill.instance()
    base_params = dict(skill.get_interaction_params())
    meta_pt = physics_tensor.setdefault("meta", {})
    if not isinstance(meta_pt, dict):
        meta_pt = {}
        physics_tensor["meta"] = meta_pt
    overlay: Dict[str, float] = {}
    if isinstance(meta_pt.get("physics_interaction_params"), dict):
        for k, v in meta_pt["physics_interaction_params"].items():
            try:
                overlay[str(k)] = float(v)
            except (TypeError, ValueError):
                continue

    applied_keys: List[str] = []
    for raw_sql in pending:
        parsed = parse_interaction_sql_patch_kv(raw_sql)
        if not parsed:
            continue
        key_raw, val = parsed
        ckey = _canonical_interaction_param_key(key_raw)
        if not ckey:
            continue
        base_params[ckey] = val
        overlay[ckey] = val
        applied_keys.append(ckey)

    if not applied_keys:
        return {"applied": False, "reason": "no_parseable_sql_patch"}

    meta_pt["physics_interaction_params"] = overlay
    phys_cfg: Dict[str, Any] = {}
    rpc = metadata.get("runtime_physics_config") if isinstance(metadata.get("runtime_physics_config"), dict) else {}
    if isinstance(rpc, dict):
        phys_cfg = dict(rpc)

    evaluate_interactions(
        physics_tensor=physics_tensor,
        metadata=metadata,
        interaction_params=base_params,
        physics_config=phys_cfg,
    )

    reg2 = metadata.setdefault("decision_impact_registry_v14_01", {})
    if isinstance(reg2, dict):
        reg2["pending_sql_patches"] = []
        log = list(reg2.get("secondary_refresh_log_v14_01") or [])
        log.append(
            {
                "at": datetime.utcnow().isoformat() + "Z",
                "applied_param_keys": applied_keys[:32],
                "protocol": "secondary_refresh.v14_01",
            }
        )
        reg2["secondary_refresh_log_v14_01"] = log[-24:]

    meta_pt["v14_01_secondary_refresh_at"] = datetime.utcnow().isoformat() + "Z"
    return {"applied": True, "applied_param_keys": applied_keys}
