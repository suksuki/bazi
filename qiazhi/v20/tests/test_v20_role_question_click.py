from __future__ import annotations

from pathlib import Path

from v20.interaction.role_question_click import analyze_role_question_click, record_role_question_click
from v20.storage.local_jsonl import LocalJsonlStore
from v20.tests.support_paths import read_v20_text


def test_v20_role_question_click_record_is_append_only_and_redacted(tmp_path: Path) -> None:
    store = LocalJsonlStore(runtime_dir=tmp_path)
    result = record_role_question_click(
        input_id="role.question.click",
        source_role="analyst",
        question={
            "question_key": "q_career_structure",
            "question_id": "qid.career",
            "domain": "career",
            "role_view_level": "technical_review",
            "question_strategy": "practitioner_review_question",
            "question_group": "structure",
            "measurement_topic": "事业",
            "measurement_stage": "structure_review",
            "role_view_source": "role_question_projection",
            "seed_source_key": "seed.career.role_pressure",
            "next_question_atom_id": "atom.user.timing.trigger",
            "next_question_topic": "timing_trigger",
            "next_question_stage": "timing",
            "action_type": "followup",
        },
        store=store,
    )
    text = (tmp_path / result["storage"]["relative_path"]).read_text(encoding="utf-8")

    assert result["version"] == "v20.role_question_click_record_result.v1"
    assert result["storage"]["ledger_name"] == "role_question_click_ledger"
    assert result["analysis"]["runtime_mutation"] is False
    assert result["analysis"]["click_signal"]["action_type"] == "followup"
    assert result["analysis"]["click_signal"]["reward_value"] == 0.8
    assert result["analysis"]["click_signal"]["next_question_atom_id"] == "atom.user.timing.trigger"
    assert result["runtime_mutation"] is True
    assert "NO_QUESTION_TITLE_PERSISTED" in result["analysis"]["guardrails"]
    assert "q_career_structure" in text
    assert "seed.career.role_pressure" in text
    assert "事业上官星" not in text


def test_v20_role_question_click_keeps_only_safe_seed_source_key() -> None:
    safe = analyze_role_question_click(
        input_id="role.question.seed",
        source_role="guest",
        question={
            "question_key": "q_income_factors",
            "domain": "wealth",
            "seed_source_key": "seed.wealth.opportunity_pressure",
        },
    )
    unsafe = analyze_role_question_click(
        input_id="role.question.seed.bad",
        source_role="guest",
        question={
            "question_key": "q_income_factors",
            "domain": "wealth",
            "seed_source_key": "decision.wealth.raw",
        },
    )

    assert safe["click_signal"]["seed_source_key"] == "seed.wealth.opportunity_pressure"
    assert unsafe["click_signal"]["seed_source_key"] == ""


def test_v20_role_question_click_normalizes_unknown_action_to_select() -> None:
    result = analyze_role_question_click(
        input_id="role.question.action",
        source_role="user",
        question={
            "question_key": "q_income_factors",
            "domain": "wealth",
            "action_type": "raw_free_text_action",
        },
    )

    assert result["click_signal"]["action_type"] == "select"
    assert result["click_signal"]["reward_value"] == 1.0


def test_v20_role_question_click_rejects_title_or_raw_text() -> None:
    try:
        analyze_role_question_click(
            input_id="role.question.bad",
            source_role="user",
            question={"question_key": "q_bad", "title": "不要保存标题"},
        )
    except ValueError as exc:
        assert "raw text" in str(exc)
    else:
        raise AssertionError("raw title marker should be rejected")


def test_v20_role_question_click_endpoint_is_declared() -> None:
    server_text = read_v20_text("server.py")
    schema_text = read_v20_text("api/schemas.py")

    assert "/api/v20/role-view/question-click/analyze" in server_text
    assert "/api/v20/role-view/question-click/record" in server_text
    assert "record_role_question_click" in server_text
    assert "RoleQuestionClickRequest" in schema_text
