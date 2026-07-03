from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

from v30.config import V30Settings
from v30.storage.artifacts import ARTIFACT_FAMILY_QUESTION_POLICY_COMPARISON, search_validation_artifacts
from v30.training.dialogue_policy_candidate_review import run_dialogue_policy_candidate_review


DIALOGUE_STRATEGY_VALIDATION_GATE_VERSION = "v30.dialogue_strategy_validation_gate.v1"


def run_dialogue_strategy_validation_gate(
    *,
    runtime_payloads: Sequence[Mapping[str, Any]] | None = None,
    sample_limit: int = 20,
    run_id: str = "dtc3-dialogue-strategy-validation-gate",
    persist_review: bool = True,
    settings: V30Settings | None = None,
) -> dict[str, object]:
    review = run_dialogue_policy_candidate_review(
        runtime_payloads=runtime_payloads,
        sample_limit=sample_limit,
        run_id=f"{run_id}:dtc2",
        persist=persist_review,
        settings=settings,
    )
    return build_dialogue_strategy_validation_gate(
        review_result=review,
        run_id=run_id,
        settings=settings,
    )


def build_dialogue_strategy_validation_gate(
    *,
    review_result: Mapping[str, Any],
    run_id: str = "dtc3-dialogue-strategy-validation-gate",
    settings: V30Settings | None = None,
) -> dict[str, object]:
    review = dict(review_result)
    comparison = _mapping(review.get("question_policy_comparison"))
    candidate = _mapping(review.get("candidate_payload"))
    review_decision = _mapping(review.get("decision"))
    artifact_search = _artifact_search_summary(
        candidate_id=str(candidate.get("candidate_id") or comparison.get("candidate_id") or ""),
        settings=settings,
    )
    replay = _replay_evaluation(comparison=comparison, candidate=candidate)
    checks = _checks(
        review=review,
        comparison=comparison,
        candidate=candidate,
        replay=replay,
        artifact_search=artifact_search,
    )
    failed = [row for row in checks if row["passed"] is not True]
    ready = not failed
    return {
        "version": DIALOGUE_STRATEGY_VALIDATION_GATE_VERSION,
        "run_id": run_id,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if ready else "blocked",
        "task": {
            "task_id": "DTC-3",
            "title": "Dialogue Strategy Validation Gate",
            "scope": "decide_whether_reviewed_dialogue_question_policy_candidate_deserves_heavier_synthetic_replay",
        },
        "review_result": review,
        "replay_evaluation": replay,
        "artifact_search": artifact_search,
        "checks": checks,
        "decision": {
            "dialogue_strategy_validation_gate_ready": ready,
            "decision_status": "dtc3_dialogue_strategy_validation_gate_ready"
            if ready else "dtc3_dialogue_strategy_validation_gate_blocked",
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "candidate_id": candidate.get("candidate_id") or comparison.get("candidate_id") or "",
            "candidate_deserves_synthetic_replay": ready and replay["synthetic_replay_recommended"],
            "promotion_allowed": False,
            "policy_pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
        },
        "policy_boundary": {
            "runtime_mutation_allowed": False,
            "chart_fact_mutation_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "auto_apply_training_allowed": False,
            "comparison_artifact_required": True,
            "operator_review_required": True,
            "blocked_targets": [
                "chart_facts",
                "calendar_conversion",
                "pillar_calculation",
                "online_policy_pointer",
                "auto_promotion",
            ],
            "boundary": "dialogue_strategy_validation_gate_routes_candidate_to_review_queue_without_promoting_policy",
        },
        "next_mainline_selection": {
            "task_id": "DTC-4" if ready else "DTC-3-FIX",
            "title": "Dialogue Synthetic Replay Queue" if ready else "Fix Dialogue Strategy Validation Gate",
            "reason": "candidate_has_measurable_readonly_replay_effect_and_safe_boundary"
            if ready else "candidate_review_or_artifact_gate_failed",
        },
        "boundary": "dtc3_is_validation_gate_for_question_strategy_not_bazi_truth_or_policy_release",
    }


def _replay_evaluation(*, comparison: Mapping[str, Any], candidate: Mapping[str, Any]) -> dict[str, object]:
    active_count = _int(_mapping(comparison.get("summary")).get("active_decision_count"))
    candidate_count = _int(_mapping(comparison.get("summary")).get("candidate_decision_count"))
    changed_rank_count = _int(comparison.get("changed_rank_count"))
    weighted_delta_count = _int(comparison.get("weighted_delta_count"))
    max_score_delta = _float(comparison.get("max_score_delta"))
    max_policy_weight_delta = _float(comparison.get("max_policy_weight_delta"))
    rank_disruption_ratio = round(changed_rank_count / max(active_count, 1), 3)
    candidate_domains = _candidate_domains(candidate)
    meaningful_policy_delta = weighted_delta_count > 0 and max_policy_weight_delta > 0
    overfit_risk = _overfit_risk(
        active_count=active_count,
        candidate_count=candidate_count,
        rank_disruption_ratio=rank_disruption_ratio,
        max_score_delta=max_score_delta,
    )
    synthetic_replay_recommended = (
        meaningful_policy_delta
        and active_count > 0
        and candidate_count > 0
        and overfit_risk in {"low", "medium"}
    )
    return {
        "version": "v30.dialogue_strategy_replay_evaluation.v1",
        "active_decision_count": active_count,
        "candidate_decision_count": candidate_count,
        "top_question_changed": bool(comparison.get("top_question_changed")),
        "changed_rank_count": changed_rank_count,
        "weighted_delta_count": weighted_delta_count,
        "max_score_delta": max_score_delta,
        "max_policy_weight_delta": max_policy_weight_delta,
        "rank_disruption_ratio": rank_disruption_ratio,
        "candidate_domains": candidate_domains,
        "meaningful_policy_delta": meaningful_policy_delta,
        "overfit_risk": overfit_risk,
        "synthetic_replay_recommended": synthetic_replay_recommended,
        "evaluation_label": "candidate_ready_for_synthetic_replay"
        if synthetic_replay_recommended else "candidate_requires_review_before_replay",
        "boundary": "replay_evaluation_scores_question_policy_behavior_not_chart_facts",
    }


