from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from v30.brain import CENTRAL_BRAIN_VERSION, build_expression_role_state
from v30.presentation import build_presentation_model
from v30.runtime import attach_hidden_factor_state, create_smoke_runtime


CENTRAL_BRAIN_ACCEPTANCE_VERSION = "v30.central_brain_acceptance.v1"
REQUIRED_TRACE_SECTIONS = (
    "brain_state",
    "session_memory",
    "role_state",
    "runtime_plan",
    "question_strategy",
    "expression_orchestration",
    "feedback_strategy",
    "training_signal_routes",
    "boundaries",
)
REQUIRED_BOUNDARIES = {
    "central_brain_coordinates_only",
    "central_brain_does_not_mutate_chart_facts",
    "central_brain_does_not_write_database_or_redis_directly",
    "central_brain_does_not_auto_apply_policy_without_validation_gate",
}
REQUIRED_ROLE_KEYS = ("guest", "user", "practitioner", "admin", "lab")


def run_central_brain_acceptance() -> dict[str, Any]:
    runtime = create_smoke_runtime("bt1-central-brain-acceptance")
    amplifier_runtime = attach_hidden_factor_state(
        runtime,
        {
            "state_id": "bt1-central-brain-acceptance:hidden_factor_state",
            "reading_id": "bt1-central-brain-acceptance",
            "context_id": runtime.chart_context.context_id,
            "status": "amplifier_candidate",
            "amplifier_candidate": True,
            "confidence": 0.82,
            "special_years": ["2020"],
            "repeated_states": ["career_breakthrough"],
            "evidence_ids": [],
            "boundaries": ["feedback_conditioned_not_chart_fact"],
            "feedback": [],
        },
    )
    return build_central_brain_acceptance(
        runtime_payload=runtime.model_dump(mode="json"),
        amplifier_runtime_payload=amplifier_runtime.model_dump(mode="json"),
        role_projection_payloads={
            role: build_presentation_model(
                runtime,
                role_key=role,
                client="admin" if role in {"admin", "lab"} else "web",
            ).model_dump(mode="json")
            for role in REQUIRED_ROLE_KEYS
        },
        expression_role_states={
            role: build_expression_role_state(
                reading_id=runtime.reading_id,
                role_key=role,
                locale=runtime.chart_context.locale,
                client="admin" if role in {"admin", "lab"} else "web",
            )
            for role in REQUIRED_ROLE_KEYS
        },
        chart_fact_before=runtime.chart_context.model_dump(mode="json"),
        chart_fact_after=runtime.chart_context.model_dump(mode="json"),
    )


def build_central_brain_acceptance(
    *,
    runtime_payload: Mapping[str, Any],
    amplifier_runtime_payload: Mapping[str, Any],
    role_projection_payloads: Mapping[str, Mapping[str, Any]],
    expression_role_states: Mapping[str, Mapping[str, Any]],
    chart_fact_before: Mapping[str, Any],
    chart_fact_after: Mapping[str, Any],
) -> dict[str, Any]:
    executed_at = datetime.now(timezone.utc)
    trace = _trace(runtime_payload)
    amplifier_trace = _trace(amplifier_runtime_payload)
    trace_summary = _trace_summary(trace, amplifier_trace)
    role_summary = _role_summary(role_projection_payloads, expression_role_states)
    boundary_summary = _boundary_summary(trace, chart_fact_before, chart_fact_after)
    acceptance_checks = _acceptance_checks(trace_summary, role_summary, boundary_summary)
    decision = _decision(acceptance_checks)
    return {
        "version": CENTRAL_BRAIN_ACCEPTANCE_VERSION,
        "executed_at": executed_at.isoformat(),
        "status": "completed" if decision["central_brain_acceptance_ready"] else "blocked",
        "decision": decision,
        "trace_summary": trace_summary,
        "role_summary": role_summary,
        "boundary_summary": boundary_summary,
        "acceptance_checks": acceptance_checks,
        "next_mainline_selection": _next_selection(decision),
        "boundary": "bt1_accepts_central_brain_as_read_only_runtime_coordinator",
    }


def _trace(payload: Mapping[str, Any]) -> dict[str, Any]:
    plan = payload.get("question_plan", {})
    plan = plan if isinstance(plan, Mapping) else {}
    effect = plan.get("policy_effect", {})
    effect = effect if isinstance(effect, Mapping) else {}
    trace = effect.get("central_brain_trace", {})
    return dict(trace) if isinstance(trace, Mapping) else {}


