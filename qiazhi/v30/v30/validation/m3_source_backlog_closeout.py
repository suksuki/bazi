from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v30.validation.m3_source_backlog_review_surface import run_m3_source_backlog_review_surface
from v30.validation.m3_training_candidate_review import run_m3_training_candidate_review
from v30.validation.synthetic_case import run_synthetic_tier


M3_SOURCE_BACKLOG_CLOSEOUT_VERSION = "v30.m3_source_backlog_closeout.v1"


def run_m3_source_backlog_closeout(
    *,
    sample_limit: int = 8,
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    training_review = run_m3_training_candidate_review(
        sample_limit=sample_limit,
        artifact_dir=artifact_dir,
    )
    backlog_surface = run_m3_source_backlog_review_surface(
        limit=50,
        artifact_dir=artifact_dir,
    )
    m3_synthetic = run_synthetic_tier("m3_core_spine").model_dump(mode="json")
    return build_m3_source_backlog_closeout(
        training_candidate_review=training_review,
        backlog_review_surface=backlog_surface,
        m3_synthetic=m3_synthetic,
        artifact_dir=artifact_dir,
    )


def build_m3_source_backlog_closeout(
    *,
    training_candidate_review: Mapping[str, Any],
    backlog_review_surface: Mapping[str, Any],
    m3_synthetic: Mapping[str, Any],
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    closed_at = datetime.now(timezone.utc)
    closeout_id = f"v30.m3.g6.{closed_at.strftime('%Y%m%d%H%M%S%f')}"
    training_summary = _training_summary(training_candidate_review)
    backlog_summary = _backlog_summary(backlog_review_surface)
    synthetic_summary = _synthetic_summary(m3_synthetic)
    checks = _checks(
        training_summary=training_summary,
        backlog_summary=backlog_summary,
        synthetic_summary=synthetic_summary,
    )
    decision = _decision(checks=checks, training_summary=training_summary, backlog_summary=backlog_summary)
    payload: dict[str, Any] = {
        "version": M3_SOURCE_BACKLOG_CLOSEOUT_VERSION,
        "closeout_id": closeout_id,
        "closed_at": closed_at.isoformat(),
        "status": "completed" if decision["m3_closeout_ready"] else "blocked",
        "decision": decision,
        "training_candidate_review_summary": training_summary,
        "backlog_review_surface_summary": backlog_summary,
        "m3_synthetic_summary": synthetic_summary,
        "closeout_checks": checks,
        "m3_steady_state": {
            "state": "steady_state_calibration" if decision["m3_steady_state_ready"] else "blocked",
            "source_backlog_flow_closed": decision["m3_closeout_ready"],
            "future_evidence_entrypoints": [
                "M3-G4 source backlog regeneration",
                "M3-G5 admin source backlog filters",
                "M3-G3 training candidate review",
                "m3_core_spine synthetic tier",
            ],
            "default_action": "monitor_and_add_source_governed_backlog_items_when_new_evidence_appears",
            "boundary": "m3_steady_state_keeps_future_calibration_open_without_reopening_core_runtime",
        },
        "policy_boundary": {
            "closeout_is_read_only": True,
            "runtime_decision_write_allowed": False,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "chart_fact_mutation_allowed": False,
            "fixed_bazi_verdict_allowed": False,
            "runtime_v20_import_allowed": False,
            "full_pytest_required": False,
            "full_518k_required": False,
            "boundary": "m3_g6_closeout_seals_source_backlog_flow_without_policy_or_chart_fact_mutation",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "m3_g6_closes_m3_source_backlog_flow_and_returns_m3_to_steady_calibration",
    }
    if artifact_dir is not None:
        payload["artifact_uri"] = str(_write_artifact(payload, Path(artifact_dir)))
    return payload


def _training_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    summary = _mapping(payload.get("candidate_summary"))
    source = _mapping(payload.get("source_summary"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "ready_for_training_review": bool(decision.get("ready_for_training_review")),
        "candidate_count": int(decision.get("candidate_count", 0) or summary.get("candidate_count", 0) or 0),
        "candidate_types": _string_list(summary.get("candidate_types")),
        "training_pipeline_passed": bool(source.get("training_pipeline_passed")),
        "has_518k_sample": bool(_mapping(source.get("validation_518k")).get("included")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "fixed_bazi_verdict_allowed": bool(decision.get("fixed_bazi_verdict_allowed")),
    }


def _backlog_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    summary = _mapping(payload.get("query_summary"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "ready_for_admin_review_surface": bool(decision.get("ready_for_admin_review_surface")),
        "row_count": int(decision.get("row_count", 0) or summary.get("row_count", 0) or 0),
        "backend": str(summary.get("backend") or ""),
        "target_domains": _string_list(summary.get("target_domains")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "fixed_bazi_verdict_allowed": bool(decision.get("fixed_bazi_verdict_allowed")),
        "runtime_v20_import_allowed": bool(decision.get("runtime_v20_import_allowed")),
    }


def _synthetic_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "suite_id": str(payload.get("suite_id") or ""),
        "passed": bool(payload.get("passed")),
        "case_count": int(payload.get("case_count", 0) or 0),
        "passed_count": int(payload.get("passed_count", 0) or 0),
        "failed_count": int(payload.get("failed_count", 0) or 0),
    }


def _checks(
    *,
    training_summary: Mapping[str, Any],
    backlog_summary: Mapping[str, Any],
    synthetic_summary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "check_id": "g3_training_candidate_review_ready",
            "passed": (
                training_summary["version"] == "v30.m3_training_candidate_review.v1"
                and training_summary["ready_for_training_review"]
                and training_summary["candidate_count"] >= 8
                and training_summary["training_pipeline_passed"]
                and training_summary["has_518k_sample"]
            ),
            "expected": "G3 training candidate review is ready with training pipeline and 518K sample evidence",
        },
        {
            "check_id": "g5_backlog_review_surface_ready",
            "passed": (
                backlog_summary["version"] == "v30.m3_source_backlog_review_surface.v1"
                and backlog_summary["ready_for_admin_review_surface"]
                and backlog_summary["row_count"] >= 6
            ),
            "expected": "G5 backlog review surface is ready with all source families visible",
        },
        {
            "check_id": "m3_core_synthetic_passed",
            "passed": (
                synthetic_summary["suite_id"] == "v30.synthetic.m3_core_spine"
                and synthetic_summary["passed"]
                and synthetic_summary["passed_count"] == synthetic_summary["case_count"]
                and synthetic_summary["case_count"] >= 8
            ),
            "expected": "M3 core synthetic tier passes",
        },
        {
            "check_id": "no_policy_or_chart_fact_mutation",
            "passed": (
                not training_summary["policy_pointer_promotion_allowed"]
                and not training_summary["chart_fact_mutation_allowed"]
                and not training_summary["fixed_bazi_verdict_allowed"]
                and not backlog_summary["policy_pointer_promotion_allowed"]
                and not backlog_summary["chart_fact_mutation_allowed"]
                and not backlog_summary["fixed_bazi_verdict_allowed"]
                and not backlog_summary["runtime_v20_import_allowed"]
            ),
            "expected": "G3/G5 remain read-only with no pointer, chart fact, fixed verdict, or V20 runtime import path",
        },
        {
            "check_id": "source_backlog_flow_connected",
            "passed": (
                "source_coverage_weight_candidate" in training_summary["candidate_types"]
                and bool(backlog_summary["backend"])
                and bool(backlog_summary["target_domains"])
            ),
            "expected": "training candidate review and admin backlog surface are connected through source coverage evidence",
        },
    ]


def _decision(
    *,
    checks: list[dict[str, Any]],
    training_summary: Mapping[str, Any],
    backlog_summary: Mapping[str, Any],
) -> dict[str, Any]:
    failed = [row["check_id"] for row in checks if not row["passed"]]
    ready = not failed
    return {
        "decision_status": "m3_g6_source_backlog_closeout_ready" if ready else "m3_g6_source_backlog_closeout_blocked",
        "m3_closeout_ready": ready,
        "m3_steady_state_ready": ready,
        "source_backlog_flow_closed": ready,
        "return_to_ranked_decision_hardening_ready": ready,
        "training_candidate_count": int(training_summary["candidate_count"]),
        "source_backlog_row_count": int(backlog_summary["row_count"]),
        "closeout_check_count": len(checks),
        "passed_closeout_check_count": sum(1 for row in checks if row["passed"]),
        "failed_closeout_check_ids": failed,
        "full_pytest_required": False,
        "full_518k_required": False,
        "policy_pointer_promotion_allowed": False,
        "pointer_write_performed": False,
        "chart_fact_mutation_allowed": False,
        "fixed_bazi_verdict_allowed": False,
        "runtime_v20_import_allowed": False,
        "blockers": ["m3_g6_closeout_checks_failed"] if failed else [],
        "rationale": (
            "M3 G1-G5 evidence is connected; source backlog flow can close and M3 can return to steady calibration."
            if ready
            else "M3 closeout is blocked until failed G6 checks are repaired."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["m3_closeout_ready"]:
        return {
            "next_task": "M5 Evidence Consumption Hardening",
            "reason": "M3 source backlog flow is closed; next consume the sealed M3 evidence spine in ranked decision hardening.",
            "full_pytest_required": False,
            "full_518k_required": False,
        }
    return {
        "next_task": "M3-G6 Remediation",
        "reason": "M3 closeout checks are blocked; repair G3/G5/M3 synthetic evidence before leaving M3.",
        "full_pytest_required": False,
            "full_518k_required": False,
    }


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(row) for row in value if str(row)]


def _write_artifact(payload: Mapping[str, Any], artifact_dir: Path) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = artifact_dir / f"{payload['closeout_id']}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
