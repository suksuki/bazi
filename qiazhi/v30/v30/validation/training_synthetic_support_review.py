from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v30.validation.corpus_518k import run_518k_validation
from v30.validation.llm_bazi_expression_support_review import run_llm_bazi_expression_support_review
from v30.validation.synthetic_case import run_synthetic_tier
from v30.validation.synthetic_coverage_manifest import run_synthetic_coverage_manifest
from v30.validation.training_signals import extract_training_signals


TRAINING_SYNTHETIC_SUPPORT_REVIEW_VERSION = "v30.training_synthetic_support_review.v1"


def run_training_synthetic_support_review(
    *,
    sample_limit: int = 8,
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    llm_support = run_llm_bazi_expression_support_review(
        sample_limit=sample_limit,
        artifact_dir=artifact_dir,
    )
    training_pipeline = run_synthetic_tier("training_pipeline")
    training_payload = training_pipeline.model_dump(mode="json")
    training_payload["training_signals"] = [
        signal.model_dump(mode="json") for signal in extract_training_signals(training_pipeline)
    ]
    manifest = run_synthetic_coverage_manifest()
    sample_518k = run_518k_validation(mode="sample", limit=sample_limit, artifact_dir=artifact_dir)
    return build_training_synthetic_support_review(
        llm_support=llm_support,
        training_pipeline=training_payload,
        synthetic_manifest=manifest,
        sample_518k=sample_518k.model_dump(mode="json"),
        artifact_dir=artifact_dir,
    )


def build_training_synthetic_support_review(
    *,
    llm_support: Mapping[str, Any],
    training_pipeline: Mapping[str, Any],
    synthetic_manifest: Mapping[str, Any],
    sample_518k: Mapping[str, Any],
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    reviewed_at = datetime.now(timezone.utc)
    review_id = f"v30.bt.s1.{reviewed_at.strftime('%Y%m%d%H%M%S%f')}"
    llm_summary = _llm_summary(llm_support)
    training_summary = _training_summary(training_pipeline)
    signal_summary = _signal_summary(training_pipeline)
    manifest_summary = _manifest_summary(synthetic_manifest)
    sample_summary = _sample_518k_summary(sample_518k)
    checks = _checks(
        llm_summary=llm_summary,
        training_summary=training_summary,
        signal_summary=signal_summary,
        manifest_summary=manifest_summary,
        sample_summary=sample_summary,
    )
    decision = _decision(checks, training_summary, signal_summary, sample_summary)
    payload: dict[str, Any] = {
        "version": TRAINING_SYNTHETIC_SUPPORT_REVIEW_VERSION,
        "review_id": review_id,
        "reviewed_at": reviewed_at.isoformat(),
        "status": "completed" if decision["training_synthetic_support_ready"] else "blocked",
        "decision": decision,
        "llm_support_summary": llm_summary,
        "training_pipeline_summary": training_summary,
        "training_signal_summary": signal_summary,
        "synthetic_manifest_summary": manifest_summary,
        "corpus_518k_sample_summary": sample_summary,
        "checks": checks,
        "policy_boundary": {
            "support_system_review_is_read_only": True,
            "training_signal_may_tune_policies": True,
            "training_signal_may_tune_expression": True,
            "training_signal_may_tune_projection": True,
            "training_signal_may_tune_question_strategy": True,
            "training_signal_may_tune_chart_facts": False,
            "runtime_decision_write_allowed": False,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "chart_fact_mutation_allowed": False,
            "fixed_bazi_verdict_allowed": False,
            "synthetic_all_required": False,
            "full_pytest_required": False,
            "full_518k_required": False,
            "boundary": "training_synthetic_support_review_validates_support_systems_without_fact_or_pointer_writes",
        },
        "monitoring_baseline": _monitoring_baseline(training_summary, sample_summary),
        "next_mainline_selection": _next_selection(decision),
        "boundary": "training_synthetic_support_review_validates_training_synthetic_518k_sample_after_llm_support",
    }
    if artifact_dir is not None:
        payload["artifact_uri"] = str(_write_artifact(payload, Path(artifact_dir)))
    return payload


def _llm_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "llm_bazi_expression_support_ready": bool(decision.get("llm_bazi_expression_support_ready")),
        "bazi_llm_acceptance_case_count": int(decision.get("bazi_llm_acceptance_case_count", 0) or 0),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "live_llm_required": bool(decision.get("live_llm_required")),
        "full_pytest_required": bool(decision.get("full_pytest_required")),
        "full_518k_required": bool(decision.get("full_518k_required")),
    }


def _training_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "suite_id": str(payload.get("suite_id") or ""),
        "passed": bool(payload.get("passed")),
        "case_count": int(payload.get("case_count", 0) or 0),
        "passed_count": int(payload.get("passed_count", 0) or 0),
        "failed_count": int(payload.get("failed_count", 0) or 0),
        "boundary": "training_pipeline_reviews_signal_candidate_validation_boundaries_not_chart_facts",
    }


