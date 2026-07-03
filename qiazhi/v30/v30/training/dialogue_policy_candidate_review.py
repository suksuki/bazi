from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

from v30.config import V30Settings
from v30.contracts import CoreRuntimeResult
from v30.policy.comparison import (
    QUESTION_POLICY_COMPARISON_VERSION,
    build_question_policy_comparison,
    persist_question_policy_comparison,
)
from v30.runtime import create_smoke_runtime
from v30.training.dialogue_calibration_loop import run_dialogue_training_calibration_loop


DIALOGUE_POLICY_CANDIDATE_REVIEW_VERSION = "v30.dialogue_policy_candidate_review.v1"
DIALOGUE_POLICY_COMPILED_CANDIDATE_VERSION = "v30.dialogue_policy_compiled_candidate.v1"


def run_dialogue_policy_candidate_review(
    *,
    runtime_payloads: Sequence[Mapping[str, Any]] | None = None,
    sample_limit: int = 20,
    run_id: str = "dtc2-dialogue-policy-candidate-review",
    persist: bool = True,
    settings: V30Settings | None = None,
) -> dict[str, object]:
    payloads = list(runtime_payloads or [])
    loop = run_dialogue_training_calibration_loop(
        runtime_payloads=payloads,
        sample_limit=sample_limit,
        run_id=f"{run_id}:dtc1",
    )
    runtime = _comparison_runtime(payloads, run_id=run_id)
    return build_dialogue_policy_candidate_review(
        loop_result=loop,
        comparison_runtime=runtime,
        run_id=run_id,
        persist=persist,
        settings=settings,
    )


def build_dialogue_policy_candidate_review(
    *,
    loop_result: Mapping[str, Any],
    comparison_runtime: CoreRuntimeResult | None = None,
    run_id: str = "dtc2-dialogue-policy-candidate-review",
    persist: bool = False,
    settings: V30Settings | None = None,
) -> dict[str, object]:
    loop = dict(loop_result)
    runtime = comparison_runtime or create_smoke_runtime(f"{run_id}:comparison")
    candidate_payload = compile_dialogue_question_policy_candidate(loop, run_id=run_id)
    comparison = build_question_policy_comparison(
        runtime,
        candidate_id=str(candidate_payload["candidate_id"]),
        candidate_payload=candidate_payload,
        candidate_question_policy_id=str(candidate_payload["policy_id"]),
    )
    if persist:
        comparison = persist_question_policy_comparison(comparison, settings=settings)
    checks = _checks(loop=loop, candidate_payload=candidate_payload, comparison=comparison.model_dump(mode="json"))
    failed = [row for row in checks if not row["passed"]]
    ready = not failed
    review_summary = {
        "training_sample_count": int(_mapping(loop.get("sample_summary")).get("sample_count") or 0),
        "dtc1_policy_candidate_count": len(_list(loop.get("policy_candidates"))),
        "compiled_weight_bucket_count": len(_mapping(candidate_payload.get("weights"))),
        "changed_rank_count": comparison.changed_rank_count,
        "weighted_delta_count": comparison.weighted_delta_count,
        "top_question_changed": comparison.top_question_changed,
        "artifact_searchable": comparison.artifact_searchable,
        "boundary": "review_summary_measures_question_policy_effect_only",
    }
    return {
        "version": DIALOGUE_POLICY_CANDIDATE_REVIEW_VERSION,
        "run_id": run_id,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if ready else "blocked",
        "task": {
            "task_id": "DTC-2",
            "title": "Dialogue Policy Candidate Review",
            "scope": "compile_dtc1_training_candidates_into_read_only_question_policy_replay_artifact",
        },
        "loop_result": loop,
        "candidate_payload": candidate_payload,
        "question_policy_comparison": comparison.model_dump(mode="json"),
        "review_summary": review_summary,
        "checks": checks,
        "decision": {
            "dialogue_policy_candidate_review_ready": ready,
            "decision_status": "dtc2_dialogue_policy_candidate_review_ready"
            if ready else "dtc2_dialogue_policy_candidate_review_blocked",
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "training_sample_count": review_summary["training_sample_count"],
            "compiled_candidate_ready": bool(candidate_payload.get("candidate_id")),
            "comparison_artifact_ready": bool(comparison.artifact_uri) if persist else comparison.version == QUESTION_POLICY_COMPARISON_VERSION,
            "chart_fact_mutation_allowed": False,
            "policy_pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
        },
        "policy_boundary": {
            "runtime_mutation_allowed": False,
            "chart_fact_mutation_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "auto_apply_training_allowed": False,
            "comparison_artifact_allowed": True,
            "operator_review_required": True,
            "blocked_targets": [
                "chart_facts",
                "calendar_conversion",
                "pillar_calculation",
                "unconfirmed_hidden_factor_facts",
                "online_policy_pointer",
            ],
            "boundary": "dialogue_policy_candidate_review_is_read_only_replay_not_policy_release",
        },
        "next_mainline_selection": {
            "task_id": "DTC-3" if ready else "DTC-2-FIX",
            "title": "Dialogue Strategy Validation Gate" if ready else "Fix Dialogue Policy Candidate Review",
            "reason": "compiled_question_policy_candidate_has_reviewable_replay_artifact"
            if ready else "candidate_review_checks_failed",
        },
        "boundary": "dtc2_reviews_dialogue_policy_candidates_without_mutating_bazi_truth_or_policy_pointer",
    }


