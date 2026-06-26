from __future__ import annotations

import json

from v20.interaction.question_ranker import question_ranking_policy_runtime
from v20.learning.question_runtime_pointer import (
    QUESTION_ACTIVE_POINTER_VERSION,
    build_question_runtime_pointer,
    write_question_runtime_pointer_activate_candidate,
)
from v20.storage.local_jsonl import local_jsonl_store_from_env
from v20.validation.next_question_synthetic import write_next_question_synthetic_validation_artifact
from v20.interaction.role_question_click import record_role_question_click
from v20.interaction.question_review import record_question_review
from v20.learning.role_question_click_training import write_role_question_click_training_artifact
from v20.learning.question_review_training import write_question_review_training_artifact


def test_v20_question_runtime_pointer_blocks_without_artifacts(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))

    pointer = build_question_runtime_pointer()

    assert pointer["status"] == "blocked"
    assert pointer["runtime_applied"] is False
    assert "question_source_training_not_ready" in pointer["blocking_gate"]


def test_v20_question_runtime_pointer_activates_source_and_ranking_policy(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    runtime = local_jsonl_store_from_env().runtime_dir
    source_dir = runtime / "training" / "question_source"
    ranking_dir = runtime / "training" / "question_ranking"
    source_dir.mkdir(parents=True, exist_ok=True)
    ranking_dir.mkdir(parents=True, exist_ok=True)
    source = {
        "version": "v20.question_source_training_report.v1",
        "status": "ready",
        "training_proposals": [
            {
                "source_key": "runtime_fusion",
                "sample_count": 4,
                "average_graph_score": 0.42,
                "average_question_score": 0.38,
            }
        ],
    }
    ranking = {
        "version": "v20.question_ranking_shadow_training_report.v1",
        "status": "ready",
        "shadow_policy": {
            "policy_id": "v20.question_ranking.test",
            "domain_weights": {"career": 0.05},
            "status_weights": {"confirmed": 0.06},
            "question_key_weights": {"q_career_direction": 0.02},
            "feature_count_weight": 0.004,
            "max_feature_count": 6,
            "alignment_weight": 0.16,
            "max_adjustment": 0.12,
            "status": "candidate",
            "guardrails": ["OFFLINE_GENERATED"],
        },
    }
    (source_dir / "latest.json").write_text(json.dumps(source), encoding="utf-8")
    (ranking_dir / "latest.json").write_text(json.dumps(ranking), encoding="utf-8")

    result = write_question_runtime_pointer_activate_candidate(source_role="system", reason="test")
    pointer = build_question_runtime_pointer()
    policy = question_ranking_policy_runtime()

    assert result["status"] == "candidate_active"
    assert result["runtime_mutation"] is True
    assert result["candidate"]["question_source_policy_count"] == 1
    assert result["candidate"]["question_rank_policy_ready"] is True
    assert pointer["status"] == "candidate_active"
    assert pointer["runtime_applied"] is True
    assert pointer["policy_payload"]["question_source_weight_policy"][0]["source_key"] == "runtime_fusion"
    assert policy.source == "active_question_pointer"
    assert policy.domain_weights["career"] == 0.05
    active_path = runtime / "training" / "question_policy_versions" / "active_pointer.json"
    active = json.loads(active_path.read_text(encoding="utf-8"))
    assert active["version"] == QUESTION_ACTIVE_POINTER_VERSION


def test_v20_question_runtime_pointer_consumes_next_question_synthetic_policy(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))

    write_next_question_synthetic_validation_artifact()
    result = write_question_runtime_pointer_activate_candidate(source_role="system", reason="next question synthetic")
    pointer = build_question_runtime_pointer()

    assert result["status"] == "candidate_active"
    assert result["candidate"]["next_question_plan_policy_ready"] is True
    assert pointer["runtime_applied"] is True
    assert pointer["policy_payload"]["next_question_plan_policy"]["stage_boosts"]["timing"] > 0


def test_v20_question_runtime_pointer_consumes_click_feedback_policy(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    store = local_jsonl_store_from_env()
    write_next_question_synthetic_validation_artifact(store=store)
    for index in range(3):
        record_role_question_click(
            input_id=f"click.feedback.{index}",
            source_role="user",
            question={
                "question_key": "q_time_relation_triggers",
                "domain": "time",
                "next_question_atom_id": "atom.user.timing.trigger",
                "next_question_topic": "timing_trigger",
                "next_question_stage": "timing",
                "action_type": "followup",
            },
            store=store,
        )
    write_role_question_click_training_artifact(store=store)

    result = write_question_runtime_pointer_activate_candidate(source_role="system", reason="click feedback")
    pointer = build_question_runtime_pointer()
    policy = pointer["policy_payload"]["next_question_plan_policy"]

    assert result["candidate"]["next_question_feedback_policy_ready"] is True
    assert policy["atom_boosts"]["atom.user.timing.trigger"] > 0
    assert pointer["runtime_applied"] is True


def test_v20_question_runtime_pointer_consumes_question_review_feedback_policy(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    store = local_jsonl_store_from_env()
    write_next_question_synthetic_validation_artifact(store=store)
    for index in range(2):
        record_question_review(
            input_id=f"review.feedback.{index}",
            source_role="analyst",
            question={
                "question_key": "q_relationship_structure",
                "domain": "relationship",
                "stage": "domain_reading",
                "role_target": "user",
                "question_strategy": "guided_user_question",
                "source": "runtime",
            },
            action="delete",
            reason="unfocused",
            store=store,
        )
    write_question_review_training_artifact(store=store)

    result = write_question_runtime_pointer_activate_candidate(source_role="system", reason="review feedback")
    pointer = build_question_runtime_pointer()
    policy = pointer["policy_payload"]["next_question_plan_policy"]

    assert result["candidate"]["question_review_feedback_policy_ready"] is True
    assert policy["atom_penalties"]["atom.guest.entry.relationship"] < 0
    assert policy["atom_penalties"]["atom.user.focus.relationship"] < 0
    assert pointer["runtime_applied"] is True