def _signal_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    signals = [_mapping(row) for row in _list(payload.get("training_signals")) if _mapping(row).get("signal_id")]
    signal_ids = {str(row.get("signal_id") or "") for row in signals}
    domains = {str(row.get("domain") or "") for row in signals if row.get("domain")}
    payloads = [_mapping(row.get("payload")) for row in signals]
    can_tune_chart_facts = [
        row for row in payloads
        if row.get("can_tune_chart_facts") is True
        or int(row.get("chart_fact_mutation_allowed_count", 0) or 0) > 0
    ]
    required = {
        "v30.training_signal.krp_unit_coverage",
        "v30.training_signal.m3_core_spine_coverage",
        "v30.training_signal.birth_chart_conversion_boundary",
        "v30.training_signal.ten_god_energy_fusion",
        "v30.training_signal.ranked_decision_fusion",
        "v30.training_signal.practical_reading_quality",
        "v30.training_signal.api_projection_contract",
        "v30.training_signal.interaction_loop_quality",
        "v30.training_signal.question_model_signal_personalization",
        "v30.training_signal.real_case_calibration_pack",
    }
    return {
        "signal_count": len(signals),
        "signal_ids": sorted(signal_ids),
        "domain_count": len(domains),
        "domains": sorted(domains),
        "required_signal_count": len(required),
        "required_signal_present_count": len(required & signal_ids),
        "missing_required_signals": sorted(required - signal_ids),
        "chart_fact_tuning_signal_count": len(can_tune_chart_facts),
        "policy_or_expression_domains_present": bool({"policy_tuning", "question_intelligence", "expression", "llm", "presentation"} & domains),
        "core_module_domains_present": bool({"core_calculation", "m3_core_spine", "ten_god_energy", "ranked_decision", "practical_reading"} & domains),
        "boundary": "training_signals_tune_support_policies_and_expression_not_deterministic_chart_facts",
    }


