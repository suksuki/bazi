from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from v20.features.schema import FeatureLayer


FEATURE_STATE_MODEL_VERSION = "v20.feature_state_model.v1"


def build_feature_state_model(feature_layer: FeatureLayer, decision_report: dict[str, Any]) -> dict[str, Any]:
    decisions = tuple(row for row in decision_report.get("decisions", ()) if isinstance(row, dict))
    mainlines = tuple(row for row in decision_report.get("mainlines", ()) if isinstance(row, dict))
    portrait_axes = tuple(
        row
        for row in decision_report.get("portrait_projection", {}).get("axes", ())
        if isinstance(row, dict)
    )
    decision_model = decision_report.get("defeasible_decision_model", {})
    argument_nodes = tuple(
        row for row in decision_model.get("argument_nodes", ()) if isinstance(row, dict)
    ) if isinstance(decision_model, dict) else ()
    states = tuple(
        _feature_state(feature, decisions, mainlines, portrait_axes, argument_nodes)
        for feature in feature_layer.features
    )
    domain_counts = Counter(str(row["domain"]) for row in states)
    readiness_counts = Counter(str(row["state"]) for row in states)
    return {
        "version": FEATURE_STATE_MODEL_VERSION,
        "status": "ready" if states else "empty",
        "algorithm": "feature_state_fusion_phase1",
        "source": "BaziFeature+DecisionState+MainlineDecision+PortraitAxis",
        "feature_state_count": len(states),
        "domain_count": len(domain_counts),
        "domain_counts": dict(sorted(domain_counts.items())),
        "state_counts": dict(sorted(readiness_counts.items())),
        "states": states,
        "priority_features": tuple(row for row in states if row["priority"] >= 0.72)[:12],
        "evidence_gap_features": tuple(row for row in states if row["state"] in {"evidence_gap", "requires_review"})[:12],
        "runtime_mutation": False,
        "guardrails": (
            "FEATURE_STATE_IS_FUSED_RUNTIME_VIEW",
            "FEATURE_STATE_DOES_NOT_MUTATE_CORE_FACTS",
            "DECISION_AND_PORTRAIT_CONTEXT_CAN_RERANK_NOT_CREATE_FACTS",
            "NO_LLM_FEATURE_ARBITRATION",
        ),
    }


def _feature_state(
    feature: object,
    decisions: tuple[dict[str, Any], ...],
    mainlines: tuple[dict[str, Any], ...],
    portrait_axes: tuple[dict[str, Any], ...],
    argument_nodes: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    feature_id = str(getattr(feature, "feature_id", ""))
    domain = str(getattr(feature, "domain", ""))
    linked_decisions = tuple(row for row in decisions if feature_id in tuple(row.get("feature_ids", ())))
    linked_mainlines = tuple(row for row in mainlines if domain == str(row.get("domain", "")))
    linked_axes = tuple(row for row in portrait_axes if feature_id in tuple(row.get("feature_ids", ())))
    linked_arguments = tuple(row for row in argument_nodes if feature_id in tuple(row.get("feature_ids", ())))
    priority = _priority(feature, linked_decisions, linked_mainlines, linked_axes, linked_arguments)
    state = _state(feature, linked_decisions, linked_arguments)
    return {
        "feature_id": feature_id,
        "title": str(getattr(feature, "title", "")),
        "domain": domain,
        "state": state,
        "priority": priority,
        "confidence": float(getattr(feature, "confidence", 0.0) or 0.0),
        "readiness": str(getattr(feature, "readiness", "")),
        "source_layers": tuple(str(row) for row in getattr(feature, "source_layers", ()) if str(row)),
        "decision_keys": tuple(str(row.get("decision_key", "")) for row in linked_decisions[:8] if row.get("decision_key")),
        "decision_states": tuple(dict.fromkeys(str(row.get("status", "")) for row in linked_decisions if row.get("status"))),
        "argument_ids": tuple(str(row.get("argument_id", "")) for row in linked_arguments[:8] if row.get("argument_id")),
        "mainline_keys": tuple(str(row.get("mainline_key", "")) for row in linked_mainlines[:4] if row.get("mainline_key")),
        "portrait_axis_ids": tuple(str(row.get("axis_id", "")) for row in linked_axes[:4] if row.get("axis_id")),
        "question_hooks": tuple(str(row) for row in getattr(feature, "question_hooks", ()) if str(row)),
        "evidence_ref_count": len(tuple(getattr(feature, "evidence_refs", ()))),
        "boundary": str(getattr(feature, "boundary", "")),
        "runtime_mutation": False,
    }


def _priority(
    feature: object,
    decisions: tuple[dict[str, Any], ...],
    mainlines: tuple[dict[str, Any], ...],
    portrait_axes: tuple[dict[str, Any], ...],
    arguments: tuple[dict[str, Any], ...],
) -> float:
    confidence = float(getattr(feature, "confidence", 0.0) or 0.0)
    decision_score = max((float(row.get("score", 0.0) or 0.0) for row in decisions), default=0.0)
    mainline_score = max((float(row.get("score", 0.0) or 0.0) for row in mainlines), default=0.0)
    axis_score = max((float(row.get("peak_confidence", 0.0) or 0.0) for row in portrait_axes), default=0.0)
    argument_score = max((float(row.get("score", 0.0) or 0.0) for row in arguments), default=0.0)
    return round(min(0.99, confidence * 0.35 + decision_score * 0.28 + mainline_score * 0.18 + axis_score * 0.11 + argument_score * 0.08), 3)


def _state(
    feature: object,
    decisions: tuple[dict[str, Any], ...],
    arguments: tuple[dict[str, Any], ...],
) -> str:
    states = {str(row.get("status", "")) for row in decisions if row.get("status")}
    states |= {str(row.get("state", "")) for row in arguments if row.get("state")}
    if states & {"blocked", "countered"}:
        return "blocked_or_countered"
    if states & {"requires_review", "mixed"}:
        return "requires_review"
    if states & {"weak_candidate", "evidence_gap"}:
        return "evidence_gap"
    if states & {"confirmed", "candidate", "volatile"}:
        return "active"
    readiness = str(getattr(feature, "readiness", ""))
    if "review" in readiness:
        return "requires_review"
    return "available"


def feature_state_by_domain(feature_state_model: dict[str, Any]) -> dict[str, tuple[dict[str, Any], ...]]:
    rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for state in feature_state_model.get("states", ()):
        if isinstance(state, dict):
            rows[str(state.get("domain", ""))].append(state)
    return {domain: tuple(values) for domain, values in rows.items()}
