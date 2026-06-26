from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Mapping

from v30.config import load_settings
from v30.validation.bazi_backend_api_journey_acceptance import run_bazi_backend_api_journey_acceptance
from v30.validation.real_bazi_diagnosis_steady_state import run_real_bazi_diagnosis_steady_state
from v30.validation.synthetic_canonical_await_trigger import run_synthetic_canonical_await_trigger
from v30.validation.synthetic_canonical_steady_state import run_synthetic_canonical_steady_state


CONTROLLED_RELEASE_READINESS_VERSION = "v30.controlled_release_readiness.v1"


def run_controlled_release_readiness(reading_id: str = "rel-s1-controlled-readiness") -> dict[str, Any]:
    scal_wait = run_synthetic_canonical_await_trigger()
    scal_steady = run_synthetic_canonical_steady_state()
    rbd_steady = run_real_bazi_diagnosis_steady_state()
    api_journey = run_bazi_backend_api_journey_acceptance(reading_id=reading_id)
    return build_controlled_release_readiness(
        synthetic_canonical_await_trigger=scal_wait,
        synthetic_canonical_steady_state=scal_steady,
        real_bazi_diagnosis_steady_state=rbd_steady,
        backend_api_journey_acceptance=api_journey,
        runtime_config=_runtime_config_summary(),
    )


def build_controlled_release_readiness(
    *,
    synthetic_canonical_await_trigger: Mapping[str, Any],
    synthetic_canonical_steady_state: Mapping[str, Any],
    real_bazi_diagnosis_steady_state: Mapping[str, Any],
    backend_api_journey_acceptance: Mapping[str, Any],
    runtime_config: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    reviewed_at = datetime.now(timezone.utc)
    scal_wait = _scal_wait_summary(synthetic_canonical_await_trigger)
    scal_steady = _scal_steady_summary(synthetic_canonical_steady_state)
    rbd = _rbd_summary(real_bazi_diagnosis_steady_state)
    api = _api_journey_summary(backend_api_journey_acceptance)
    runtime = dict(runtime_config or _runtime_config_summary())
    checks = _checks(scal_wait, scal_steady, rbd, api, runtime)
    decision = _decision(checks, runtime)
    return {
        "version": CONTROLLED_RELEASE_READINESS_VERSION,
        "reviewed_at": reviewed_at.isoformat(),
        "status": "completed" if decision["controlled_release_readiness_ready"] else "blocked",
        "task": {
            "task_id": "REL-S1",
            "title": "Controlled Release-Boundary Readiness Review",
            "scope": "targeted_system_readiness_review_without_external_release_authorization_or_heavy_default_gates",
        },
        "synthetic_canonical_wait_summary": scal_wait,
        "synthetic_canonical_steady_summary": scal_steady,
        "real_bazi_diagnosis_summary": rbd,
        "backend_api_journey_summary": api,
        "runtime_config_summary": runtime,
        "checks": checks,
        "decision": decision,
        "release_boundary_policy": {
            "controlled_readiness_complete": decision["controlled_release_readiness_ready"],
            "external_release_ready": False,
            "external_release_requires_explicit_operator_approval": True,
            "full_pytest_required_before_external_release": True,
            "real_env_smoke_required_before_external_release": True,
            "live_llm_smoke_required_before_external_release_if_llm_enabled": True,
            "policy_pointer_promotion_requires_separate_decision": True,
            "boundary": "rel_s1_is_controlled_readiness_not_external_release_approval",
        },
        "policy_boundary": {
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
            "live_llm_required": False,
            "real_env_smoke_required": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "external_release_allowed": False,
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "controlled_release_readiness_reviews_current_system_without_running_heavy_gates_by_default",
    }


def _scal_wait_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "ready": bool(decision.get("synthetic_canonical_await_trigger_ready")),
        "waiting": bool(decision.get("waiting_for_synthetic_canonical_trigger")),
        "gate_run_required": bool(decision.get("synthetic_canonical_gate_run_required")),
        "case_count": int(decision.get("case_count", 0) or 0),
        "covered_family_count": int(decision.get("covered_family_count", 0) or 0),
    }


def _scal_steady_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "ready": bool(decision.get("synthetic_canonical_steady_state_ready")),
        "routine_gate_ready": bool(decision.get("routine_gate_ready")),
        "case_count": int(decision.get("case_count", 0) or 0),
        "covered_family_count": int(decision.get("covered_family_count", 0) or 0),
    }


def _rbd_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "ready": bool(decision.get("rbd_steady_state_ready")),
        "mainline_closed": bool(decision.get("rbd_mainline_closed_for_current_scope")),
        "training_signal_count": int(decision.get("training_signal_count", 0) or 0),
        "queued_item_count": int(decision.get("queued_item_count", 0) or 0),
        "full_pytest_required": bool(decision.get("full_pytest_required")),
        "full_518k_required": bool(decision.get("full_518k_required")),
    }


