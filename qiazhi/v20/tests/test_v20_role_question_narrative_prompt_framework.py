from __future__ import annotations

from pathlib import Path

from v20.role_view.narrative_prompt_framework import (
    answer_prompt_profile_for_role,
    build_role_question_narrative_prompt_framework,
    question_narrative_contract_for_role,
    voice_profile_for_role,
)


def test_v20_role_question_narrative_prompt_framework_defines_voice_profiles() -> None:
    framework = build_role_question_narrative_prompt_framework()

    assert framework["version"] == "v20.role_question_narrative_prompt_framework.v1"
    assert framework["status"] == "runtime_consumed_and_training_ready"
    assert framework["completion_percent"] == 100
    profiles = {row["voice_profile"]: row for row in framework["voice_profiles"]}
    assert set(profiles) == {
        "guest_soft_entry",
        "user_guided_reading",
        "practitioner_evidence_review",
        "admin_runtime_observe",
    }
    assert "why_now" in profiles["user_guided_reading"]["question_structure"]
    assert "boundary" in profiles["practitioner_evidence_review"]["question_structure"]
    assert "runtime" in profiles["admin_runtime_observe"]["required_elements"]
    assert framework["mainline_steps"][0]["status"] == "completed"
    assert framework["mainline_steps"][1]["label"] == "add_question_narrative_schema"
    assert framework["mainline_steps"][1]["status"] == "completed"
    assert framework["mainline_steps"][2]["status"] == "completed"
    assert all(row["status"] == "completed" for row in framework["mainline_steps"])
    assert "llm.practitioner_answer_prompt.answer_prompt_profile" in framework["runtime_consumers"]
    assert "NO_HUMAN_REVIEW_GATE" in framework["guardrails"]


def test_v20_role_question_narrative_contracts_are_role_specific() -> None:
    guest = question_narrative_contract_for_role("guest")
    user = question_narrative_contract_for_role("user")
    practitioner = question_narrative_contract_for_role("practitioner")
    admin = question_narrative_contract_for_role("admin")

    assert guest["voice_profile"] == "guest_soft_entry"
    assert user["voice_profile"] == "user_guided_reading"
    assert practitioner["voice_profile"] == "practitioner_evidence_review"
    assert admin["voice_profile"] == "admin_runtime_observe"
    assert "dense_jargon" in " ".join(guest["tone_guardrails"])
    assert "counterexample_condition" in " ".join(practitioner["tone_guardrails"])
    assert "preserve_question_key_domain_and_rank" in admin["tone_guardrails"]


def test_v20_answer_prompt_profile_for_role_controls_llm_voice() -> None:
    profile = answer_prompt_profile_for_role("analyst", locale="zh")

    assert profile["version"] == "v20.answer_prompt_profile.v1"
    assert profile["voice_profile"] == "practitioner_evidence_review"
    assert "证据链" in profile["answer_structure"]
    assert "candidate_as_conclusion" in profile["forbidden_patterns"]
    assert profile["locale_policy"]["locale"] == "zh"
    assert "PROMPT_MUST_USE_VERIFIED_CONTEXT" in profile["guardrails"]


def test_v20_role_question_narrative_prompt_framework_is_documented() -> None:
    root = Path(__file__).resolve().parents[1]
    doc = root.joinpath("docs/V20_ROLE_QUESTION_NARRATIVE_PROMPT_FRAMEWORK.md").read_text(encoding="utf-8")
    roadmap = root.joinpath("docs/V20_MAINLINE_TRAINING_ROADMAP.md").read_text(encoding="utf-8")

    assert "guest_soft_entry" in doc
    assert "answer_prompt_profile_training" in doc
    assert "docs/V20_ROLE_QUESTION_NARRATIVE_PROMPT_FRAMEWORK.md" in roadmap
    assert "docs/V20_LLM_PROMPT_CONTEXT_DESIGN.md" in roadmap
    assert "role_question_narrative_prompt_framework" in roadmap
    llm_doc = root.joinpath("docs/V20_LLM_PROMPT_CONTEXT_DESIGN.md").read_text(encoding="utf-8")
    assert "context.system_understanding" in llm_doc
    assert "role_context" in llm_doc
    assert "bazi_context_profile" in llm_doc
    assert "answer_contract" in llm_doc
    assert "answer_plan_rewrite.context.v2" in llm_doc
    assert "answer/prompt_context.py" in llm_doc


def test_v20_voice_profile_for_role_maps_known_roles() -> None:
    assert voice_profile_for_role("guest")["voice_profile"] == "guest_soft_entry"
    assert voice_profile_for_role("user")["voice_profile"] == "user_guided_reading"
    assert voice_profile_for_role("practitioner")["voice_profile"] == "practitioner_evidence_review"
    assert voice_profile_for_role("lab")["voice_profile"] == "admin_runtime_observe"
