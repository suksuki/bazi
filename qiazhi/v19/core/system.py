from __future__ import annotations

from typing import Any, Dict, List

from v19.core.features import extract_core_features
from v19.core.inference import infer_core_bazi
from v19.core.inference_schema import validate_inference_bundle
from v19.core.strength import evaluate_strength
from v19.core.structure import evaluate_structure
from v19.domains.wealth import evaluate_wealth_domain


V19_SYSTEM_VERSION = "v19.core_system.v2"


def evaluate_core(chart: Dict[str, Any]) -> Dict[str, Any]:
    features = extract_core_features(chart)
    strength = evaluate_strength(features)
    structure = evaluate_structure(features, strength)
    bazi_inference = infer_core_bazi(features, strength, structure)
    validation = validate_inference_bundle(bazi_inference)
    if not validation["valid"]:
        raise ValueError("V19_INFERENCE_SCHEMA_INVALID: " + "; ".join(validation["errors"]))
    return {
        "version": V19_SYSTEM_VERSION,
        "features": features,
        "strength": strength,
        "structure": structure,
        "inference": bazi_inference,
        "guardrails": [
            "CORE_BAZI_FIRST",
            "PURE_FUNCTION_OUTPUT",
            "NO_PREDICTION_ID",
            "NO_LEDGER",
            "NO_NARRATIVE",
            "NO_DOMAIN_CONCLUSION",
            "CONTRACT_READY",
        ],
    }


def evaluate(chart: Dict[str, Any], intent: str = "core_bazi") -> Dict[str, Any]:
    core = evaluate_core(chart)
    result = {
        "version": V19_SYSTEM_VERSION,
        "intent": intent,
        "features": core["features"],
        "strength": core["strength"],
        "structure": core["structure"],
        "bazi_inference_bundle": core["inference"],
        "guardrails": [
            "CORE_BAZI_FIRST",
            "PURE_FUNCTION_OUTPUT",
            "NO_PREDICTION_ID",
            "NO_LEDGER",
            "NO_NARRATIVE",
            "NO_DOMAIN_CONCLUSION_BY_DEFAULT",
            "DOMAIN_AFTER_INFERENCE",
            "DOMAIN_AFTER_STRUCTURE",
            "CONTRACT_READY",
        ],
    }
    if intent in {"core_bazi", "core"}:
        return result
    if intent == "wealth":
        wealth = evaluate_wealth_domain(core["features"], core["strength"], core["structure"])
        result["wealth_profile"] = wealth["wealth_profile"]
        result["evidence"] = wealth["evidence"]
        result["domain_guardrails"] = wealth.get("guardrails", [])
        return result
    raise ValueError("V19 phase 1 supports intent='core_bazi' and optional adapter intent='wealth'")


def _float(value: Any) -> float:
    try:
        return round(float(value), 3)
    except (TypeError, ValueError):
        return 0.0


def _values_for_key(payload: Any, key: str) -> List[Any]:
    found: List[Any] = []
    if isinstance(payload, dict):
        for item_key, item_value in payload.items():
            if item_key == key:
                found.append(item_value)
            found.extend(_values_for_key(item_value, key))
    elif isinstance(payload, list):
        for item in payload:
            found.extend(_values_for_key(item, key))
    return found


def _relation_bucket(relation_type: Any) -> str:
    raw = str(relation_type or "")
    if raw in {"six_harmony", "hidden_harmony", "three_harmony", "three_meeting", "half_harmony", "arch_harmony", "combination"}:
        return "combination"
    if raw in {"clash", "harm"}:
        return raw
    if raw in {"break", "punishment"}:
        return "disruptive"
    return raw or "unknown"