def _api_journey_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    journey = _mapping(payload.get("journey_summary"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "ready": bool(decision.get("api_journey_ready")),
        "check_count": int(decision.get("check_count", 0) or 0),
        "passed_check_count": int(decision.get("passed_check_count", 0) or 0),
        "created_status": str(journey.get("created_status") or ""),
        "projection_contract_version": str(journey.get("projection_contract_version") or ""),
        "answer_accepted": bool(journey.get("answer_accepted")),
        "interaction_state_version": str(journey.get("interaction_state_version") or ""),
        "history_count": int(journey.get("history_count", 0) or 0),
        "live_llm_required": bool(decision.get("live_llm_required")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
    }


def _runtime_config_summary() -> dict[str, Any]:
    settings = load_settings()
    llm_enabled = os.getenv("V30_LLM_ENABLED", "").lower() in {"1", "true", "yes", "on"}
    llm_execute = os.getenv("V30_LLM_EXECUTE", "").lower() in {"1", "true", "yes", "on"}
    return {
        "repository": settings.repository,
        "database_url_configured": bool(settings.database_url),
        "redis_url_configured": bool(settings.redis_url),
        "redis_prefix": settings.redis_prefix,
        "runtime_dir": str(settings.runtime_dir),
        "host": settings.host,
        "port": settings.port,
        "llm_enabled": llm_enabled,
        "llm_execute": llm_execute,
        "llm_api_key_configured": bool(os.getenv("V30_LLM_API_KEY")),
        "real_env_smoke_run": False,
        "live_llm_smoke_run": False,
        "full_pytest_run": False,
        "boundary": "runtime_config_summary_records_configuration_only_without_network_or_live_smoke",
    }


def _checks(
    scal_wait: Mapping[str, Any],
    scal_steady: Mapping[str, Any],
    rbd: Mapping[str, Any],
    api: Mapping[str, Any],
    runtime: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "check_id": "synthetic_canonical_gate_waiting_without_trigger",
            "passed": scal_wait["ready"] and scal_wait["waiting"] and not scal_wait["gate_run_required"],
            "observed": scal_wait,
        },
        {
            "check_id": "synthetic_canonical_steady_gate_ready",
            "passed": scal_steady["ready"]
            and scal_steady["routine_gate_ready"]
            and scal_steady["case_count"] >= 16
            and scal_steady["covered_family_count"] >= 10,
            "observed": scal_steady,
        },
        {
            "check_id": "real_bazi_diagnosis_steady_ready",
            "passed": rbd["ready"] and rbd["mainline_closed"] and not rbd["full_pytest_required"] and not rbd["full_518k_required"],
            "observed": rbd,
        },
        {
            "check_id": "backend_api_customer_journey_ready",
            "passed": api["ready"]
            and api["created_status"] == "ready"
            and api["projection_contract_version"] == "v30.api_projection_contract.v1"
            and api["answer_accepted"]
            and api["interaction_state_version"] == "v30.interaction_state.v1"
            and api["history_count"] >= 1,
            "observed": api,
        },
        {
            "check_id": "runtime_config_is_v30_scoped",
            "passed": runtime.get("redis_prefix") == "v30" and "v20" not in str(runtime.get("database_url_configured")),
            "observed": {
                "repository": runtime.get("repository"),
                "database_url_configured": runtime.get("database_url_configured"),
                "redis_url_configured": runtime.get("redis_url_configured"),
                "redis_prefix": runtime.get("redis_prefix"),
                "llm_enabled": runtime.get("llm_enabled"),
                "llm_execute": runtime.get("llm_execute"),
            },
        },
        {
            "check_id": "heavy_and_live_gates_not_run_by_default",
            "passed": not runtime.get("real_env_smoke_run")
            and not runtime.get("live_llm_smoke_run")
            and not runtime.get("full_pytest_run")
            and not api["live_llm_required"]
            and not api["chart_fact_mutation_allowed"],
            "observed": {
                "real_env_smoke_run": runtime.get("real_env_smoke_run"),
                "live_llm_smoke_run": runtime.get("live_llm_smoke_run"),
                "full_pytest_run": runtime.get("full_pytest_run"),
                "api_live_llm_required": api["live_llm_required"],
                "api_chart_fact_mutation_allowed": api["chart_fact_mutation_allowed"],
            },
        },
    ]


def _decision(checks: list[Mapping[str, Any]], runtime: Mapping[str, Any]) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if row.get("passed") is not True]
    ready = not failed
    real_env_configured = bool(runtime.get("database_url_configured")) and bool(runtime.get("redis_url_configured"))
    return {
        "controlled_release_readiness_ready": ready,
        "decision_status": "rel_s1_controlled_release_readiness_ready" if ready else "rel_s1_controlled_release_readiness_blocked",
        "check_count": len(checks),
        "passed_check_count": len(checks) - len(failed),
        "failed_check_ids": failed,
        "external_release_ready": False,
        "controlled_trial_ready": ready,
        "real_env_configured": real_env_configured,
        "real_env_smoke_required_before_external_release": True,
        "full_pytest_required_before_external_release": True,
        "live_llm_smoke_required_before_external_release_if_llm_enabled": True,
        "full_pytest_required": False,
        "synthetic_all_required": False,
        "full_518k_required": False,
        "live_llm_required": False,
        "real_env_smoke_required": False,
        "policy_pointer_promotion_allowed": False,
        "pointer_write_allowed": False,
        "chart_fact_mutation_allowed": False,
        "blockers": ["controlled_release_readiness_checks_failed"] if failed else [],
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision.get("controlled_release_readiness_ready"):
        return {
            "task_id": "REL-S2",
            "title": "Explicit Release Gate Authorization Decision",
            "selected_track": "controlled_release_boundary",
            "scope": [
                "decide whether to run real-env smoke, live LLM smoke, synthetic all, or full pytest",
                "keep external release disabled until explicit operator approval",
                "do not promote policy pointers by default",
            ],
        }
    return {
        "task_id": "REL-S1-FR",
        "title": "Controlled Release Readiness Failure Review",
        "selected_track": "controlled_release_boundary",
        "scope": [
            "repair failed targeted readiness checks",
            "do not run full gates while blocked",
            "keep chart facts and policy pointers immutable",
        ],
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}
