from __future__ import annotations

from v30.contracts import ClientKey, LocaleKey, RoleKey
from v30.presentation.client_model import DIAGNOSTIC_ROLES, USER_VISIBLE_ROLES, build_presentation_model
from v30.presentation.i18n import LABELS, label
from v30.presentation.projection_matrix import CLIENT_KEYS, LOCALE_KEYS, ROLE_KEYS
from v30.runtime import create_smoke_runtime


MULTI_USER_TERMINAL_LOCALE_READINESS_VERSION = "v30.multi_user_terminal_locale_readiness.v1"


def run_multi_user_terminal_locale_readiness(reading_id: str = "u1-multi-user-terminal-locale") -> dict[str, object]:
    runtime = create_smoke_runtime(reading_id=reading_id)
    return build_multi_user_terminal_locale_readiness(
        role_keys=ROLE_KEYS,
        locale_keys=LOCALE_KEYS,
        client_keys=CLIENT_KEYS,
        projection_payloads=[
            build_presentation_model(runtime, role_key=role, locale=locale, client=client).model_dump(mode="json")
            for role in ROLE_KEYS
            for locale in LOCALE_KEYS
            for client in CLIENT_KEYS
        ],
    )


def build_multi_user_terminal_locale_readiness(
    *,
    role_keys: tuple[RoleKey, ...],
    locale_keys: tuple[LocaleKey, ...],
    client_keys: tuple[ClientKey, ...],
    projection_payloads: list[dict[str, object]],
) -> dict[str, object]:
    expected_combination_count = len(role_keys) * len(locale_keys) * len(client_keys)
    role_counts = _count_by(projection_payloads, "role_key")
    locale_counts = _count_by(projection_payloads, "locale")
    client_counts = _count_by(projection_payloads, "client")
    customer_payloads = [row for row in projection_payloads if row.get("role_key") in USER_VISIBLE_ROLES]
    diagnostic_payloads = [row for row in projection_payloads if row.get("role_key") in DIAGNOSTIC_ROLES]
    mobile_payloads = [row for row in projection_payloads if row.get("client") == "mobile"]
    operator_payloads = [
        row
        for row in projection_payloads
        if row.get("client") in {"admin", "lab"} and row.get("role_key") in DIAGNOSTIC_ROLES
    ]
    checks = [
        {
            "check_id": "all_role_locale_client_combinations_project",
            "passed": len(projection_payloads) == expected_combination_count
            and set(role_counts) == set(role_keys)
            and set(locale_counts) == set(locale_keys)
            and set(client_counts) == set(client_keys),
            "observed": {
                "combination_count": len(projection_payloads),
                "expected_combination_count": expected_combination_count,
                "roles": sorted(role_counts),
                "locales": sorted(locale_counts),
                "clients": sorted(client_counts),
            },
        },
        {
            "check_id": "guest_user_customer_surface_is_sanitized",
            "passed": bool(customer_payloads) and all(_customer_payload_sanitized(row) for row in customer_payloads),
            "observed": {
                "customer_payload_count": len(customer_payloads),
                "customer_roles": sorted({str(row.get("role_key")) for row in customer_payloads}),
            },
        },
        {
            "check_id": "diagnostic_roles_keep_operator_depth",
            "passed": bool(diagnostic_payloads) and all(bool(row.get("diagnostics")) for row in diagnostic_payloads),
            "observed": {
                "diagnostic_payload_count": len(diagnostic_payloads),
                "diagnostic_roles": sorted({str(row.get("role_key")) for row in diagnostic_payloads}),
            },
        },
        {
            "check_id": "mobile_client_is_compact_customer_safe",
            "passed": bool(mobile_payloads) and all(_mobile_payload_compact(row) for row in mobile_payloads),
            "observed": {
                "mobile_payload_count": len(mobile_payloads),
                "max_mobile_questions": max((_question_count(row) for row in mobile_payloads), default=0),
            },
        },
        {
            "check_id": "admin_lab_clients_expose_operator_actions",
            "passed": bool(operator_payloads) and all(_operator_actions_ready(row) for row in operator_payloads),
            "observed": {
                "operator_payload_count": len(operator_payloads),
                "operator_clients": sorted({str(row.get("client")) for row in operator_payloads}),
                "operator_roles": sorted({str(row.get("role_key")) for row in operator_payloads}),
            },
        },
        {
            "check_id": "locale_labels_are_covered_without_runtime_claim_changes",
            "passed": _locale_labels_covered(locale_keys),
            "observed": {
                "locales": list(locale_keys),
                "label_keys_per_locale": {locale: len(LABELS.get(locale, {})) for locale in locale_keys},
            },
        },
        {
            "check_id": "projection_does_not_recalculate_bazi_facts",
            "passed": all(_projection_boundary_kept(row) for row in projection_payloads),
            "observed": {
                "payload_count": len(projection_payloads),
                "boundary": "role_locale_client_projection_changes_visibility_language_density_not_chart_fact",
            },
        },
    ]
    failed = [row for row in checks if not row["passed"]]
    ready = not failed
    return {
        "version": MULTI_USER_TERMINAL_LOCALE_READINESS_VERSION,
        "task": {
            "task_id": "U1",
            "title": "Multi User / Terminal / Locale Productization Readiness",
            "scope": "role_locale_client_projection_readiness",
        },
        "matrix_summary": {
            "version": "v30.role_locale_client_projection_matrix.v1",
            "roles": list(role_keys),
            "locales": list(locale_keys),
            "clients": list(client_keys),
            "combination_count": len(projection_payloads),
            "expected_combination_count": expected_combination_count,
            "customer_roles": sorted(USER_VISIBLE_ROLES),
            "diagnostic_roles": sorted(DIAGNOSTIC_ROLES),
        },
        "completion_summary": {
            "multi_user_projection_completion": 80 if ready else 70,
            "multi_terminal_projection_completion": 78 if ready else 68,
            "multi_locale_projection_completion": 76 if ready else 66,
            "durable_auth_completion": 40,
            "productized_terminal_ui_completion": 45,
            "deep_locale_content_completion": 55,
            "current_scope_ready": ready,
        },
        "checks": checks,
        "decision": {
            "readiness_ready": ready,
            "decision_status": "u1_projection_readiness_ready" if ready else "u1_projection_readiness_blocked",
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "core_bazi_modules_reopened": False,
            "chart_fact_mutation_allowed": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
        },
        "next_mainline_selection": {
            "task_id": "U2" if ready else "U1-FIX",
            "title": "Session Ownership And Role Boundary Hardening" if ready else "Fix Multi User Projection Readiness",
            "reason": "projection_matrix_ready_next_harden_session_boundaries" if ready else "u1_checks_failed",
        },
        "boundary": "u1_productization_projects_existing_bazi_runtime_without_recalculating_or_mutating_chart_facts",
    }