def compile_dialogue_question_policy_candidate(
    loop_result: Mapping[str, Any],
    *,
    run_id: str,
) -> dict[str, object]:
    candidates = [_mapping(row) for row in _list(loop_result.get("policy_candidates"))]
    samples = [_mapping(row) for row in _list(loop_result.get("training_samples"))]
    topic_weights: dict[str, float] = {}
    intent_weights: dict[str, float] = {}
    question_weights: dict[str, float] = {}
    stage_weights: dict[str, float] = {}
    model_signal_topic_weights: dict[str, float] = {}
    evidence_routes: list[dict[str, object]] = []

    for candidate in candidates:
        candidate_type = str(candidate.get("candidate_type") or "")
        group_id = str(candidate.get("group_id") or "")
        direction = str(candidate.get("recommended_direction") or "")
        multiplier = _direction_multiplier(direction)
        if candidate_type == "macro_domain_question_slot_weight" and group_id.startswith("macro_domain:"):
            domain = group_id.split(":", 1)[1]
            topic_weights[domain] = _bounded_weight(topic_weights.get(domain, 1.0) * multiplier)
            model_signal_topic_weights[domain] = _bounded_weight(model_signal_topic_weights.get(domain, 1.0) * multiplier)
        elif candidate_type == "semantic_question_weight":
            _apply_semantic_slot_weight(group_id, multiplier, topic_weights=topic_weights, intent_weights=intent_weights)
        elif candidate_type == "dialogue_action_policy":
            if direction == "review_overask_penalty":
                stage_weights["user_question_entry"] = 0.98
            elif direction == "keep_current":
                stage_weights["user_question_entry"] = 1.0
        evidence_routes.append(
            {
                "source_candidate_id": candidate.get("candidate_id"),
                "candidate_type": candidate_type,
                "group_id": group_id,
                "recommended_direction": direction,
                "compiled_multiplier": multiplier,
                "sample_count": candidate.get("sample_count"),
            }
        )

    for sample in samples:
        question_id = str(sample.get("question_id") or "")
        label = str(sample.get("policy_label") or "")
        if not question_id:
            continue
        if label == "ask_was_useful":
            question_weights[question_id] = _bounded_weight(question_weights.get(question_id, 1.0) * 1.04)
        elif label == "ask_needs_better_answer_quality":
            question_weights[question_id] = _bounded_weight(question_weights.get(question_id, 1.0) * 0.96)

    weights = {
        "topic_weights": topic_weights or {"*": 1.0},
        "intent_weights": intent_weights or {"*": 1.0},
        "stage_weights": stage_weights or {"user_question_entry": 1.0},
        "question_weights": question_weights or {"*": 1.0},
        "model_signal_question_policy": {
            "topic_weights": model_signal_topic_weights or {"*": 1.0},
            "boundary": "model_signal_weight_is_question_ranking_signal_not_chart_fact",
        },
    }
    candidate_id = f"{run_id}.question_policy.candidate"
    return {
        "version": DIALOGUE_POLICY_COMPILED_CANDIDATE_VERSION,
        "candidate_id": candidate_id,
        "policy_id": f"question_policy.{candidate_id}",
        "source_loop_version": str(loop_result.get("version") or ""),
        "source_run_id": str(loop_result.get("run_id") or ""),
        "weights": weights,
        "evidence_routes": evidence_routes,
        "training_sample_ids": [str(row.get("sample_id") or "") for row in samples if row.get("sample_id")],
        "requires_operator_review": True,
        "auto_apply_allowed": False,
        "policy_pointer_promotion_allowed": False,
        "chart_fact_mutation_allowed": False,
        "boundary": "compiled_dialogue_question_policy_candidate_is_review_artifact_not_live_policy",
    }


