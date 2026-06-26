from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
import json

from v30.validation.latent_attribute_admin_training_review import (
    FORBIDDEN_LATENT_TRAINING_SCOPE,
    run_latent_attribute_admin_training_review,
)
from v30.validation.latent_policy_observability import run_latent_policy_observability_readiness
from v30.validation.synthetic_case import run_synthetic_tier
from v30.validation.training_signals import extract_training_signals


LATENT_ATTRIBUTE_WORKFLOW_CLOSEOUT_VERSION = "v30.latent_attribute_workflow_closeout.v1"


def run_latent_attribute_workflow_closeout(
    *,
    closeout_id: str = "",
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    observability = run_latent_policy_observability_readiness(
        reading_id=closeout_id or "hf-r28-latent-attribute-workflow-closeout"
    )
    review = run_latent_attribute_admin_training_review(
        review_id=closeout_id or "hf-r28-latent-attribute-workflow-closeout"
    )
    suite = run_synthetic_tier("latent_bazi_divergence")
    signals = [signal.model_dump(mode="json") for signal in extract_training_signals(suite)]
    return build_latent_attribute_workflow_closeout(
        observability=observability,
        admin_training_review=review,
        latent_divergence_suite=suite.model_dump(mode="json"),
        training_signals=signals,
        ui_source=_ui_source_snapshot(),
        closeout_id=closeout_id,
        artifact_dir=artifact_dir,
    )


def build_latent_attribute_workflow_closeout(
    *,
    observability: Mapping[str, Any],
    admin_training_review: Mapping[str, Any],
    latent_divergence_suite: Mapping[str, Any],
    training_signals: list[Mapping[str, Any]],
    ui_source: Mapping[str, Any],
    closeout_id: str = "",
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    closed_at = datetime.now(timezone.utc)
    resolved_closeout_id = closeout_id or f"v30.hf.r28.{closed_at.strftime('%Y%m%d%H%M%S%f')}"
    latent_signal = _latent_signal(training_signals)
    checks = _checks(
        observability=observability,
        admin_training_review=admin_training_review,
        latent_divergence_suite=latent_divergence_suite,
        latent_signal=latent_signal,
        ui_source=ui_source,
    )
    decision = _decision(checks)
    payload: dict[str, Any] = {
        "version": LATENT_ATTRIBUTE_WORKFLOW_CLOSEOUT_VERSION,
        "closeout_id": resolved_closeout_id,
        "closed_at": closed_at.isoformat(),
        "status": "completed" if decision["closeout_ready"] else "blocked",
        "decision": decision,
        "source_summary": {
            "observability_version": str(observability.get("version") or ""),
            "observability_ready": _mapping(observability.get("decision")).get("readiness_ready") is True,
            "admin_review_version": str(admin_training_review.get("version") or ""),
            "admin_review_ready": _mapping(admin_training_review.get("decision")).get("review_ready") is True,
            "latent_divergence_suite_id": str(latent_divergence_suite.get("suite_id") or ""),
            "latent_divergence_passed": latent_divergence_suite.get("passed") is True,
            "latent_training_signal_present": bool(latent_signal),
            "ui_review_panel_present": ui_source.get("latent_review_panel_present") is True,
        },
        "workflow_summary": {
            "runtime_latent_attribute_update_validated": latent_divergence_suite.get("passed") is True,
            "training_routes": _str_list(_mapping(latent_signal.get("payload")).get("training_routes")),
            "blocked_training_routes": _str_list(_mapping(latent_signal.get("payload")).get("blocked_training_routes")),
            "admin_candidate_count": _mapping(admin_training_review.get("decision")).get("candidate_count", 0),
            "customer_policy_internals_hidden": _customer_policy_internals_hidden(observability),
            "admin_review_is_read_only": _admin_review_read_only(admin_training_review),
        },
        "checks": checks,
        "policy_boundary": {
            "closeout_only": True,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
            "live_llm_required": False,
            "boundary": "hf_r28_closes_latent_attribute_workflow_without_promoting_policy_or_mutating_chart_facts",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "latent_attribute_workflow_closeout_verifies_runtime_synthetic_training_admin_and_ui_surfaces",
    }
    if artifact_dir is not None:
        payload["artifact_uri"] = str(_write_artifact(payload, Path(artifact_dir)))
    return payload


def _checks(
    *,
    observability: Mapping[str, Any],
    admin_training_review: Mapping[str, Any],
    latent_divergence_suite: Mapping[str, Any],
    latent_signal: Mapping[str, Any],
    ui_source: Mapping[str, Any],
) -> list[dict[str, Any]]:
    obs_decision = _mapping(observability.get("decision"))
    review_decision = _mapping(admin_training_review.get("decision"))
    signal_payload = _mapping(latent_signal.get("payload"))
    review_summary = _mapping(admin_training_review.get("candidate_summary"))
    blocked_routes = set(_str_list(signal_payload.get("blocked_training_routes")))
    review_forbidden_scope = set(_str_list(review_summary.get("forbidden_training_scope")))
    training_routes = set(_str_list(signal_payload.get("training_routes")))
    return [
        {
            "check_id": "hf_r25_observability_ready",
            "passed": observability.get("version") == "v30.latent_policy_observability_readiness.v1"
            and obs_decision.get("readiness_ready") is True,
            "observed": {"version": observability.get("version"), "decision": obs_decision.get("decision_status")},
        },
        {
            "check_id": "latent_divergence_runtime_and_synthetic_ready",
            "passed": latent_divergence_suite.get("passed") is True
            and int(latent_divergence_suite.get("passed_count", 0) or 0) >= 2,
            "observed": {
                "suite_id": latent_divergence_suite.get("suite_id"),
                "passed": latent_divergence_suite.get("passed"),
                "passed_count": latent_divergence_suite.get("passed_count"),
                "case_count": latent_divergence_suite.get("case_count"),
            },
        },
        {
            "check_id": "latent_training_signal_routes_are_bounded",
            "passed": latent_signal.get("signal_id") == "v30.training_signal.latent_bazi_attribute_alignment"
            and {"latent_attribute_inference", "question_strategy", "individualized_projection"} <= training_routes
            and {"chart_facts", "calendar_conversion", "luck_cycle", "flow_timing"} <= blocked_routes
            and signal_payload.get("can_tune_chart_facts") is False
            and _int_value(signal_payload.get("chart_fact_mutation_allowed_count"), default=1) == 0,
            "observed": {
                "signal_id": latent_signal.get("signal_id"),
                "training_routes": sorted(training_routes),
                "blocked_training_routes": sorted(blocked_routes),
                "can_tune_chart_facts": signal_payload.get("can_tune_chart_facts"),
                "chart_fact_mutation_allowed_count": signal_payload.get("chart_fact_mutation_allowed_count"),
            },
        },
        {
            "check_id": "hf_r26_admin_review_ready_and_review_only",
            "passed": admin_training_review.get("version") == "v30.latent_attribute_admin_training_review.v1"
            and review_decision.get("review_ready") is True
            and _admin_review_read_only(admin_training_review),
            "observed": {
                "version": admin_training_review.get("version"),
                "decision": review_decision.get("decision_status"),
                "candidate_count": review_decision.get("candidate_count"),
                "policy_boundary": admin_training_review.get("policy_boundary", {}),
                "candidate_summary": admin_training_review.get("candidate_summary", {}),
            },
        },
        {
            "check_id": "customer_projection_hides_policy_internals",
            "passed": _customer_policy_internals_hidden(observability),
            "observed": _mapping(observability.get("observability")).get("customer_projection", {}),
        },
        {
            "check_id": "admin_training_ui_has_read_only_review_panel",
            "passed": ui_source.get("latent_review_panel_present") is True
            and ui_source.get("latent_review_endpoint_loaded") is True
            and ui_source.get("forbidden_apply_controls_present") is False,
            "observed": ui_source,
        },
        {
            "check_id": "closeout_keeps_core_bazi_facts_out_of_latent_training",
            "passed": {"chart_facts", "calendar_conversion", "luck_cycle", "flow_timing"} <= blocked_routes
            and FORBIDDEN_LATENT_TRAINING_SCOPE <= review_forbidden_scope
            and _admin_review_read_only(admin_training_review),
            "observed": {
                "forbidden_scope": sorted(FORBIDDEN_LATENT_TRAINING_SCOPE),
                "blocked_training_routes": sorted(blocked_routes),
                "review_forbidden_scope": sorted(review_forbidden_scope),
            },
        },
    ]


def _decision(checks: list[Mapping[str, Any]]) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if row.get("passed") is not True]
    ready = not failed
    return {
        "closeout_ready": ready,
        "decision_status": "hf_r28_latent_attribute_workflow_closeout_ready"
        if ready
        else "hf_r28_latent_attribute_workflow_closeout_blocked",
        "check_count": len(checks),
        "passed_check_count": len(checks) - len(failed),
        "failed_check_ids": failed,
        "rationale": (
            "Latent Bazi attributes are connected across runtime, synthetic validation, bounded training signals, Admin observability, and read-only review UI."
            if ready
            else "Repair the failed latent attribute workflow checks before treating HF-R2 as closed."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision.get("closeout_ready") is True:
        return {
            "task_id": "HF-S1",
            "title": "Latent Attribute Steady-State Watch",
            "scope": [
                "keep latent attribute training in review-only mode",
                "collect additional synthetic calibration evidence before policy promotion",
                "return mainline focus to core Bazi reading quality and synthetic calibration gates",
            ],
        }
    return {
        "task_id": "HF-R2.8-FIX",
        "title": "Repair Latent Attribute Workflow Closeout",
        "scope": ["repair failed runtime, synthetic, training, Admin, or UI closeout checks"],
    }


def _ui_source_snapshot() -> dict[str, Any]:
    path = Path("frontend/app.js")
    source = path.read_text(encoding="utf-8") if path.exists() else ""
    forbidden_terms = [
        "applyLatentTrainingCandidate",
        "promoteLatentPolicy",
        "latentPolicyPointerPromotion",
    ]
    return {
        "source_path": str(path),
        "source_exists": path.exists(),
        "latent_review_endpoint_loaded": "/api/v30/admin/training/latent-attribute-review" in source,
        "latent_review_panel_present": "renderLatentAttributeTrainingReview" in source
        and "隐藏属性训练候选审核" in source,
        "forbidden_apply_controls_present": any(term in source for term in forbidden_terms),
        "forbidden_terms_checked": forbidden_terms,
    }


def _admin_review_read_only(review: Mapping[str, Any]) -> bool:
    boundary = _mapping(review.get("policy_boundary"))
    summary = _mapping(review.get("candidate_summary"))
    return (
        boundary.get("review_only") is True
        and boundary.get("auto_apply_training_allowed") is False
        and boundary.get("policy_pointer_promotion_allowed") is False
        and boundary.get("chart_fact_mutation_allowed") is False
        and _int_value(summary.get("auto_apply_allowed_count"), default=1) == 0
        and _int_value(summary.get("pointer_promotion_allowed_count"), default=1) == 0
        and _int_value(summary.get("chart_fact_mutation_allowed_count"), default=1) == 0
    )


def _customer_policy_internals_hidden(observability: Mapping[str, Any]) -> bool:
    checks = observability.get("checks", [])
    if not isinstance(checks, list):
        return False
    return any(
        isinstance(row, Mapping)
        and row.get("check_id") == "customer_projection_hides_latent_policy_observability"
        and row.get("passed") is True
        for row in checks
    )


def _latent_signal(signals: list[Mapping[str, Any]]) -> Mapping[str, Any]:
    for signal in signals:
        if signal.get("signal_id") == "v30.training_signal.latent_bazi_attribute_alignment":
            return signal
    return {}


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _str_list(value: object) -> list[str]:
    return [str(row) for row in value] if isinstance(value, list) else []


def _int_value(value: object, *, default: int = 0) -> int:
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _write_artifact(payload: Mapping[str, Any], artifact_dir: Path) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = artifact_dir / f"{payload['closeout_id']}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