def _manifest_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    summary = _mapping(payload.get("summary"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "synthetic_coverage_manifest_ready": bool(decision.get("synthetic_coverage_manifest_ready")),
        "synthetic_completion": int(decision.get("synthetic_completion", 0) or 0),
        "implemented_tier_count": int(summary.get("implemented_tier_count", 0) or 0),
        "implemented_case_count": int(summary.get("implemented_case_count", 0) or 0),
        "major_node_only_tiers": _list(summary.get("major_node_only_tiers")),
        "full_pytest_required": bool(decision.get("full_pytest_required")),
        "full_518k_required": bool(decision.get("full_518k_required")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
    }


def _sample_518k_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    coverage = _mapping(payload.get("coverage_metrics"))
    drift = _mapping(payload.get("drift_metrics"))
    return {
        "run_id": str(payload.get("run_id") or ""),
        "mode": str(payload.get("mode") or ""),
        "case_count": int(payload.get("case_count", 0) or 0),
        "promotion_signal": str(payload.get("promotion_signal") or ""),
        "failure_cluster_count": len(_list(payload.get("failure_clusters"))),
        "artifact_record_id": str(payload.get("artifact_record_id") or ""),
        "artifact_search_backend": str(payload.get("artifact_search_backend") or ""),
        "artifact_searchable": bool(payload.get("artifact_searchable")),
        "question_recommendation_coverage": int(coverage.get("question_recommendation_coverage", 0) or 0),
        "model_signal_summary_coverage": int(coverage.get("model_signal_summary_coverage", 0) or 0),
        "interaction_state_coverage": int(coverage.get("interaction_state_coverage", 0) or 0),
        "visible_internal_next_question_split_count": int(coverage.get("visible_internal_next_question_split_count", 0) or 0),
        "calibration_probe_user_visible_count": int(coverage.get("calibration_probe_user_visible_count", 0) or 0),
        "unsupported_question_rate": float(drift.get("unsupported_question_rate", 1.0) or 0.0),
        "missing_model_signal_summary_rate": float(drift.get("missing_model_signal_summary_rate", 1.0) or 0.0),
        "missing_interaction_state_rate": float(drift.get("missing_interaction_state_rate", 1.0) or 0.0),
        "calibration_probe_user_visible_rate": float(drift.get("calibration_probe_user_visible_rate", 1.0) or 0.0),
        "boundary": "518k_sample_is_distribution_evidence_not_full_corpus_or_pointer_promotion",
    }


def _checks(
    *,
    llm_summary: Mapping[str, Any],
    training_summary: Mapping[str, Any],
    signal_summary: Mapping[str, Any],
    manifest_summary: Mapping[str, Any],
    sample_summary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "check_id": "llm_support_ready_before_training_review",
            "passed": (
                llm_summary["version"] == "v30.llm_bazi_expression_support_review.v1"
                and llm_summary["llm_bazi_expression_support_ready"]
                and llm_summary["bazi_llm_acceptance_case_count"] >= 5
                and not llm_summary["chart_fact_mutation_allowed"]
                and not llm_summary["policy_pointer_promotion_allowed"]
            ),
            "expected": "LLM-S1 is ready before training/synthetic support review",
        },
        {
            "check_id": "training_pipeline_synthetic_ready",
            "passed": (
                training_summary["suite_id"] == "v30.synthetic.training_pipeline"
                and training_summary["passed"]
                and training_summary["case_count"] == training_summary["passed_count"]
                and training_summary["case_count"] >= 90
                and training_summary["failed_count"] == 0
            ),
            "expected": "training_pipeline synthetic tier passes with broad support coverage",
        },
        {
            "check_id": "training_signal_coverage_ready",
            "passed": (
                signal_summary["signal_count"] >= 30
                and signal_summary["domain_count"] >= 8
                and signal_summary["required_signal_present_count"] == signal_summary["required_signal_count"]
                and not signal_summary["missing_required_signals"]
                and signal_summary["policy_or_expression_domains_present"]
                and signal_summary["core_module_domains_present"]
            ),
            "expected": "training signals cover core modules, projection, question, expression, LLM, and real-case calibration",
        },
        {
            "check_id": "training_cannot_tune_chart_facts",
            "passed": signal_summary["chart_fact_tuning_signal_count"] == 0,
            "expected": "no extracted training signal can tune deterministic chart facts",
        },
        {
            "check_id": "synthetic_manifest_ready_and_heavy_tiers_explicit",
            "passed": (
                manifest_summary["version"] == "v30.synthetic_coverage_manifest.v1"
                and manifest_summary["synthetic_coverage_manifest_ready"]
                and manifest_summary["synthetic_completion"] >= 99
                and manifest_summary["implemented_tier_count"] >= 20
                and "all" in manifest_summary["major_node_only_tiers"]
                and not manifest_summary["full_pytest_required"]
                and not manifest_summary["full_518k_required"]
                and not manifest_summary["chart_fact_mutation_allowed"]
            ),
            "expected": "synthetic manifest is ready and synthetic-all/full-518K remain explicit",
        },
        {
            "check_id": "518k_sample_distribution_ready",
            "passed": (
                sample_summary["mode"] == "sample"
                and sample_summary["case_count"] >= 8
                and sample_summary["promotion_signal"] == "eligible"
                and sample_summary["failure_cluster_count"] == 0
                and sample_summary["question_recommendation_coverage"] >= sample_summary["case_count"]
                and sample_summary["model_signal_summary_coverage"] >= sample_summary["case_count"]
                and sample_summary["interaction_state_coverage"] >= sample_summary["case_count"]
                and sample_summary["visible_internal_next_question_split_count"] >= sample_summary["case_count"]
                and sample_summary["calibration_probe_user_visible_count"] == 0
            ),
            "expected": "518K sample gives lightweight distribution evidence without visible calibration leaks",
        },
        {
            "check_id": "support_review_no_write_or_heavy_default",
            "passed": True,
            "expected": "review does not promote pointers, run synthetic all, run full pytest, or run full 518K by default",
        },
    ]


def _decision(
    checks: list[Mapping[str, Any]],
    training_summary: Mapping[str, Any],
    signal_summary: Mapping[str, Any],
    sample_summary: Mapping[str, Any],
) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if row.get("passed") is not True]
    ready = not failed
    return {
        "decision_status": "training_synthetic_support_ready" if ready else "training_synthetic_support_blocked",
        "training_synthetic_support_ready": ready,
        "training_pipeline_case_count": int(training_summary.get("case_count", 0) or 0),
        "training_signal_count": int(signal_summary.get("signal_count", 0) or 0),
        "sample_518k_case_count": int(sample_summary.get("case_count", 0) or 0),
        "closeout_check_count": len(checks),
        "passed_closeout_check_count": sum(1 for row in checks if row.get("passed") is True),
        "failed_closeout_check_ids": failed,
        "policy_pointer_promotion_allowed": False,
        "pointer_write_performed": False,
        "chart_fact_mutation_allowed": False,
        "fixed_bazi_verdict_allowed": False,
        "synthetic_all_required": False,
        "full_pytest_required": False,
        "full_518k_required": False,
        "blockers": ["training_synthetic_support_checks_failed"] if failed else [],
        "rationale": (
            "Training, synthetic validation, and 518K sample support are ready for the stable M1-M8/IQ/LLM chain."
            if ready
            else "Training/synthetic support review is blocked until failed support checks pass."
        ),
    }


