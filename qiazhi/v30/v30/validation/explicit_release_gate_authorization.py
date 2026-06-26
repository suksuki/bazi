from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Mapping

from v30.validation.controlled_release_readiness import (
    CONTROLLED_RELEASE_READINESS_VERSION,
    run_controlled_release_readiness,
)


EXPLICIT_RELEASE_GATE_AUTHORIZATION_VERSION = "v30.explicit_release_gate_authorization.v1"
AuthorizationDecision = Literal["authorize_stage_a", "defer_all"]

GATE_CATALOG: dict[str, dict[str, Any]] = {
    "controlled_release_readiness": {
        "category": "targeted",
        "command": "python3 scripts/run_controlled_release_readiness.py",
        "heavy": False,
        "live": False,
        "full": False,
        "default_stage_a": True,
    },
    "synthetic_all": {
        "category": "synthetic",
        "command": "python3 scripts/run_synthetic_validation.py --tier all",
        "heavy": True,
        "live": False,
        "full": False,
        "default_stage_a": True,
    },
    "518k_sample": {
        "category": "distribution",
        "command": "python3 scripts/run_518k_validation.py --mode sample --limit 8",
        "heavy": False,
        "live": False,
        "full": False,
        "default_stage_a": True,
    },
    "518k_shard": {
        "category": "distribution",
        "command": "python3 scripts/run_518k_validation.py --mode shard --shard-id 7 --limit 16",
        "heavy": True,
        "live": False,
        "full": False,
        "default_stage_a": True,
    },
    "full_pytest": {
        "category": "test",
        "command": "pytest -q",
        "heavy": True,
        "live": False,
        "full": True,
        "default_stage_a": False,
    },
    "live_llm_smoke": {
        "category": "llm",
        "command": "python3 scripts/run_llm_live_smoke.py --json",
        "heavy": False,
        "live": True,
        "full": False,
        "default_stage_a": False,
    },
    "real_env_smoke": {
        "category": "runtime",
        "command": "python3 scripts/real_env_smoke.py",
        "heavy": False,
        "live": True,
        "full": False,
        "default_stage_a": False,
    },
    "full_518k": {
        "category": "distribution",
        "command": "python3 scripts/run_518k_validation.py --mode full --confirm-full",
        "heavy": True,
        "live": False,
        "full": True,
        "default_stage_a": False,
    },
}


def run_explicit_release_gate_authorization(
    *,
    authorization_decision: AuthorizationDecision = "authorize_stage_a",
    reading_id: str = "rel-s2-explicit-release-gate-authorization",
) -> dict[str, Any]:
    readiness = run_controlled_release_readiness(reading_id=reading_id)
    return build_explicit_release_gate_authorization(
        controlled_release_readiness=readiness,
        authorization_decision=authorization_decision,
    )


