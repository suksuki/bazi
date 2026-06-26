from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from v30.presentation.client_model import build_presentation_model
from v30.runtime import attach_question_outcome, create_smoke_runtime
from v30.validation.real_business_bazi_reading_regression_pack import (
    run_real_business_bazi_reading_regression_pack,
)


REAL_BUSINESS_ANSWER_REFRESH_REGRESSION_VERSION = "v30.real_business_answer_refresh_regression.v1"

ANSWER_REFRESH_CASES: tuple[dict[str, Any], ...] = (
    {
        "case_id": "b3.answer_refresh.career_direct_001",
        "day_master": "甲",
        "day_master_element": "wood",
        "question_id": "q_v30_user_career_direction",
        "answer": "I want career direction first.",
        "selected_option": "",
        "expected_selected_domain": "career",
    },
    {
        "case_id": "b3.answer_refresh.practical_domain_choice_001",
        "day_master": "丙",
        "day_master_element": "fire",
        "question_id": "q_v30_practical_domain_focus",
        "answer": "Career",
        "selected_option": "domain:career",
        "expected_selected_domain": "career",
    },
    {
        "case_id": "b3.answer_refresh.wealth_direct_001",
        "day_master": "戊",
        "day_master_element": "earth",
        "question_id": "q_v30_user_wealth_tendency",
        "answer": "I want to understand wealth tendency.",
        "selected_option": "",
        "expected_selected_domain": "wealth",
    },
    {
        "case_id": "b3.answer_refresh.relationship_direct_001",
        "day_master": "庚",
        "day_master_element": "metal",
        "question_id": "q_v30_user_relationship_pattern",
        "answer": "I want relationship pattern first.",
        "selected_option": "",
        "expected_selected_domain": "relationship",
    },
    {
        "case_id": "b3.answer_refresh.hidden_factor_to_career_001",
        "day_master": "壬",
        "day_master_element": "water",
        "question_id": "q_v30_hidden_factor_boundary_discovery",
        "answer": "2021 and 2024 repeated as career pressure years.",
        "selected_option": "domain:career",
        "expected_selected_domain": "career",
    },
)


def run_real_business_answer_refresh_regression(*, case_limit: int = 5) -> dict[str, Any]:
    b2 = run_real_business_bazi_reading_regression_pack(case_limit=24)
    return build_real_business_answer_refresh_regression(
        b2_regression_pack=b2,
        answer_cases=ANSWER_REFRESH_CASES[: max(1, min(case_limit, len(ANSWER_REFRESH_CASES)))],
    )


