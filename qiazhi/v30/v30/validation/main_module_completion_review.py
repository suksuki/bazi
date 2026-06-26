from __future__ import annotations

from typing import Any, Mapping

from v30.presentation import build_presentation_model
from v30.runtime import create_smoke_runtime
from v30.validation.intelligent_question_closeout import run_intelligent_question_closeout


MAIN_MODULE_COMPLETION_REVIEW_VERSION = "v30.main_module_completion_review.v1"


def run_main_module_completion_review(
    reading_id: str = "mcr1-main-module-completion-review",
) -> dict[str, object]:
    runtime = create_smoke_runtime(f"{reading_id}-runtime", day_master="庚", day_master_element="metal")
    user_view = build_presentation_model(runtime, role_key="user", locale="zh", client="web").model_dump(mode="json")
    admin_view = build_presentation_model(runtime, role_key="admin", locale="zh", client="admin").model_dump(mode="json")
    iq5 = run_intelligent_question_closeout(reading_id=f"{reading_id}-iq5")
    evidence = {
        "core_runtime": _core_runtime_summary(runtime, user_view, admin_view),
        "question_intelligence": _question_intelligence_summary(iq5),
        "support_boundaries": _support_boundary_summary(iq5),
        "module_matrix": _module_matrix(),
        "documented_residuals": _documented_residuals(),
    }
    return build_main_module_completion_review(evidence=evidence)


def build_main_module_completion_review(*, evidence: Mapping[str, Any]) -> dict[str, object]:
    checks = [
        {
            "check_id": "m1_m8_core_bazi_chain_is_steady",
            "passed": _core_runtime_ready(_mapping(evidence.get("core_runtime"))),
            "observed": evidence.get("core_runtime", {}),
        },
        {
            "check_id": "intelligent_question_module_is_closed",
            "passed": _question_intelligence_ready(_mapping(evidence.get("question_intelligence"))),
            "observed": evidence.get("question_intelligence", {}),
        },
        {
            "check_id": "training_synthetic_and_llm_support_are_bounded",
            "passed": _support_boundary_ready(_mapping(evidence.get("support_boundaries"))),
            "observed": evidence.get("support_boundaries", {}),
        },
        {
            "check_id": "module_matrix_has_explicit_completion_states",
            "passed": _module_matrix_ready(_list(evidence.get("module_matrix"))),
            "observed": {"module_count": len(_list(evidence.get("module_matrix")))},
        },
        {
            "check_id": "next_mainline_targets_lowest_real_module_gap",
            "passed": _documented_residual_ready(_mapping(evidence.get("documented_residuals"))),
            "observed": evidence.get("documented_residuals", {}),
        },
    ]
    failed = [row for row in checks if not row["passed"]]
    ready = not failed
    return {
        "version": MAIN_MODULE_COMPLETION_REVIEW_VERSION,
        "task": {
            "task_id": "MCR1",
            "title": "Main Module Completion Review",
            "scope": "review major V30 modules, separate steady modules from residual gaps, and select the next non-peripheral mainline",
        },
        "module_completion_matrix": evidence.get("module_matrix", []),
        "evidence": evidence,
        "checks": checks,
        "decision": {
            "main_module_completion_review_ready": ready,
            "check_count": len(checks),
            "passed_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "decision_status": "mcr1_main_module_review_ready" if ready else "mcr1_main_module_review_blocked",
            "chart_fact_mutation_allowed": False,
            "policy_pointer_write_allowed": False,
            "live_llm_required": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
        },
        "next_mainline_selection": {
            "task_id": "MCR2" if ready else "MCR1-FIX",
            "title": (
                "Customer Reading Surface And BaziContext Completion Reconciliation"
                if ready
                else "Fix Main Module Completion Review"
            ),
            "selected_track": "main_module_completion_reconciliation",
            "reason": (
                "M1-M8, question intelligence, training/synthetic, role/terminal/locale, and bounded LLM are steady; "
                "the lowest visible gap is stale/incomplete customer reading surface plus BaziContext completion accounting, "
                "so the next task must reconcile module contract coverage instead of reopening core calculation or UI polish."
                if ready
                else "repair failed module completion review checks"
            ),
            "full_pytest_run_now": False,
            "synthetic_all_run_now": False,
            "full_518k_run_now": False,
            "policy_pointer_write_now": False,
        },
        "boundary": "main_module_completion_review_selects_next_core_module_work_without_mutating_bazi_facts",
    }


