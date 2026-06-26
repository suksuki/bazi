from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v30.validation.m6_practical_reading_closeout import run_m6_practical_reading_closeout
from v30.validation.production_replay_metadata import summarize_production_replay_metadata
from v30.validation.synthetic_case import run_synthetic_tier
from v30.validation.training_signals import extract_training_signals


M7_REAL_CASE_CALIBRATION_STEADY_STATE_REVIEW_VERSION = "v30.m7_real_case_calibration_steady_state_review.v1"

M7_REQUIRED_CATEGORIES = (
    "solar",
    "lunar",
    "leap_month_lunar",
    "true_solar",
    "unknown_hour",
    "unknown_gender",
)


def run_m7_real_case_calibration_steady_state_review(
    *,
    sample_limit: int = 8,
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    m6_closeout = run_m6_practical_reading_closeout(
        sample_limit=sample_limit,
        artifact_dir=artifact_dir,
    )
    real_case = run_synthetic_tier("real_case_calibration_pack")
    training_signals = [
        signal.model_dump(mode="json")
        for signal in extract_training_signals(real_case)
    ]
    return build_m7_real_case_calibration_steady_state_review(
        m6_closeout=m6_closeout,
        real_case_synthetic=real_case.model_dump(mode="json"),
        training_signals=training_signals,
        artifact_dir=artifact_dir,
    )


def build_m7_real_case_calibration_steady_state_review(
    *,
    m6_closeout: Mapping[str, Any],
    real_case_synthetic: Mapping[str, Any],
    training_signals: list[Mapping[str, Any]],
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    reviewed_at = datetime.now(timezone.utc)
    review_id = f"v30.m7.s1.{reviewed_at.strftime('%Y%m%d%H%M%S%f')}"
    m6_summary = _m6_closeout_summary(m6_closeout)
    real_case_summary = _real_case_summary(real_case_synthetic)
    metadata_summary = _metadata_summary(real_case_synthetic)
    training_summary = _training_summary(training_signals)
    checks = _checks(
        m6_summary=m6_summary,
        real_case_summary=real_case_summary,
        metadata_summary=metadata_summary,
        training_summary=training_summary,
    )
    decision = _decision(checks=checks, real_case_summary=real_case_summary)
    payload: dict[str, Any] = {
        "version": M7_REAL_CASE_CALIBRATION_STEADY_STATE_REVIEW_VERSION,
        "review_id": review_id,
        "reviewed_at": reviewed_at.isoformat(),
        "status": "completed" if decision["m7_steady_state_review_ready"] else "blocked",
        "decision": decision,
        "m6_closeout_summary": m6_summary,
        "real_case_calibration_summary": real_case_summary,
        "production_replay_metadata_summary": metadata_summary,
        "training_signal_summary": training_summary,
        "review_checks": checks,
        "policy_boundary": {
            "review_only": True,
            "real_case_pack_expansion_allowed": False,
            "runtime_decision_write_allowed": False,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "chart_fact_mutation_allowed": False,
            "fixed_bazi_verdict_allowed": False,
            "private_user_content_allowed": False,
            "full_pytest_required": False,
            "full_518k_required": False,
            "boundary": "m7_reviews_real_case_calibration_metadata_and_drift_without_mutating_chart_facts",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "m7_real_case_calibration_steady_state_review_validates_canonical_fixture_backbone",
    }
    if artifact_dir is not None:
        payload["artifact_uri"] = str(_write_artifact(payload, Path(artifact_dir)))
    return payload


def _m6_closeout_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "m6_practical_reading_closed": bool(decision.get("m6_practical_reading_closed")),
        "m6_ready_for_release_acceptance": bool(decision.get("m6_ready_for_release_acceptance")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "fixed_bazi_verdict_allowed": bool(decision.get("fixed_bazi_verdict_allowed")),
    }


def _real_case_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    fixtures = _fixtures(payload)
    drift_rows = [_mapping(row.get("calibration_drift_summary")) for row in fixtures]
    categories = {
        "solar": any(row.get("calendar_type") == "solar" for row in fixtures),
        "lunar": any(row.get("calendar_type") == "lunar" and not row.get("lunar_is_leap_month") for row in fixtures),
        "leap_month_lunar": any(row.get("lunar_is_leap_month") for row in fixtures),
        "true_solar": any(row.get("use_true_solar_time") for row in fixtures),
        "unknown_hour": any(row.get("unknown_hour") for row in fixtures),
        "unknown_gender": any(row.get("gender_status") == "unknown" for row in fixtures),
    }
    ready_rows = [row for row in fixtures if row.get("status") == "ready"]
    pending_or_blocked_rows = [row for row in fixtures if row.get("status") in {"pending", "blocked", "unsupported"}]
    drift_flags = Counter(
        str(flag)
        for drift in drift_rows
        for flag in (_list(drift.get("drift_flags")))
        if flag
    )
    module_adjustments = Counter(
        str(module_id)
        for drift in drift_rows
        for module_id in _list(drift.get("module_adjustment_targets"))
        if module_id
    )
    module_readiness = Counter(
        str(module_id)
        for drift in drift_rows
        for module_id, is_ready in _mapping(drift.get("module_readiness")).items()
        if is_ready
    )
    practical_contract_rows = [
        contract
        for row in fixtures
        for contract in (
            _mapping(row.get("practical_domain_contracts")).values()
        )
        if isinstance(contract, Mapping)
    ]
    return {
        "suite_id": str(payload.get("suite_id") or ""),
        "suite_passed": bool(payload.get("passed")),
        "case_count": int(payload.get("case_count", 0) or 0),
        "fixture_count": len(fixtures),
        "ready_count": len(ready_rows),
        "pending_or_blocked_count": len(pending_or_blocked_rows),
        "categories": categories,
        "covered_categories": sorted(category for category, covered in categories.items() if covered),
        "calendar_types": sorted({str(row.get("calendar_type")) for row in fixtures if row.get("calendar_type")}),
        "no_fake_fact_count": sum(1 for row in pending_or_blocked_rows if not row.get("has_pillars")),
        "model_signal_ready_count": sum(1 for row in ready_rows if row.get("model_signal_ready")),
        "ranked_decision_ready_count": sum(1 for row in ready_rows if int(row.get("ranked_decision_count", 0) or 0) >= 3),
        "six_pillar_ready_count": sum(1 for row in ready_rows if row.get("six_pillar_status") == "ready"),
        "practical_ready_or_natal_only_count": sum(1 for row in fixtures if row.get("practical_reading_status") in {"ready", "natal_only"}),
        "m6_practical_domain_contract_count": len(practical_contract_rows),
        "m6_practical_raw_score_leak_count": sum(1 for row in practical_contract_rows if row.get("raw_score_leak")),
        "drift_summary_count": len(drift_rows),
        "drift_stable_count": sum(1 for row in drift_rows if row.get("calibration_status") == "stable"),
        "drift_needs_module_review_count": sum(1 for row in drift_rows if row.get("calibration_status") == "needs_module_review"),
        "drift_flag_counts": dict(drift_flags),
        "module_adjustment_counts": dict(module_adjustments),
        "module_readiness_counts": dict(module_readiness),
        "drift_boundary_count": sum(
            1
            for row in drift_rows
            if row.get("boundary") == "real_case_calibration_drift_routes_to_module_adjustments_not_chart_fact_mutation"
        ),
        "boundary": "m7_real_case_summary_reviews_fixture_coverage_and_drift_not_chart_facts",
    }


def _metadata_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    metadata_rows = [
        _mapping(_mapping(row.get("observed")).get("production_replay_metadata"))
        for row in _result_rows(payload)
        if _mapping(_mapping(row.get("observed")).get("production_replay_metadata"))
    ]
    summary = summarize_production_replay_metadata([dict(row) for row in metadata_rows])
    return {
        **summary,
        "metadata_row_count": len(metadata_rows),
        "all_metadata_only": summary["privacy_guard_pass_count"] == summary["row_count"],
        "all_projection_leak_scan_passed": summary["projection_leak_scan_pass_count"] == summary["row_count"],
    }


def _training_summary(signals: list[Mapping[str, Any]]) -> dict[str, Any]:
    signal_by_id = {
        str(signal.get("signal_id") or ""): signal
        for signal in signals
        if signal.get("signal_id")
    }
    signal = _mapping(signal_by_id.get("v30.training_signal.real_case_calibration_pack"))
    payload = _mapping(signal.get("payload"))
    return {
        "signal_count": len(signals),
        "signal_ids": sorted(signal_by_id),
        "real_case_calibration_signal_present": bool(signal),
        "real_case_calibration_domain": str(signal.get("domain") or ""),
        "real_case_calibration_strength": float(signal.get("strength", 0.0) or 0.0),
        "case_count": int(payload.get("case_count", 0) or 0),
        "ready_count": int(payload.get("ready_count", 0) or 0),
        "m7_calibration_drift_summary_count": int(payload.get("m7_calibration_drift_summary_count", 0) or 0),
        "m7_calibration_stable_count": int(payload.get("m7_calibration_stable_count", 0) or 0),
        "m7_calibration_needs_module_review_count": int(payload.get("m7_calibration_needs_module_review_count", 0) or 0),
        "production_replay_metadata_count": int(payload.get("production_replay_metadata_count", 0) or 0),
        "production_replay_metadata_privacy_guard_pass_count": int(payload.get("production_replay_metadata_privacy_guard_pass_count", 0) or 0),
        "production_replay_metadata_projection_leak_pass_count": int(payload.get("production_replay_metadata_projection_leak_pass_count", 0) or 0),
        "boundary": str(payload.get("boundary") or ""),
    }


def _checks(
    *,
    m6_summary: Mapping[str, Any],
    real_case_summary: Mapping[str, Any],
    metadata_summary: Mapping[str, Any],
    training_summary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "check_id": "m6_closeout_ready_for_m7",
            "passed": (
                m6_summary["version"] == "v30.m6_practical_reading_closeout.v1"
                and m6_summary["m6_practical_reading_closed"]
                and m6_summary["m6_ready_for_release_acceptance"]
            ),
            "expected": "M6-H2 closeout is ready before M7 steady-state review",
        },
        {
            "check_id": "real_case_pack_canonical_coverage_complete",
            "passed": (
                real_case_summary["suite_id"] == "v30.synthetic.real_case_calibration_pack"
                and real_case_summary["suite_passed"]
                and real_case_summary["case_count"] >= 30
                and set(M7_REQUIRED_CATEGORIES) <= set(real_case_summary["covered_categories"])
                and {"solar", "lunar"} <= set(real_case_summary["calendar_types"])
            ),
            "expected": "real-case pack covers solar, lunar, leap month, true solar, unknown hour, and unknown gender",
        },
        {
            "check_id": "real_case_downstream_module_readiness",
            "passed": (
                real_case_summary["ready_count"] >= 20
                and real_case_summary["model_signal_ready_count"] >= 20
                and real_case_summary["ranked_decision_ready_count"] >= 20
                and real_case_summary["six_pillar_ready_count"] >= 20
                and real_case_summary["practical_ready_or_natal_only_count"] >= real_case_summary["ready_count"]
                and real_case_summary["no_fake_fact_count"] >= real_case_summary["pending_or_blocked_count"]
                and real_case_summary["m6_practical_domain_contract_count"] >= 100
                and real_case_summary["m6_practical_raw_score_leak_count"] == 0
            ),
            "expected": "M4/M5/M6 and six-pillar readiness remain sufficient across real-case fixtures",
        },
        {
            "check_id": "real_case_drift_stable_no_module_adjustment",
            "passed": (
                real_case_summary["drift_summary_count"] >= real_case_summary["fixture_count"]
                and real_case_summary["drift_stable_count"] == real_case_summary["drift_summary_count"]
                and real_case_summary["drift_needs_module_review_count"] == 0
                and not real_case_summary["drift_flag_counts"]
                and not real_case_summary["module_adjustment_counts"]
                and real_case_summary["module_readiness_counts"].get("M7_real_case_calibration", 0) >= 30
                and real_case_summary["drift_boundary_count"] == real_case_summary["drift_summary_count"]
            ),
            "expected": "M7 drift summaries are stable and do not request module adjustments",
        },
        {
            "check_id": "production_replay_metadata_privacy_ready",
            "passed": (
                metadata_summary["version"] == "v30.production_replay_metadata_summary.v1"
                and metadata_summary["row_count"] >= 30
                and metadata_summary["ready_count"] >= 20
                and metadata_summary["pending_count"] >= 1
                and metadata_summary["blocked_count"] >= 1
                and metadata_summary["all_metadata_only"]
                and metadata_summary["all_projection_leak_scan_passed"]
                and metadata_summary["metadata_only_boundary_count"] == metadata_summary["row_count"]
            ),
            "expected": "production replay metadata is metadata-only, privacy-safe, and projection-leak free",
        },
        {
            "check_id": "real_case_training_signal_boundary_locked",
            "passed": (
                training_summary["real_case_calibration_signal_present"]
                and training_summary["real_case_calibration_domain"] == "real_case_validation"
                and training_summary["case_count"] >= 30
                and training_summary["m7_calibration_drift_summary_count"] >= 30
                and training_summary["m7_calibration_stable_count"] >= 30
                and training_summary["m7_calibration_needs_module_review_count"] == 0
                and training_summary["production_replay_metadata_count"] >= 30
                and training_summary["production_replay_metadata_privacy_guard_pass_count"] == training_summary["production_replay_metadata_count"]
                and training_summary["production_replay_metadata_projection_leak_pass_count"] == training_summary["production_replay_metadata_count"]
                and training_summary["boundary"] == "real_case_calibration_pack_trains_validation_policy_not_chart_facts"
            ),
            "expected": "real-case calibration training signal trains validation policy, not chart facts",
        },
        {
            "check_id": "m7_no_write_boundary_preserved",
            "passed": (
                not m6_summary["policy_pointer_promotion_allowed"]
                and not m6_summary["chart_fact_mutation_allowed"]
                and not m6_summary["fixed_bazi_verdict_allowed"]
            ),
            "expected": "M7 review is read-only and inherits no-write boundaries from upstream closeout",
        },
    ]


def _decision(*, checks: list[dict[str, Any]], real_case_summary: Mapping[str, Any]) -> dict[str, Any]:
    failed = [row["check_id"] for row in checks if not row["passed"]]
    ready = not failed
    needs_expansion = ready and int(real_case_summary.get("case_count", 0) or 0) < 40
    return {
        "decision_status": "m7_real_case_calibration_steady_state_ready" if ready else "m7_real_case_calibration_steady_state_blocked",
        "m7_steady_state_review_ready": ready,
        "m7_real_case_calibration_steady": ready,
        "focused_real_case_expansion_recommended": needs_expansion,
        "ready_for_m7_closeout": ready,
        "real_case_fixture_count": int(real_case_summary.get("fixture_count", 0) or 0),
        "review_check_count": len(checks),
        "passed_review_check_count": sum(1 for row in checks if row["passed"]),
        "failed_review_check_ids": failed,
        "policy_pointer_promotion_allowed": False,
        "pointer_write_performed": False,
        "chart_fact_mutation_allowed": False,
        "fixed_bazi_verdict_allowed": False,
        "full_pytest_required": False,
        "full_518k_required": False,
        "blockers": ["m7_steady_state_review_checks_failed"] if failed else [],
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["m7_steady_state_review_ready"]:
        return {
            "next_task": "M7 Real-Case Calibration Closeout",
            "reason": "M7 real-case calibration is stable; next close M7 and decide whether focused expansion is deferred or scheduled.",
            "full_pytest_required": False,
            "full_518k_required": False,
        }
    return {
        "next_task": "M7 Real-Case Calibration Remediation",
        "reason": "M7 steady-state review checks failed; repair canonical coverage, metadata privacy, drift routing, or training boundary.",
        "full_pytest_required": False,
        "full_518k_required": False,
    }


def _fixtures(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [
        _mapping(_mapping(row.get("observed")).get("real_case_fixture"))
        for row in _result_rows(payload)
        if _mapping(_mapping(row.get("observed")).get("real_case_fixture"))
    ]


def _result_rows(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows = payload.get("results", [])
    return [row for row in rows if isinstance(row, Mapping)] if isinstance(rows, list) else []


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _write_artifact(payload: Mapping[str, Any], artifact_dir: Path) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = artifact_dir / f"{payload['review_id']}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
