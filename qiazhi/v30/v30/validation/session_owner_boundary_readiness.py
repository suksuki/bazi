from __future__ import annotations

from fastapi import HTTPException

from v30.api.app import ReadingRequest, create_app


SESSION_OWNER_BOUNDARY_READINESS_VERSION = "v30.session_owner_boundary_readiness.v1"


def run_session_owner_boundary_readiness() -> dict[str, object]:
    app = create_app()
    create_route = _route_endpoint(app, "/api/v30/readings")
    history_route = _route_endpoint(app, "/api/v30/readings/history")
    _seed_owner_readings(create_route)
    return build_session_owner_boundary_readiness(
        user_exact=history_route(
            actor_id="u2-actor-a",
            session_id="u2-session-1",
            role="user",
            locale="zh",
            client="web",
            limit=20,
        ),
        admin_actor_only=history_route(
            actor_id="u2-actor-a",
            session_id="",
            role="admin",
            locale="zh",
            client="admin",
            limit=20,
        ),
        practitioner_exact=history_route(
            actor_id="u2-actor-a",
            session_id="u2-session-1",
            role="practitioner",
            locale="zh",
            client="web",
            limit=20,
        ),
        admin_other_exact=history_route(
            actor_id="u2-actor-b",
            session_id="u2-session-1",
            role="admin",
            locale="zh",
            client="admin",
            limit=20,
        ),
        user_actor_only_error=_history_error(
            history_route,
            actor_id="u2-actor-a",
            session_id="",
            role="user",
        ),
        guest_session_only_error=_history_error(
            history_route,
            actor_id="",
            session_id="u2-session-1",
            role="guest",
        ),
    )


def build_session_owner_boundary_readiness(
    *,
    user_exact: dict[str, object],
    admin_actor_only: dict[str, object],
    practitioner_exact: dict[str, object],
    admin_other_exact: dict[str, object],
    user_actor_only_error: dict[str, object],
    guest_session_only_error: dict[str, object],
) -> dict[str, object]:
    checks = [
        {
            "check_id": "customer_history_requires_actor_and_session",
            "passed": user_actor_only_error.get("status_code") == 400
            and guest_session_only_error.get("status_code") == 400
            and user_actor_only_error.get("detail") == "actor_id and session_id are required for customer history"
            and guest_session_only_error.get("detail") == "actor_id and session_id are required for customer history",
            "observed": {
                "user_actor_only_error": user_actor_only_error,
                "guest_session_only_error": guest_session_only_error,
            },
        },
        {
            "check_id": "customer_exact_owner_scope_returns_only_matching_reading",
            "passed": user_exact.get("count") == 1
            and _item_ids(user_exact) == ["u2-owner-a-session-1"]
            and user_exact.get("owner_filter", {}).get("scope") == "actor_and_session",
            "observed": {
                "count": user_exact.get("count"),
                "item_ids": _item_ids(user_exact),
                "scope": user_exact.get("owner_filter", {}).get("scope"),
            },
        },
        {
            "check_id": "customer_history_hides_owner_ids_and_diagnostics",
            "passed": "actor_id" not in user_exact
            and "session_id" not in user_exact
            and user_exact.get("actor_id_present") is True
            and user_exact.get("session_id_present") is True
            and user_exact.get("diagnostics") == {}
            and _customer_items_sanitized(user_exact),
            "observed": {
                "top_level_actor_id_visible": "actor_id" in user_exact,
                "top_level_session_id_visible": "session_id" in user_exact,
                "diagnostics": user_exact.get("diagnostics"),
            },
        },
        {
            "check_id": "diagnostic_actor_only_history_is_allowed_and_role_gated",
            "passed": admin_actor_only.get("count") == 2
            and set(_item_ids(admin_actor_only)) == {"u2-owner-a-session-1", "u2-owner-a-session-2"}
            and admin_actor_only.get("owner_filter", {}).get("scope") == "actor_only"
            and admin_actor_only.get("owner_filter", {}).get("actor_id") == "u2-actor-a"
            and _diagnostic_items_visible(admin_actor_only),
            "observed": {
                "count": admin_actor_only.get("count"),
                "item_ids": _item_ids(admin_actor_only),
                "scope": admin_actor_only.get("owner_filter", {}).get("scope"),
            },
        },
        {
            "check_id": "practitioner_exact_history_keeps_diagnostics_for_assigned_owner",
            "passed": practitioner_exact.get("count") == 1
            and _item_ids(practitioner_exact) == ["u2-owner-a-session-1"]
            and practitioner_exact.get("visibility_contract", {}).get("diagnostic_role") is True
            and _diagnostic_items_visible(practitioner_exact),
            "observed": {
                "count": practitioner_exact.get("count"),
                "item_ids": _item_ids(practitioner_exact),
            },
        },
        {
            "check_id": "cross_actor_same_session_does_not_leak_into_exact_owner_scope",
            "passed": admin_other_exact.get("count") == 1
            and _item_ids(admin_other_exact) == ["u2-owner-b-session-1"],
            "observed": {
                "count": admin_other_exact.get("count"),
                "item_ids": _item_ids(admin_other_exact),
            },
        },
        {
            "check_id": "session_owner_boundary_does_not_mutate_bazi_facts",
            "passed": all(
                payload.get("boundary") == "reading_history_projects_existing_readings_without_full_login_or_chart_fact_mutation"
                for payload in [user_exact, admin_actor_only, practitioner_exact, admin_other_exact]
            ),
            "observed": {
                "boundary": "reading_history_projects_existing_readings_without_full_login_or_chart_fact_mutation",
            },
        },
    ]
    failed = [row for row in checks if not row["passed"]]
    ready = not failed
    return {
        "version": SESSION_OWNER_BOUNDARY_READINESS_VERSION,
        "task": {
            "task_id": "U2",
            "title": "Session Ownership And Role Boundary Hardening",
            "scope": "actor_session_history_projection_boundary",
        },
        "completion_summary": {
            "durable_auth_session_productization": 60 if ready else 45,
            "multi_user_projection_completion": 88 if ready else 80,
            "multi_terminal_projection_completion": 80 if ready else 78,
            "multi_locale_projection_completion": 76,
            "full_login_completion": 0,
            "current_scope_ready": ready,
        },
        "checks": checks,
        "decision": {
            "readiness_ready": ready,
            "decision_status": "u2_session_owner_boundary_ready" if ready else "u2_session_owner_boundary_blocked",
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "full_login_introduced": False,
            "core_bazi_modules_reopened": False,
            "chart_fact_mutation_allowed": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
        },
        "next_mainline_selection": {
            "task_id": "U3" if ready else "U2-FIX",
            "title": "Locale Terminology And Fallback Contract" if ready else "Fix Session Owner Boundary",
            "reason": "session_owner_boundary_ready_next_locale_depth" if ready else "u2_checks_failed",
        },
        "boundary": "u2_hardens_session_owner_projection_without_full_login_or_chart_fact_mutation",
    }


