from __future__ import annotations

from pathlib import Path

from v20.interaction.question_review import record_question_review
from v20.learning.question_dag_policy_replay import (
    build_question_dag_policy_replay_report,
    read_question_dag_policy_replay_artifact,
    write_question_dag_policy_replay_artifact,
)
from v20.learning.question_dag_training import build_question_dag_training_report
from v20.learning.question_review_training import build_question_review_training_report
from v20.storage.local_jsonl import LocalJsonlStore
from v20.tests.support_paths import read_v20_text


def test_v20_question_dag_policy_replay_compares_candidate_to_baseline(tmp_path: Path) -> None:
    store = LocalJsonlStore(runtime_dir=tmp_path)
    for index in range(2):
        record_question_review(
            input_id=f"dag.replay.review.{index}",
            source_role="analyst",
            action="downrank",
            reason="too_technical",
            question={
                "question_key": "q_branch_relation_detail",
                "domain": "branch",
                "stage": "review",
                "role_target": "user",
            },
            store=store,
        )
    review = build_question_review_training_report(store=store)
    dag = build_question_dag_training_report(question_review_training_report=review)
    replay = build_question_dag_policy_replay_report(question_dag_training_report=dag)

    assert replay["version"] == "v20.question_dag_policy_replay_report.v1"
    assert replay["status"] == "ready_for_review"
    assert replay["policy_key"] == "next_question_policy"
    assert replay["comparison_count"] >= 4
    assert any(row["comparison_key"] == "coherence_gate" for row in replay["comparisons"])
    assert any(row["comparison_key"] == "question_review_recommendations" for row in replay["comparisons"])
    assert replay["impact_summary"]["candidate_win"] is True
    assert replay["impact_summary"]["risk_count"] == 0
    assert replay["replay_result"]["eligible_for_runtime"] is False
    assert replay["replay_result"]["blocking_gate"] == "question_dag_runtime_pointer_not_enabled"
    assert all(row["runtime_allowed"] is False for row in replay["comparisons"])
    assert "QUESTION_DAG_REPLAY_IS_OFFLINE_ONLY" in replay["guardrails"]


def test_v20_question_dag_policy_replay_artifact_status_and_write(tmp_path: Path) -> None:
    store = LocalJsonlStore(runtime_dir=tmp_path)
    before = read_question_dag_policy_replay_artifact(output_dir=tmp_path / "training" / "question_dag_policy_replay")
    written = write_question_dag_policy_replay_artifact(store=store)

    assert before["status"] == "not_built"
    assert written["version"] == "v20.question_dag_policy_replay_artifact_write.v1"
    assert written["status"] == "written"
    assert written["comparison_count"] >= 1
    assert Path(written["latest_path"]).exists()


def test_v20_question_dag_policy_replay_endpoint_is_declared() -> None:
    server_text = read_v20_text("server.py")

    assert "/api/v20/learning/question-dag-replay" in server_text
    assert "build_question_dag_policy_replay_report" in server_text
