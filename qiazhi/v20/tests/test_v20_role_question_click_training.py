from __future__ import annotations

from pathlib import Path

from v20.interaction.role_question_click import record_role_question_click
from v20.learning.role_question_click_training import (
    build_role_question_click_training_report,
    read_role_question_click_training_artifact,
    write_role_question_click_training_artifact,
)
from v20.storage.local_jsonl import LocalJsonlStore
from v20.tests.support_paths import read_v20_text


def test_v20_role_question_click_training_aggregates_role_group_domain_and_strategy(tmp_path: Path) -> None:
    store = LocalJsonlStore(runtime_dir=tmp_path)
    for index in range(3):
        record_role_question_click(
            input_id=f"role.click.{index}",
            source_role="analyst",
            question={
                "question_key": "q_career_structure",
                "domain": "career",
                "role_view_level": "technical_review",
                "question_strategy": "practitioner_review_question",
                "question_group": "domain",
                "seed_source_key": "seed.career.role_pressure",
                "next_question_atom_id": "atom.user.timing.trigger",
                "next_question_topic": "timing_trigger",
                "next_question_stage": "timing",
                "action_type": "answer_helpful",
            },
            store=store,
        )
    record_role_question_click(
        input_id="role.click.guest",
        source_role="guest",
        question={
            "question_key": "q_guest_entry",
            "domain": "career",
            "role_view_level": "entry",
            "question_strategy": "guest_entry_question",
            "question_group": "entry",
            "action_type": "skip",
        },
        store=store,
    )

    report = build_role_question_click_training_report(store=store)

    assert report["version"] == "v20.role_question_click_training_report.v1"
    assert report["status"] == "ready"
    assert report["click_count"] == 4
    analyst = next(row for row in report["role_summaries"] if row["role_key"] == "analyst")
    group = next(row for row in report["group_summaries"] if row["source_role"] == "analyst")
    seed = next(row for row in report["seed_summaries"] if row["source_role"] == "analyst")
    atom = next(row for row in report["next_question_atom_summaries"] if row["source_role"] == "analyst")
    reward = next(row for row in report["reward_summaries"] if row["source_role"] == "analyst")
    assert analyst["click_count"] == 3
    assert analyst["top_domain"] == "career"
    assert group["group_key"] == "domain"
    assert seed["seed_key"] == "seed.career.role_pressure"
    assert seed["click_count"] == 3
    assert atom["atom_id"] == "atom.user.timing.trigger"
    assert atom["sample_count"] == 3
    assert atom["reward_average"] == 1.0
    assert report["next_question_feedback_policy"]["status"] == "ready"
    assert report["next_question_feedback_policy"]["atom_boosts"]["atom.user.timing.trigger"] > 0
    assert reward["sample_count"] == 3
    assert reward["reward_average"] == 1.0
    assert any(row["action_key"] == "answer_helpful" for row in report["action_summaries"])
    assert report["recommendations"]
    assert any(row["recommendation_type"] == "review_seed_question_fit" for row in report["recommendations"])
    assert any(row["recommendation_type"] == "boost_question_candidate" for row in report["recommendations"])
    assert report["runtime_mutation"] is False
    assert "NO_QUESTION_TITLE_IN_CLICK_LEDGER" in report["guardrails"]


def test_v20_role_question_click_training_artifact_status_and_write(tmp_path: Path) -> None:
    store = LocalJsonlStore(runtime_dir=tmp_path)
    before = read_role_question_click_training_artifact(output_dir=tmp_path / "training" / "role_question_click")
    record_role_question_click(
        input_id="role.click.write",
        source_role="user",
        question={
            "question_key": "q_user_guided",
            "domain": "wealth",
            "role_view_level": "guided",
            "question_strategy": "guided_user_question",
            "question_group": "guided",
            "action_type": "select",
        },
        store=store,
    )
    written = write_role_question_click_training_artifact(store=store)

    assert before["status"] == "not_built"
    assert written["version"] == "v20.role_question_click_training_artifact_write.v1"
    assert written["status"] == "written"
    assert written["click_count"] == 1
    assert Path(written["latest_path"]).exists()


def test_v20_role_question_click_training_builds_atom_penalty_from_skip_feedback(tmp_path: Path) -> None:
    store = LocalJsonlStore(runtime_dir=tmp_path)
    for index in range(3):
        record_role_question_click(
            input_id=f"role.skip.{index}",
            source_role="user",
            question={
                "question_key": "q_relationship_structure",
                "domain": "relationship",
                "role_view_level": "guided",
                "question_strategy": "guided_user_question",
                "question_group": "domain",
                "next_question_atom_id": "atom.user.focus.relationship",
                "next_question_topic": "relationship_pattern",
                "next_question_stage": "focus",
                "action_type": "skip",
            },
            store=store,
        )

    report = build_role_question_click_training_report(store=store)

    assert report["next_question_feedback_policy"]["status"] == "ready"
    assert report["next_question_feedback_policy"]["atom_penalties"]["atom.user.focus.relationship"] < 0


def test_v20_role_question_click_learning_endpoint_is_declared() -> None:
    server_text = read_v20_text("server.py")

    assert "/api/v20/learning/role-question-click" in server_text
    assert "build_role_question_click_training_report" in server_text
