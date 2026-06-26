from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

from v30.api.app import AnswerRequest, ReadingRequest, create_app


BAZI_BACKEND_API_JOURNEY_ACCEPTANCE_VERSION = "v30.bazi_backend_api_journey_acceptance.v1"


def run_bazi_backend_api_journey_acceptance(
    reading_id: str = "ir2-bazi-backend-api-journey",
) -> dict[str, object]:
    previous_env = {
        "V30_REPOSITORY": os.environ.get("V30_REPOSITORY"),
        "V30_RUNTIME_DIR": os.environ.get("V30_RUNTIME_DIR"),
        "V30_REDIS_URL": os.environ.get("V30_REDIS_URL"),
    }
    with tempfile.TemporaryDirectory(prefix="v30-ir2-api-journey-") as temp_root:
        try:
            os.environ["V30_REPOSITORY"] = "local_json"
            os.environ["V30_RUNTIME_DIR"] = str(Path(temp_root) / ".runtime")
            os.environ.pop("V30_REDIS_URL", None)
            app = create_app()
            evidence = _run_journey(app, reading_id=reading_id)
        except Exception as exc:  # pragma: no cover - unexpected exceptions are summarized as blockers.
            evidence = {
                "exception": f"{type(exc).__name__}:{exc}",
                "routes_checked": [],
            }
        finally:
            for key, value in previous_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
    return build_bazi_backend_api_journey_acceptance(evidence=evidence)


def build_bazi_backend_api_journey_acceptance(*, evidence: dict[str, Any]) -> dict[str, object]:
    checks = [
        {
            "check_id": "api_routes_cover_backend_bazi_customer_journey",
            "passed": _routes_ready(evidence),
            "observed": {
                "routes_checked": evidence.get("routes_checked", []),
                "route_count": len(evidence.get("routes_checked", [])) if isinstance(evidence.get("routes_checked"), list) else 0,
                "exception": evidence.get("exception", ""),
            },
        },
        {
            "check_id": "birth_input_create_and_customer_view_are_core_bazi_first",
            "passed": _birth_and_view_ready(evidence),
            "observed": {
                "created_status": evidence.get("created_status"),
                "trace_id": evidence.get("trace_id"),
                "core_bazi_reading_version": evidence.get("core_bazi_reading_version"),
                "customer_surface_type": evidence.get("customer_surface_type"),
                "projection_contract_version": evidence.get("projection_contract_version"),
                "user_diagnostics_hidden": evidence.get("user_diagnostics_hidden"),
            },
        },
        {
            "check_id": "question_answer_refreshes_view_and_preserves_interaction_state",
            "passed": _answer_ready(evidence),
            "observed": {
                "answer_accepted": evidence.get("answer_accepted"),
                "question_outcome_consumed": evidence.get("question_outcome_consumed"),
                "interaction_state_version": evidence.get("interaction_state_version"),
                "visible_next_question_changed": evidence.get("visible_next_question_changed"),
                "answer_panel_present": evidence.get("answer_panel_present"),
                "answer_boundary": evidence.get("answer_boundary"),
            },
        },
        {
            "check_id": "hidden_factor_feedback_persists_and_rehydrates_as_calibration_state",
            "passed": _hidden_factor_ready(evidence),
            "observed": {
                "hidden_factor_state_status": evidence.get("hidden_factor_state_status"),
                "hidden_factor_state_id": evidence.get("hidden_factor_state_id"),
                "stored_hidden_factor_state_id": evidence.get("stored_hidden_factor_state_id"),
                "admin_hidden_factor_state_visible": evidence.get("admin_hidden_factor_state_visible"),
                "hidden_factor_chart_fact_mutation_allowed": evidence.get("hidden_factor_chart_fact_mutation_allowed"),
            },
        },
        {
            "check_id": "history_and_role_boundaries_are_preserved",
            "passed": _history_ready(evidence),
            "observed": {
                "history_count": evidence.get("history_count"),
                "history_owner_scope": evidence.get("history_owner_scope"),
                "user_history_owner_ids_hidden": evidence.get("user_history_owner_ids_hidden"),
                "user_history_diagnostics_hidden": evidence.get("user_history_diagnostics_hidden"),
                "admin_history_diagnostics_visible": evidence.get("admin_history_diagnostics_visible"),
            },
        },
        {
            "check_id": "integrated_requirements_gate_is_exposed_read_only",
            "passed": _ir1_ready(evidence),
            "observed": {
                "ir1_version": evidence.get("ir1_version"),
                "ir1_decision_status": evidence.get("ir1_decision_status"),
                "ir1_ready": evidence.get("ir1_ready"),
                "ir1_policy_pointer_write_allowed": evidence.get("ir1_policy_pointer_write_allowed"),
                "ir1_chart_fact_mutation_allowed": evidence.get("ir1_chart_fact_mutation_allowed"),
            },
        },
    ]
    failed = [row for row in checks if not row["passed"]]
    ready = not failed
    return {
        "version": BAZI_BACKEND_API_JOURNEY_ACCEPTANCE_VERSION,
        "task": {
            "task_id": "IR2",
            "title": "Bazi Backend API Journey Acceptance",
            "scope": "verify the integrated Bazi intelligence chain through /api/v30 backend route handlers",
        },
        "journey_summary": evidence,
        "checks": checks,
        "decision": {
            "api_journey_ready": ready,
            "decision_status": "ir2_bazi_backend_api_journey_accepted"
            if ready
            else "ir2_bazi_backend_api_journey_blocked",
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
            "live_llm_required": False,
            "chart_fact_mutation_allowed": False,
            "policy_pointer_write_allowed": False,
        },
        "next_mainline_selection": {
            "task_id": "IR-S1" if ready else "IR2-FIX",
            "title": "Integrated Bazi Intelligence Steady State"
            if ready
            else "Fix Backend API Journey",
            "reason": "backend_api_journey_covers_integrated_requirements"
            if ready
            else "backend_api_journey_checks_failed",
            "default_next_step": "wait_for_new_business_or_calibration_evidence",
        },
        "boundary": "ir2_validates_backend_api_journey_without_live_llm_full_pytest_or_policy_promotion",
    }


