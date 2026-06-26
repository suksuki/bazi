from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from v30.learning.auto_apply import _candidate_payload
from v30.policy import make_baseline_candidate
from v30.policy.runtime_pointer import PolicyFamily
from v30.validation.frozen_core_calibration_review import (
    DEFAULT_FROZEN_CORE_CALIBRATION_TIERS,
    build_frozen_core_calibration_review,
)
from v30.validation.synthetic_case import SyntheticValidationResult, SyntheticValidationSuiteResult, run_synthetic_tier
from v30.validation.training_signals import SyntheticTrainingSignal, extract_training_signals


TARGETED_CALIBRATION_CANDIDATE_REVIEW_VERSION = "v30.targeted_calibration_candidate_review.v1"

DEFAULT_TARGETED_CALIBRATION_FAMILIES: tuple[PolicyFamily, ...] = (
    "structure_policy",
    "rule_policy",
    "question_policy",
    "answer_policy",
)

FORBIDDEN_PAYLOAD_KEYS = {
    "chart_facts",
    "chart_fact",
    "pillars",
    "four_pillars",
    "luck_cycle",
    "luck_cycle_facts",
    "flow_year",
    "flow_month",
    "deterministic_chart_facts",
    "base_fact_explanations",
}


def run_targeted_calibration_candidate_review(
    *,
    families: Sequence[PolicyFamily] = DEFAULT_TARGETED_CALIBRATION_FAMILIES,
    tiers: Sequence[str] = DEFAULT_FROZEN_CORE_CALIBRATION_TIERS,
    review_id: str | None = None,
) -> dict[str, Any]:
    suite_results = {tier: run_synthetic_tier(tier) for tier in tiers}
    combined = _combined_suite_result(suite_results.values())
    signals = extract_training_signals(combined)
    f1_review = build_frozen_core_calibration_review(
        suite_results=suite_results,
        training_signals=signals,
    )
    return build_targeted_calibration_candidate_review(
        frozen_core_calibration_review=f1_review,
        training_signals=signals,
        families=families,
        review_id=review_id,
    )


