from __future__ import annotations

import math
from typing import Any, Dict, List

from v17_rebirth.backend.logic.core_engine.work_evidence_protocol import WORK_EVIDENCE_KEY
from v17_rebirth.backend.services.pattern_confidence import derive_pattern_confidence
from v17_rebirth.backend.services.plugin_display import plugin_source_label
from v17_rebirth.backend.services.target_god_resolver import resolve_target_god


def infer_decision_hint(*, plugin_id: str, fact_text: str, meta: Dict[str, Any]) -> str:
    text = str(fact_text or "").strip()
    pid = str(plugin_id or "").strip()
    if not text:
        return ""
    explicit_map = (
        ("六冲", "六冲"),
        ("六破", "六破"),
        ("六合", "六合"),
        ("六害", "六害"),
        ("三刑", "三刑"),
        ("半合", "半合聚势"),
        ("墓库", "墓库门态"),
        ("天干五合", "天干羁绊"),
        ("地支场烈度", "地支场烈度"),
        ("格局", "格局对焦"),
        ("做功", "做功检视"),
        ("状态机", "状态机节律"),
    )
    for marker, label in explicit_map:
        if marker in text:
            return label
    suffix_map = {
        "liuchong": "六冲",
        "liupo": "六破",
        "liuhe": "六合",
        "sanxing": "三刑",
        "banhe": "半合聚势",
        "muku": "墓库门态",
        "stem_fusion_stuck": "天干羁绊",
        "full_bandwidth": "地支场烈度",
    }
    for suffix, label in suffix_map.items():
        if pid.endswith(suffix):
            return label
    if "impact_ratio" in meta:
        return text.split("：", 1)[0][:12]
    return ""


def _resolve_exclusivity_key(
    *,
    source: str,
    target_god: str,
    meta: Dict[str, Any] | None,
    source_event: str = "",
) -> str:
    source_name = str(source or "").strip()
    target_name = str(target_god or "").strip() or "any"
    if not isinstance(meta, dict):
        meta = {}
    explicit = str(meta.get("exclusivity_key") or "").strip()
    if explicit:
        return explicit
    explicit = str(meta.get("source_event") or meta.get("source_key") or "").strip()
    if explicit:
        return explicit
    event = str(source_event or "").strip()
    if event:
        return event
    if source_name:
        return f"{source_name}|{target_name}"
    return f"manual|{target_name}"


def decision_relative_impact(title: str, target_god: str) -> Dict[str, Any]:
    text = str(title or "").strip()
    impact: Dict[str, Any] = {"target_god": str(target_god or "").strip()}
    if not text:
        return impact

    if any(k in text for k in ["格局转换", "坍塌", "翻盘", "断裂"]):
        return {
            **impact,
            "impact_ratio": 0.20,
            "intensity_level": 4,
            "significance_level": "L3",
            "significance_weight": 1.0,
            "resistance_mod": {"path": "pattern_shift", "factor": 0.35},
        }
    if any(k in text for k in ["冲", "刑", "破", "害", "克", "制", "杀"]):
        return {
            **impact,
            "impact_ratio": 0.12,
            "intensity_level": 3,
            "significance_level": "L3",
            "significance_weight": 1.0,
            "resistance_mod": {"path": "auto_clash", "factor": 0.4},
        }
    if any(k in text for k in ["合", "化", "生", "助", "聚势", "护持"]):
        return {
            **impact,
            "impact_ratio": 0.06,
            "intensity_level": 2,
            "significance_level": "L2",
            "significance_weight": 1.0,
            "resistance_mod": {"path": "auto_sheng", "factor": 0.75},
        }
    if any(k in text for k in ["节律", "边界", "确认", "校准", "承诺", "节奏"]):
        return {
            **impact,
            "impact_ratio": 0.025,
            "intensity_level": 1,
            "significance_level": "L1",
            "significance_weight": 0.8,
        }
    return {
        **impact,
        "impact_ratio": 0.015,
        "intensity_level": 1,
        "significance_level": "L0",
        "significance_weight": 0.6,
    }


def _source_label(source: Any) -> str:
    raw = str(source or "").strip()
    if not raw:
        return "未知规则"
    return plugin_source_label(raw)


def _normalize_match_ratio(meta: Dict[str, Any], *, fallback: float = 1.0) -> float:
    raw = meta.get("match_ratio", meta.get("pattern_match_ratio", fallback))
    try:
        value = float(raw)
    except (TypeError, ValueError):
        value = float(fallback)
    if not math.isfinite(value):
        value = float(fallback)
    return max(0.0, min(1.0, value))


