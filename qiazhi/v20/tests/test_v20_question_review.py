from __future__ import annotations

from pathlib import Path

from v20.interaction.question_review import (
    analyze_question_review,
    question_review_manifest,
    record_question_review,
)
from v20.storage.local_jsonl import LocalJsonlStore


def test_v20_question_review_manifest_declares_structured_actions() -> None:
    manifest = question_review_manifest()

    assert manifest["version"] == "v20.question_review_manifest.v1"
    assert {"approve", "rewrite", "downrank", "merge", "delete"}.issubset(set(manifest["actions"]))
    assert {"role_mismatch", "mainline_mismatch", "too_technical", "duplicate", "unfocused"}.issubset(
        set(manifest["reasons"])
    )
    assert manifest["ledger_name"] == "question_review_ledger"
    assert manifest["runtime_mutation"] is False
    assert "NO_RUNTIME_RULE_OR_MAINLINE_MUTATION" in manifest["guardrails"]


def test_v20_question_review_analysis_is_redacted_and_candidate_policy_only() -> None:
    analysis = analyze_question_review(
        input_id="question.review",
        source_role="analyst",
        action="downrank",
        reason="too_technical",
        question={
            "question_key": "q_branch_relation_detail",
            "question_id": "qid.branch",
            "domain": "branch",
            "stage": "review",
            "role_target": "analyst",
            "question_strategy": "practitioner_review_question",
        },
    )

    assert analysis["action"] == "downrank"
    assert analysis["reason"] == "too_technical"
    assert analysis["question_key"] == "q_branch_relation_detail"
    assert analysis["runtime_mutation"] is False
    assert "QUESTION_REVIEW_TRAINS_CANDIDATE_POLICY_ONLY" in analysis["guardrails"]


def test_v20_question_review_record_is_append_only_and_does_not_persist_title(tmp_path: Path) -> None:
    store = LocalJsonlStore(runtime_dir=tmp_path)
    result = record_question_review(
        input_id="question.review.record",
        source_role="admin",
        action="rewrite",
        reason="role_mismatch",
        question={
            "question_key": "q_income_stability",
            "question_id": "qid.wealth",
            "domain": "wealth",
            "stage": "focus",
            "role_target": "guest",
            "question_strategy": "guest_entry_question",
        },
        store=store,
    )
    text = (tmp_path / result["storage"]["relative_path"]).read_text(encoding="utf-8")

    assert result["storage"]["ledger_name"] == "question_review_ledger"
    assert result["runtime_mutation"] is True
    assert "q_income_stability" in text
    assert "role_mismatch" in text
    assert "财运怎么看" not in text


def test_v20_question_review_rejects_raw_text_and_invalid_source_role() -> None:
    try:
        analyze_question_review(
            input_id="question.review.bad",
            source_role="user",
            action="approve",
            question={"question_key": "q_bad"},
        )
    except ValueError as exc:
        assert "source role" in str(exc)
    else:
        raise AssertionError("user source role should not review questions")

    try:
        analyze_question_review(
            input_id="question.review.raw",
            source_role="analyst",
            action="approve",
            question={"question_key": "q_bad", "title": "不要保存标题"},
        )
    except ValueError as exc:
        assert "raw text" in str(exc)
    else:
        raise AssertionError("raw title marker should be rejected")