def build_targeted_calibration_candidate_review(
    *,
    frozen_core_calibration_review: Mapping[str, Any],
    training_signals: Sequence[SyntheticTrainingSignal | Mapping[str, Any]],
    families: Sequence[PolicyFamily] = DEFAULT_TARGETED_CALIBRATION_FAMILIES,
    review_id: str | None = None,
) -> dict[str, Any]:
    reviewed_at = datetime.now(timezone.utc)
    review_id = review_id or f"v30.targeted_calibration.{reviewed_at.strftime('%Y%m%d%H%M%S')}"
    signals = [
        signal if isinstance(signal, SyntheticTrainingSignal) else SyntheticTrainingSignal.model_validate(signal)
        for signal in training_signals
    ]
    candidates = [
        _candidate_summary(family, review_id, signals)
        for family in families
    ]
    decision = _decision(
        f1_review=frozen_core_calibration_review,
        candidates=candidates,
    )
    return {
        "version": TARGETED_CALIBRATION_CANDIDATE_REVIEW_VERSION,
        "review_id": review_id,
        "reviewed_at": reviewed_at.isoformat(),
        "status": "completed",
        "decision": decision,
        "f1_summary": _f1_summary(frozen_core_calibration_review),
        "candidate_summary": {
            "candidate_count": len(candidates),
            "families": [candidate["family"] for candidate in candidates],
            "allowed_candidate_tracks": [
                "model_signal_weights",
                "rule_weights",
                "question_strategy",
                "expression_policy",
            ],
            "forbidden_payload_key_hits": {
                candidate["family"]: candidate["forbidden_payload_key_hits"]
                for candidate in candidates
                if candidate["forbidden_payload_key_hits"]
            },
        },
        "candidates": candidates,
        "policy_boundary": {
            "policy_pointer_promotion_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "requires_synthetic_all_before_pointer_review": True,
            "requires_518k_sample_before_pointer_review": True,
            "boundary": "f2_candidate_review_is_read_only_and_does_not_promote_policy",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "targeted_calibration_candidate_review_reviews_candidates_without_mutating_chart_facts_or_policy_pointers",
    }


def _combined_suite_result(results: Sequence[SyntheticValidationSuiteResult]) -> SyntheticValidationSuiteResult:
    rows: list[SyntheticValidationResult] = []
    for result in results:
        rows.extend(result.results)
    passed_count = sum(1 for row in rows if row.passed)
    failed_count = len(rows) - passed_count
    return SyntheticValidationSuiteResult(
        suite_id="v30.synthetic.targeted_calibration_candidate_combined",
        passed=failed_count == 0,
        case_count=len(rows),
        passed_count=passed_count,
        failed_count=failed_count,
        results=rows,
    )


def _candidate_summary(
    family: PolicyFamily,
    review_id: str,
    signals: Sequence[SyntheticTrainingSignal],
) -> dict[str, Any]:
    if family == "answer_policy":
        payload = _answer_policy_payload(review_id, signals)
    else:
        payload = _candidate_payload(family, review_id, list(signals))
        payload["mode"] = "targeted_calibration_candidate_review"
        payload["auto_apply"] = False
    candidate = make_baseline_candidate(
        candidate_id=f"{review_id}.{family}",
        family=family,
        payload=payload,
        change_summary="targeted calibration candidate review only",
    )
    payload_dump = candidate.payload
    return {
        "candidate_id": candidate.candidate_id,
        "family": candidate.family,
        "artifact_id": f"{candidate.family}.{candidate.candidate_id}",
        "change_summary": candidate.change_summary,
        "allowed_track": _allowed_track(family),
        "source_signal_ids": _source_signal_ids(payload_dump),
        "weight_summary": _weight_summary(family, payload_dump.get("weights", {})),
        "policy_payload": payload_dump,
        "forbidden_payload_key_hits": sorted(_forbidden_key_hits(payload_dump)),
        "promotion_allowed": False,
        "chart_fact_mutation_allowed": False,
        "boundary": "candidate_summary_is_review_only_not_pointer_promotion",
    }


def _answer_policy_payload(review_id: str, signals: Sequence[SyntheticTrainingSignal]) -> dict[str, Any]:
    expression_strength = _signal_strength(signals, "v30.training_signal.expression_quality")
    llm_strength = _signal_strength(signals, "v30.training_signal.llm_output_contract_quality")
    practical_strength = _signal_strength(signals, "v30.training_signal.practical_reading_quality")
    return {
        "mode": "targeted_calibration_candidate_review",
        "family": "answer_policy",
        "training_run_id": review_id,
        "source": "frozen_core_calibration_review",
        "auto_apply": False,
        "training_signals": [signal.model_dump(mode="json") for signal in signals],
        "weights": {
            "expression_policy": {
                "version": "v30.expression_policy_candidate.v1",
                "bazi_term_density_weight": round(1.0 + min(0.04, expression_strength * 0.025), 3),
                "boundary_language_weight": round(1.0 + min(0.035, practical_strength * 0.02), 3),
                "fallback_observation_weight": round(1.0 + min(0.025, llm_strength * 0.015), 3),
                "raw_score_leak_penalty": 0.0,
                "fact_generation_allowed": False,
                "boundary": "expression_policy_tunes_wording_not_chart_facts",
            }
        },
    }


def _signal_strength(signals: Sequence[SyntheticTrainingSignal], signal_id: str) -> float:
    for signal in signals:
        if signal.signal_id == signal_id:
            return float(signal.strength)
    return 0.0


def _allowed_track(family: PolicyFamily) -> str:
    if family == "structure_policy":
        return "model_signal_weights"
    if family == "rule_policy":
        return "rule_weights"
    if family == "question_policy":
        return "question_strategy"
    if family == "answer_policy":
        return "expression_policy"
    return "unsupported"


def _source_signal_ids(payload: Mapping[str, Any]) -> list[str]:
    rows = payload.get("training_signals", [])
    if not isinstance(rows, list):
        return []
    return sorted({
        str(row.get("signal_id"))
        for row in rows
        if isinstance(row, dict) and row.get("signal_id")
    })


def _weight_summary(family: PolicyFamily, weights: Any) -> dict[str, Any]:
    if not isinstance(weights, dict):
        return {"weight_count": 0, "changed_weight_count": 0}
    if family == "structure_policy":
        return _flat_weight_summary(weights, prefixes=("model_signal.", "ranked_decision.", "dynamic_graph."))
    if family == "rule_policy":
        rule_weights = weights.get("rule_weights", {})
        domain_weights = weights.get("domain_weights", {})
        return {
            "rule_weight_count": len(rule_weights) if isinstance(rule_weights, dict) else 0,
            "domain_weight_count": len(domain_weights) if isinstance(domain_weights, dict) else 0,
            "changed_weight_count": _changed_float_count(rule_weights) + _changed_float_count(domain_weights),
            "has_per_unit_policy": isinstance(weights.get("per_unit_parameter_policy"), dict),
        }
    if family == "question_policy":
        topic = weights.get("topic_weights", {})
        intent = weights.get("intent_weights", {})
        stage = weights.get("stage_weights", {})
        return {
            "topic_weight_count": len(topic) if isinstance(topic, dict) else 0,
            "intent_weight_count": len(intent) if isinstance(intent, dict) else 0,
            "stage_weight_count": len(stage) if isinstance(stage, dict) else 0,
            "changed_weight_count": (
                _changed_float_count(topic)
                + _changed_float_count(intent)
                + _changed_float_count(stage)
            ),
            "has_adaptive_question_policy": isinstance(weights.get("adaptive_question_policy"), dict),
            "has_interaction_followup_policy": isinstance(weights.get("interaction_followup_policy"), dict),
            "has_model_signal_question_policy": isinstance(weights.get("model_signal_question_policy"), dict),
        }
    if family == "answer_policy":
        expression = weights.get("expression_policy", {})
        return {
            "expression_weight_count": len(expression) if isinstance(expression, dict) else 0,
            "changed_weight_count": _changed_float_count(expression),
            "fact_generation_allowed": bool(expression.get("fact_generation_allowed")) if isinstance(expression, dict) else False,
        }
    return {"weight_count": len(weights), "changed_weight_count": _changed_float_count(weights)}


def _flat_weight_summary(weights: Mapping[str, Any], *, prefixes: Sequence[str]) -> dict[str, Any]:
    changed = {
        str(key): float(value)
        for key, value in weights.items()
        if any(str(key).startswith(prefix) for prefix in prefixes)
        and _is_changed_float(value)
    }
    return {
        "weight_count": len(weights),
        "changed_weight_count": len(changed),
        "changed_weight_keys": sorted(changed),
    }


def _changed_float_count(value: Any) -> int:
    if not isinstance(value, dict):
        return 0
    return sum(1 for raw in value.values() if _is_changed_float(raw))


def _is_changed_float(value: Any) -> bool:
    try:
        return float(value) != 1.0 and float(value) != 0.0
    except (TypeError, ValueError):
        return False


def _forbidden_key_hits(payload: Any) -> set[str]:
    hits: set[str] = set()
    if isinstance(payload, dict):
        for key, value in payload.items():
            key_text = str(key)
            if key_text in FORBIDDEN_PAYLOAD_KEYS:
                hits.add(key_text)
            hits.update(_forbidden_key_hits(value))
    elif isinstance(payload, list):
        for row in payload:
            hits.update(_forbidden_key_hits(row))
    return hits


def _f1_summary(review: Mapping[str, Any]) -> dict[str, Any]:
    decision = review.get("decision", {})
    decision = decision if isinstance(decision, dict) else {}
    tier_summary = review.get("synthetic_tier_summary", {})
    tier_summary = tier_summary if isinstance(tier_summary, dict) else {}
    signal_summary = review.get("training_signal_summary", {})
    signal_summary = signal_summary if isinstance(signal_summary, dict) else {}
    return {
        "version": str(review.get("version") or ""),
        "calibration_baseline_ready": bool(decision.get("calibration_baseline_ready")),
        "tier_count": len(tier_summary),
        "training_signal_count": int(signal_summary.get("signal_count", 0) or 0),
        "decision_status": str(decision.get("decision_status") or ""),
    }


def _decision(
    *,
    f1_review: Mapping[str, Any],
    candidates: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    blockers: list[str] = []
    f1_decision = f1_review.get("decision", {})
    f1_decision = f1_decision if isinstance(f1_decision, dict) else {}
    if not f1_decision.get("calibration_baseline_ready"):
        blockers.append("f1_calibration_baseline_not_ready")
    if len(candidates) < 4:
        blockers.append("targeted_candidate_count_low")
    forbidden = {
        candidate["family"]: candidate["forbidden_payload_key_hits"]
        for candidate in candidates
        if candidate["forbidden_payload_key_hits"]
    }
    if forbidden:
        blockers.append("candidate_payload_contains_forbidden_fact_keys")
    missing_tracks = {
        "model_signal_weights",
        "rule_weights",
        "question_strategy",
        "expression_policy",
    } - {candidate["allowed_track"] for candidate in candidates}
    if missing_tracks:
        blockers.append("targeted_candidate_track_missing")
    ready = not blockers
    return {
        "targeted_calibration_review_ready": ready,
        "policy_pointer_review_allowed": False,
        "policy_pointer_promotion_allowed": False,
        "chart_fact_mutation_allowed": False,
        "decision_status": "ready_for_validation_gate_review" if ready else "targeted_calibration_review_blocked",
        "blockers": blockers,
        "missing_tracks": sorted(missing_tracks),
        "forbidden_candidate_payloads": forbidden,
        "rationale": (
            "Targeted calibration candidates are ready for a later validation gate review; no policy pointer can be promoted from this review."
            if ready
            else "Targeted calibration candidate review needs the listed blockers closed before validation-gate review."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["targeted_calibration_review_ready"]:
        return {
            "task_id": "F3",
            "title": "Targeted Calibration Validation Gate",
            "selected_track": "targeted_calibration",
            "scope": [
                "run synthetic all against reviewed candidates",
                "run 518K sample before any pointer review",
                "keep policy pointer promotion disallowed until a separate explicit review",
            ],
        }
    return {
        "task_id": "F2",
        "title": "Targeted Calibration Candidate Gap Closure",
        "selected_track": "targeted_calibration",
        "scope": [
            "restore missing candidate tracks",
            "remove forbidden chart-fact keys from candidate payloads",
            "rerun F1 if calibration baseline is stale or blocked",
        ],
    }