def _run_journey(app: Any, *, reading_id: str) -> dict[str, Any]:
    health_route = _route_endpoint(app, "/api/v30/health")
    create_route = _route_endpoint(app, "/api/v30/readings")
    view_route = _route_endpoint(app, "/api/v30/readings/{reading_id}/view")
    answer_route = _route_endpoint(app, "/api/v30/readings/{reading_id}/questions/{question_id}/answer")
    hidden_feedback_route = _route_endpoint(app, "/api/v30/readings/{reading_id}/hidden-factor/feedback")
    hidden_state_route = _route_endpoint(app, "/api/v30/readings/{reading_id}/hidden-factor/state")
    history_route = _route_endpoint(app, "/api/v30/readings/history")
    ir1_route = _route_endpoint(app, "/api/v30/admin/mainline/bazi-intelligence-requirements-coverage")

    health = health_route()
    created = create_route(
        ReadingRequest(
            reading_id=reading_id,
            locale="zh",
            target_year=2030,
            actor_id="ir2-user",
            session_id="ir2-session",
            birth_input={
                "input_id": f"{reading_id}-input",
                "calendar_type": "solar",
                "birth_date": "1990-02-04",
                "birth_time": "23:30",
                "timezone": "Asia/Shanghai",
                "gender": "female",
            },
        )
    )
    user_view = view_route(reading_id, role="user", locale="zh", client="web")
    practitioner_view = view_route(reading_id, role="practitioner", locale="en", client="web")
    admin_view = view_route(reading_id, role="admin", locale="ko", client="admin")
    surface = _mapping(user_view.get("reading_surface"))
    core_reading = _mapping(surface.get("core_bazi_reading"))
    next_question = _mapping(surface.get("next_question"))
    question_id = str(next_question.get("question_id") or "")
    answer = answer_route(
        reading_id,
        question_id,
        AnswerRequest(
            answer="我想先看事业方向，2020 年后反复遇到同类压力。",
            role="user",
            locale="zh",
            client="web",
            outcome_status="answered",
            selected_option="career:pressure",
            confidence=0.8,
            feedback_tags=["career", "hidden_factor_followup"],
        ),
    )
    answer_view = _mapping(answer.get("view"))
    answer_surface = _mapping(answer_view.get("reading_surface"))
    answer_panel = _mapping(answer_view.get("answer_panel"))
    answer_llm = _mapping(answer_panel.get("llm_metadata"))
    hidden_state = hidden_feedback_route(
        reading_id,
        {
            "feedback_id": f"{reading_id}-hidden-feedback",
            "special_event_years": [2020],
            "repeated_states": ["career_repeated_state"],
            "time_context_bindings": ["flow_year"],
            "feedback_status": "affirmed",
        },
    )
    stored_hidden_state = hidden_state_route(reading_id)
    admin_after_hidden = view_route(reading_id, role="admin", locale="zh", client="admin")
    history = history_route(
        actor_id="ir2-user",
        session_id="ir2-session",
        role="user",
        locale="zh",
        client="web",
        limit=10,
    )
    admin_history = history_route(
        actor_id="ir2-user",
        session_id="ir2-session",
        role="admin",
        locale="zh",
        client="admin",
        limit=10,
    )
    ir1 = ir1_route(reading_id=f"{reading_id}-ir1")
    ir1_decision = _mapping(ir1.get("decision"))
    history_item = history.get("items", [{}])[0] if history.get("items") else {}
    admin_history_item = admin_history.get("items", [{}])[0] if admin_history.get("items") else {}
    return {
        "routes_checked": [
            "/api/v30/health",
            "/api/v30/readings",
            "/api/v30/readings/{reading_id}/view:user",
            "/api/v30/readings/{reading_id}/view:practitioner",
            "/api/v30/readings/{reading_id}/view:admin",
            "/api/v30/readings/{reading_id}/questions/{question_id}/answer",
            "/api/v30/readings/{reading_id}/hidden-factor/feedback",
            "/api/v30/readings/{reading_id}/hidden-factor/state",
            "/api/v30/readings/history:user",
            "/api/v30/readings/history:admin",
            "/api/v30/admin/mainline/bazi-intelligence-requirements-coverage",
        ],
        "health_ok": health.get("ok") is True,
        "created_status": created.get("status"),
        "reading_id": created.get("reading_id"),
        "trace_id": created.get("trace_id"),
        "core_bazi_reading_version": core_reading.get("version"),
        "customer_surface_type": surface.get("surface_type"),
        "projection_contract_version": _mapping(user_view.get("projection_contract")).get("version"),
        "user_diagnostics_hidden": user_view.get("diagnostics") == {},
        "practitioner_diagnostics_visible": bool(_mapping(practitioner_view.get("diagnostics"))),
        "admin_diagnostics_visible": bool(_mapping(admin_view.get("diagnostics"))),
        "question_id": question_id,
        "answer_accepted": answer.get("accepted") is True,
        "question_outcome_consumed": answer.get("question_outcome_consumed") is True,
        "interaction_state_version": _mapping(answer.get("interaction_state")).get("version"),
        "visible_next_question_changed": _mapping(answer_surface.get("next_question")).get("question_id") != question_id,
        "answer_panel_present": bool(answer_panel),
        "answer_boundary": answer_llm.get("boundary"),
        "hidden_factor_state_status": hidden_state.get("status"),
        "hidden_factor_state_id": hidden_state.get("state_id"),
        "stored_hidden_factor_state_id": stored_hidden_state.get("state_id"),
        "admin_hidden_factor_state_visible": bool(
            _mapping(_mapping(admin_after_hidden.get("diagnostics")).get("hidden_factor_state")).get("state_id")
        ),
        "hidden_factor_chart_fact_mutation_allowed": hidden_state.get("chart_fact_mutation_allowed", False),
        "history_count": history.get("count"),
        "history_owner_scope": _mapping(history.get("owner_filter")).get("scope"),
        "user_history_owner_ids_hidden": "actor_id" not in _mapping(history.get("owner_filter"))
        and "session_id" not in _mapping(history.get("owner_filter")),
        "user_history_diagnostics_hidden": history.get("diagnostics") == {},
        "user_history_internal_fields_hidden": "actor_context" not in history_item
        and "internal_next_question_id" not in history_item,
        "admin_history_diagnostics_visible": bool(_mapping(admin_history.get("diagnostics")).get("trace_ids"))
        and bool(_mapping(admin_history_item).get("actor_context"))
        and bool(_mapping(admin_history_item).get("internal_next_question_id")),
        "ir1_version": ir1.get("version"),
        "ir1_ready": ir1_decision.get("requirements_coverage_ready"),
        "ir1_decision_status": ir1_decision.get("decision_status"),
        "ir1_policy_pointer_write_allowed": ir1_decision.get("policy_pointer_write_allowed", False),
        "ir1_chart_fact_mutation_allowed": ir1_decision.get("chart_fact_mutation_allowed", False),
    }