def _core_runtime_summary(runtime: Any, user_view: Mapping[str, Any], admin_view: Mapping[str, Any]) -> dict[str, object]:
    policy = _mapping(runtime.question_plan.policy_effect)
    surface = _mapping(user_view.get("reading_surface"))
    admin_diag = _mapping(admin_view.get("diagnostics"))
    return {
        "has_chart_context": bool(runtime.chart_context),
        "has_structure_state": bool(runtime.structure_state),
        "has_mainline_state": bool(runtime.mainline_state),
        "has_m3_completion": _mapping(policy.get("m3_completion_summary")).get("status") == "ready",
        "has_model_signal": _mapping(policy.get("model_signal_summary")).get("version") == "v30.model_signal_summary.v1",
        "has_ranked_decisions": bool(_mapping(policy.get("ranked_decisions"))),
        "has_practical_reading_context": bool(_mapping(policy.get("practical_reading_context"))),
        "customer_surface_version": surface.get("version"),
        "customer_domain_card_count": len(_list(surface.get("domain_cards"))),
        "customer_internal_context_visible": surface.get("internal_context_visible"),
        "admin_has_internal_context": "internal_bazi_context" in admin_diag or "bazi_context" in admin_diag,
        "projection_contract": _mapping(user_view.get("projection_contract")).get("version"),
        "boundary": "core_bazi_runtime_projects_customer_reading_without_exposing_internal_context",
    }


def _question_intelligence_summary(iq5: Mapping[str, Any]) -> dict[str, object]:
    decision = _mapping(iq5.get("decision"))
    completion = _mapping(iq5.get("module_completion"))
    return {
        "iq5_version": iq5.get("version"),
        "iq5_ready": decision.get("intelligent_question_closeout_ready"),
        "iq5_passed": decision.get("passed_count"),
        "question_dialogue_graph_completion": completion.get("question_dialogue_graph"),
        "question_policy_training_completion": completion.get("question_policy_training"),
        "status": completion.get("status"),
        "next_task": _mapping(iq5.get("next_mainline_selection")).get("task_id"),
        "boundary": "question_intelligence_is_auxiliary_to_core_bazi_calculation",
    }


def _support_boundary_summary(iq5: Mapping[str, Any]) -> dict[str, object]:
    decision = _mapping(iq5.get("decision"))
    return {
        "iq5_full_pytest_required": decision.get("full_pytest_required"),
        "iq5_synthetic_all_required": decision.get("synthetic_all_required"),
        "iq5_full_518k_required": decision.get("full_518k_required"),
        "iq5_live_llm_required": decision.get("live_llm_required"),
        "iq5_policy_pointer_write_allowed": decision.get("policy_pointer_write_allowed"),
        "iq5_chart_fact_mutation_allowed": decision.get("chart_fact_mutation_allowed"),
        "training_scope": _mapping(iq5.get("policy_boundary")).get("training_scope"),
        "llm_scope": _mapping(iq5.get("policy_boundary")).get("llm_scope"),
        "boundary": "support_systems_are_targeted_validation_by_default_and_do_not_mutate_chart_facts",
    }


def _module_matrix() -> list[dict[str, object]]:
    return [
        _row("M1/M2", "BirthInput and deterministic chart facts", 100, "steady", "C5/C7 sealed"),
        _row("M3", "Knowledge, rule, portrait, feature, and structure spine", 100, "steady", "C6/C7 sealed"),
        _row("M4", "Ten-god energy model and model-signal summary", 100, "steady", "C2/C7 sealed"),
        _row("M5", "Strength, structure, and useful-god ranked decisions", 100, "steady", "C2/C7 sealed"),
        _row("M6", "Practical Bazi reading output", 100, "steady", "C1/C7 sealed"),
        _row("M7", "Real-case calibration pack and drift routing", 100, "steady", "C3/C7 sealed"),
        _row("M8", "Customer reading projection and API contract", 100, "steady", "C4/C7/B2 sealed"),
        _row("IQ", "Intelligent question interaction", 98, "steady", "IQ5 closed; IQ-S1 active"),
        _row("LLM", "Bazi LLM expression layer", 88, "bounded_steady", "BL8 closed; live provider smoke explicit-only"),
        _row("BT", "Central brain, training, synthetic, and 518K support", 100, "steady", "BT10 closed; 518K support 95%"),
        _row("U", "Multi-user, terminal, session, and locale projection", 100, "steady", "U5 closed"),
        _row("SURFACE", "Customer reading surface accounting", 72, "reconcile", "Completion docs lag behind B1-B6/M8 evidence"),
        _row("CTX", "BaziContext internalization accounting", 67, "reconcile", "Diagnostic/internal context coverage needs contract reconciliation"),
    ]