def _should_infer_physical_impact(*, source: str, plugin_id: str = "", meta: Dict[str, Any] | None = None) -> bool:
    source_name = str(source or plugin_id or "").strip()
    if isinstance(meta, dict) and bool(meta.get("observe_only")):
        return False
    if source_name.startswith("classical."):
        return False
    if source_name.startswith("l2."):
        return False
    if source_name in {"kong_wang", "shensha", "ten_god_pattern"}:
        return False
    return True


def _is_observational_plugin_fact(*, plugin_id: str, meta: Dict[str, Any] | None = None) -> bool:
    source_name = str(plugin_id or "").strip()
    if source_name.startswith("classical."):
        return True
    if isinstance(meta, dict) and bool(meta.get("observe_only")):
        return True
    if meta:
        claim_type = str(meta.get("claim_type") or "").strip()
        entity_scope = str(meta.get("entity_scope") or "").strip().lower()
        if claim_type == "pattern_candidate" and entity_scope == "pattern":
            return True
    if source_name == "ten_god_pattern":
        return True
    if source_name.startswith("classical.pattern."):
        return True
    if source_name.startswith("classical.ziping."):
        return True
    if source_name.startswith("classical.blind."):
        return True
    return False


def _is_observational_row(
    *,
    source: str,
    plugin_id: str | None = None,
    meta: Dict[str, Any] | None = None,
    physical_impact: Dict[str, Any] | None = None,
) -> bool:
    source_name = str(source or plugin_id or "").strip()
    if _is_observational_plugin_fact(plugin_id=source_name, meta=meta):
        return True
    if isinstance(meta, dict) and bool(meta.get("observe_only")):
        return True
    if not isinstance(meta, dict) and isinstance(physical_impact, dict) and physical_impact.get("observe_only") is True:
        return True
    if source_name.startswith("classical.") or source_name == "ten_god_pattern":
        return True
    return False


def _clear_observational_physics(row: Dict[str, Any]) -> None:
    row["physical_impact"] = {}
    row["physical_impact_inferred"] = False


def _promote_display_meta(row: Dict[str, Any], meta: Dict[str, Any] | None = None) -> None:
    info = meta if isinstance(meta, dict) else {}
    for field in (
        "pattern_name",
        "pattern_candidate",
        "pattern_profile",
        "pattern_mix_mode",
        "pattern_scope",
        "pattern_scope_label",
        "pattern_dynamic_candidates",
        "pattern_confidence",
        "pattern_confidence_percent",
        "pattern_confidence_label",
        "pattern_confidence_breakdown",
        "match_ratio",
        "manifestation_state",
        "origin_type",
        "origin_multiplier",
        "projection_share",
        "cluster_projection",
    ):
        if field in info and row.get(field) is None:
            row[field] = info.get(field)


_PHYSICAL_IMPACT_KEYS = {
    "target_god",
    "impact_ratio",
    "intensity_level",
    "significance_level",
    "significance_weight",
    "resistance_mod",
    "projection_share",
    "cluster_projection",
    "detailed_projection",
    "raw_impact_ratio",
    "match_ratio",
    WORK_EVIDENCE_KEY,
    "relation_family",
    "origin_type",
    "interaction_layer",
    "condition_state",
    "condition_multiplier",
    "origin_multiplier",
    "clash_pair",
}


def _pick_physical_impact_from_meta(meta: Dict[str, Any] | None = None) -> Dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    return {key: value for key, value in meta.items() if key in _PHYSICAL_IMPACT_KEYS}


def _arbitration_mode_label(mode: str) -> str:
    if mode == "manual":
        return "手动"
    if mode == "system":
        return "自动"
    return "LLM"


def _annotate_arbitration_trace(row: Dict[str, Any], mode: str) -> Dict[str, Any]:
    cloned = dict(row)
    impact = cloned.get("physical_impact") if isinstance(cloned.get("physical_impact"), dict) else {}
    level = 0 if bool(cloned.get("physical_impact_inferred")) else int(impact.get("intensity_level") or 0)
    cloned["source_label"] = str(cloned.get("source_label") or _source_label(cloned.get("source") or cloned.get("plugin_id")))
    cloned["arbitration_mode"] = mode
    cloned["arbitration_trace"] = f"{cloned['source_label']} -> L{level if level > 0 else '?'} -> {_arbitration_mode_label(mode)}"
    return cloned


def _llm_resolution_policy(row: Dict[str, Any]) -> str:
    impact = row.get("physical_impact") if isinstance(row.get("physical_impact"), dict) else {}
    label = str(row.get("label") or row.get("title") or "").strip()
    title = str(row.get("title") or "").strip()
    text = f"{label} {title}"
    level = int(impact.get("intensity_level") or 0)
    try:
        ratio = abs(float(impact.get("impact_ratio", 0.0) or 0.0))
    except (TypeError, ValueError):
        ratio = 0.0
    target_god = str(row.get("target_god") or impact.get("target_god") or "").strip()
    hard_risk_markers = ("格局", "坍塌", "转换", "翻盘", "断裂")
    if any(marker in text for marker in hard_risk_markers):
        return "context_only"
    if target_god and ratio <= 1e-6:
        return "context_only"
    if target_god and 0 < level <= 2:
        return "auto_apply"
    if target_god:
        return "suggest_only"
    return "context_only"


