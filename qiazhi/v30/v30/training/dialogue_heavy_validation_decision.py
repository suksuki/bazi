from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

from v30.config import V30Settings
from v30.training.dialogue_operator_review_pack import run_dialogue_operator_review_pack


DIALOGUE_HEAVY_VALIDATION_DECISION_VERSION = "v30.dialogue_heavy_validation_decision.v1"


HEAVY_VALIDATION_GATE_CATALOG: dict[str, dict[str, object]] = {
    "dialogue_synthetic_all": {
        "category": "synthetic",
        "command": "python3 scripts/run_synthetic_validation.py --tier all",
        "required_before_promotion": True,
        "full": False,
    },
    "dialogue_518k_sample": {
        "category": "distribution",
        "command": "python3 scripts/run_518k_validation.py --mode sample --limit 8",
        "required_before_promotion": True,
        "full": False,
    },
    "dialogue_full_pytest": {
        "category": "test",
        "command": "pytest -q",
        "required_before_promotion": False,
        "full": True,
    },
    "dialogue_full_518k": {
        "category": "distribution",
        "command": "python3 scripts/run_518k_validation.py --mode full --confirm-full",
        "required_before_promotion": False,
        "full": True,
    },
}


def run_dialogue_heavy_validation_decision(
    *,
    runtime_payloads: Sequence[Mapping[str, Any]] | None = None,
    sample_limit: int = 20,
    run_id: str = "dtc6-dialogue-heavy-validation-decision",
    persist_review: bool = True,
    settings: V30Settings | None = None,
) -> dict[str, object]:
    pack = run_dialogue_operator_review_pack(
        runtime_payloads=runtime_payloads,
        sample_limit=sample_limit,
        run_id=f"{run_id}:dtc5",
        persist_review=persist_review,
        settings=settings,
    )
    return build_dialogue_heavy_validation_decision(pack_result=pack, run_id=run_id)


def build_dialogue_heavy_validation_decision(
    *,
    pack_result: Mapping[str, Any],
    run_id: str = "dtc6-dialogue-heavy-validation-decision",
) -> dict[str, object]:
    pack = dict(pack_result)
    evidence = _mapping(pack.get("evidence_summary"))
    pack_decision = _mapping(pack.get("decision"))
    risk_summary = _risk_summary(_list(pack.get("risk_register")))
    readiness = _readiness_summary(pack=pack, evidence=evidence, risk_summary=risk_summary)
    gate_matrix = [_gate_row(gate_id, readiness=readiness) for gate_id in HEAVY_VALIDATION_GATE_CATALOG]
    checks = _checks(pack=pack, readiness=readiness, gate_matrix=gate_matrix)
    failed = [row for row in checks if row["passed"] is not True]
    ready = not failed
    recommended_gate_ids = [str(row["gate_id"]) for row in gate_matrix if row["recommended_pending_operator_execution"]]
    return {
        "version": DIALOGUE_HEAVY_VALIDATION_DECISION_VERSION,
        "run_id": run_id,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if ready else "blocked",
        "task": {
            "task_id": "DTC-6",
            "title": "Dialogue Heavy Validation Decision",
            "scope": "recommend_heavy_validation_gates_for_reviewed_dialogue_question_policy_candidate_without_executing_or_releasing",
        },
        "pack_result": pack,
        "readiness_summary": readiness,
        "risk_summary": risk_summary,
        "gate_matrix": gate_matrix,
        "checks": checks,
        "decision": {
            "dialogue_heavy_validation_decision_ready": ready,
            "decision_status": "dtc6_dialogue_heavy_validation_decision_ready"
            if ready else "dtc6_dialogue_heavy_validation_decision_blocked",
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "candidate_id": pack_decision.get("candidate_id") or evidence.get("candidate_id") or "",
            "heavy_validation_recommended": ready and bool(recommended_gate_ids),
            "recommended_gate_ids": recommended_gate_ids,
            "recommended_gate_count": len(recommended_gate_ids),
            "runs_triggered": False,
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
            "runs_triggered": False,
            "heavy_validation_execution_allowed": False,
            "operator_authorization_required_before_execution": True,
            "policy_promotion_requires_separate_flow": True,
            "blocked_targets": [
                "chart_facts",
                "calendar_conversion",
                "pillar_calculation",
                "online_policy_pointer",
                "auto_promotion",
                "automatic_heavy_validation_execution",
            ],
            "boundary": "dialogue_heavy_validation_decision_recommends_gates_without_executing_or_promoting_policy",
        },
        "next_mainline_selection": {
            "task_id": "DTC-7" if ready else "DTC-6-FIX",
            "title": "Dialogue Heavy Validation Authorization" if ready else "Fix Dialogue Heavy Validation Decision",
            "reason": "heavy_validation_gates_are_recommended_but_require_explicit_operator_authorization"
            if ready else "heavy_validation_decision_checks_failed",
        },
        "boundary": "dtc6_records_heavy_validation_decision_not_test_execution_or_policy_release",
    }


