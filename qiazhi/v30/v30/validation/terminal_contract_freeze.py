from __future__ import annotations

from v30.presentation.client_model import build_presentation_model
from v30.runtime import create_smoke_runtime


TERMINAL_CONTRACT_FREEZE_VERSION = "v30.terminal_contract_freeze.v1"

TERMINAL_CASES = (
    ("web_user", "user", "zh", "web"),
    ("mobile_guest", "guest", "zh", "mobile"),
    ("practitioner_web", "practitioner", "zh", "web"),
    ("admin_terminal", "admin", "en", "admin"),
    ("lab_terminal", "lab", "ko", "lab"),
)

REQUIRED_TOP_LEVEL_FIELDS = {
    "reading_surface",
    "chart_summary",
    "mainline_card",
    "structure_card",
    "questions",
    "answer_panel",
    "actions",
    "diagnostics",
    "projection_contract",
}
REQUIRED_READING_SURFACE_FIELDS = {
    "core_bazi_reading",
    "domain_cards",
    "time_context",
    "next_question",
    "options",
    "interaction_goal",
}


def run_terminal_contract_freeze(reading_id: str = "u4-terminal-contract") -> dict[str, object]:
    runtime = create_smoke_runtime(reading_id=reading_id)
    projections = {
        case_id: build_presentation_model(
            runtime,
            role_key=role,
            locale=locale,
            client=client,
        ).model_dump(mode="json")
        for case_id, role, locale, client in TERMINAL_CASES
    }
    return build_terminal_contract_freeze(projections=projections)


def build_terminal_contract_freeze(*, projections: dict[str, dict[str, object]]) -> dict[str, object]:
    checks = [
        {
            "check_id": "all_terminal_cases_project",
            "passed": set(projections) == {case_id for case_id, *_ in TERMINAL_CASES},
            "observed": {"case_ids": sorted(projections)},
        },
        {
            "check_id": "required_top_level_fields_are_frozen",
            "passed": all(REQUIRED_TOP_LEVEL_FIELDS.issubset(payload) for payload in projections.values()),
            "observed": {
                case_id: sorted(REQUIRED_TOP_LEVEL_FIELDS - set(payload))
                for case_id, payload in projections.items()
            },
        },
        {
            "check_id": "required_reading_surface_fields_are_frozen",
            "passed": all(_reading_surface_fields_ready(payload) for payload in projections.values()),
            "observed": {
                case_id: sorted(REQUIRED_READING_SURFACE_FIELDS - set(_reading_surface(payload)))
                for case_id, payload in projections.items()
            },
        },
        {
            "check_id": "web_and_mobile_customer_contracts_are_sanitized",
            "passed": _customer_terminal_ready(projections.get("web_user", {}), expected_density="standard", max_questions=4)
            and _customer_terminal_ready(projections.get("mobile_guest", {}), expected_density="compact", max_questions=3),
            "observed": {
                "web_user": _terminal_summary(projections.get("web_user", {})),
                "mobile_guest": _terminal_summary(projections.get("mobile_guest", {})),
            },
        },
        {
            "check_id": "practitioner_review_terminal_has_diagnostics_without_operator_actions",
            "passed": _diagnostic_terminal_ready(
                projections.get("practitioner_web", {}),
                expected_density="standard",
                expected_actions={"submit_answer"},
                max_questions=4,
            ),
            "observed": {"practitioner_web": _terminal_summary(projections.get("practitioner_web", {}))},
        },
        {
            "check_id": "admin_and_lab_terminals_have_operator_contracts",
            "passed": _diagnostic_terminal_ready(
                projections.get("admin_terminal", {}),
                expected_density="diagnostic",
                expected_actions={"submit_answer", "run_training", "open_trace"},
                max_questions=8,
            )
            and _diagnostic_terminal_ready(
                projections.get("lab_terminal", {}),
                expected_density="diagnostic",
                expected_actions={"submit_answer", "run_training", "open_trace"},
                max_questions=8,
            ),
            "observed": {
                "admin_terminal": _terminal_summary(projections.get("admin_terminal", {})),
                "lab_terminal": _terminal_summary(projections.get("lab_terminal", {})),
            },
        },
        {
            "check_id": "terminal_projection_contracts_keep_additive_policy",
            "passed": all(_projection_contract_ready(payload) for payload in projections.values()),
            "observed": {
                case_id: _projection_contract_summary(payload)
                for case_id, payload in projections.items()
            },
        },
        {
            "check_id": "terminal_contracts_do_not_mutate_bazi_facts",
            "passed": len(set(_chart_fact_fingerprint(payload) for payload in projections.values())) == 1,
            "observed": {
                case_id: _chart_fact_fingerprint(payload)
                for case_id, payload in projections.items()
            },
        },
    ]
    failed = [row for row in checks if not row["passed"]]
    ready = not failed
    return {
        "version": TERMINAL_CONTRACT_FREEZE_VERSION,
        "task": {
            "task_id": "U4",
            "title": "Terminal Contract Freeze",
            "scope": "web_mobile_admin_lab_projection_contract",
        },
        "terminal_contract": {
            "version": "v30.terminal_contract_freeze.v1",
            "terminal_cases": [case_id for case_id, *_ in TERMINAL_CASES],
            "required_top_level_fields": sorted(REQUIRED_TOP_LEVEL_FIELDS),
            "required_reading_surface_fields": sorted(REQUIRED_READING_SURFACE_FIELDS),
            "customer_terminals": ["web_user", "mobile_guest"],
            "diagnostic_terminals": ["practitioner_web", "admin_terminal", "lab_terminal"],
            "boundary": "terminal_contract_freezes_projection_shape_not_ui_design_or_chart_facts",
        },
        "completion_summary": {
            "multi_terminal_projection_completion": 92 if ready else 80,
            "productized_terminal_ui_completion": 65 if ready else 45,
            "role_session_client_locale_productization": 95 if ready else 90,
            "current_scope_ready": ready,
        },
        "checks": checks,
        "decision": {
            "freeze_ready": ready,
            "decision_status": "u4_terminal_contract_frozen" if ready else "u4_terminal_contract_blocked",
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "ui_redesign_required": False,
            "chart_fact_mutation_allowed": False,
            "core_bazi_modules_reopened": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
        },
        "next_mainline_selection": {
            "task_id": "U5" if ready else "U4-FIX",
            "title": "Productization Closeout" if ready else "Fix Terminal Contract Freeze",
            "reason": "terminal_contract_frozen_next_productization_closeout" if ready else "u4_checks_failed",
        },
        "boundary": "u4_freezes_terminal_projection_contract_without_reopening_core_or_redesigning_ui",
    }