def _route_endpoint(app: Any, path: str) -> Any:
    return next(route.endpoint for route in app.routes if getattr(route, "path", "") == path)


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _routes_ready(evidence: dict[str, Any]) -> bool:
    required = {
        "/api/v30/health",
        "/api/v30/readings",
        "/api/v30/readings/{reading_id}/view:user",
        "/api/v30/readings/{reading_id}/view:practitioner",
        "/api/v30/readings/{reading_id}/view:admin",
        "/api/v30/readings/{reading_id}/questions/{question_id}/answer",
        "/api/v30/readings/{reading_id}/hidden-factor/feedback",
        "/api/v30/readings/{reading_id}/hidden-factor/state",
        "/api/v30/readings/history:user",
        "/api/v30/readings/history:admin",
        "/api/v30/admin/mainline/bazi-intelligence-requirements-coverage",
    }
    return not evidence.get("exception") and required <= set(evidence.get("routes_checked", []))


def _birth_and_view_ready(evidence: dict[str, Any]) -> bool:
    return (
        evidence.get("health_ok") is True
        and evidence.get("created_status") == "ready"
        and bool(evidence.get("trace_id"))
        and evidence.get("core_bazi_reading_version") == "v30.core_bazi_reading.v1"
        and evidence.get("customer_surface_type") == "customer_reading_loop"
        and evidence.get("projection_contract_version") == "v30.api_projection_contract.v1"
        and evidence.get("user_diagnostics_hidden") is True
        and evidence.get("practitioner_diagnostics_visible") is True
        and evidence.get("admin_diagnostics_visible") is True
    )


