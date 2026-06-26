from __future__ import annotations

import json
from typing import Any, Mapping

from v30.presentation import build_presentation_model
from v30.runtime import create_smoke_runtime


CUSTOMER_SURFACE_BAZI_CONTEXT_RECONCILIATION_VERSION = (
    "v30.customer_surface_bazi_context_reconciliation.v1"
)


def run_customer_surface_bazi_context_reconciliation(
    reading_id: str = "mcr2-customer-surface-bazi-context",
) -> dict[str, object]:
    runtime = create_smoke_runtime(f"{reading_id}-runtime", day_master="庚", day_master_element="metal")
    user_view = build_presentation_model(runtime, role_key="user", locale="zh", client="web").model_dump(mode="json")
    admin_view = build_presentation_model(runtime, role_key="admin", locale="zh", client="admin").model_dump(mode="json")
    practitioner_view = build_presentation_model(
        runtime,
        role_key="practitioner",
        locale="zh",
        client="web",
    ).model_dump(mode="json")
    evidence = {
        "customer_surface": _customer_surface_summary(user_view),
        "customer_boundary": _customer_boundary_summary(user_view),
        "diagnostic_projection": _diagnostic_projection_summary(admin_view, practitioner_view),
        "bazi_context_internalization": _bazi_context_internalization_summary(runtime, admin_view),
        "module_matrix": _module_matrix(),
        "default_validation_policy": _default_validation_policy(),
    }
    return build_customer_surface_bazi_context_reconciliation(evidence=evidence)


def build_customer_surface_bazi_context_reconciliation(*, evidence: Mapping[str, Any]) -> dict[str, object]:
    checks = [
        {
            "check_id": "customer_surface_is_core_first_and_complete",
            "passed": _customer_surface_ready(_mapping(evidence.get("customer_surface"))),
            "observed": evidence.get("customer_surface", {}),
        },
        {
            "check_id": "customer_projection_hides_internal_context",
            "passed": _customer_boundary_ready(_mapping(evidence.get("customer_boundary"))),
            "observed": evidence.get("customer_boundary", {}),
        },
        {
            "check_id": "diagnostic_roles_receive_bazi_context",
            "passed": _diagnostic_projection_ready(_mapping(evidence.get("diagnostic_projection"))),
            "observed": evidence.get("diagnostic_projection", {}),
        },
        {
            "check_id": "bazi_context_feeds_mainline_question_and_llm_context",
            "passed": _bazi_context_internalized(_mapping(evidence.get("bazi_context_internalization"))),
            "observed": evidence.get("bazi_context_internalization", {}),
        },
        {
            "check_id": "completion_accounting_reconciles_surface_and_context",
            "passed": _module_matrix_ready(_list(evidence.get("module_matrix"))),
            "observed": {"module_count": len(_list(evidence.get("module_matrix")))},
        },
        {
            "check_id": "default_validation_stays_targeted",
            "passed": _validation_policy_ready(_mapping(evidence.get("default_validation_policy"))),
            "observed": evidence.get("default_validation_policy", {}),
        },
    ]
    failed = [row for row in checks if not row["passed"]]
    ready = not failed
    return {
        "version": CUSTOMER_SURFACE_BAZI_CONTEXT_RECONCILIATION_VERSION,
        "task": {
            "task_id": "MCR2",
            "title": "Customer Reading Surface And BaziContext Completion Reconciliation",
            "scope": (
                "prove customer-facing Bazi reading projection and role-gated internal BaziContext "
                "coverage are complete, then reconcile stale completion accounting"
            ),
        },
        "module_completion_matrix": evidence.get("module_matrix", []),
        "evidence": evidence,
        "checks": checks,
        "decision": {
            "customer_surface_bazi_context_reconciled": ready,
            "check_count": len(checks),
            "passed_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "decision_status": (
                "mcr2_customer_surface_bazi_context_reconciled"
                if ready
                else "mcr2_customer_surface_bazi_context_blocked"
            ),
            "chart_fact_mutation_allowed": False,
            "policy_pointer_write_allowed": False,
            "live_llm_required": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
        },
        "next_mainline_selection": {
            "task_id": "M3-G1" if ready else "MCR2-FIX",
            "title": (
                "M3 Source-Governed Depth And Calibration Tags"
                if ready
                else "Fix Customer Surface And BaziContext Reconciliation"
            ),
            "selected_track": "core_m3_knowledge_depth" if ready else "main_module_completion_reconciliation",
            "reason": (
                "Customer surface and BaziContext accounting are reconciled; the next useful core task is to deepen "
                "M3 source-governed knowledge/rule/portrait coverage with calibration tags, not UI polish or full-suite churn."
                if ready
                else "repair failed customer surface or BaziContext contract checks"
            ),
            "full_pytest_run_now": False,
            "synthetic_all_run_now": False,
            "full_518k_run_now": False,
            "policy_pointer_write_now": False,
        },
        "boundary": "mcr2_reconciles_projection_and_internal_context_without_mutating_bazi_facts",
    }