def build_explicit_release_gate_authorization(
    *,
    controlled_release_readiness: Mapping[str, Any],
    authorization_decision: AuthorizationDecision = "authorize_stage_a",
) -> dict[str, Any]:
    decided_at = datetime.now(timezone.utc)
    readiness = _readiness_summary(controlled_release_readiness)
    requested = _requested_gates(authorization_decision)
    gate_matrix = [_gate_row(gate_id, requested=gate_id in requested, readiness=readiness) for gate_id in GATE_CATALOG]
    decision = _decision(readiness=readiness, gate_matrix=gate_matrix, authorization_decision=authorization_decision)
    return {
        "version": EXPLICIT_RELEASE_GATE_AUTHORIZATION_VERSION,
        "decided_at": decided_at.isoformat(),
        "status": "completed" if decision["authorization_recorded"] else "blocked",
        "task": {
            "task_id": "REL-S2",
            "title": "Explicit Release Gate Authorization Decision",
            "scope": "record_which_release_boundary_gates_may_run_next_without_executing_them",
        },
        "controlled_release_readiness_summary": readiness,
        "authorization_decision": {
            "operator_decision": authorization_decision,
            "requested_gate_ids": list(requested),
            "runs_triggered": False,
            "external_release_authorized": False,
            "boundary": "rel_s2_records_authorization_only_and_does_not_execute_gates",
        },
        "gate_matrix": gate_matrix,
        "decision": decision,
        "policy_boundary": {
            "full_pytest_run_allowed_by_default": False,
            "synthetic_all_run_allowed_by_default": False,
            "full_518k_run_allowed_by_default": False,
            "live_llm_run_allowed_by_default": False,
            "real_env_smoke_run_allowed_by_default": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "external_release_allowed": False,
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "explicit_release_gate_authorization_records_stage_a_without_running_or_releasing",
    }


def _readiness_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    boundary = _mapping(payload.get("policy_boundary"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "controlled_release_readiness_ready": bool(decision.get("controlled_release_readiness_ready")),
        "controlled_trial_ready": bool(decision.get("controlled_trial_ready")),
        "external_release_ready": bool(decision.get("external_release_ready")),
        "real_env_configured": bool(decision.get("real_env_configured")),
        "full_pytest_required": bool(boundary.get("full_pytest_required")),
        "synthetic_all_required": bool(boundary.get("synthetic_all_required")),
        "full_518k_required": bool(boundary.get("full_518k_required")),
        "live_llm_required": bool(boundary.get("live_llm_required")),
        "policy_pointer_promotion_allowed": bool(boundary.get("policy_pointer_promotion_allowed")),
        "chart_fact_mutation_allowed": bool(boundary.get("chart_fact_mutation_allowed")),
    }


def _requested_gates(authorization_decision: AuthorizationDecision) -> tuple[str, ...]:
    if authorization_decision == "authorize_stage_a":
        return tuple(gate_id for gate_id, spec in GATE_CATALOG.items() if spec["default_stage_a"])
    return ()


def _gate_row(gate_id: str, *, requested: bool, readiness: Mapping[str, Any]) -> dict[str, Any]:
    spec = GATE_CATALOG[gate_id]
    readiness_ok = (
        readiness["version"] == CONTROLLED_RELEASE_READINESS_VERSION
        and readiness["controlled_release_readiness_ready"]
        and readiness["controlled_trial_ready"]
        and not readiness["external_release_ready"]
        and not readiness["policy_pointer_promotion_allowed"]
        and not readiness["chart_fact_mutation_allowed"]
    )
    authorized = requested and readiness_ok
    deferred_reason = ""
    if not requested:
        deferred_reason = "not_in_stage_a_or_explicitly_deferred"
    elif not readiness_ok:
        deferred_reason = "controlled_release_readiness_not_ready"
    return {
        "gate_id": gate_id,
        "category": spec["category"],
        "command": spec["command"],
        "requested": requested,
        "authorized_pending_execution": authorized,
        "run_triggered": False,
        "heavy": spec["heavy"],
        "live": spec["live"],
        "full": spec["full"],
        "deferred_reason": deferred_reason,
    }


def _decision(
    *,
    readiness: Mapping[str, Any],
    gate_matrix: list[Mapping[str, Any]],
    authorization_decision: AuthorizationDecision,
) -> dict[str, Any]:
    blockers: list[str] = []
    if readiness["version"] != CONTROLLED_RELEASE_READINESS_VERSION:
        blockers.append("controlled_release_readiness_missing")
    if not readiness["controlled_release_readiness_ready"]:
        blockers.append("controlled_release_readiness_not_ready")
    if readiness["external_release_ready"]:
        blockers.append("external_release_unexpectedly_ready")
    if readiness["policy_pointer_promotion_allowed"]:
        blockers.append("unexpected_policy_pointer_permission")
    if readiness["chart_fact_mutation_allowed"]:
        blockers.append("unexpected_chart_fact_mutation_permission")

    authorized = [row["gate_id"] for row in gate_matrix if row["authorized_pending_execution"]]
    deferred = [row["gate_id"] for row in gate_matrix if not row["authorized_pending_execution"]]
    recorded = not blockers
    status = (
        "rel_s2_stage_a_gates_authorized_pending_execution"
        if recorded and authorized
        else "rel_s2_all_gates_deferred"
        if recorded
        else "rel_s2_authorization_blocked"
    )
    return {
        "authorization_recorded": recorded,
        "decision_status": status,
        "operator_decision": authorization_decision,
        "authorized_gate_ids": authorized,
        "deferred_gate_ids": deferred,
        "authorized_gate_count": len(authorized),
        "deferred_gate_count": len(deferred),
        "runs_triggered": False,
        "external_release_ready": False,
        "external_release_allowed": False,
        "policy_pointer_promotion_allowed": False,
        "pointer_write_performed": False,
        "chart_fact_mutation_allowed": False,
        "full_pytest_authorized": "full_pytest" in authorized,
        "live_llm_smoke_authorized": "live_llm_smoke" in authorized,
        "real_env_smoke_authorized": "real_env_smoke" in authorized,
        "full_518k_authorized": "full_518k" in authorized,
        "blockers": blockers,
        "rationale": (
            "Stage-A authorizes non-live release-boundary gates only; execution is a separate REL-S3 step."
            if status == "rel_s2_stage_a_gates_authorized_pending_execution"
            else "All release-boundary gates remain deferred; no execution or release is authorized."
            if status == "rel_s2_all_gates_deferred"
            else "Close the listed blockers before authorizing release-boundary gates."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["authorization_recorded"] and decision["authorized_gate_ids"]:
        return {
            "task_id": "REL-S3",
            "title": "Execute Stage-A Authorized Release Gates",
            "selected_track": "controlled_release_boundary",
            "scope": [
                "run only authorized Stage-A gates",
                "record pass/fail evidence without pointer promotion",
                "defer full pytest, live LLM, real-env smoke, and full 518K unless separately authorized",
            ],
        }
    if decision["authorization_recorded"]:
        return {
            "task_id": "MCR3",
            "title": "Return To Core Module Mainline Selection",
            "selected_track": "mainline_selection",
            "scope": [
                "keep release-boundary gates deferred",
                "continue targeted module work",
                "do not run heavy or live gates by default",
            ],
        }
    return {
        "task_id": "REL-S2-FR",
        "title": "Release Gate Authorization Failure Review",
        "selected_track": "controlled_release_boundary",
        "scope": [
            "repair blocked authorization evidence",
            "rerun REL-S1 before REL-S2",
            "do not run release gates while authorization is blocked",
        ],
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}