def _answer_ready(evidence: dict[str, Any]) -> bool:
    return (
        bool(evidence.get("question_id"))
        and evidence.get("answer_accepted") is True
        and evidence.get("question_outcome_consumed") is True
        and evidence.get("interaction_state_version") == "v30.interaction_state.v1"
        and evidence.get("visible_next_question_changed") is True
        and evidence.get("answer_panel_present") is True
        and evidence.get("answer_boundary")
        in {
            "fast_sync_mode_returns_rule_bound_rbd_answer_without_waiting_for_llm",
            "llm_answer_draft_expression_only_no_chart_fact_mutation",
            "llm_fallback_keeps_rule_answer_and_does_not_mutate_chart_facts",
        }
    )


def _hidden_factor_ready(evidence: dict[str, Any]) -> bool:
    return (
        evidence.get("hidden_factor_state_status") in {"amplifier_candidate", "dialogue_in_progress"}
        and evidence.get("hidden_factor_state_id") == evidence.get("stored_hidden_factor_state_id")
        and evidence.get("admin_hidden_factor_state_visible") is True
        and evidence.get("hidden_factor_chart_fact_mutation_allowed") is False
    )


def _history_ready(evidence: dict[str, Any]) -> bool:
    return (
        evidence.get("history_count") == 1
        and evidence.get("history_owner_scope") == "actor_and_session"
        and evidence.get("user_history_owner_ids_hidden") is True
        and evidence.get("user_history_diagnostics_hidden") is True
        and evidence.get("user_history_internal_fields_hidden") is True
        and evidence.get("admin_history_diagnostics_visible") is True
    )


def _ir1_ready(evidence: dict[str, Any]) -> bool:
    return (
        evidence.get("ir1_version") == "v30.bazi_intelligence_requirements_coverage.v1"
        and evidence.get("ir1_ready") is True
        and evidence.get("ir1_decision_status") == "ir1_bazi_intelligence_requirements_covered"
        and evidence.get("ir1_policy_pointer_write_allowed") is False
        and evidence.get("ir1_chart_fact_mutation_allowed") is False
    )
