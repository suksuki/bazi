from __future__ import annotations

from pathlib import Path

from v20.interaction.question_review import record_question_review
from v20.learning.question_review_training import (
    build_question_review_training_report,
    read_question_review_training_artifact,
    write_question_review_training_artifact,
)
from v20.storage.local_jsonl import LocalJsonlStore
from v20.tests.support_paths import read_v20_text


def test_v20_question_review_training_aggregates_reviews_and_recommends_candidates(tmp_path: Path) -> None:
    store = LocalJsonlStore(runtime_dir=tmp_path)
    for index in range(2):
        record_question_review(
            input_id=f"question.review.training.{index}",
            source_role="analyst",
            action="downrank",
            reason="too_technical",
            question={
                "question_key": "q_branch_relation_detail",
                "question_id": "qid.branch",
                "domain": "branch",
                "stage": "review",
                "role_target": "user",
                "question_strategy": "practitioner_review_question",
            },
            store=store,
        )
    record_question_review(
        input_id="question.review.training.approve",
        source_role="admin",
        action="approve",
        reason="",
        question={
            "question_key": "q_admin_observe",
            "question_id": "qid.observe",
            "domain": "system",
            "stage": "observe",
            "role_target": "admin",
            "question_strategy": "observation_questions",
        },
        store=store,
    )

    report = build_question_review_training_report(store=store)

    assert report["version"] == "v20.question_review_training_report.v1"
    assert report["status"] == "ready"
    assert report["review_count"] == 3
    action = next(row for row in report["action_summaries"] if row["action_key"] == "downrank")
    reason = next(row for row in report["reason_summaries"] if row["reason_key"] == "too_technical")
    question = next(row for row in report["question_summaries"] if row["question_key"] == "q_branch_relation_detail")
    assert action["review_count"] == 2
    assert reason["review_count"] == 2
    assert question["negative_ratio"] == 1.0
    assert any(row["recommendation_type"] == "suppress_question_candidate" for row in report["recommendations"])
    assert any(row["recommendation_type"] == "suppress_role_stage_question_candidate" for row in report["recommendations"])
    assert report["runtime_mutation"] is False
    assert "QUESTION_REVIEW_TRAINING_IS_OFFLINE_ONLY" in report["guardrails"]


def test_v20_question_review_training_artifact_status_and_write(tmp_path: Path) -> None:
    store = LocalJsonlStore(runtime_dir=tmp_path)
    before = read_question_review_training_artifact(output_dir=tmp_path / "training" / "question_review")
    record_question_review(
        input_id="question.review.training.write",
        source_role="admin",
        action="approve",
        reason="",
        question={
            "question_key": "q_approve",
            "domain": "career",
            "stage": "focus",
            "role_target": "user",
        },
        store=store,
    )
    written = write_question_review_training_artifact(store=store)

    assert before["status"] == "not_built"
    assert written["version"] == "v20.question_review_training_artifact_write.v1"
    assert written["status"] == "written"
    assert written["review_count"] == 1
    assert Path(written["latest_path"]).exists()


def test_v20_question_review_training_endpoints_are_declared() -> None:
    server_text = read_v20_text("server.py")

    assert "/api/v20/learning/question-review" in server_text
    assert "/api/v20/learning/question-dag" in server_text
    assert "/api/v20/question-review/analyze" in server_text
    assert "/api/v20/question-review/record" in server_text
    assert "build_question_review_training_report" in server_text
    assert "build_question_dag_training_report" in server_text
    assert "record_question_review" in server_text