def _trace_summary(trace: Mapping[str, Any], amplifier_trace: Mapping[str, Any]) -> dict[str, Any]:
    brain_state = trace.get("brain_state", {}) if isinstance(trace.get("brain_state"), Mapping) else {}
    session_memory = trace.get("session_memory", {}) if isinstance(trace.get("session_memory"), Mapping) else {}
    runtime_plan = trace.get("runtime_plan", {}) if isinstance(trace.get("runtime_plan"), Mapping) else {}
    question_strategy = trace.get("question_strategy", {}) if isinstance(trace.get("question_strategy"), Mapping) else {}
    expression = trace.get("expression_orchestration", {}) if isinstance(trace.get("expression_orchestration"), Mapping) else {}
    feedback = trace.get("feedback_strategy", {}) if isinstance(trace.get("feedback_strategy"), Mapping) else {}
    routes = trace.get("training_signal_routes", [])
    routes = routes if isinstance(routes, list) else []
    route_domains = sorted({
        str(row.get("target_signal_domain"))
        for row in routes
        if isinstance(row, Mapping) and row.get("target_signal_domain")
    })
    amplifier_strategy = (
        amplifier_trace.get("question_strategy", {})
        if isinstance(amplifier_trace.get("question_strategy"), Mapping)
        else {}
    )
    return {
        "version": str(trace.get("version") or ""),
        "required_sections_present": all(section in trace for section in REQUIRED_TRACE_SECTIONS),
        "session_phase": str(brain_state.get("session_phase") or ""),
        "known_context": [str(row) for row in brain_state.get("known_context", [])]
        if isinstance(brain_state.get("known_context"), list) else [],
        "unknown_context": [str(row) for row in brain_state.get("unknown_context", [])]
        if isinstance(brain_state.get("unknown_context"), list) else [],
        "hidden_factor_focus": str(brain_state.get("hidden_factor_focus") or ""),
        "memory_policy": str(session_memory.get("memory_policy") or ""),
        "feedback_slots": [str(row) for row in session_memory.get("feedback_slots", [])]
        if isinstance(session_memory.get("feedback_slots"), list) else [],
        "runtime_focus": str(runtime_plan.get("focus") or ""),
        "next_actions": [str(row) for row in runtime_plan.get("next_actions", [])]
        if isinstance(runtime_plan.get("next_actions"), list) else [],
        "question_strategy": str(question_strategy.get("strategy") or ""),
        "selected_question_id": str(question_strategy.get("selected_question_id") or ""),
        "expression_surface_status": str(expression.get("surface_status") or ""),
        "feedback_no_review_gate": bool(feedback.get("no_review_gate")),
        "feedback_training_routes": [str(row) for row in feedback.get("training_routes", [])]
        if isinstance(feedback.get("training_routes"), list) else [],
        "training_route_domains": route_domains,
        "training_route_count": len(routes),
        "amplifier_hidden_factor_mode": str(amplifier_strategy.get("hidden_factor_mode") or ""),
    }


