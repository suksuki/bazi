from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v30.validation.m5_calibration_replay_review import (
    M5_REPLAY_SYNTHETIC_TIERS,
    run_m5_calibration_replay_review,
)
from v30.validation.m5_evidence_consumption_hardening import M5_DECISION_DOMAINS


M5_CALIBRATION_REPLAY_CLOSEOUT_VERSION = "v30.m5_calibration_replay_closeout.v1"


def run_m5_calibration_replay_closeout(
    *,
    sample_limit: int = 8,
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    replay_review = run_m5_calibration_replay_review(
        sample_limit=sample_limit,
        artifact_dir=artifact_dir,
    )
    return build_m5_calibration_replay_closeout(
        replay_review=replay_review,
        artifact_dir=artifact_dir,
    )


def build_m5_calibration_replay_closeout(
    *,
    replay_review: Mapping[str, Any],
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    closed_at = datetime.now(timezone.utc)
    closeout_id = f"v30.m5.h3.{closed_at.strftime('%Y%m%d%H%M%S%f')}"
    review_summary = _review_summary(replay_review)
    module_summary = _module_summary(replay_review)
    monitoring_baseline = _monitoring_baseline(review_summary, module_summary)
    closeout_checks = _closeout_checks(review_summary, module_summary)
    decision = _decision(
        review_summary=review_summary,
        module_summary=module_summary,
        closeout_checks=closeout_checks,
    )
    payload: dict[str, Any] = {
        "version": M5_CALIBRATION_REPLAY_CLOSEOUT_VERSION,
        "closeout_id": closeout_id,
        "closed_at": closed_at.isoformat(),
        "status": "completed" if decision["m5_calibration_replay_closed"] else "blocked",
        "decision": decision,
        "replay_review_summary": review_summary,
        "m5_module_summary": module_summary,
        "monitoring_baseline": monitoring_baseline,
        "closeout_checks": closeout_checks,
        "policy_boundary": {
            "ranked_candidates_only": True,
            "steady_state_support_module": decision["m5_calibration_replay_closed"],
            "threshold_change_allowed": False,
            "score_floor_change_allowed": False,
            "runtime_decision_write_allowed": False,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "chart_fact_mutation_allowed": False,
            "fixed_bazi_verdict_allowed": False,
            "raw_model_score_visible": False,
            "full_pytest_required": False,
            "full_518k_required": False,
            "boundary": "m5_h3_closes_calibration_replay_without_threshold_pointer_or_chart_fact_writes",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "m5_calibration_replay_closeout_marks_m5_as_steady_ranked_decision_support_when_checks_pass",
    }
    if artifact_dir is not None:
        payload["artifact_uri"] = str(_write_artifact(payload, Path(artifact_dir)))
    return payload


def _review_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    evidence = _mapping(payload.get("evidence_hardening_summary"))
    synthetic = _mapping(payload.get("synthetic_summary"))
    replay = _mapping(payload.get("ranked_decision_replay_summary"))
    training = _mapping(payload.get("training_signal_summary"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "m5_calibration_replay_review_ready": bool(decision.get("m5_calibration_replay_review_ready")),
        "ready_for_m5_calibration_replay_closeout": bool(decision.get("ready_for_m5_calibration_replay_closeout")),
        "ready_for_threshold_change": bool(decision.get("ready_for_threshold_change")),
        "ranked_observation_count": int(decision.get("ranked_observation_count", 0) or replay.get("ranked_observation_count", 0) or 0),
        "complete_domain_observation_count": int(decision.get("complete_domain_observation_count", 0) or replay.get("complete_domain_observation_count", 0) or 0),
        "close_candidate_count": int(decision.get("close_candidate_count", 0) or replay.get("close_candidate_count", 0) or 0),
        "passed_review_check_count": int(decision.get("passed_review_check_count", 0) or 0),
        "review_check_count": int(decision.get("review_check_count", 0) or 0),
        "m5_h1_ready": bool(evidence.get("m5_evidence_consumption_ready")),
        "m5_weight_replay_present": bool(training.get("m5_weight_replay_present")),
        "m5_weight_replay_boundary": str(training.get("m5_weight_replay_boundary") or ""),
        "synthetic_required_tier_count": int(synthetic.get("required_tier_count", 0) or 0),
        "synthetic_passed_tier_count": int(synthetic.get("passed_tier_count", 0) or 0),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "pointer_write_performed": bool(decision.get("pointer_write_performed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "fixed_bazi_verdict_allowed": bool(decision.get("fixed_bazi_verdict_allowed")),
        "threshold_write_performed": bool(decision.get("threshold_write_performed")),
    }


def _module_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    replay = _mapping(payload.get("ranked_decision_replay_summary"))
    synthetic = _mapping(payload.get("synthetic_summary"))
    top_gap_summary = _mapping(replay.get("top_gap_summary"))
    return {
        "module_id": "M5",
        "module_name": "Strength / structure / useful-god ranked decisions",
        "module_status": "steady_support_candidate",
        "decision_domains": list(M5_DECISION_DOMAINS),
        "domains_with_primary_candidates": _list(replay.get("domains_with_primary_candidates")),
        "domains_with_candidate_scores": _list(replay.get("domains_with_candidate_scores")),
        "ranked_observation_count": int(replay.get("ranked_observation_count", 0) or 0),
        "complete_domain_observation_count": int(replay.get("complete_domain_observation_count", 0) or 0),
        "close_candidate_count": int(replay.get("close_candidate_count", 0) or 0),
        "top_gap_summary": dict(top_gap_summary),
        "basis_signal_counts": dict(_mapping(replay.get("basis_signal_counts"))),
        "required_synthetic_tiers": list(M5_REPLAY_SYNTHETIC_TIERS),
        "synthetic_case_count_total": int(synthetic.get("case_count_total", 0) or 0),
        "m6_consumption_ready": True,
        "iq_question_strategy_consumption_ready": True,
        "training_consumption_ready": True,
        "threshold_review_deferred": True,
        "boundary": "m5_outputs_ranked_candidate_support_for_downstream_reading_not_fixed_bazi_conclusions",
    }


def _monitoring_baseline(
    review_summary: Mapping[str, Any],
    module_summary: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "monitoring_id": "m5_ranked_decision_steady_state_monitoring",
        "recommended_trigger": "before_release_or_after_new_real_case_pack",
        "commands": [
            "python3 scripts/run_m5_calibration_replay_closeout.py --sample-limit 8",
            "python3 scripts/run_synthetic_validation.py --tier m5_ranked_decision_contract",
            "python3 scripts/run_synthetic_validation.py --tier real_case_calibration_pack",
        ],
        "watched_metrics": {
            "ranked_observation_count": int(review_summary.get("ranked_observation_count", 0) or 0),
            "complete_domain_observation_count": int(review_summary.get("complete_domain_observation_count", 0) or 0),
            "close_candidate_count": int(review_summary.get("close_candidate_count", 0) or 0),
            "decision_domains": _list(module_summary.get("decision_domains")),
            "basis_signal_counts": dict(_mapping(module_summary.get("basis_signal_counts"))),
        },
        "full_pytest_required": False,
        "full_518k_required": False,
        "threshold_review_deferred": True,
        "boundary": "monitoring_tracks_m5_replay_drift_without_runtime_weight_or_threshold_writes",
    }


def _closeout_checks(
    review_summary: Mapping[str, Any],
    module_summary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "check_id": "m5_h2_replay_review_ready",
            "passed": (
                review_summary["version"] == "v30.m5_calibration_replay_review.v1"
                and review_summary["m5_calibration_replay_review_ready"]
                and review_summary["ready_for_m5_calibration_replay_closeout"]
                and review_summary["passed_review_check_count"] == review_summary["review_check_count"]
            ),
            "expected": "M5-H2 replay review is ready for closeout",
        },
        {
            "check_id": "m5_h1_h2_lineage_complete",
            "passed": (
                review_summary["m5_h1_ready"]
                and review_summary["synthetic_passed_tier_count"] == review_summary["synthetic_required_tier_count"]
                and review_summary["synthetic_required_tier_count"] == len(M5_REPLAY_SYNTHETIC_TIERS)
            ),
            "expected": "M5-H1 and all H2 replay tiers are present",
        },
        {
            "check_id": "m5_ranked_decision_domains_steady",
            "passed": (
                set(module_summary["domains_with_primary_candidates"]) == set(M5_DECISION_DOMAINS)
                and set(module_summary["domains_with_candidate_scores"]) == set(M5_DECISION_DOMAINS)
                and module_summary["ranked_observation_count"] >= 30
                and module_summary["complete_domain_observation_count"] >= 30
            ),
            "expected": "strength, structure-pattern, and useful-god have steady ranked replay coverage",
        },
        {
            "check_id": "m5_training_signal_boundary_locked",
            "passed": (
                review_summary["m5_weight_replay_present"]
                and review_summary["m5_weight_replay_boundary"] == "m5_weight_replay_trains_candidate_weights_not_chart_facts"
            ),
            "expected": "M5 training signal can tune candidate weights only, never chart facts",
        },
        {
            "check_id": "m5_close_candidate_monitoring_ready",
            "passed": (
                module_summary["close_candidate_count"] >= 1
                and bool(_mapping(module_summary["basis_signal_counts"]))
                and review_summary["ready_for_threshold_change"] is False
            ),
            "expected": "close candidates are monitored, while threshold changes remain deferred",
        },
        {
            "check_id": "m5_no_write_boundary_preserved",
            "passed": (
                not review_summary["policy_pointer_promotion_allowed"]
                and not review_summary["pointer_write_performed"]
                and not review_summary["chart_fact_mutation_allowed"]
                and not review_summary["fixed_bazi_verdict_allowed"]
                and not review_summary["threshold_write_performed"]
            ),
            "expected": "no pointer, threshold, fixed-verdict, or chart-fact write occurred",
        },
    ]


def _decision(
    *,
    review_summary: Mapping[str, Any],
    module_summary: Mapping[str, Any],
    closeout_checks: list[dict[str, Any]],
) -> dict[str, Any]:
    failed = [row["check_id"] for row in closeout_checks if not row["passed"]]
    ready = not failed
    return {
        "decision_status": "m5_calibration_replay_closed" if ready else "m5_calibration_replay_closeout_blocked",
        "m5_calibration_replay_closed": ready,
        "m5_ranked_decision_steady_support_ready": ready,
        "m5_ready_for_m6_consumption": ready and bool(module_summary.get("m6_consumption_ready")),
        "m5_ready_for_iq_consumption": ready and bool(module_summary.get("iq_question_strategy_consumption_ready")),
        "m5_ready_for_training_consumption": ready and bool(module_summary.get("training_consumption_ready")),
        "threshold_review_deferred": True,
        "threshold_change_allowed": False,
        "score_floor_change_allowed": False,
        "closeout_check_count": len(closeout_checks),
        "passed_closeout_check_count": sum(1 for row in closeout_checks if row["passed"]),
        "failed_closeout_check_ids": failed,
        "ranked_observation_count": int(review_summary.get("ranked_observation_count", 0) or 0),
        "complete_domain_observation_count": int(review_summary.get("complete_domain_observation_count", 0) or 0),
        "close_candidate_count": int(review_summary.get("close_candidate_count", 0) or 0),
        "policy_pointer_promotion_allowed": False,
        "pointer_write_performed": False,
        "chart_fact_mutation_allowed": False,
        "fixed_bazi_verdict_allowed": False,
        "full_pytest_required": False,
        "full_518k_required": False,
        "blockers": ["m5_calibration_replay_closeout_checks_failed"] if failed else [],
        "rationale": (
            "M5-H1/H2 are complete; M5 can serve M6/IQ/training as a ranked-candidate support module with threshold review deferred."
            if ready
            else "M5 cannot close until the failed closeout checks are resolved."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["m5_calibration_replay_closed"]:
        return {
            "next_task": "M6 Practical Reading Consumption Hardening",
            "reason": "M5 is closed as ranked-decision support; next verify M6 consumes M1-M5 evidence cleanly in customer-facing readings.",
            "full_pytest_required": False,
            "full_518k_required": False,
        }
    return {
        "next_task": "M5 Calibration Replay Closeout Remediation",
        "reason": "M5 closeout checks failed; repair H2 lineage, replay coverage, training signal boundary, or write guards before moving downstream.",
            "full_pytest_required": False,
            "full_518k_required": False,
    }


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _write_artifact(payload: Mapping[str, Any], artifact_dir: Path) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = artifact_dir / f"{payload['closeout_id']}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
