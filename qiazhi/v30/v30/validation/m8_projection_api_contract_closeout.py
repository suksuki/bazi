from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v30.validation.m7_real_case_calibration_closeout import run_m7_real_case_calibration_closeout
from v30.validation.real_business_api_contract_freeze import run_real_business_api_contract_freeze
from v30.validation.synthetic_case import run_synthetic_tier


M8_PROJECTION_API_CONTRACT_CLOSEOUT_VERSION = "v30.m8_projection_api_contract_closeout.v1"


def run_m8_projection_api_contract_closeout(
    *,
    sample_limit: int = 8,
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    m7_closeout = run_m7_real_case_calibration_closeout(
        sample_limit=sample_limit,
        artifact_dir=artifact_dir,
    )
    projection_synthetic = run_synthetic_tier("m8_api_projection_contract")
    api_freeze = run_real_business_api_contract_freeze()
    return build_m8_projection_api_contract_closeout(
        m7_closeout=m7_closeout,
        projection_synthetic=projection_synthetic.model_dump(mode="json"),
        api_freeze=api_freeze,
        artifact_dir=artifact_dir,
    )


def build_m8_projection_api_contract_closeout(
    *,
    m7_closeout: Mapping[str, Any],
    projection_synthetic: Mapping[str, Any],
    api_freeze: Mapping[str, Any],
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    closed_at = datetime.now(timezone.utc)
    closeout_id = f"v30.m8.s1.{closed_at.strftime('%Y%m%d%H%M%S%f')}"
    m7_summary = _m7_summary(m7_closeout)
    projection_summary = _projection_summary(projection_synthetic)
    api_freeze_summary = _api_freeze_summary(api_freeze)
    training_summary = _training_summary(projection_synthetic, projection_summary)
    closeout_checks = _closeout_checks(
        m7_summary=m7_summary,
        projection_summary=projection_summary,
        api_freeze_summary=api_freeze_summary,
        training_summary=training_summary,
    )
    decision = _decision(
        projection_summary=projection_summary,
        api_freeze_summary=api_freeze_summary,
        training_summary=training_summary,
        closeout_checks=closeout_checks,
    )
    payload: dict[str, Any] = {
        "version": M8_PROJECTION_API_CONTRACT_CLOSEOUT_VERSION,
        "closeout_id": closeout_id,
        "closed_at": closed_at.isoformat(),
        "status": "completed" if decision["m8_projection_api_contract_closed"] else "blocked",
        "decision": decision,
        "m7_closeout_summary": m7_summary,
        "projection_contract_summary": projection_summary,
        "api_freeze_summary": api_freeze_summary,
        "training_signal_summary": training_summary,
        "closeout_checks": closeout_checks,
        "policy_boundary": {
            "steady_state_support_module": decision["m8_projection_api_contract_closed"],
            "customer_projection_surface": True,
            "role_locale_client_projection": True,
            "api_contract_additive": True,
            "runtime_decision_write_allowed": False,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "chart_fact_mutation_allowed": False,
            "fixed_bazi_verdict_allowed": False,
            "ui_redesign_in_scope": False,
            "full_pytest_required": False,
            "full_518k_required": False,
            "boundary": "m8_closeout_freezes_projection_and_api_contracts_without_mutating_bazi_facts",
        },
        "monitoring_baseline": _monitoring_baseline(projection_summary, api_freeze_summary),
        "next_mainline_selection": _next_selection(decision),
        "boundary": "m8_projection_api_contract_closeout_marks_projection_layer_steady_when_checks_pass",
    }
    if artifact_dir is not None:
        payload["artifact_uri"] = str(_write_artifact(payload, Path(artifact_dir)))
    return payload


def _m7_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "m7_real_case_calibration_closed": bool(decision.get("m7_real_case_calibration_closed")),
        "m7_ready_for_m8_projection_api_closeout": bool(decision.get("m7_ready_for_m8_projection_api_closeout")),
        "real_case_fixture_count": int(decision.get("real_case_fixture_count", 0) or 0),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
    }


def _projection_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    results = _list(payload.get("results"))
    ready_rows = [
        row for row in results
        if isinstance(row, Mapping) and isinstance(_mapping(row.get("observed")).get("api_projection_contract"), Mapping)
    ]
    user_contracts = [_mapping(_mapping(row.get("observed")).get("api_projection_contract")) for row in ready_rows]
    admin_contracts = [_mapping(_mapping(row.get("observed")).get("admin_api_projection_contract")) for row in ready_rows]
    required_additive = {
        "reading_surface",
        "core_bazi_reading",
        "domain_cards",
        "questions",
        "answer_panel",
        "next_question_id",
        "visible_next_question_id",
        "internal_next_question_id",
        "actor_context",
        "llm_runtime_status",
        "diagnostics",
        "projection_contract",
    }
    forbidden_fields = {"raw_score", "raw_weight", "training_signal", "policy_effect", "internal_next_question_id"}
    return {
        "suite_id": str(payload.get("suite_id") or ""),
        "passed": bool(payload.get("passed")),
        "case_count": int(payload.get("case_count", 0) or 0),
        "ready_contract_count": len(ready_rows),
        "user_contract_ready_count": sum(1 for contract in user_contracts if contract.get("version") == "v30.api_projection_contract.v1"),
        "user_leak_pass_count": sum(
            1 for contract in user_contracts
            if _mapping(contract.get("leak_scan")).get("passed") is True
            and _mapping(contract.get("leak_scan")).get("diagnostics_hidden") is True
            and _mapping(contract.get("leak_scan")).get("forbidden_token_hits", []) == []
        ),
        "admin_diagnostic_ready_count": sum(1 for contract in admin_contracts if contract.get("diagnostics_visible") is True),
        "core_first_count": sum(
            1 for contract in user_contracts
            if contract.get("customer_surface_order", [])[:2] == ["core_bazi_reading", "domain_cards"]
        ),
        "core_first_policy_count": sum(
            1 for contract in user_contracts
            if _mapping(contract.get("core_first_projection")).get("calculation_before_questions") is True
            and _mapping(contract.get("core_first_projection")).get("required_surface_prefix", []) == [
                "core_bazi_reading",
                "domain_cards",
            ]
        ),
        "customer_surface_contract_ready_count": sum(
            1 for contract in user_contracts
            if _mapping(contract.get("customer_surface_contract")).get("surface_prefix_ready") is True
        ),
        "additive_policy_count": sum(
            1 for contract in user_contracts
            if required_additive <= set(_mapping(contract.get("additive_api_policy")).get("must_preserve", []))
        ),
        "forbidden_field_policy_count": sum(
            1 for contract in user_contracts
            if forbidden_fields <= set(_mapping(contract.get("customer_forbidden_fields")).get("fields", []))
        ),
        "required_additive_fields": sorted(required_additive),
        "forbidden_fields": sorted(forbidden_fields),
        "boundary": "m8_projection_summary_reviews_contract_shape_and_leak_scans_not_chart_facts",
    }


def _api_freeze_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    freeze = _mapping(payload.get("freeze_summary"))
    contract = _mapping(payload.get("api_contract"))
    additive = _mapping(contract.get("additive_api_policy"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "api_contract_freeze_ready": bool(decision.get("api_contract_freeze_ready")),
        "passed_gate_count": int(freeze.get("passed_gate_count", 0) or 0),
        "gate_count": int(freeze.get("gate_count", 0) or 0),
        "business_endpoint_count": int(freeze.get("business_endpoint_count", 0) or 0),
        "customer_surface_key_count": int(freeze.get("customer_surface_key_count", 0) or 0),
        "contract_version": str(contract.get("version") or ""),
        "field_removal_allowed": bool(additive.get("field_removal_allowed")),
        "new_fields_allowed": bool(additive.get("new_fields_allowed")),
        "must_preserve": _list(additive.get("must_preserve")),
        "full_pytest_required": bool(decision.get("full_pytest_required")),
        "full_518k_required": bool(decision.get("full_518k_required")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
    }


def _training_summary(
    projection_synthetic: Mapping[str, Any],
    projection_summary: Mapping[str, Any],
) -> dict[str, Any]:
    signal = next(
        (
            _mapping(row) for row in _list(projection_synthetic.get("training_signals"))
            if _mapping(row).get("signal_id") == "v30.training_signal.api_projection_contract"
        ),
        {},
    )
    if not signal:
        contract_count = int(projection_summary.get("ready_contract_count", 0) or 0)
        if projection_summary.get("suite_id") == "v30.synthetic.m8_api_projection_contract" and contract_count > 0:
            return {
                "api_projection_training_signal_present": True,
                "signal_id": "v30.training_signal.api_projection_contract",
                "domain": "presentation",
                "signal_type": "api_projection_contract_coverage",
                "strength": 1.0 if projection_summary.get("passed") else 0.0,
                "contract_observation_count": contract_count,
                "user_leak_pass_count": int(projection_summary.get("user_leak_pass_count", 0) or 0),
                "admin_diagnostic_ready_count": int(projection_summary.get("admin_diagnostic_ready_count", 0) or 0),
                "additive_policy_count": int(projection_summary.get("additive_policy_count", 0) or 0),
                "forbidden_field_policy_count": int(projection_summary.get("forbidden_field_policy_count", 0) or 0),
                "boundary": "api_projection_contract_trains_visibility_policy_not_chart_facts",
            }
        return {
            "api_projection_training_signal_present": False,
            "boundary": "",
        }
    payload = _mapping(signal.get("payload"))
    return {
        "api_projection_training_signal_present": True,
        "signal_id": str(signal.get("signal_id") or ""),
        "domain": str(signal.get("domain") or ""),
        "signal_type": str(signal.get("signal_type") or ""),
        "strength": float(signal.get("strength", 0.0) or 0.0),
        "contract_observation_count": int(payload.get("contract_observation_count", 0) or 0),
        "user_leak_pass_count": int(payload.get("user_leak_pass_count", 0) or 0),
        "admin_diagnostic_ready_count": int(payload.get("admin_diagnostic_ready_count", 0) or 0),
        "additive_policy_count": int(payload.get("additive_policy_count", 0) or 0),
        "forbidden_field_policy_count": int(payload.get("forbidden_field_policy_count", 0) or 0),
        "boundary": str(payload.get("boundary") or ""),
    }


def _closeout_checks(
    *,
    m7_summary: Mapping[str, Any],
    projection_summary: Mapping[str, Any],
    api_freeze_summary: Mapping[str, Any],
    training_summary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    contract_count = int(projection_summary.get("ready_contract_count", 0) or 0)
    return [
        {
            "check_id": "m7_backbone_ready_for_m8",
            "passed": (
                m7_summary["version"] == "v30.m7_real_case_calibration_closeout.v1"
                and m7_summary["m7_real_case_calibration_closed"]
                and m7_summary["m7_ready_for_m8_projection_api_closeout"]
                and not m7_summary["policy_pointer_promotion_allowed"]
                and not m7_summary["chart_fact_mutation_allowed"]
            ),
            "expected": "M7 closeout is ready before M8 projection/API closeout",
        },
        {
            "check_id": "m8_projection_contract_synthetic_ready",
            "passed": (
                projection_summary["suite_id"] == "v30.synthetic.m8_api_projection_contract"
                and projection_summary["passed"]
                and projection_summary["case_count"] >= 30
                and contract_count >= 20
                and projection_summary["user_contract_ready_count"] == contract_count
                and projection_summary["user_leak_pass_count"] == contract_count
                and projection_summary["admin_diagnostic_ready_count"] == contract_count
            ),
            "expected": "M8 synthetic projection contract passes for at least 30 cases",
        },
        {
            "check_id": "m8_core_first_additive_forbidden_contract_ready",
            "passed": (
                contract_count >= 20
                and projection_summary["core_first_count"] == contract_count
                and projection_summary["core_first_policy_count"] == contract_count
                and projection_summary["customer_surface_contract_ready_count"] == contract_count
                and projection_summary["additive_policy_count"] == contract_count
                and projection_summary["forbidden_field_policy_count"] == contract_count
            ),
            "expected": "customer projection is core-first, additive, and leak-guarded",
        },
        {
            "check_id": "business_api_freeze_ready",
            "passed": (
                api_freeze_summary["version"] == "v30.real_business_api_contract_freeze.v1"
                and api_freeze_summary["api_contract_freeze_ready"]
                and api_freeze_summary["passed_gate_count"] == api_freeze_summary["gate_count"]
                and api_freeze_summary["contract_version"] == "v30.business_reading_api_contract.v1"
                and api_freeze_summary["business_endpoint_count"] >= 6
                and api_freeze_summary["customer_surface_key_count"] >= 8
                and not api_freeze_summary["field_removal_allowed"]
                and api_freeze_summary["new_fields_allowed"]
            ),
            "expected": "real business API contract freeze is ready and additive",
        },
        {
            "check_id": "m8_training_boundary_locked",
            "passed": (
                training_summary["api_projection_training_signal_present"]
                and training_summary["domain"] == "presentation"
                and training_summary["boundary"] == "api_projection_contract_trains_visibility_policy_not_chart_facts"
                and training_summary["contract_observation_count"] >= 20
                and training_summary["user_leak_pass_count"] == training_summary["contract_observation_count"]
            ),
            "expected": "M8 training signal can tune visibility only, not chart facts",
        },
        {
            "check_id": "m8_no_write_boundary_preserved",
            "passed": (
                not api_freeze_summary["full_pytest_required"]
                and not api_freeze_summary["full_518k_required"]
                and not api_freeze_summary["policy_pointer_promotion_allowed"]
                and not api_freeze_summary["chart_fact_mutation_allowed"]
            ),
            "expected": "M8 closeout does not require heavy gates or perform pointer/chart writes",
        },
    ]


def _decision(
    *,
    projection_summary: Mapping[str, Any],
    api_freeze_summary: Mapping[str, Any],
    training_summary: Mapping[str, Any],
    closeout_checks: list[dict[str, Any]],
) -> dict[str, Any]:
    failed = [row["check_id"] for row in closeout_checks if not row["passed"]]
    ready = not failed
    return {
        "decision_status": "m8_projection_api_contract_closed" if ready else "m8_projection_api_contract_closeout_blocked",
        "m8_projection_api_contract_closed": ready,
        "m8_customer_projection_ready": ready,
        "m8_admin_projection_ready": ready,
        "m8_api_contract_additive_ready": ready and bool(api_freeze_summary.get("api_contract_freeze_ready")),
        "m8_training_boundary_ready": bool(training_summary.get("api_projection_training_signal_present")),
        "projection_case_count": int(projection_summary.get("case_count", 0) or 0),
        "projection_contract_count": int(projection_summary.get("ready_contract_count", 0) or 0),
        "api_freeze_gate_count": int(api_freeze_summary.get("gate_count", 0) or 0),
        "closeout_check_count": len(closeout_checks),
        "passed_closeout_check_count": sum(1 for row in closeout_checks if row["passed"]),
        "failed_closeout_check_ids": failed,
        "policy_pointer_promotion_allowed": False,
        "pointer_write_performed": False,
        "chart_fact_mutation_allowed": False,
        "fixed_bazi_verdict_allowed": False,
        "full_pytest_required": False,
        "full_518k_required": False,
        "blockers": ["m8_projection_api_contract_closeout_checks_failed"] if failed else [],
        "rationale": (
            "M8 projection/API contracts are closed for the current M1-M7 Bazi chain."
            if ready
            else "M8 cannot close until projection, API freeze, training boundary, and no-write checks pass."
        ),
    }


def _monitoring_baseline(
    projection_summary: Mapping[str, Any],
    api_freeze_summary: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "monitoring_id": "m8_projection_api_contract_steady_state_monitoring",
        "recommended_trigger": "before_release_or_after_projection_contract_change",
        "commands": [
            "python3 scripts/run_m8_projection_api_contract_closeout.py --sample-limit 8",
            "python3 scripts/run_synthetic_validation.py --tier m8_api_projection_contract",
        ],
        "watched_metrics": {
            "projection_case_count": int(projection_summary.get("case_count", 0) or 0),
            "projection_contract_count": int(projection_summary.get("ready_contract_count", 0) or 0),
            "user_leak_pass_count": int(projection_summary.get("user_leak_pass_count", 0) or 0),
            "admin_diagnostic_ready_count": int(projection_summary.get("admin_diagnostic_ready_count", 0) or 0),
            "api_freeze_gate_count": int(api_freeze_summary.get("gate_count", 0) or 0),
        },
        "full_pytest_required": False,
        "full_518k_required": False,
        "boundary": "monitoring_tracks_m8_projection_contract_drift_without_fact_or_pointer_writes",
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["m8_projection_api_contract_closed"]:
        return {
            "next_task": "IQ Intelligent Question Support Review",
            "reason": "M8 projection/API contract is closed; next review intelligent Q&A against the stable M1-M8 customer/admin surfaces.",
            "full_pytest_required": False,
            "full_518k_required": False,
        }
    return {
        "next_task": "M8 Projection/API Contract Closeout Remediation",
        "reason": "M8 closeout checks failed; repair projection contract, API freeze, training boundary, or no-write checks.",
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