def _comparison_runtime(payloads: Sequence[Mapping[str, Any]], *, run_id: str) -> CoreRuntimeResult:
    for payload in payloads:
        try:
            return CoreRuntimeResult.model_validate(payload)
        except Exception:
            continue
    return create_smoke_runtime(f"{run_id}:comparison")


def _checks(
    *,
    loop: Mapping[str, Any],
    candidate_payload: Mapping[str, Any],
    comparison: Mapping[str, Any],
) -> list[dict[str, object]]:
    decision = _mapping(loop.get("decision"))
    boundary = _mapping(loop.get("policy_boundary"))
    weights = _mapping(candidate_payload.get("weights"))
    return [
        _check(
            "dtc1_loop_ready",
            str(loop.get("status")) == "completed" and bool(decision.get("dialogue_training_calibration_ready")),
            {"loop_status": loop.get("status"), "decision_status": decision.get("decision_status")},
        ),
        _check(
            "candidate_compiled_from_training_evidence",
            candidate_payload.get("version") == DIALOGUE_POLICY_COMPILED_CANDIDATE_VERSION
            and bool(candidate_payload.get("evidence_routes"))
            and bool(weights),
            {
                "candidate_id": candidate_payload.get("candidate_id"),
                "evidence_route_count": len(_list(candidate_payload.get("evidence_routes"))),
                "weight_buckets": sorted(weights.keys()),
            },
        ),
        _check(
            "comparison_replay_ready",
            comparison.get("version") == QUESTION_POLICY_COMPARISON_VERSION
            and bool(comparison.get("candidate_top_question_id")),
            {
                "comparison_version": comparison.get("version"),
                "weighted_delta_count": comparison.get("weighted_delta_count"),
                "changed_rank_count": comparison.get("changed_rank_count"),
            },
        ),
        _check(
            "review_boundaries_are_safe",
            boundary.get("chart_fact_mutation_allowed") is False
            and boundary.get("policy_pointer_promotion_allowed") is False
            and candidate_payload.get("auto_apply_allowed") is False
            and candidate_payload.get("chart_fact_mutation_allowed") is False,
            {
                "chart_fact_mutation_allowed": boundary.get("chart_fact_mutation_allowed"),
                "policy_pointer_promotion_allowed": boundary.get("policy_pointer_promotion_allowed"),
                "candidate_auto_apply_allowed": candidate_payload.get("auto_apply_allowed"),
            },
        ),
    ]


def _apply_semantic_slot_weight(
    group_id: str,
    multiplier: float,
    *,
    topic_weights: dict[str, float],
    intent_weights: dict[str, float],
) -> None:
    slot = group_id.split(":", 1)[1] if ":" in group_id else group_id
    if "career" in slot or "事业" in slot:
        topic_weights["career"] = _bounded_weight(topic_weights.get("career", 1.0) * multiplier)
    elif "relationship" in slot or "感情" in slot:
        topic_weights["relationship"] = _bounded_weight(topic_weights.get("relationship", 1.0) * multiplier)
    elif "wealth" in slot or "财" in slot:
        topic_weights["wealth"] = _bounded_weight(topic_weights.get("wealth", 1.0) * multiplier)
    elif "health" in slot or "身体" in slot:
        topic_weights["health"] = _bounded_weight(topic_weights.get("health", 1.0) * multiplier)
    elif "hidden" in slot or "latent" in slot or "隐藏" in slot:
        topic_weights["hidden_factor"] = _bounded_weight(topic_weights.get("hidden_factor", 1.0) * multiplier)
        intent_weights["discover_hidden_factor_amplifier"] = _bounded_weight(
            intent_weights.get("discover_hidden_factor_amplifier", 1.0) * multiplier
        )


def _direction_multiplier(direction: str) -> float:
    if direction == "increase":
        return 1.06
    if direction == "hold_until_answer_quality_improves":
        return 0.96
    if direction == "review_overask_penalty":
        return 0.98
    return 1.0


def _bounded_weight(value: float) -> float:
    return round(max(0.1, min(float(value), 2.0)), 3)


def _check(check_id: str, passed: bool, observed: Mapping[str, object]) -> dict[str, object]:
    return {"check_id": check_id, "passed": bool(passed), "observed": dict(observed)}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []
