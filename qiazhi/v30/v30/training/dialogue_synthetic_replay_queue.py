from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

from v30.config import V30Settings
from v30.policy.comparison import build_question_policy_comparison
from v30.runtime import attach_question_outcome, create_smoke_runtime
from v30.training.dialogue_strategy_validation_gate import run_dialogue_strategy_validation_gate


DIALOGUE_SYNTHETIC_REPLAY_QUEUE_VERSION = "v30.dialogue_synthetic_replay_queue.v1"
REPLAY_CASE_VERSION = "v30.dialogue_synthetic_replay_case.v1"


def run_dialogue_synthetic_replay_queue(
    *,
    runtime_payloads: Sequence[Mapping[str, Any]] | None = None,
    sample_limit: int = 20,
    run_id: str = "dtc4-dialogue-synthetic-replay-queue",
    persist_review: bool = True,
    settings: V30Settings | None = None,
) -> dict[str, object]:
    gate = run_dialogue_strategy_validation_gate(
        runtime_payloads=runtime_payloads,
        sample_limit=sample_limit,
        run_id=f"{run_id}:dtc3",
        persist_review=persist_review,
        settings=settings,
    )
    return build_dialogue_synthetic_replay_queue(gate_result=gate, run_id=run_id)


def build_dialogue_synthetic_replay_queue(
    *,
    gate_result: Mapping[str, Any],
    run_id: str = "dtc4-dialogue-synthetic-replay-queue",
) -> dict[str, object]:
    gate = dict(gate_result)
    review = _mapping(gate.get("review_result"))
    candidate = _mapping(review.get("candidate_payload"))
    candidate_id = str(candidate.get("candidate_id") or _mapping(gate.get("decision")).get("candidate_id") or "")
    candidate_policy_id = str(candidate.get("policy_id") or f"question_policy.{candidate_id}")
    replay_cases = [
        _replay_case(
            row,
            candidate_payload=candidate,
            candidate_id=candidate_id,
            candidate_policy_id=candidate_policy_id,
        )
        for row in _synthetic_case_specs(run_id)
    ]
    aggregate = _aggregate(replay_cases=replay_cases, gate=gate, candidate=candidate)
    checks = _checks(gate=gate, candidate=candidate, replay_cases=replay_cases, aggregate=aggregate)
    failed = [row for row in checks if row["passed"] is not True]
    ready = not failed
    return {
        "version": DIALOGUE_SYNTHETIC_REPLAY_QUEUE_VERSION,
        "run_id": run_id,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if ready else "blocked",
        "task": {
            "task_id": "DTC-4",
            "title": "Dialogue Synthetic Replay Queue",
            "scope": "batch_replay_reviewed_dialogue_question_policy_candidate_against_multiple_synthetic_contexts",
        },
        "gate_result": gate,
        "candidate_payload": candidate,
        "replay_cases": replay_cases,
        "aggregate": aggregate,
        "checks": checks,
        "decision": {
            "dialogue_synthetic_replay_queue_ready": ready,
            "decision_status": "dtc4_dialogue_synthetic_replay_queue_ready"
            if ready else "dtc4_dialogue_synthetic_replay_queue_blocked",
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "candidate_id": candidate_id,
            "synthetic_replay_case_count": len(replay_cases),
            "passed_replay_case_count": aggregate["passed_case_count"],
            "candidate_ready_for_operator_review": ready,
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
            "operator_review_required": True,
            "blocked_targets": [
                "chart_facts",
                "calendar_conversion",
                "pillar_calculation",
                "online_policy_pointer",
                "auto_promotion",
            ],
            "boundary": "dialogue_synthetic_replay_queue_batches_question_strategy_evidence_without_promoting_policy",
        },
        "next_mainline_selection": {
            "task_id": "DTC-5" if ready else "DTC-4-FIX",
            "title": "Dialogue Operator Review Pack" if ready else "Fix Dialogue Synthetic Replay Queue",
            "reason": "candidate_is_stable_across_synthetic_replay_cases"
            if ready else "candidate_batch_replay_checks_failed",
        },
        "boundary": "dtc4_is_batch_question_strategy_replay_not_bazi_truth_or_policy_release",
    }


def _replay_case(
    spec: Mapping[str, Any],
    *,
    candidate_payload: Mapping[str, Any],
    candidate_id: str,
    candidate_policy_id: str,
) -> dict[str, object]:
    runtime = create_smoke_runtime(
        reading_id=str(spec["reading_id"]),
        day_master=str(spec["day_master"]),
        day_master_element=str(spec["day_master_element"]),
        luck_pillar=str(spec.get("luck_pillar") or ""),
        flow_year_pillar=str(spec.get("flow_year_pillar") or ""),
        hidden_factor_user_calibrated=bool(spec.get("hidden_factor_user_calibrated")),
        useful_god_path_resolved=bool(spec.get("useful_god_path_resolved")),
        branch_single_factor_confirmed=bool(spec.get("branch_single_factor_confirmed")),
    )
    if spec.get("answered_question_id"):
        runtime = attach_question_outcome(
            runtime,
            str(spec["answered_question_id"]),
            {
                "event_id": f"{spec['case_id']}:answer",
                "answer": str(spec.get("answer") or "用户已给出简短反馈。"),
                "selected_option": str(spec.get("selected_option") or "neutral"),
                "confidence": 0.78,
                "feedback_tags": list(spec.get("feedback_tags") or []),
            },
        )
    comparison = build_question_policy_comparison(
        runtime,
        candidate_id=f"{candidate_id}.{spec['case_id']}",
        candidate_payload=dict(candidate_payload),
        candidate_question_policy_id=candidate_policy_id,
    )
    active_count = int(comparison.summary.get("active_decision_count") or 0)
    rank_disruption_ratio = round(comparison.changed_rank_count / max(active_count, 1), 3)
    passed = (
        active_count > 0
        and comparison.weighted_delta_count > 0
        and comparison.max_policy_weight_delta > 0
        and rank_disruption_ratio <= 0.85
        and comparison.max_score_delta <= 0.55
    )
    return {
        "version": REPLAY_CASE_VERSION,
        "case_id": str(spec["case_id"]),
        "reading_id": runtime.reading_id,
        "focus_domain": str(spec["focus_domain"]),
        "active_top_question_id": comparison.active_top_question_id,
        "candidate_top_question_id": comparison.candidate_top_question_id,
        "top_question_changed": comparison.top_question_changed,
        "changed_rank_count": comparison.changed_rank_count,
        "weighted_delta_count": comparison.weighted_delta_count,
        "max_score_delta": comparison.max_score_delta,
        "max_policy_weight_delta": comparison.max_policy_weight_delta,
        "rank_disruption_ratio": rank_disruption_ratio,
        "passed": passed,
        "comparison_summary": comparison.summary,
        "boundary": "synthetic_replay_case_compares_question_strategy_without_mutating_runtime_or_chart_facts",
    }


def _aggregate(
    *,
    replay_cases: Sequence[Mapping[str, Any]],
    gate: Mapping[str, Any],
    candidate: Mapping[str, Any],
) -> dict[str, object]:
    case_count = len(replay_cases)
    passed_count = sum(1 for row in replay_cases if row.get("passed") is True)
    weighted_delta_counts = [_int(row.get("weighted_delta_count")) for row in replay_cases]
    rank_ratios = [_float(row.get("rank_disruption_ratio")) for row in replay_cases]
    score_deltas = [_float(row.get("max_score_delta")) for row in replay_cases]
    domains = sorted({str(row.get("focus_domain") or "") for row in replay_cases if row.get("focus_domain")})
    candidate_domains = _candidate_domains(candidate)
    return {
        "version": "v30.dialogue_synthetic_replay_aggregate.v1",
        "case_count": case_count,
        "passed_case_count": passed_count,
        "pass_ratio": round(passed_count / max(case_count, 1), 3),
        "average_weighted_delta_count": round(sum(weighted_delta_counts) / max(case_count, 1), 3),
        "average_rank_disruption_ratio": round(sum(rank_ratios) / max(case_count, 1), 3),
        "max_rank_disruption_ratio": max(rank_ratios, default=0.0),
        "max_score_delta": max(score_deltas, default=0.0),
        "focus_domains": domains,
        "candidate_domains": candidate_domains,
        "gate_ready": _mapping(gate.get("decision")).get("dialogue_strategy_validation_gate_ready") is True,
        "stable_enough_for_operator_review": passed_count == case_count and case_count >= 4,
        "boundary": "aggregate_scores_candidate_question_strategy_stability_not_bazi_truth",
    }