def _reading_surface(payload: dict[str, object]) -> dict[str, object]:
    surface = payload.get("reading_surface", {})
    return surface if isinstance(surface, dict) else {}


def _reading_surface_fields_ready(payload: dict[str, object]) -> bool:
    return REQUIRED_READING_SURFACE_FIELDS.issubset(_reading_surface(payload))


def _terminal_summary(payload: dict[str, object]) -> dict[str, object]:
    layout = payload.get("layout", {})
    layout = layout if isinstance(layout, dict) else {}
    return {
        "role_key": payload.get("role_key"),
        "client": payload.get("client"),
        "density": layout.get("density"),
        "question_count": len(payload.get("questions", [])) if isinstance(payload.get("questions"), list) else 0,
        "actions": sorted(_action_types(payload)),
        "diagnostics_visible": bool(payload.get("diagnostics")),
        "locale_contract_ready": layout.get("locale_terminology_contract", {}).get("ready")
        if isinstance(layout.get("locale_terminology_contract"), dict)
        else False,
    }


def _customer_terminal_ready(payload: dict[str, object], *, expected_density: str, max_questions: int) -> bool:
    contract = payload.get("projection_contract", {})
    leak_scan = contract.get("leak_scan", {}) if isinstance(contract, dict) else {}
    return (
        _density(payload) == expected_density
        and _question_count(payload) <= max_questions
        and _action_types(payload) == {"submit_answer"}
        and not bool(payload.get("diagnostics"))
        and isinstance(leak_scan, dict)
        and leak_scan.get("passed") is True
        and _reading_surface(payload).get("internal_context_visible") is False
    )


def _diagnostic_terminal_ready(
    payload: dict[str, object],
    *,
    expected_density: str,
    expected_actions: set[str],
    max_questions: int,
) -> bool:
    return (
        _density(payload) == expected_density
        and _question_count(payload) <= max_questions
        and _action_types(payload) == expected_actions
        and bool(payload.get("diagnostics"))
        and _reading_surface(payload).get("internal_context_visible") is True
    )


def _projection_contract_ready(payload: dict[str, object]) -> bool:
    contract = payload.get("projection_contract", {})
    if not isinstance(contract, dict):
        return False
    additive = contract.get("additive_api_policy", {})
    must_preserve = additive.get("must_preserve", []) if isinstance(additive, dict) else []
    return (
        contract.get("version") == "v30.api_projection_contract.v1"
        and contract.get("boundary") == "api_projection_contract_keeps_customer_surface_simple_and_internal_context_role_gated"
        and {"reading_surface", "questions", "answer_panel", "actions", "diagnostics", "projection_contract"}.issubset(
            set(must_preserve) if isinstance(must_preserve, list) else set()
        )
    )


def _projection_contract_summary(payload: dict[str, object]) -> dict[str, object]:
    contract = payload.get("projection_contract", {})
    contract = contract if isinstance(contract, dict) else {}
    additive = contract.get("additive_api_policy", {})
    additive = additive if isinstance(additive, dict) else {}
    return {
        "version": contract.get("version"),
        "diagnostics_visible": contract.get("diagnostics_visible"),
        "must_preserve_count": len(additive.get("must_preserve", [])) if isinstance(additive.get("must_preserve"), list) else 0,
        "boundary": contract.get("boundary"),
    }


def _density(payload: dict[str, object]) -> str:
    layout = payload.get("layout", {})
    return str(layout.get("density") if isinstance(layout, dict) else "")


def _question_count(payload: dict[str, object]) -> int:
    questions = payload.get("questions", [])
    return len(questions) if isinstance(questions, list) else 0


def _action_types(payload: dict[str, object]) -> set[str]:
    actions = payload.get("actions", [])
    if not isinstance(actions, list):
        return set()
    return {
        str(row.get("type") or "")
        for row in actions
        if isinstance(row, dict)
    }


def _chart_fact_fingerprint(payload: dict[str, object]) -> tuple[str, str, str]:
    chart = payload.get("chart_summary", {})
    chart = chart if isinstance(chart, dict) else {}
    surface = _reading_surface(payload)
    core = surface.get("core_bazi_reading", {})
    core = core if isinstance(core, dict) else {}
    fact_integrity = core.get("fact_integrity", {})
    fact_integrity = fact_integrity if isinstance(fact_integrity, dict) else {}
    return (
        str(chart.get("day_master") or ""),
        str(chart.get("day_master_element") or ""),
        str(fact_integrity.get("source_type") or ""),
    )