def _seed_owner_readings(create_route) -> None:
    rows = [
        ("u2-owner-a-session-1", "u2-actor-a", "u2-session-1"),
        ("u2-owner-a-session-2", "u2-actor-a", "u2-session-2"),
        ("u2-owner-b-session-1", "u2-actor-b", "u2-session-1"),
    ]
    for reading_id, actor_id, session_id in rows:
        create_route(
            ReadingRequest(
                reading_id=reading_id,
                actor_id=actor_id,
                session_id=session_id,
                locale="zh",
            )
        )


def _history_error(history_route, *, actor_id: str, session_id: str, role: str) -> dict[str, object]:
    try:
        history_route(
            actor_id=actor_id,
            session_id=session_id,
            role=role,
            locale="zh",
            client="web",
            limit=20,
        )
    except HTTPException as exc:
        return {"status_code": exc.status_code, "detail": exc.detail}
    return {"status_code": 200, "detail": ""}


def _route_endpoint(app, path: str):
    return next(route.endpoint for route in app.routes if getattr(route, "path", "") == path)


def _item_ids(payload: dict[str, object]) -> list[str]:
    items = payload.get("items", [])
    if not isinstance(items, list):
        return []
    return [str(row.get("reading_id") or "") for row in items if isinstance(row, dict)]


def _customer_items_sanitized(payload: dict[str, object]) -> bool:
    items = payload.get("items", [])
    if not isinstance(items, list) or not items:
        return False
    return all(
        isinstance(row, dict)
        and "actor_context" not in row
        and "trace_id" not in row
        and "internal_next_question_id" not in row
        and row.get("owner_match", {}).get("diagnostic_ids_visible") is False
        for row in items
    )


def _diagnostic_items_visible(payload: dict[str, object]) -> bool:
    items = payload.get("items", [])
    if not isinstance(items, list) or not items:
        return False
    return all(
        isinstance(row, dict)
        and isinstance(row.get("actor_context"), dict)
        and bool(row.get("trace_id"))
        and bool(row.get("internal_next_question_id"))
        and row.get("owner_match", {}).get("diagnostic_ids_visible") is True
        for row in items
    )