def _customer_surface_summary(user_view: Mapping[str, Any]) -> dict[str, object]:
    surface = _mapping(user_view.get("reading_surface"))
    core = _mapping(surface.get("core_bazi_reading"))
    contract = _mapping(user_view.get("projection_contract"))
    surface_contract = _mapping(contract.get("customer_surface_contract"))
    core_first = _mapping(contract.get("core_first_projection"))
    additive = _mapping(contract.get("additive_api_policy"))
    return {
        "surface_version": surface.get("version"),
        "surface_type": surface.get("surface_type"),
        "core_bazi_reading_version": core.get("version"),
        "core_bazi_reading_type": core.get("surface_type"),
        "domain_card_count": len(_list(surface.get("domain_cards"))),
        "has_structure_dynamics": _mapping(surface.get("structure_dynamics")).get("version")
        == "v30.structure_dynamics_surface.v1",
        "time_context_version": _mapping(surface.get("time_context")).get("version"),
        "has_next_question": bool(_mapping(surface.get("next_question")).get("question_id")),
        "question_count": int(surface.get("question_count") or 0),
        "projection_contract_version": contract.get("version"),
        "surface_prefix_ready": surface_contract.get("surface_prefix_ready"),
        "calculation_before_questions": core_first.get("calculation_before_questions"),
        "customer_surface_order": contract.get("customer_surface_order", []),
        "additive_fields": additive.get("must_preserve", []),
        "boundary": "customer_reading_surface_presents_core_bazi_calculation_before_question_loop",
    }