def _artifact_search_summary(*, candidate_id: str, settings: V30Settings | None) -> dict[str, object]:
    if not candidate_id:
        return {
            "version": "v30.dialogue_strategy_artifact_search.v1",
            "candidate_id": "",
            "count": 0,
            "searchable": False,
            "backend": "none",
            "artifact_record_ids": [],
            "boundary": "artifact_search_missing_candidate_id",
        }
    result = search_validation_artifacts(
        settings=settings,
        family=ARTIFACT_FAMILY_QUESTION_POLICY_COMPARISON,
        candidate_id=candidate_id,
        limit=5,
    )
    return {
        "version": "v30.dialogue_strategy_artifact_search.v1",
        "candidate_id": candidate_id,
        "count": result.count,
        "searchable": result.searchable,
        "backend": result.backend,
        "fallback_used": result.fallback_used,
        "artifact_record_ids": [row.artifact_record_id for row in result.artifacts],
        "artifact_uris": [row.runtime_path for row in result.artifacts if row.runtime_path],
        "boundary": "artifact_search_reads_question_policy_comparison_artifacts_only",
    }


def _checks(
    *,
    review: Mapping[str, Any],
    comparison: Mapping[str, Any],
    candidate: Mapping[str, Any],
    replay: Mapping[str, Any],
    artifact_search: Mapping[str, Any],
) -> list[dict[str, object]]:
    review_decision = _mapping(review.get("decision"))
    return [
        _check(
            "dtc2_review_ready",
            review.get("status") == "completed"
            and review_decision.get("dialogue_policy_candidate_review_ready") is True,
            {"review_status": review.get("status"), "decision_status": review_decision.get("decision_status")},
        ),
        _check(
            "comparison_artifact_discoverable",
            bool(comparison.get("artifact_uri"))
            and _int(artifact_search.get("count")) >= 1,
            {
                "artifact_uri": comparison.get("artifact_uri"),
                "artifact_count": artifact_search.get("count"),
                "backend": artifact_search.get("backend"),
            },
        ),
        _check(
            "candidate_has_measurable_policy_effect",
            replay.get("meaningful_policy_delta") is True
            and _int(replay.get("active_decision_count")) > 0
            and _int(replay.get("candidate_decision_count")) > 0,
            {
                "weighted_delta_count": replay.get("weighted_delta_count"),
                "max_policy_weight_delta": replay.get("max_policy_weight_delta"),
                "active_decision_count": replay.get("active_decision_count"),
                "candidate_decision_count": replay.get("candidate_decision_count"),
            },
        ),
        _check(
            "candidate_boundary_safe",
            candidate.get("auto_apply_allowed") is False
            and candidate.get("policy_pointer_promotion_allowed") is False
            and candidate.get("chart_fact_mutation_allowed") is False,
            {
                "auto_apply_allowed": candidate.get("auto_apply_allowed"),
                "policy_pointer_promotion_allowed": candidate.get("policy_pointer_promotion_allowed"),
                "chart_fact_mutation_allowed": candidate.get("chart_fact_mutation_allowed"),
            },
        ),
        _check(
            "overfit_risk_is_reviewable",
            replay.get("overfit_risk") in {"low", "medium"},
            {
                "overfit_risk": replay.get("overfit_risk"),
                "rank_disruption_ratio": replay.get("rank_disruption_ratio"),
                "max_score_delta": replay.get("max_score_delta"),
            },
        ),
    ]


def _candidate_domains(candidate: Mapping[str, Any]) -> list[str]:
    weights = _mapping(candidate.get("weights"))
    topic_weights = _mapping(weights.get("topic_weights"))
    return sorted(str(key) for key in topic_weights if str(key) != "*")


def _overfit_risk(
    *,
    active_count: int,
    candidate_count: int,
    rank_disruption_ratio: float,
    max_score_delta: float,
) -> str:
    if active_count <= 0 or candidate_count <= 0:
        return "high"
    if rank_disruption_ratio >= 0.72 or max_score_delta >= 0.45:
        return "high"
    if rank_disruption_ratio >= 0.35 or max_score_delta >= 0.18:
        return "medium"
    return "low"


def _check(check_id: str, passed: bool, observed: Mapping[str, object]) -> dict[str, object]:
    return {"check_id": check_id, "passed": bool(passed), "observed": dict(observed)}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _int(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
