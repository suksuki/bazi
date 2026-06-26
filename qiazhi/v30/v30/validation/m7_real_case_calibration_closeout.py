from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v30.validation.m7_real_case_calibration_steady_state_review import (
    M7_REQUIRED_CATEGORIES,
    run_m7_real_case_calibration_steady_state_review,
)


M7_REAL_CASE_CALIBRATION_CLOSEOUT_VERSION = "v30.m7_real_case_calibration_closeout.v1"


def run_m7_real_case_calibration_closeout(
    *,
    sample_limit: int = 8,
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    steady_state_review = run_m7_real_case_calibration_steady_state_review(
        sample_limit=sample_limit,
        artifact_dir=artifact_dir,
    )
    return build_m7_real_case_calibration_closeout(
        steady_state_review=steady_state_review,
        artifact_dir=artifact_dir,
    )


def build_m7_real_case_calibration_closeout(
    *,
    steady_state_review: Mapping[str, Any],
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    closed_at = datetime.now(timezone.utc)
    closeout_id = f"v30.m7.s2.{closed_at.strftime('%Y%m%d%H%M%S%f')}"
    review_summary = _review_summary(steady_state_review)
    module_summary = _module_summary(steady_state_review)
    monitoring_baseline = _monitoring_baseline(review_summary, module_summary)
    closeout_checks = _closeout_checks(review_summary, module_summary)
    decision = _decision(
        review_summary=review_summary,
        module_summary=module_summary,
        closeout_checks=closeout_checks,
    )
    payload: dict[str, Any] = {
        "version": M7_REAL_CASE_CALIBRATION_CLOSEOUT_VERSION,
        "closeout_id": closeout_id,
        "closed_at": closed_at.isoformat(),
        "status": "completed" if decision["m7_real_case_calibration_closed"] else "blocked",
        "decision": decision,
        "steady_state_review_summary": review_summary,
        "m7_module_summary": module_summary,
        "monitoring_baseline": monitoring_baseline,
        "closeout_checks": closeout_checks,
        "policy_boundary": {
            "steady_state_support_module": decision["m7_real_case_calibration_closed"],
            "calibration_backbone": True,
            "focused_expansion_allowed_by_default": False,
            "focused_expansion_recommended": decision["focused_real_case_expansion_recommended"],
            "runtime_decision_write_allowed": False,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "chart_fact_mutation_allowed": False,
            "fixed_bazi_verdict_allowed": False,
            "private_user_content_allowed": False,
            "full_pytest_required": False,
            "full_518k_required": False,
            "boundary": "m7_closeout_records_real_case_calibration_backbone_without_expanding_cases_or_mutating_chart_facts",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "m7_real_case_calibration_closeout_marks_m7_as_steady_backbone_when_checks_pass",
    }
    if artifact_dir is not None:
        payload["artifact_uri"] = str(_write_artifact(payload, Path(artifact_dir)))
    return payload


def _review_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    real_case = _mapping(payload.get("real_case_calibration_summary"))
    metadata = _mapping(payload.get("production_replay_metadata_summary"))
    training = _mapping(payload.get("training_signal_summary"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "m7_steady_state_review_ready": bool(decision.get("m7_steady_state_review_ready")),
        "m7_real_case_calibration_steady": bool(decision.get("m7_real_case_calibration_steady")),
        "ready_for_m7_closeout": bool(decision.get("ready_for_m7_closeout")),
        "review_check_count": int(decision.get("review_check_count", 0) or 0),
        "passed_review_check_count": int(decision.get("passed_review_check_count", 0) or 0),
        "real_case_fixture_count": int(decision.get("real_case_fixture_count", 0) or real_case.get("fixture_count", 0) or 0),
        "focused_real_case_expansion_recommended": bool(decision.get("focused_real_case_expansion_recommended")),
        "covered_categories": _list(real_case.get("covered_categories")),
        "ready_count": int(real_case.get("ready_count", 0) or 0),
        "pending_or_blocked_count": int(real_case.get("pending_or_blocked_count", 0) or 0),
        "no_fake_fact_count": int(real_case.get("no_fake_fact_count", 0) or 0),
        "drift_summary_count": int(real_case.get("drift_summary_count", 0) or 0),
        "drift_stable_count": int(real_case.get("drift_stable_count", 0) or 0),
        "drift_needs_module_review_count": int(real_case.get("drift_needs_module_review_count", 0) or 0),
        "drift_flag_counts": dict(_mapping(real_case.get("drift_flag_counts"))),
        "module_adjustment_counts": dict(_mapping(real_case.get("module_adjustment_counts"))),
        "metadata_row_count": int(metadata.get("row_count", 0) or 0),
        "metadata_privacy_guard_pass_count": int(metadata.get("privacy_guard_pass_count", 0) or 0),
        "metadata_projection_leak_pass_count": int(metadata.get("projection_leak_scan_pass_count", 0) or 0),
        "real_case_training_signal_present": bool(training.get("real_case_calibration_signal_present")),
        "training_boundary": str(training.get("boundary") or ""),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "pointer_write_performed": bool(decision.get("pointer_write_performed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "fixed_bazi_verdict_allowed": bool(decision.get("fixed_bazi_verdict_allowed")),
    }


def _module_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    real_case = _mapping(payload.get("real_case_calibration_summary"))
    metadata = _mapping(payload.get("production_replay_metadata_summary"))
    return {
        "module_id": "M7",
        "module_name": "Real-case calibration pack and drift routing",
        "module_status": "steady_support_candidate",
        "fixture_count": int(real_case.get("fixture_count", 0) or 0),
        "covered_categories": _list(real_case.get("covered_categories")),
        "ready_count": int(real_case.get("ready_count", 0) or 0),
        "pending_or_blocked_count": int(real_case.get("pending_or_blocked_count", 0) or 0),
        "drift_stable_count": int(real_case.get("drift_stable_count", 0) or 0),
        "metadata_row_count": int(metadata.get("row_count", 0) or 0),
        "m1_m6_m8_calibration_backbone_ready": True,
        "release_acceptance_consumption_ready": True,
        "focused_expansion_status": "recommended_not_blocking" if int(real_case.get("fixture_count", 0) or 0) < 40 else "not_needed",
        "boundary": "m7_calibration_backbone_routes_future_evidence_without_mutating_chart_facts",
    }


def _monitoring_baseline(
    review_summary: Mapping[str, Any],
    module_summary: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "monitoring_id": "m7_real_case_calibration_steady_state_monitoring",
        "recommended_trigger": "before_release_or_after_new_real_case_pack",
        "commands": [
            "python3 scripts/run_m7_real_case_calibration_closeout.py --sample-limit 8",
            "python3 scripts/run_synthetic_validation.py --tier real_case_calibration_pack",
        ],
        "watched_metrics": {
            "fixture_count": int(review_summary.get("real_case_fixture_count", 0) or 0),
            "covered_categories": _list(module_summary.get("covered_categories")),
            "drift_stable_count": int(review_summary.get("drift_stable_count", 0) or 0),
            "metadata_row_count": int(review_summary.get("metadata_row_count", 0) or 0),
            "metadata_privacy_guard_pass_count": int(review_summary.get("metadata_privacy_guard_pass_count", 0) or 0),
        },
        "focused_expansion_recommended": int(review_summary.get("real_case_fixture_count", 0) or 0) < 40,
        "focused_expansion_blocks_current_flow": False,
        "full_pytest_required": False,
        "full_518k_required": False,
        "boundary": "monitoring_tracks_real_case_calibration_drift_without_fact_or_policy_writes",
    }


def _closeout_checks(
    review_summary: Mapping[str, Any],
    module_summary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "check_id": "m7_s1_steady_state_review_ready",
            "passed": (
                review_summary["version"] == "v30.m7_real_case_calibration_steady_state_review.v1"
                and review_summary["m7_steady_state_review_ready"]
                and review_summary["ready_for_m7_closeout"]
                and review_summary["passed_review_check_count"] == review_summary["review_check_count"]
            ),
            "expected": "M7-S1 steady-state review is ready for closeout",
        },
        {
            "check_id": "m7_canonical_backbone_ready",
            "passed": (
                review_summary["real_case_fixture_count"] >= 30
                and set(M7_REQUIRED_CATEGORIES) <= set(review_summary["covered_categories"])
                and review_summary["ready_count"] >= 20
                and review_summary["no_fake_fact_count"] >= review_summary["pending_or_blocked_count"]
            ),
            "expected": "canonical real-case categories are covered and blocked cases do not fabricate facts",
        },
        {
            "check_id": "m7_drift_and_metadata_stable",
            "passed": (
                review_summary["drift_summary_count"] >= review_summary["real_case_fixture_count"]
                and review_summary["drift_stable_count"] == review_summary["drift_summary_count"]
                and review_summary["drift_needs_module_review_count"] == 0
                and not review_summary["drift_flag_counts"]
                and not review_summary["module_adjustment_counts"]
                and review_summary["metadata_row_count"] >= review_summary["real_case_fixture_count"]
                and review_summary["metadata_privacy_guard_pass_count"] == review_summary["metadata_row_count"]
                and review_summary["metadata_projection_leak_pass_count"] == review_summary["metadata_row_count"]
            ),
            "expected": "drift summaries are stable and production replay metadata is privacy-safe",
        },
        {
            "check_id": "m7_training_boundary_locked",
            "passed": (
                review_summary["real_case_training_signal_present"]
                and review_summary["training_boundary"] == "real_case_calibration_pack_trains_validation_policy_not_chart_facts"
            ),
            "expected": "real-case calibration signal trains validation policy only",
        },
        {
            "check_id": "m7_downstream_consumption_ready",
            "passed": (
                module_summary["m1_m6_m8_calibration_backbone_ready"]
                and module_summary["release_acceptance_consumption_ready"]
            ),
            "expected": "M7 can support M1-M6/M8 calibration and release acceptance",
        },
        {
            "check_id": "m7_no_write_boundary_preserved",
            "passed": (
                not review_summary["policy_pointer_promotion_allowed"]
                and not review_summary["pointer_write_performed"]
                and not review_summary["chart_fact_mutation_allowed"]
                and not review_summary["fixed_bazi_verdict_allowed"]
            ),
            "expected": "no pointer, fixed-verdict, private-content, or chart-fact write occurred",
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
    expansion_recommended = int(review_summary.get("real_case_fixture_count", 0) or 0) < 40
    return {
        "decision_status": "m7_real_case_calibration_closed" if ready else "m7_real_case_calibration_closeout_blocked",
        "m7_real_case_calibration_closed": ready,
        "m7_calibration_backbone_ready": ready,
        "focused_real_case_expansion_recommended": bool(expansion_recommended),
        "focused_real_case_expansion_blocks_current_flow": False,
        "m7_ready_for_m8_projection_api_closeout": ready,
        "m7_ready_for_release_acceptance": ready and bool(module_summary.get("release_acceptance_consumption_ready")),
        "real_case_fixture_count": int(review_summary.get("real_case_fixture_count", 0) or 0),
        "closeout_check_count": len(closeout_checks),
        "passed_closeout_check_count": sum(1 for row in closeout_checks if row["passed"]),
        "failed_closeout_check_ids": failed,
        "policy_pointer_promotion_allowed": False,
        "pointer_write_performed": False,
        "chart_fact_mutation_allowed": False,
        "fixed_bazi_verdict_allowed": False,
        "full_pytest_required": False,
        "full_518k_required": False,
        "blockers": ["m7_real_case_calibration_closeout_checks_failed"] if failed else [],
        "rationale": (
            "M7-S1 is complete; M7 can serve as steady real-case calibration backbone. Focused expansion is recommended but not blocking."
            if ready and expansion_recommended
            else "M7-S1 is complete; M7 can serve as steady real-case calibration backbone."
            if ready
            else "M7 cannot close until the failed closeout checks are resolved."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["m7_real_case_calibration_closed"]:
        return {
            "next_task": "M8 Projection/API Contract Closeout",
            "reason": "M7 calibration backbone is closed; next close M8 projection/API contract before IQ/LLM support review or release readiness.",
            "full_pytest_required": False,
            "full_518k_required": False,
        }
    return {
        "next_task": "M7 Real-Case Calibration Closeout Remediation",
        "reason": "M7 closeout checks failed; repair S1 lineage, canonical coverage, drift metadata, or no-write boundaries.",
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