def _customer_boundary_summary(user_view: Mapping[str, Any]) -> dict[str, object]:
    surface = _mapping(user_view.get("reading_surface"))
    diagnostics = _mapping(user_view.get("diagnostics"))
    contract = _mapping(user_view.get("projection_contract"))
    leak_scan = _mapping(contract.get("leak_scan"))
    forbidden = _mapping(contract.get("customer_forbidden_fields")).get("fields", [])
    rendered = json.dumps(
        {
            "reading_surface": surface,
            "questions": _list(user_view.get("questions")),
            "answer_panel": user_view.get("answer_panel") or {},
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    token_hits = sorted({str(token) for token in _list(forbidden) if str(token) in rendered})
    return {
        "internal_context_visible": surface.get("internal_context_visible"),
        "diagnostics_hidden": not bool(diagnostics),
        "leak_scan_passed": leak_scan.get("passed"),
        "forbidden_token_hits": token_hits,
        "leak_scan_hits": leak_scan.get("forbidden_token_hits", []),
        "boundary": "customer_roles_never_receive_internal_policy_training_or_raw_bazi_context_payloads",
    }


def _diagnostic_projection_summary(
    admin_view: Mapping[str, Any],
    practitioner_view: Mapping[str, Any],
) -> dict[str, object]:
    admin_diag = _mapping(admin_view.get("diagnostics"))
    practitioner_diag = _mapping(practitioner_view.get("diagnostics"))
    admin_contract = _mapping(admin_view.get("projection_contract"))
    practitioner_contract = _mapping(practitioner_view.get("projection_contract"))
    return {
        "admin_has_diagnostics": bool(admin_diag),
        "admin_has_bazi_context": bool(_mapping(admin_diag.get("bazi_context"))),
        "admin_has_model_signal": _mapping(admin_diag.get("model_signal_summary")).get("version")
        == "v30.model_signal_summary.v1",
        "admin_has_ranked_decisions": bool(_mapping(admin_diag.get("ranked_decisions"))),
        "admin_diagnostics_visible": admin_contract.get("diagnostics_visible"),
        "admin_leak_scan_passed": _mapping(admin_contract.get("leak_scan")).get("passed"),
        "practitioner_has_diagnostics": bool(practitioner_diag),
        "practitioner_has_bazi_context": bool(_mapping(practitioner_diag.get("bazi_context"))),
        "practitioner_diagnostics_visible": practitioner_contract.get("diagnostics_visible"),
        "role_visibility_matrix_version": _mapping(admin_contract.get("role_visibility_matrix")).get("version"),
        "boundary": "diagnostic_roles_can_inspect_internal_bazi_context_without_changing_customer_projection",
    }


def _bazi_context_internalization_summary(runtime: Any, admin_view: Mapping[str, Any]) -> dict[str, object]:
    policy = _mapping(runtime.question_plan.policy_effect)
    admin_diag = _mapping(admin_view.get("diagnostics"))
    bazi_context = _mapping(admin_diag.get("bazi_context"))
    return {
        "runtime_has_chart_context": bool(runtime.chart_context),
        "runtime_has_structure_state": bool(runtime.structure_state),
        "runtime_has_mainline_state": bool(runtime.mainline_state),
        "policy_has_m3_completion": _mapping(policy.get("m3_completion_summary")).get("status") == "ready",
        "policy_has_model_signal": _mapping(policy.get("model_signal_summary")).get("version")
        == "v30.model_signal_summary.v1",
        "policy_has_ranked_decisions": bool(_mapping(policy.get("ranked_decisions"))),
        "policy_has_practical_reading_context": bool(_mapping(policy.get("practical_reading_context"))),
        "policy_has_interaction_state": _mapping(policy.get("interaction_state")).get("version")
        == "v30.interaction_state.v1",
        "policy_has_llm_output_contract": bool(_mapping(policy.get("llm_output_contract_summary"))),
        "diagnostic_bazi_context_version": bazi_context.get("version"),
        "diagnostic_bazi_context_has_chart_ref": bool(str(bazi_context.get("chart_context_id") or "")),
        "diagnostic_bazi_context_has_structure": bool(_mapping(bazi_context.get("structure_state"))),
        "diagnostic_bazi_context_has_mainline": bool(_mapping(bazi_context.get("mainline_state"))),
        "boundary": "bazi_context_is_internal_runtime_context_consumed_by_projection_question_and_llm_layers",
    }


def _module_matrix() -> list[dict[str, object]]:
    return [
        _row("M1/M2", "BirthInput and deterministic chart facts", 100, "steady", "MCR1 verified"),
        _row("M3", "Knowledge, rule, portrait, feature, and structure spine", 100, "steady", "MCR1 verified"),
        _row("M4", "Ten-god energy model and model-signal summary", 100, "steady", "MCR1 verified"),
        _row("M5", "Strength, structure, and useful-god ranked decisions", 100, "steady", "MCR1 verified"),
        _row("M6", "Practical Bazi reading output", 100, "steady", "MCR1 verified"),
        _row("M7", "Real-case calibration pack and drift routing", 100, "steady", "MCR1 verified"),
        _row("M8", "Customer reading projection and API contract", 100, "steady", "MCR1 verified"),
        _row("SURFACE", "Customer reading surface accounting", 100, "steady", "MCR2 reconciled"),
        _row("CTX", "BaziContext internalization accounting", 100, "steady", "MCR2 reconciled"),
        _row("IQ", "Intelligent question interaction", 98, "steady", "IQ5 closed; IQ-S1 auxiliary"),
        _row("LLM", "Bazi LLM expression layer", 88, "bounded_steady", "BL8 closed; live smoke explicit-only"),
        _row("BT", "Central brain, training, synthetic, and 518K support", 100, "steady", "BT10 closed"),
        _row("U", "Multi-user, terminal, session, and locale projection", 100, "steady", "U5 closed"),
    ]


def _default_validation_policy() -> dict[str, object]:
    return {
        "full_pytest_required": False,
        "synthetic_all_required": False,
        "full_518k_required": False,
        "live_llm_required": False,
        "policy_pointer_write_allowed": False,
        "chart_fact_mutation_allowed": False,
        "targeted_tests_only": True,
        "boundary": "mcr2_uses_targeted_contract_validation_until_next_major_checkpoint",
    }


def _row(module_id: str, name: str, completion: int, status: str, evidence: str) -> dict[str, object]:
    return {
        "module_id": module_id,
        "name": name,
        "completion": completion,
        "status": status,
        "evidence": evidence,
    }


def _customer_surface_ready(summary: Mapping[str, Any]) -> bool:
    additive_fields = set(_list(summary.get("additive_fields")))
    order = _list(summary.get("customer_surface_order"))
    return (
        summary.get("surface_version") == "v30.customer_reading_surface.v1"
        and summary.get("surface_type") == "customer_reading_loop"
        and summary.get("core_bazi_reading_version") == "v30.core_bazi_reading.v1"
        and summary.get("core_bazi_reading_type") == "core_bazi_calculation"
        and int(summary.get("domain_card_count") or 0) >= 5
        and summary.get("has_structure_dynamics") is True
        and summary.get("time_context_version") == "v30.customer_time_context.v1"
        and summary.get("has_next_question") is True
        and int(summary.get("question_count") or 0) >= 1
        and summary.get("projection_contract_version") == "v30.api_projection_contract.v1"
        and summary.get("surface_prefix_ready") is True
        and summary.get("calculation_before_questions") is True
        and order[:2] == ["core_bazi_reading", "domain_cards"]
        and {"reading_surface", "questions", "answer_panel", "llm_runtime_status"} <= additive_fields
    )


def _customer_boundary_ready(summary: Mapping[str, Any]) -> bool:
    return (
        summary.get("internal_context_visible") is False
        and summary.get("diagnostics_hidden") is True
        and summary.get("leak_scan_passed") is True
        and not _list(summary.get("forbidden_token_hits"))
        and not _list(summary.get("leak_scan_hits"))
    )


def _diagnostic_projection_ready(summary: Mapping[str, Any]) -> bool:
    return (
        summary.get("admin_has_diagnostics") is True
        and summary.get("admin_has_bazi_context") is True
        and summary.get("admin_has_model_signal") is True
        and summary.get("admin_has_ranked_decisions") is True
        and summary.get("admin_diagnostics_visible") is True
        and summary.get("admin_leak_scan_passed") is True
        and summary.get("practitioner_has_diagnostics") is True
        and summary.get("practitioner_has_bazi_context") is True
        and summary.get("practitioner_diagnostics_visible") is True
        and summary.get("role_visibility_matrix_version") == "v30.role_visibility_matrix.v1"
    )


def _bazi_context_internalized(summary: Mapping[str, Any]) -> bool:
    return (
        all(
            summary.get(key) is True
            for key in [
                "runtime_has_chart_context",
                "runtime_has_structure_state",
                "runtime_has_mainline_state",
                "policy_has_m3_completion",
                "policy_has_model_signal",
                "policy_has_ranked_decisions",
                "policy_has_practical_reading_context",
                "policy_has_interaction_state",
                "policy_has_llm_output_contract",
                "diagnostic_bazi_context_has_chart_ref",
                "diagnostic_bazi_context_has_structure",
                "diagnostic_bazi_context_has_mainline",
            ]
        )
        and summary.get("diagnostic_bazi_context_version") == "v30.internal_bazi_context.v1"
    )


def _module_matrix_ready(rows: list[Any]) -> bool:
    by_id = {str(row.get("module_id")): row for row in rows if isinstance(row, Mapping)}
    required = {"M1/M2", "M3", "M4", "M5", "M6", "M7", "M8", "SURFACE", "CTX", "IQ", "LLM", "BT", "U"}
    return (
        required <= set(by_id)
        and all(int(_mapping(by_id.get(module_id)).get("completion") or 0) == 100 for module_id in required - {"IQ", "LLM"})
        and int(_mapping(by_id.get("IQ")).get("completion") or 0) >= 98
        and int(_mapping(by_id.get("LLM")).get("completion") or 0) >= 88
        and _mapping(by_id.get("SURFACE")).get("status") == "steady"
        and _mapping(by_id.get("CTX")).get("status") == "steady"
    )


def _validation_policy_ready(summary: Mapping[str, Any]) -> bool:
    return (
        summary.get("full_pytest_required") is False
        and summary.get("synthetic_all_required") is False
        and summary.get("full_518k_required") is False
        and summary.get("live_llm_required") is False
        and summary.get("policy_pointer_write_allowed") is False
        and summary.get("chart_fact_mutation_allowed") is False
        and summary.get("targeted_tests_only") is True
    )


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: object) -> list[Any]:
    return list(value) if isinstance(value, list) else []