def _llm_resolution_result(policy: str) -> str:
    if policy == "auto_apply":
        return "collapse_system"
    if policy == "suggest_only":
        return "promote_manual"
    return "consume_context"


def _llm_resolution_state(policy: str) -> str:
    if policy == "auto_apply":
        return "collapsed_to_system"
    if policy == "suggest_only":
        return "promoted_to_manual"
    return "pending_context"


def _collapse_llm_auto_apply(row: Dict[str, Any]) -> Dict[str, Any]:
    cloned = dict(row)
    cloned["arbitration_mode"] = "system"
    cloned["resolved_from_llm"] = True
    cloned["llm_resolution_state"] = _llm_resolution_state("auto_apply")
    cloned["llm_terminal_state"] = "collapse_system"
    cloned["arbitration_trace"] = f"{cloned.get('source_label') or _source_label(cloned.get('source') or cloned.get('plugin_id'))} -> L{int((cloned.get('physical_impact') or {}).get('intensity_level') or 0) or '?'} -> LLM裁决 -> 自动"
    return cloned


def _promote_llm_suggest(row: Dict[str, Any]) -> Dict[str, Any]:
    cloned = dict(row)
    cloned["arbitration_mode"] = "manual"
    cloned["resolved_from_llm"] = True
    cloned["llm_resolution_state"] = _llm_resolution_state("suggest_only")
    cloned["llm_terminal_state"] = "promote_manual"
    cloned["arbitration_trace"] = f"{cloned.get('source_label') or _source_label(cloned.get('source') or cloned.get('plugin_id'))} -> L{int((cloned.get('physical_impact') or {}).get('intensity_level') or 0) or '?'} -> LLM裁决 -> 手动"
    return cloned


def _ensure_exclusivity_key(row: Dict[str, Any]) -> None:
    if row.get("exclusivity_key"):
        return
    source = str(row.get("source") or row.get("plugin_id") or "")
    target = str(row.get("target_god") or (row.get("physical_impact") or {}).get("target_god") or "")
    source_event = str(row.get("source_event") or row.get("source_key") or "")
    impact = row.get("physical_impact") if isinstance(row.get("physical_impact"), dict) else None
    row["exclusivity_key"] = _resolve_exclusivity_key(
        source=source,
        target_god=target,
        meta=impact if isinstance(impact, dict) else None,
        source_event=source_event,
    )


def _is_manual_candidate(row: Dict[str, Any]) -> bool:
    arbiter_val = str(row.get("arbiter_type") or "").strip().lower()
    impact = row.get("physical_impact") if isinstance(row.get("physical_impact"), dict) else {}
    target_god = str(row.get("target_god") or impact.get("target_god") or "").strip()
    label = str(row.get("label") or row.get("hint") or "").strip()
    title = str(row.get("title") or "").strip()
    text = f"{label} {title}"
    has_ratio = "impact_ratio" in impact
    try:
        impact_ratio = abs(float(impact.get("impact_ratio", 0.0) or 0.0))
    except (TypeError, ValueError):
        impact_ratio = 0.0
    executable = bool(target_god and has_ratio and impact_ratio > 1e-6)

    if arbiter_val == "user":
        return executable

    blockers = ("状态机", "快照", "显影", "诊断", "报告", "映射", "墓库", "观察")
    if not executable:
        return False
    return not any(k in text for k in blockers)


def _is_auto_candidate(row: Dict[str, Any]) -> bool:
    arbiter_val = str(row.get("arbiter_type") or "").strip().lower()
    if arbiter_val == "system":
        return True

    impact = row.get("physical_impact") if isinstance(row.get("physical_impact"), dict) else {}
    target_god = str(row.get("target_god") or impact.get("target_god") or "").strip()
    if not target_god:
        return False

    significance = str(impact.get("significance_level") or "").strip().upper()
    source = str(row.get("source") or row.get("plugin_id") or "").strip()
    return significance == "L3" and source.startswith("l2.")


def ensure_display_confidence(meta: Dict[str, Any] | None, *, plugin_id: str, priority: float, salience_weight: float) -> Dict[str, Any] | None:
    if not isinstance(meta, dict):
        meta = {}
    return derive_pattern_confidence(
        plugin_id=str(plugin_id or ""),
        meta=meta,
        priority=priority,
        salience_weight=salience_weight,
    )
