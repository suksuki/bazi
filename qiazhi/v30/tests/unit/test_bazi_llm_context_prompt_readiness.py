from __future__ import annotations

import pytest

from v30.llm import (
    BAZI_LLM_CONTEXT_PACK_VERSION,
    BAZI_LLM_PROMPT_REGISTRY_VERSION,
    build_bazi_llm_context_pack,
    build_bazi_llm_prompt_request,
    prompt_contract_for_task,
    supported_bazi_llm_roles,
    supported_bazi_llm_tasks,
)
from v30.runtime import create_smoke_runtime
from v30.validation import run_bazi_llm_context_prompt_readiness


def test_bazi_llm_context_packs_are_task_specific_and_bounded() -> None:
    runtime = create_smoke_runtime(reading_id="pytest-bl-context")

    customer = build_bazi_llm_context_pack(runtime, task_type="customer_initial_reading")
    hidden = build_bazi_llm_context_pack(runtime, task_type="hidden_factor_dialogue")

    assert customer["version"] == BAZI_LLM_CONTEXT_PACK_VERSION
    assert customer["context_pack"] == "BaziCoreContext"
    assert hidden["context_pack"] == "BaziHiddenFactorDialogueContext"
    assert customer["sections"] != hidden["sections"]
    assert customer["fact_boundary"]["chart_fact_mutation_allowed"] is False
    assert customer["budget"]["observed_context_sections"] <= customer["budget"]["max_context_sections"]
    assert customer["budget"]["observed_evidence_items"] <= customer["budget"]["max_evidence_items"]
    assert "raw_runtime_payload" in customer["excluded_modules"]
    assert "training" in customer["excluded_modules"]
    assert customer["role_contract"]["audience"] == "customer_reading"
    assert customer["role_contract"]["diagnostics_visible"] is False


def test_prompt_registry_builds_matching_contracts_for_all_bazi_tasks() -> None:
    runtime = create_smoke_runtime(reading_id="pytest-bl-prompts")

    for task_type in supported_bazi_llm_tasks():
        role_key = "practitioner" if task_type == "practitioner_analysis" else "user"
        request = build_bazi_llm_prompt_request(runtime, task_type=task_type, role_key=role_key)
        contract = request["prompt_contract"]
        context = request["context_pack"]
        assert contract["version"] == BAZI_LLM_PROMPT_REGISTRY_VERSION
        assert contract["task_type"] == task_type
        assert context["context_pack"] == contract["required_context_pack"]
        assert request["raw_runtime_payload_included"] is False
        assert request["chart_fact_mutation_allowed"] is False
        assert contract["verifier"]["checks"]
        assert contract["fallback"]["on_verifier_failure"] == "block_llm_output_and_keep_verified_answer"
        assert contract["role_contract"]["role_contract_id"] == context["role_contract"]["role_contract_id"]


def test_bazi_llm_role_contracts_gate_user_visibility() -> None:
    runtime = create_smoke_runtime(reading_id="pytest-bl-roles")

    guest = build_bazi_llm_prompt_request(runtime, task_type="customer_initial_reading", role_key="guest")
    user = build_bazi_llm_prompt_request(runtime, task_type="customer_initial_reading", role_key="user")
    practitioner = build_bazi_llm_prompt_request(runtime, task_type="practitioner_analysis", role_key="practitioner")

    guest_context = guest["context_pack"]
    user_context = user["context_pack"]
    practitioner_context = practitioner["context_pack"]
    guest_sections = {section["section_id"] for section in guest_context["sections"]}
    user_sections = {section["section_id"] for section in user_context["sections"]}
    practitioner_sections = {section["section_id"] for section in practitioner_context["sections"]}

    assert guest_context["role_contract"]["audience"] == "guest_preview"
    assert guest_context["budget"]["max_context_sections"] == 3
    assert "diagnostics_summary" not in guest_sections
    assert "structure_dynamics" not in guest_sections
    assert user_context["role_contract"]["audience"] == "customer_reading"
    assert "diagnostics_summary" not in user_sections
    assert practitioner_context["role_contract"]["diagnostics_visible"] is True
    assert "structure_dynamics" in practitioner_sections


def test_every_bazi_llm_role_is_covered_by_readiness() -> None:
    result = run_bazi_llm_context_prompt_readiness(reading_id="pytest-bl-role-coverage")
    observed_roles = {row["role_key"] for row in result["task_results"]}

    assert observed_roles == set(supported_bazi_llm_roles())
    assert "all_required_roles_have_prompt_contracts" in {row["check_id"] for row in result["checks"]}


def test_bazi_llm_context_prompt_readiness_accepts_bl1_bl3() -> None:
    result = run_bazi_llm_context_prompt_readiness(reading_id="pytest-bl-readiness")

    assert result["version"] == "v30.bazi_llm_context_prompt_readiness.v1"
    assert result["decision"]["decision_status"] == "bl1_bl3_bazi_llm_context_prompt_ready"
    assert result["decision"]["readiness_ready"] is True
    assert result["decision"]["llm_execution_performed"] is False
    assert result["next_mainline_selection"]["task_id"] == "BL4"


def test_unknown_bazi_llm_task_is_rejected() -> None:
    runtime = create_smoke_runtime(reading_id="pytest-bl-invalid")

    with pytest.raises(ValueError):
        build_bazi_llm_context_pack(runtime, task_type="giant_prompt_all_context")
    with pytest.raises(ValueError):
        prompt_contract_for_task("giant_prompt_all_context")
    with pytest.raises(ValueError):
        build_bazi_llm_prompt_request(runtime, task_type="practitioner_analysis", role_key="guest")