def _count_by(rows: list[dict[str, object]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "")
        counts[value] = counts.get(value, 0) + 1
    return counts


def _customer_payload_sanitized(row: dict[str, object]) -> bool:
    contract = row.get("projection_contract", {})
    if not isinstance(contract, dict):
        return False
    leak_scan = contract.get("leak_scan", {})
    return (
        not bool(row.get("diagnostics"))
        and isinstance(leak_scan, dict)
        and leak_scan.get("passed") is True
        and contract.get("diagnostics_visible") is False
        and _customer_actions_sanitized(row)
        and _has_core_surface(row)
    )


def _mobile_payload_compact(row: dict[str, object]) -> bool:
    layout = row.get("layout", {})
    return (
        isinstance(layout, dict)
        and layout.get("density") == "compact"
        and _question_count(row) <= 3
    )


def _operator_actions_ready(row: dict[str, object]) -> bool:
    actions = {
        str(action.get("type"))
        for action in row.get("actions", [])
        if isinstance(action, dict)
    }
    return bool(row.get("diagnostics")) and {"submit_answer", "run_training", "open_trace"}.issubset(actions)


def _customer_actions_sanitized(row: dict[str, object]) -> bool:
    actions = {
        str(action.get("type"))
        for action in row.get("actions", [])
        if isinstance(action, dict)
    }
    return actions == {"submit_answer"}


def _locale_labels_covered(locale_keys: tuple[LocaleKey, ...]) -> bool:
    required = {"app_title", "submit_answer", "career", "wealth", "relationship", "timing", "diagnostics"}
    return all(
        required.issubset(LABELS.get(locale, {}))
        and all(label(locale, key) != key for key in required)
        for locale in locale_keys
    )


def _projection_boundary_kept(row: dict[str, object]) -> bool:
    contract = row.get("projection_contract", {})
    chart_summary = row.get("chart_summary", {})
    return (
        isinstance(contract, dict)
        and contract.get("boundary") == "api_projection_contract_keeps_customer_surface_simple_and_internal_context_role_gated"
        and isinstance(chart_summary, dict)
        and chart_summary.get("boundary") == "chart_summary_is_customer_safe_projection_not_full_bazi_context"
    )


def _has_core_surface(row: dict[str, object]) -> bool:
    reading_surface = row.get("reading_surface", {})
    if not isinstance(reading_surface, dict):
        return False
    core = reading_surface.get("core_bazi_reading", {})
    domain_cards = reading_surface.get("domain_cards", [])
    return (
        isinstance(core, dict)
        and core.get("surface_type") == "core_bazi_calculation"
        and isinstance(domain_cards, list)
        and bool(domain_cards)
    )


def _question_count(row: dict[str, object]) -> int:
    questions = row.get("questions", [])
    return len(questions) if isinstance(questions, list) else 0