def build_real_business_answer_refresh_regression(
    *,
    b2_regression_pack: Mapping[str, Any],
    answer_cases: Sequence[Mapping[str, Any]] = ANSWER_REFRESH_CASES,
) -> dict[str, Any]:
    rows = [_answer_refresh_row(case) for case in answer_cases]
    summary = _summary(b2_regression_pack, rows)
    decision = _decision(summary, rows)
    return {
        "version": REAL_BUSINESS_ANSWER_REFRESH_REGRESSION_VERSION,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if decision["answer_refresh_regression_ready"] else "blocked",
        "decision": decision,
        "refresh_summary": summary,
        "refresh_rows": rows,
        "business_scope": {
            "task_id": "B3",
            "title": "Business Reading Answer Refresh Regression",
            "acceptance_target": "structured answer refresh preserves accepted Bazi reading surface",
            "required_checks": [
                "b2_regression_pack_ready",
                "answer_panel_present",
                "interaction_state_consumes_answer",
                "chart_context_stable",
                "core_reading_fingerprint_stable",
                "customer_projection_still_safe",
            ],
            "boundary": "b3_regresses_answer_refresh_not_ui_polish_or_chart_fact_mutation",
        },
        "policy_boundary": {
            "full_pytest_run_by_default": False,
            "full_518k_run_by_default": False,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
            "training_signal_may_change_chart_facts": False,
            "boundary": "b3_is_read_only_answer_refresh_regression_and_does_not_mutate_chart_facts",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "b3_validates_answer_refresh_preserves_business_reading",
    }


def _answer_refresh_row(case: Mapping[str, Any]) -> dict[str, Any]:
    runtime = create_smoke_runtime(
        reading_id=str(case.get("case_id") or "b3-answer-refresh"),
        day_master=str(case.get("day_master") or "甲"),
        day_master_element=str(case.get("day_master_element") or "wood"),
        locale="zh",
    )
    before_view = build_presentation_model(runtime, role_key="user", locale="zh", client="web").model_dump(mode="json")
    before_fingerprint = _reading_fingerprint(before_view)
    question_id = str(case.get("question_id") or "")
    answer_payload = {
        "answer": str(case.get("answer") or ""),
        "outcome_status": "answered",
        "selected_option": str(case.get("selected_option") or ""),
        "confidence": 0.82,
        "feedback_tags": [str(case.get("expected_selected_domain") or "")],
    }
    refreshed = attach_question_outcome(runtime, question_id, answer_payload)
    after_view = build_presentation_model(refreshed, role_key="user", locale="zh", client="web").model_dump(mode="json")
    after_fingerprint = _reading_fingerprint(after_view)
    interaction = refreshed.question_plan.policy_effect.get("interaction_state", {})
    interaction = interaction if isinstance(interaction, Mapping) else {}
    answer_panel = after_view.get("answer_panel", {})
    answer_panel = answer_panel if isinstance(answer_panel, Mapping) else {}
    projection = after_view.get("projection_contract", {})
    projection = projection if isinstance(projection, Mapping) else {}
    reading_surface = after_view.get("reading_surface", {})
    reading_surface = reading_surface if isinstance(reading_surface, Mapping) else {}
    domain_cards = reading_surface.get("domain_cards", [])
    domain_cards = domain_cards if isinstance(domain_cards, list) else []
    expected_domain = str(case.get("expected_selected_domain") or "")
    checks = {
        "answer_panel_present": bool(answer_panel)
        and answer_panel.get("llm_metadata", {}).get("status") in {"accepted", "fallback", "deferred"},
        "interaction_state_version_ready": interaction.get("version") == "v30.interaction_state.v1",
        "interaction_consumes_answer": question_id in set(_str_list(interaction.get("answered_question_ids", []))),
        "selected_domain_expected": (
            not expected_domain
            or str(interaction.get("selected_domain") or "") == expected_domain
            or question_id.startswith("q_v30_user_")
        ),
        "visible_next_question_ready": bool(str(interaction.get("visible_next_question_id") or "")),
        "chart_context_stable": refreshed.chart_context == runtime.chart_context,
        "feature_evidence_stable": refreshed.feature_evidence == runtime.feature_evidence,
        "core_reading_fingerprint_stable": before_fingerprint == after_fingerprint,
        "five_customer_domain_cards_preserved": len(domain_cards) >= 5,
        "projection_contract_safe": (
            projection.get("version") == "v30.api_projection_contract.v1"
            and projection.get("leak_scan", {}).get("passed") is True
        ),
        "answer_boundary_non_mutating": answer_panel.get("boundary") in {
            "rule_bound_answer_no_llm_fact_mutation",
            "bounded_llm_answer_no_chart_fact_mutation",
        },
    }
    failed = [check_id for check_id, passed in checks.items() if not passed]
    return {
        "case_id": str(case.get("case_id") or ""),
        "question_id": question_id,
        "answer_refresh_ready": not failed,
        "checks": checks,
        "failed_check_ids": failed,
        "answer_panel_source": str(answer_panel.get("source") or ""),
        "llm_status": str(answer_panel.get("llm_metadata", {}).get("status") if isinstance(answer_panel.get("llm_metadata"), Mapping) else ""),
        "interaction_stage": str(interaction.get("interaction_stage") or ""),
        "selected_domain": str(interaction.get("selected_domain") or ""),
        "visible_next_question_id": str(interaction.get("visible_next_question_id") or ""),
        "domain_card_count": len(domain_cards),
        "boundary": "b3_case_checks_answer_refresh_not_chart_fact_mutation",
    }


def _reading_fingerprint(view: Mapping[str, Any]) -> dict[str, Any]:
    surface = view.get("reading_surface", {})
    surface = surface if isinstance(surface, Mapping) else {}
    core = surface.get("core_bazi_reading", {})
    core = core if isinstance(core, Mapping) else {}
    return {
        "chart_status": surface.get("chart_status"),
        "four_pillars": core.get("four_pillars"),
        "day_master": core.get("day_master"),
        "base_fact_summary": core.get("base_fact_summary"),
        "base_fact_explanations": core.get("base_fact_explanations"),
        "m1_m2_completion_summary": core.get("m1_m2_completion_summary"),
        "ranked_decisions": core.get("ranked_decisions"),
        "model_signal_summary": core.get("model_signal_summary"),
        "practical_domains": core.get("practical_domains"),
        "domain_cards": surface.get("domain_cards"),
    }


def _str_list(value: object) -> list[str]:
    return [str(row) for row in value] if isinstance(value, list) else []


def _summary(b2: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    b2_decision = b2.get("decision", {})
    b2_decision = b2_decision if isinstance(b2_decision, Mapping) else {}
    return {
        "b2_version": str(b2.get("version") or ""),
        "b2_ready": bool(b2_decision.get("business_reading_regression_ready")),
        "answer_case_count": len(rows),
        "passed_answer_case_count": sum(1 for row in rows if row.get("answer_refresh_ready")),
        "failed_answer_case_count": sum(1 for row in rows if not row.get("answer_refresh_ready")),
        "answer_panel_ready_count": sum(1 for row in rows if row.get("checks", {}).get("answer_panel_present") is True),
        "stable_core_fingerprint_count": sum(1 for row in rows if row.get("checks", {}).get("core_reading_fingerprint_stable") is True),
        "five_domain_card_count": sum(1 for row in rows if row.get("checks", {}).get("five_customer_domain_cards_preserved") is True),
    }


def _decision(summary: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    blockers: list[str] = []
    failed_rows = [row for row in rows if not row.get("answer_refresh_ready")]
    if summary.get("b2_version") != "v30.real_business_bazi_reading_regression_pack.v1":
        blockers.append("b2_regression_pack_missing")
    if not summary.get("b2_ready"):
        blockers.append("b2_regression_pack_not_ready")
    if int(summary.get("answer_case_count", 0) or 0) < 5:
        blockers.append("answer_refresh_case_count_below_minimum")
    if failed_rows:
        blockers.append("answer_refresh_rows_failed")
    ready = not blockers
    return {
        "answer_refresh_regression_ready": ready,
        "decision_status": "b3_answer_refresh_regression_ready" if ready else "b3_answer_refresh_regression_blocked",
        "blockers": blockers,
        "failed_case_ids": [str(row.get("case_id") or "") for row in failed_rows],
        "full_pytest_required": False,
        "full_518k_required": False,
        "policy_pointer_promotion_allowed": False,
        "chart_fact_mutation_allowed": False,
        "rationale": (
            "B3 ready: structured answer refresh preserves the accepted business reading surface."
            if ready
            else "B3 blocked: repair answer refresh or reading-surface stability failures."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision.get("answer_refresh_regression_ready"):
        return {
            "task_id": "B4",
            "title": "Business Reading Boundary And Blocked Input Regression",
            "selected_track": "business_bazi_acceptance",
            "scope": [
                "verify blocked and pending BirthInput states explain missing chart facts cleanly",
                "preserve customer-safe surface for unknown hour and invalid input",
                "keep deterministic chart facts sealed",
            ],
        }
    return {
        "task_id": "B3-FR",
        "title": "Business Reading Answer Refresh Failure Review",
        "selected_track": "business_bazi_acceptance",
        "scope": [
            "repair failed answer refresh rows",
            "do not reopen M1-M8 globally",
            "do not run full pytest unless release/full-freeze is explicitly requested",
        ],
    }