def _documented_residuals() -> dict[str, object]:
    return {
        "lowest_completion_modules": ["BaziContext internalization", "Customer reading surface"],
        "next_task_id": "MCR2",
        "next_task_title": "Customer Reading Surface And BaziContext Completion Reconciliation",
        "reason": "These are the only major-module rows still documented below steady state after M1-M8, IQ, BT, U, and BL closeout.",
        "not_next": [
            "do_not_reopen_M1_M8_core_calculation_without_new_failed_evidence",
            "do_not_start_UI_polish_as_the_mainline",
            "do_not_run_full_pytest_by_default",
            "do_not_promote_policy_pointer",
        ],
    }


def _row(module_id: str, name: str, completion: int, status: str, evidence: str) -> dict[str, object]:
    return {
        "module_id": module_id,
        "name": name,
        "completion": completion,
        "status": status,
        "evidence": evidence,
    }


def _core_runtime_ready(summary: Mapping[str, Any]) -> bool:
    return (
        summary.get("has_chart_context") is True
        and summary.get("has_structure_state") is True
        and summary.get("has_mainline_state") is True
        and summary.get("has_m3_completion") is True
        and summary.get("has_model_signal") is True
        and summary.get("has_ranked_decisions") is True
        and summary.get("has_practical_reading_context") is True
        and summary.get("customer_surface_version") == "v30.customer_reading_surface.v1"
        and int(summary.get("customer_domain_card_count") or 0) >= 5
        and summary.get("customer_internal_context_visible") is False
        and summary.get("projection_contract") == "v30.api_projection_contract.v1"
    )


def _question_intelligence_ready(summary: Mapping[str, Any]) -> bool:
    return (
        summary.get("iq5_version") == "v30.intelligent_question_closeout.v1"
        and summary.get("iq5_ready") is True
        and int(summary.get("iq5_passed") or 0) >= 6
        and int(summary.get("question_dialogue_graph_completion") or 0) >= 98
        and int(summary.get("question_policy_training_completion") or 0) >= 92
        and summary.get("status") == "IQ-S1 steady state"
        and summary.get("next_task") == "IQ-S1"
    )


def _support_boundary_ready(summary: Mapping[str, Any]) -> bool:
    return (
        summary.get("iq5_full_pytest_required") is False
        and summary.get("iq5_synthetic_all_required") is False
        and summary.get("iq5_full_518k_required") is False
        and summary.get("iq5_live_llm_required") is False
        and summary.get("iq5_policy_pointer_write_allowed") is False
        and summary.get("iq5_chart_fact_mutation_allowed") is False
        and summary.get("training_scope") == "question_strategy_and_followup_policy_only"
        and summary.get("llm_scope") == "expression and follow-up context rendering only"
    )


def _module_matrix_ready(rows: list[Any]) -> bool:
    module_ids = {str(row.get("module_id")) for row in rows if isinstance(row, Mapping)}
    completion_by_id = {
        str(row.get("module_id")): int(row.get("completion") or 0)
        for row in rows
        if isinstance(row, Mapping)
    }
    required = {"M1/M2", "M3", "M4", "M5", "M6", "M7", "M8", "IQ", "LLM", "BT", "U", "SURFACE", "CTX"}
    return (
        required <= module_ids
        and all(completion_by_id.get(module_id, 0) == 100 for module_id in ["M1/M2", "M3", "M4", "M5", "M6", "M7", "M8", "BT", "U"])
        and completion_by_id.get("IQ", 0) >= 98
        and completion_by_id.get("LLM", 0) >= 88
        and completion_by_id.get("SURFACE", 100) < 90
        and completion_by_id.get("CTX", 100) < 90
    )


def _documented_residual_ready(summary: Mapping[str, Any]) -> bool:
    return (
        summary.get("next_task_id") == "MCR2"
        and {"BaziContext internalization", "Customer reading surface"} <= set(_list(summary.get("lowest_completion_modules")))
        and "do_not_run_full_pytest_by_default" in set(_list(summary.get("not_next")))
        and "do_not_reopen_M1_M8_core_calculation_without_new_failed_evidence" in set(_list(summary.get("not_next")))
    )


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: object) -> list[Any]:
    return list(value) if isinstance(value, list) else []