def _monitoring_baseline(
    training_summary: Mapping[str, Any],
    sample_summary: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "monitoring_id": "training_synthetic_support_steady_state_monitoring",
        "recommended_trigger": "after_training_signal_or_synthetic_tier_change",
        "commands": [
            "python3 scripts/run_training_synthetic_support_review.py --sample-limit 8",
            "python3 scripts/run_synthetic_validation.py --tier training_pipeline",
            "python3 scripts/run_518k_validation.py --mode sample --limit 8",
        ],
        "major_node_commands": [
            "python3 scripts/run_synthetic_validation.py --tier all",
            "pytest -q",
            "python3 scripts/run_518k_validation.py --mode full --confirm-full",
        ],
        "watched_metrics": {
            "training_pipeline_case_count": int(training_summary.get("case_count", 0) or 0),
            "sample_518k_case_count": int(sample_summary.get("case_count", 0) or 0),
            "sample_518k_run_id": str(sample_summary.get("run_id") or ""),
        },
        "synthetic_all_required": False,
        "full_pytest_required": False,
        "full_518k_required": False,
        "boundary": "monitoring_tracks_training_synthetic_distribution_without_fact_or_pointer_writes",
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["training_synthetic_support_ready"]:
        return {
            "next_task": "Core Chain Steady-State Summary",
            "reason": "Training/synthetic support is ready; next summarize current module completion and steady-state cadence.",
            "full_pytest_required": False,
            "full_518k_required": False,
        }
    return {
        "next_task": "Training/Synthetic Support Remediation",
        "reason": "Training/synthetic checks failed; repair training signals, synthetic tiers, or sample distribution evidence.",
        "full_pytest_required": False,
        "full_518k_required": False,
    }


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _write_artifact(payload: Mapping[str, Any], artifact_dir: Path) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = artifact_dir / f"{payload['review_id']}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