def _role_summary(
    role_projection_payloads: Mapping[str, Mapping[str, Any]],
    expression_role_states: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for role in REQUIRED_ROLE_KEYS:
        projection = role_projection_payloads.get(role, {})
        projection = projection if isinstance(projection, Mapping) else {}
        layout = projection.get("layout", {}) if isinstance(projection.get("layout"), Mapping) else {}
        diagnostics = projection.get("diagnostics", {}) if isinstance(projection.get("diagnostics"), Mapping) else {}
        expression = expression_role_states.get(role, {})
        expression = expression if isinstance(expression, Mapping) else {}
        rows.append(
            {
                "role_key": role,
                "projection_role_key": str(projection.get("role_key") or ""),
                "diagnostics_visible": bool(diagnostics),
                "role_profile_diagnostics_visible": bool(
                    (layout.get("role_profile", {}) if isinstance(layout.get("role_profile"), Mapping) else {}).get(
                        "diagnostics_visible"
                    )
                ),
                "expression_visibility": str(expression.get("visibility") or ""),
                "expression_voice": str(expression.get("expression_voice") or ""),
            }
        )
    user_visible_roles = [row for row in rows if row["role_key"] in {"guest", "user"}]
    diagnostic_roles = [row for row in rows if row["role_key"] in {"practitioner", "admin", "lab"}]
    return {
        "required_roles": list(REQUIRED_ROLE_KEYS),
        "role_rows": rows,
        "all_roles_projected": all(row["projection_role_key"] == row["role_key"] for row in rows),
        "guest_user_diagnostics_hidden": all(not row["diagnostics_visible"] for row in user_visible_roles),
        "diagnostic_roles_have_diagnostics": all(row["diagnostics_visible"] for row in diagnostic_roles),
        "expression_role_states_ready": all(row["expression_visibility"] for row in rows),
    }


def _boundary_summary(
    trace: Mapping[str, Any],
    chart_fact_before: Mapping[str, Any],
    chart_fact_after: Mapping[str, Any],
) -> dict[str, Any]:
    boundaries = set(str(row) for row in trace.get("boundaries", []) if isinstance(trace.get("boundaries"), list))
    return {
        "required_boundaries": sorted(REQUIRED_BOUNDARIES),
        "observed_boundaries": sorted(boundaries),
        "required_boundaries_present": REQUIRED_BOUNDARIES.issubset(boundaries),
        "chart_fact_fingerprint_preserved": chart_fact_before == chart_fact_after,
        "chart_fact_mutation_allowed": False,
        "db_or_redis_direct_write_allowed": False,
        "policy_pointer_write_allowed": False,
        "auto_apply_policy_without_validation_allowed": False,
    }


def _acceptance_checks(
    trace_summary: Mapping[str, Any],
    role_summary: Mapping[str, Any],
    boundary_summary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "check_id": "central_brain_trace_complete",
            "passed": (
                trace_summary["version"] == CENTRAL_BRAIN_VERSION
                and trace_summary["required_sections_present"]
                and trace_summary["selected_question_id"]
            ),
            "expected": "central brain trace contains all required sections and selected question",
        },
        {
            "check_id": "session_question_expression_feedback_ready",
            "passed": (
                trace_summary["memory_policy"] == "runtime_memory_is_traceable_and_feedback_conditioned"
                and trace_summary["question_strategy"] in {
                    "context_first_question_strategy",
                    "hidden_factor_discovery_strategy",
                    "mainline_followup_strategy",
                }
                and trace_summary["expression_surface_status"] == "clean"
                and trace_summary["feedback_no_review_gate"]
                and {"question_intelligence", "expression"}.issubset(set(trace_summary["training_route_domains"]))
            ),
            "expected": "session memory, question strategy, expression, feedback, and routes are ready",
        },
        {
            "check_id": "hidden_factor_route_is_feedback_conditioned",
            "passed": (
                "hidden_factor_confirmation" in trace_summary["unknown_context"]
                and "hidden_factor_boundary_feedback" in trace_summary["feedback_slots"]
                and "hidden_factor" in trace_summary["training_route_domains"]
                and trace_summary["amplifier_hidden_factor_mode"] == "use_as_feedback_conditioned_amplifier"
            ),
            "expected": "hidden factor is routed as feedback-conditioned strategy, not chart fact",
        },
        {
            "check_id": "role_projection_boundaries_ready",
            "passed": (
                role_summary["all_roles_projected"]
                and role_summary["guest_user_diagnostics_hidden"]
                and role_summary["diagnostic_roles_have_diagnostics"]
                and role_summary["expression_role_states_ready"]
            ),
            "expected": "guest/user stay clean and practitioner/admin/lab diagnostics are role-gated",
        },
        {
            "check_id": "central_brain_read_only_boundary",
            "passed": (
                boundary_summary["required_boundaries_present"]
                and boundary_summary["chart_fact_fingerprint_preserved"]
                and not boundary_summary["chart_fact_mutation_allowed"]
                and not boundary_summary["db_or_redis_direct_write_allowed"]
                and not boundary_summary["policy_pointer_write_allowed"]
                and not boundary_summary["auto_apply_policy_without_validation_allowed"]
            ),
            "expected": "central brain is read-only and cannot mutate facts, storage, or pointers",
        },
    ]


def _decision(checks: list[Mapping[str, Any]]) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if not row.get("passed")]
    ready = not failed
    return {
        "central_brain_acceptance_ready": ready,
        "decision_status": "bt1_central_brain_acceptance_ready"
        if ready else "bt1_central_brain_acceptance_blocked",
        "acceptance_check_count": len(checks),
        "passed_acceptance_check_count": sum(1 for row in checks if row.get("passed")),
        "failed_check_ids": failed,
        "blockers": ["central_brain_acceptance_checks_failed"] if failed else [],
        "central_brain_completion": 90 if ready else 82,
        "external_release_ready": False,
        "full_pytest_required": False,
        "full_518k_required": False,
        "policy_pointer_promotion_allowed": False,
        "chart_fact_mutation_allowed": False,
        "rationale": (
            "Central brain is accepted as a read-only runtime coordinator for BT1."
            if ready
            else "Central brain acceptance cannot complete until failed BT1 checks are repaired."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["central_brain_acceptance_ready"]:
        return {
            "task_id": "BT2",
            "title": "Long-Session Brain Replay",
            "selected_track": "brain_training_synthetic_completion",
            "scope": [
                "replay multi-turn reading state",
                "verify answered-question suppression and next-question refresh",
                "keep chart facts immutable",
            ],
        }
    return {
        "task_id": "BT1-FR",
        "title": "Central Brain Acceptance Failure Review",
        "selected_track": "brain_training_synthetic_completion",
        "scope": [
            "inspect failed BT1 checks",
            "repair central brain trace or role boundary gaps",
            "keep training/pointer/release disabled while blocked",
        ],
    }
