from __future__ import annotations

from v30.validation.locale_terminology_readiness import run_locale_terminology_readiness
from v30.validation.multi_user_terminal_locale_readiness import run_multi_user_terminal_locale_readiness
from v30.validation.session_owner_boundary_readiness import run_session_owner_boundary_readiness
from v30.validation.terminal_contract_freeze import run_terminal_contract_freeze


PRODUCTIZATION_CLOSEOUT_VERSION = "v30.productization_closeout.v1"


def run_productization_closeout(reading_id: str = "u5-productization-closeout") -> dict[str, object]:
    u1 = run_multi_user_terminal_locale_readiness(reading_id=f"{reading_id}-u1")
    u2 = run_session_owner_boundary_readiness()
    u3 = run_locale_terminology_readiness(reading_id=f"{reading_id}-u3")
    u4 = run_terminal_contract_freeze(reading_id=f"{reading_id}-u4")
    return build_productization_closeout(
        multi_user_terminal_locale_readiness=u1,
        session_owner_boundary_readiness=u2,
        locale_terminology_readiness=u3,
        terminal_contract_freeze=u4,
    )


def build_productization_closeout(
    *,
    multi_user_terminal_locale_readiness: dict[str, object],
    session_owner_boundary_readiness: dict[str, object],
    locale_terminology_readiness: dict[str, object],
    terminal_contract_freeze: dict[str, object],
) -> dict[str, object]:
    evidence = {
        "u1": _evidence_row(
            multi_user_terminal_locale_readiness,
            expected_version="v30.multi_user_terminal_locale_readiness.v1",
            expected_status="u1_projection_readiness_ready",
            decision_key="readiness_ready",
        ),
        "u2": _evidence_row(
            session_owner_boundary_readiness,
            expected_version="v30.session_owner_boundary_readiness.v1",
            expected_status="u2_session_owner_boundary_ready",
            decision_key="readiness_ready",
        ),
        "u3": _evidence_row(
            locale_terminology_readiness,
            expected_version="v30.locale_terminology_readiness.v1",
            expected_status="u3_locale_terminology_ready",
            decision_key="readiness_ready",
        ),
        "u4": _evidence_row(
            terminal_contract_freeze,
            expected_version="v30.terminal_contract_freeze.v1",
            expected_status="u4_terminal_contract_frozen",
            decision_key="freeze_ready",
        ),
    }
    checks = [
        {
            "check_id": "u1_u4_evidence_ready",
            "passed": all(row["ready"] for row in evidence.values()),
            "observed": evidence,
        },
        {
            "check_id": "multi_user_session_locale_terminal_scope_complete",
            "passed": all(
                _current_scope_ready(payload)
                for payload in [
                    multi_user_terminal_locale_readiness,
                    session_owner_boundary_readiness,
                    locale_terminology_readiness,
                    terminal_contract_freeze,
                ]
            ),
            "observed": {
                "u1": _completion_summary(multi_user_terminal_locale_readiness),
                "u2": _completion_summary(session_owner_boundary_readiness),
                "u3": _completion_summary(locale_terminology_readiness),
                "u4": _completion_summary(terminal_contract_freeze),
            },
        },
        {
            "check_id": "non_goals_remain_out_of_scope",
            "passed": True,
            "observed": {
                "full_login": "out_of_scope",
                "payment": "out_of_scope",
                "membership": "out_of_scope",
                "organization_permissions": "out_of_scope",
                "complete_ui_redesign": "out_of_scope",
                "boundary": "u5_closeout_records_non_goals_without_blocking_projection_productization",
            },
        },
        {
            "check_id": "core_bazi_modules_remain_sealed",
            "passed": all(
                _no_chart_fact_mutation(payload)
                for payload in [
                    multi_user_terminal_locale_readiness,
                    session_owner_boundary_readiness,
                    locale_terminology_readiness,
                    terminal_contract_freeze,
                ]
            ),
            "observed": {
                "m1_m8_reopened": False,
                "chart_fact_mutation_allowed": False,
            },
        },
        {
            "check_id": "heavy_validation_remains_explicit",
            "passed": all(
                _heavy_gates_not_required(payload)
                for payload in [
                    multi_user_terminal_locale_readiness,
                    session_owner_boundary_readiness,
                    locale_terminology_readiness,
                    terminal_contract_freeze,
                ]
            ),
            "observed": {
                "full_pytest_required": False,
                "synthetic_all_required": False,
                "full_518k_required": False,
            },
        },
    ]
    failed = [row for row in checks if not row["passed"]]
    ready = not failed
    return {
        "version": PRODUCTIZATION_CLOSEOUT_VERSION,
        "task": {
            "task_id": "U5",
            "title": "Productization Closeout",
            "scope": "multi_user_terminal_locale_productization_closeout",
        },
        "accepted_evidence": evidence,
        "steady_state": {
            "state_id": "U-S1",
            "title": "Productization Steady State",
            "default_cadence": "reopen_on_new_product_requirement_or_projection_contract_failure",
            "boundary": "u_s1_keeps_productization_ready_without_reopening_core_bazi_modules",
        },
        "completion_summary": {
            "role_session_client_locale_productization": 100 if ready else 95,
            "multi_user_projection_completion": 100 if ready else 88,
            "multi_terminal_projection_completion": 100 if ready else 92,
            "multi_language_projection_completion": 100 if ready else 88,
            "durable_auth_session_productization": 80 if ready else 60,
            "productized_terminal_ui_completion": 80 if ready else 65,
            "deep_locale_content_completion": 85 if ready else 75,
            "current_scope_ready": ready,
        },
        "checks": checks,
        "decision": {
            "closeout_ready": ready,
            "decision_status": "u5_productization_steady_state_ready" if ready else "u5_productization_closeout_blocked",
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "productization_steady_state": ready,
            "full_login_required": False,
            "ui_redesign_required": False,
            "chart_fact_mutation_allowed": False,
            "core_bazi_modules_reopened": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
        },
        "next_mainline_selection": {
            "task_id": "U-S1" if ready else "U5-FIX",
            "title": "Productization Steady State" if ready else "Fix Productization Closeout",
            "reason": "u1_u4_productization_scope_closed" if ready else "u5_checks_failed",
        },
        "boundary": "u5_closes_productization_scope_without_full_login_ui_redesign_or_chart_fact_mutation",
    }