def _checks(
    *,
    gate: Mapping[str, Any],
    candidate: Mapping[str, Any],
    replay_cases: Sequence[Mapping[str, Any]],
    aggregate: Mapping[str, Any],
) -> list[dict[str, object]]:
    gate_decision = _mapping(gate.get("decision"))
    return [
        _check(
            "dtc3_gate_ready",
            gate_decision.get("dialogue_strategy_validation_gate_ready") is True
            and gate_decision.get("candidate_deserves_synthetic_replay") is True,
            {
                "decision_status": gate_decision.get("decision_status"),
                "candidate_deserves_synthetic_replay": gate_decision.get("candidate_deserves_synthetic_replay"),
            },
        ),
        _check(
            "synthetic_replay_cases_present",
            len(replay_cases) >= 4,
            {"case_count": len(replay_cases)},
        ),
        _check(
            "candidate_effect_is_consistent",
            aggregate.get("stable_enough_for_operator_review") is True
            and _float(aggregate.get("average_weighted_delta_count")) > 0,
            {
                "passed_case_count": aggregate.get("passed_case_count"),
                "case_count": aggregate.get("case_count"),
                "average_weighted_delta_count": aggregate.get("average_weighted_delta_count"),
            },
        ),
        _check(
            "rank_disruption_is_bounded",
            _float(aggregate.get("max_rank_disruption_ratio")) <= 0.85
            and _float(aggregate.get("max_score_delta")) <= 0.55,
            {
                "max_rank_disruption_ratio": aggregate.get("max_rank_disruption_ratio"),
                "max_score_delta": aggregate.get("max_score_delta"),
            },
        ),
        _check(
            "candidate_boundary_still_safe",
            candidate.get("auto_apply_allowed") is False
            and candidate.get("policy_pointer_promotion_allowed") is False
            and candidate.get("chart_fact_mutation_allowed") is False,
            {
                "auto_apply_allowed": candidate.get("auto_apply_allowed"),
                "policy_pointer_promotion_allowed": candidate.get("policy_pointer_promotion_allowed"),
                "chart_fact_mutation_allowed": candidate.get("chart_fact_mutation_allowed"),
            },
        ),
    ]


def _synthetic_case_specs(run_id: str) -> list[dict[str, object]]:
    return [
        {
            "case_id": "career_pressure",
            "reading_id": f"{run_id}:career-pressure",
            "focus_domain": "career",
            "day_master": "甲",
            "day_master_element": "wood",
            "luck_pillar": "庚午",
            "flow_year_pillar": "甲辰",
            "answered_question_id": "q_v30_user_career_direction",
            "answer": "事业压力明显，更关心职责边界和转型节奏。",
            "selected_option": "career:pressure",
            "feedback_tags": ["career", "pressure"],
        },
        {
            "case_id": "relationship_boundary",
            "reading_id": f"{run_id}:relationship-boundary",
            "focus_domain": "relationship",
            "day_master": "丙",
            "day_master_element": "fire",
            "luck_pillar": "辛未",
            "flow_year_pillar": "乙巳",
            "answered_question_id": "q_v30_user_relationship_pattern",
            "answer": "关系里反复感强，希望先看相处边界。",
            "selected_option": "relationship:boundary",
            "feedback_tags": ["relationship", "boundary"],
        },
        {
            "case_id": "wealth_timing",
            "reading_id": f"{run_id}:wealth-timing",
            "focus_domain": "wealth",
            "day_master": "庚",
            "day_master_element": "metal",
            "luck_pillar": "壬申",
            "flow_year_pillar": "丙午",
            "useful_god_path_resolved": True,
        },
        {
            "case_id": "hidden_factor_probe",
            "reading_id": f"{run_id}:hidden-factor",
            "focus_domain": "hidden_factor",
            "day_master": "壬",
            "day_master_element": "water",
            "luck_pillar": "癸酉",
            "flow_year_pillar": "丁未",
            "hidden_factor_user_calibrated": False,
            "branch_single_factor_confirmed": False,
        },
    ]


def _candidate_domains(candidate: Mapping[str, Any]) -> list[str]:
    topic_weights = _mapping(_mapping(candidate.get("weights")).get("topic_weights"))
    return sorted(str(key) for key in topic_weights if str(key) != "*")


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