def _relation_counts(payload: Dict[str, Any]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for relation_type in _values_for_key(payload, "relation_type"):
        bucket = _relation_bucket(relation_type)
        counts[bucket] = counts.get(bucket, 0) + 1
    return counts


def _normalized_ten_god_scores(strength: Dict[str, Any]) -> Dict[str, float]:
    rows = strength.get("ten_god_strengths") if isinstance(strength.get("ten_god_strengths"), dict) else {}
    key_map = {
        "officer_killing": "officer",
        "officer": "officer",
        "seal": "seal",
        "resource": "seal",
        "wealth": "wealth",
        "output": "output",
        "peer": "peer",
    }
    scores: Dict[str, float] = {}
    for raw_key, row in rows.items():
        key = key_map.get(str(raw_key), str(raw_key))
        if isinstance(row, dict):
            scores[key] = _float(row.get("score"))
    return scores


def _conflicts_from_scores(scores: Dict[str, float], relation_counts: Dict[str, int]) -> List[str]:
    conflicts: List[str] = []
    if scores.get("output", 0.0) >= 0.5 and scores.get("officer", 0.0) >= 0.5:
        conflicts.append("output_vs_officer")
    if scores.get("peer", 0.0) >= 0.5 and scores.get("wealth", 0.0) >= 0.5:
        conflicts.append("peer_vs_wealth")
    if scores.get("seal", 0.0) >= 0.5 and scores.get("output", 0.0) >= 0.5:
        conflicts.append("seal_vs_output")
    if relation_counts.get("clash", 0) > 0:
        conflicts.append("branch_clash")
    if relation_counts.get("harm", 0) > 0:
        conflicts.append("branch_harm")
    if relation_counts.get("combination", 0) > 0 and relation_counts.get("clash", 0) > 0:
        conflicts.append("clash_vs_combination")
    return sorted(set(conflicts))


def _v19_core_summary(result: Dict[str, Any]) -> Dict[str, Any]:
    strength = result.get("strength") if isinstance(result.get("strength"), dict) else {}
    structure = result.get("structure") if isinstance(result.get("structure"), dict) else {}
    inference = result.get("inference") if isinstance(result.get("inference"), dict) else {}
    day_master = inference.get("day_master_state") if isinstance(inference.get("day_master_state"), dict) else {}
    ten_god = inference.get("ten_god_structure") if isinstance(inference.get("ten_god_structure"), dict) else {}
    stability = inference.get("structural_stability") if isinstance(inference.get("structural_stability"), dict) else {}
    strength_axis = strength.get("day_master_strength") if isinstance(strength.get("day_master_strength"), dict) else {}
    relation_counts = stability.get("relation_counts") if isinstance(stability.get("relation_counts"), dict) else _relation_counts(structure)
    return {
        "available": True,
        "day_master_state": str(day_master.get("tendency") or ""),
        "strength_tendency": str(strength_axis.get("tendency") or day_master.get("model_tendency") or ""),
        "support_score": _float(strength_axis.get("support_score")),
        "pressure_score": _float(strength_axis.get("pressure_score")),
        "active_ten_gods": sorted(str(key) for key, row in ten_god.items() if isinstance(row, dict) and row.get("activity") in {"active", "high"}),
        "dominant_ten_gods": sorted(str(key) for key, row in ten_god.items() if isinstance(row, dict) and row.get("presence") == "dominant"),
        "relation_counts": dict(relation_counts),
        "vault_states": sorted(str(item) for item in _values_for_key(structure, "vault_state") if item),
        "conflicts": sorted(
            str(item.get("type") or "")
            for item in inference.get("internal_conflicts", [])
            if isinstance(item, dict)
        ),
        "uncertainty_types": sorted(
            str(item.get("type") or "")
            for item in inference.get("uncertainty_sources", [])
            if isinstance(item, dict)
        ),
    }


def _v19_wealth_summary(result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "wealth_type": str((result.get("wealth_profile") or {}).get("wealth_type") or ""),
        "evidence_types": sorted({str(row.get("evidence_type") or "") for row in result.get("evidence", [])}),
        "evidence_count": len(result.get("evidence", [])),
    }


def _v18_core_summary(chart: Dict[str, Any]) -> Dict[str, Any]:
    try:
        from v17_rebirth.backend.services.core_bazi_feature_layer import extract_core_bazi_features
        from v17_rebirth.backend.services.core_bazi_strength_model import evaluate_core_strength
        from v17_rebirth.backend.services.core_bazi_structure_effect_layer import evaluate_core_structure_effect

        core = extract_core_bazi_features({"chart_snapshot": dict(chart.get("chart_snapshot") or chart)})
        strength = evaluate_core_strength({"core_feature_bundle": core})
        structure = evaluate_core_structure_effect({"core_feature_bundle": core, "core_strength_bundle": strength})
        strength_axis = strength.get("day_master_strength") if isinstance(strength.get("day_master_strength"), dict) else {}
        relation_counts = _relation_counts(structure)
        ten_god_scores = _normalized_ten_god_scores(strength)
        return {
            "available": True,
            "day_master_state": str(strength_axis.get("tendency") or ""),
            "strength_tendency": str(strength_axis.get("tendency") or ""),
            "support_score": _float(strength_axis.get("support_score")),
            "pressure_score": _float(strength_axis.get("pressure_score")),
            "ten_god_scores": ten_god_scores,
            "relation_counts": relation_counts,
            "vault_states": sorted(str(item) for item in _values_for_key(structure, "vault_state") if item),
            "conflicts": _conflicts_from_scores(ten_god_scores, relation_counts),
        }
    except Exception as exc:
        return {"available": False, "error": str(exc)}


def _core_difference_notes(v18: Dict[str, Any], v19: Dict[str, Any]) -> List[str]:
    if not v18.get("available"):
        return ["v18 comparison unavailable"]
    notes: List[str] = []
    if v18.get("strength_tendency") != v19.get("strength_tendency"):
        notes.append("day master strength tendency differs")
    if abs(_float(v18.get("support_score")) - _float(v19.get("support_score"))) > 0.18:
        notes.append("support_score delta exceeds tolerance")
    if abs(_float(v18.get("pressure_score")) - _float(v19.get("pressure_score"))) > 0.18:
        notes.append("pressure_score delta exceeds tolerance")
    if v18.get("relation_counts") != v19.get("relation_counts"):
        notes.append("relation structure counts differ")
    missing_conflicts = sorted(set(v18.get("conflicts", [])) - set(v19.get("conflicts", [])))
    added_conflicts = sorted(set(v19.get("conflicts", [])) - set(v18.get("conflicts", [])))
    if missing_conflicts:
        notes.append("v19 missing v18 conflict signals: " + ",".join(missing_conflicts))
    if added_conflicts:
        notes.append("v19 added conflict signals: " + ",".join(added_conflicts))
    return notes or ["v18 and v19 core summaries are aligned at comparison granularity"]


def compare_v18_vs_v19(chart: Dict[str, Any]) -> Dict[str, Any]:
    v19_result = evaluate_core(chart)
    v19 = _v19_core_summary(v19_result)
    v18 = _v18_core_summary(chart)
    return {
        "chart_id": str((v19_result.get("features") or {}).get("chart_id") or ""),
        "v18": v18,
        "v19": v19,
        "comparison": {
            "strength_tendency_match": bool(v18.get("available") and v18.get("strength_tendency") == v19.get("strength_tendency")),
            "support_score_delta": round(abs(_float(v18.get("support_score")) - _float(v19.get("support_score"))), 3)
            if v18.get("available")
            else None,
            "pressure_score_delta": round(abs(_float(v18.get("pressure_score")) - _float(v19.get("pressure_score"))), 3)
            if v18.get("available")
            else None,
            "relation_counts_match": bool(v18.get("available") and v18.get("relation_counts") == v19.get("relation_counts")),
            "conflict_overlap": sorted(set(v18.get("conflicts", [])) & set(v19.get("conflicts", []))) if v18.get("available") else [],
            "difference_notes": _core_difference_notes(v18, v19),
        },
    }
