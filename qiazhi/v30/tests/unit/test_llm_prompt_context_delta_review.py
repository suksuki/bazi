from __future__ import annotations

from v30.llm.prompt_registry import build_bazi_llm_prompt_request
from v30.runtime import create_smoke_runtime
from v30.validation.llm_prompt_context_delta_review import (
    LLM_PROMPT_CONTEXT_DELTA_REVIEW_VERSION,
    build_llm_prompt_context_delta_review,
    run_llm_prompt_context_delta_review,
)


def test_llm_prompt_context_delta_review_accepts_module_bound_contexts() -> None:
    result = run_llm_prompt_context_delta_review(reading_id="pytest-core-evidence-3")

    assert result["version"] == LLM_PROMPT_CONTEXT_DELTA_REVIEW_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["llm_prompt_context_delta_ready"] is True
    assert result["decision"]["failed_check_ids"] == []
    assert result["quality_summary"]["domain_followup_domains"] == [
        "career",
        "relationship",
        "timing",
        "wealth",
    ]
    assert result["next_mainline_selection"]["task_id"] == "CORE-EVIDENCE-4"


def test_domain_followup_llm_context_uses_m3_m4_m5_m6_and_interaction_layers() -> None:
    runtime = create_smoke_runtime(reading_id="pytest-core-evidence-3-domain")
    request = build_bazi_llm_prompt_request(
        runtime,
        task_type="domain_followup",
        domain="career",
        role_key="user",
    )
    context = request["context_pack"]

    assert {"M3", "M4", "M5", "M6", "interaction_state", "known_user_signals"}.issubset(
        set(context["included_modules"])
    )
    assert {
        "structure_dynamics",
        "model_signals",
        "ranked_decisions",
        "practical_reading",
        "interaction_state",
        "known_user_signals",
    }.issubset({section["section_id"] for section in context["sections"]})
    assert context["budget"]["observed_context_sections"] <= context["budget"]["max_context_sections"]
    assert request["raw_runtime_payload_included"] is False
    assert request["chart_fact_mutation_allowed"] is False


def test_llm_prompt_context_delta_review_blocks_legacy_domain_followup_without_m3_m4() -> None:
    runtime = create_smoke_runtime(reading_id="pytest-core-evidence-3-legacy")
    request = build_bazi_llm_prompt_request(
        runtime,
        task_type="domain_followup",
        domain="career",
        role_key="user",
    )
    context = request["context_pack"]
    context["included_modules"] = ["M5", "M6", "interaction_state", "known_user_signals"]
    context["sections"] = [
        section
        for section in context["sections"]
        if section["section_id"] not in {"structure_dynamics", "model_signals"}
    ]

    result = build_llm_prompt_context_delta_review(
        reading_id="pytest-core-evidence-3-legacy",
        prompt_requests=[request],
    )

    assert result["status"] == "blocked"
    assert result["decision"]["llm_prompt_context_delta_ready"] is False
    assert "domain_followup_uses_core_bazi_modules" in result["decision"]["failed_check_ids"]
    assert "domain_followup_uses_module_sections" in result["decision"]["failed_check_ids"]