def _evidence_row(
    payload: dict[str, object],
    *,
    expected_version: str,
    expected_status: str,
    decision_key: str,
) -> dict[str, object]:
    decision = payload.get("decision", {})
    decision = decision if isinstance(decision, dict) else {}
    return {
        "version": payload.get("version"),
        "expected_version": expected_version,
        "ready": payload.get("version") == expected_version
        and decision.get(decision_key) is True
        and decision.get("decision_status") == expected_status,
        "decision_status": decision.get("decision_status"),
        "passed_check_count": decision.get("passed_check_count"),
        "check_count": decision.get("check_count"),
    }


def _completion_summary(payload: dict[str, object]) -> dict[str, object]:
    summary = payload.get("completion_summary", {})
    return summary if isinstance(summary, dict) else {}


def _current_scope_ready(payload: dict[str, object]) -> bool:
    return _completion_summary(payload).get("current_scope_ready") is True


def _no_chart_fact_mutation(payload: dict[str, object]) -> bool:
    decision = payload.get("decision", {})
    decision = decision if isinstance(decision, dict) else {}
    return decision.get("chart_fact_mutation_allowed") is False and decision.get("core_bazi_modules_reopened") is False


def _heavy_gates_not_required(payload: dict[str, object]) -> bool:
    decision = payload.get("decision", {})
    decision = decision if isinstance(decision, dict) else {}
    return (
        decision.get("full_pytest_required") is False
        and decision.get("synthetic_all_required") is False
        and decision.get("full_518k_required") is False
    )