def _readiness_summary(
    *,
    pack: Mapping[str, Any],
    evidence: Mapping[str, Any],
    risk_summary: Mapping[str, Any],
) -> dict[str, object]:
    decision = _mapping(pack.get("decision"))
    boundary = _mapping(pack.get("policy_boundary"))
    pass_ratio = _float(evidence.get("dtc4_pass_ratio"))
    return {
        "version": "v30.dialogue_heavy_validation_readiness_summary.v1",
        "pack_status": str(pack.get("status") or ""),
        "pack_decision_status": str(decision.get("decision_status") or ""),
        "candidate_id": str(decision.get("candidate_id") or evidence.get("candidate_id") or ""),
        "operator_review_pack_ready": bool(decision.get("dialogue_operator_review_pack_ready")),
        "candidate_ready_for_heavy_validation_review": bool(decision.get("candidate_ready_for_heavy_validation_review")),
        "dtc1_sample_count": _int(evidence.get("dtc1_sample_count")),
        "dtc4_case_count": _int(evidence.get("dtc4_case_count")),
        "dtc4_pass_ratio": pass_ratio,
        "dtc4_max_rank_disruption_ratio": _float(evidence.get("dtc4_max_rank_disruption_ratio")),
        "dtc4_max_score_delta": _float(evidence.get("dtc4_max_score_delta")),
        "high_risk_count": _int(risk_summary.get("high_risk_count")),
        "medium_risk_count": _int(risk_summary.get("medium_risk_count")),
        "promotion_allowed": bool(decision.get("promotion_allowed")),
        "policy_pointer_write_allowed": bool(decision.get("policy_pointer_write_allowed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "boundary_allows_promotion": bool(boundary.get("policy_pointer_promotion_allowed")),
        "ready_for_recommended_heavy_gates": (
            pack.get("status") == "completed"
            and decision.get("candidate_ready_for_heavy_validation_review") is True
            and pass_ratio >= 1.0
            and _int(risk_summary.get("high_risk_count")) == 0
            and decision.get("promotion_allowed") is False
            and decision.get("policy_pointer_write_allowed") is False
            and decision.get("chart_fact_mutation_allowed") is False
            and boundary.get("policy_pointer_promotion_allowed") is False
        ),
        "boundary": "readiness_summary_uses_operator_pack_evidence_without_running_heavy_gates",
    }


def _risk_summary(risks: Sequence[object]) -> dict[str, object]:
    rows = [_mapping(row) for row in risks]
    severity_counts: dict[str, int] = {}
    for row in rows:
        severity = str(row.get("severity") or "unknown")
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    return {
        "version": "v30.dialogue_heavy_validation_risk_summary.v1",
        "risk_count": len(rows),
        "high_risk_count": severity_counts.get("high", 0),
        "medium_risk_count": severity_counts.get("medium", 0),
        "low_risk_count": severity_counts.get("low", 0),
        "risk_ids": [str(row.get("risk_id") or "") for row in rows if row.get("risk_id")],
        "boundary": "risk_summary_informs_validation_gate_recommendation_not_policy_release",
    }


def _gate_row(gate_id: str, *, readiness: Mapping[str, Any]) -> dict[str, object]:
    spec = HEAVY_VALIDATION_GATE_CATALOG[gate_id]
    default_recommended = gate_id in {"dialogue_synthetic_all", "dialogue_518k_sample"}
    recommended = bool(readiness.get("ready_for_recommended_heavy_gates")) and default_recommended
    deferred_reason = ""
    if not readiness.get("ready_for_recommended_heavy_gates"):
        deferred_reason = "operator_review_pack_not_ready_for_heavy_validation"
    elif not default_recommended:
        deferred_reason = "full_gate_deferred_until_explicit_later_stage"
    return {
        "gate_id": gate_id,
        "category": spec["category"],
        "command": spec["command"],
        "required_before_promotion": bool(spec["required_before_promotion"]),
        "full": bool(spec["full"]),
        "recommended_pending_operator_execution": recommended,
        "run_triggered": False,
        "promotion_allowed_after_gate": False,
        "deferred_reason": deferred_reason,
        "boundary": "heavy_validation_gate_row_is_recommendation_only_no_execution",
    }


def _checks(
    *,
    pack: Mapping[str, Any],
    readiness: Mapping[str, Any],
    gate_matrix: Sequence[Mapping[str, Any]],
) -> list[dict[str, object]]:
    recommended = [row for row in gate_matrix if row.get("recommended_pending_operator_execution") is True]
    return [
        _check(
            "operator_review_pack_ready",
            readiness.get("operator_review_pack_ready") is True
            and readiness.get("candidate_ready_for_heavy_validation_review") is True,
            {
                "pack_status": pack.get("status"),
                "pack_decision_status": readiness.get("pack_decision_status"),
            },
        ),
        _check(
            "batch_replay_evidence_complete",
            _int(readiness.get("dtc1_sample_count")) >= 1
            and _int(readiness.get("dtc4_case_count")) >= 4
            and _float(readiness.get("dtc4_pass_ratio")) >= 1.0,
            {
                "dtc1_sample_count": readiness.get("dtc1_sample_count"),
                "dtc4_case_count": readiness.get("dtc4_case_count"),
                "dtc4_pass_ratio": readiness.get("dtc4_pass_ratio"),
            },
        ),
        _check(
            "risk_level_allows_heavy_validation_recommendation",
            _int(readiness.get("high_risk_count")) == 0,
            {
                "high_risk_count": readiness.get("high_risk_count"),
                "medium_risk_count": readiness.get("medium_risk_count"),
            },
        ),
        _check(
            "gate_recommendations_are_present_but_not_executed",
            {row.get("gate_id") for row in recommended} == {"dialogue_synthetic_all", "dialogue_518k_sample"}
            and all(row.get("run_triggered") is False for row in gate_matrix),
            {
                "recommended_gate_ids": [row.get("gate_id") for row in recommended],
                "run_triggered_count": sum(1 for row in gate_matrix if row.get("run_triggered") is True),
            },
        ),
        _check(
            "release_and_pointer_are_blocked",
            readiness.get("promotion_allowed") is False
            and readiness.get("policy_pointer_write_allowed") is False
            and readiness.get("chart_fact_mutation_allowed") is False
            and readiness.get("boundary_allows_promotion") is False,
            {
                "promotion_allowed": readiness.get("promotion_allowed"),
                "policy_pointer_write_allowed": readiness.get("policy_pointer_write_allowed"),
                "chart_fact_mutation_allowed": readiness.get("chart_fact_mutation_allowed"),
                "boundary_allows_promotion": readiness.get("boundary_allows_promotion"),
            },
        ),
    ]


def _check(check_id: str, passed: bool, observed: Mapping[str, object]) -> dict[str, object]:
    return {"check_id": check_id, "passed": bool(passed), "observed": dict(observed)}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


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
