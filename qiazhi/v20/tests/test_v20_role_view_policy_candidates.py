from __future__ import annotations

from pathlib import Path

from v20.interaction.role_question_click import record_role_question_click
from v20.learning.role_question_click_training import build_role_question_click_training_report
from v20.learning.role_view_policy_candidates import (
    build_role_view_policy_candidate_report,
    read_role_view_policy_candidate_artifact,
    write_role_view_policy_candidate_artifact,
)
from v20.storage.local_jsonl import LocalJsonlStore
from v20.tests.support_paths import read_v20_text


def test_v20_role_view_policy_candidates_are_built_from_click_recommendations(tmp_path: Path) -> None:
    store = LocalJsonlStore(runtime_dir=tmp_path)
    for index in range(3):
        record_role_question_click(
            input_id=f"role.policy.{index}",
            source_role="analyst",
            question={
                "question_key": "q_career_structure",
                "domain": "career",
                "role_view_level": "technical_review",
                "question_strategy": "practitioner_review_question",
                "question_group": "domain",
                "seed_source_key": "seed.career.role_pressure",
                "action_type": "answer_helpful",
            },
            store=store,
        )
    training = build_role_question_click_training_report(store=store)
    report = build_role_view_policy_candidate_report(click_training_report=training)

    assert report["version"] == "v20.role_view_policy_candidate_report.v1"
    assert report["status"] == "ready_for_replay"
    assert report["baseline_policy_version"] == "v20.role_view_policy.v1"
    assert report["candidate_policy_version"].startswith("v20.role_view_policy.candidate.")
    assert report["candidate_count"] >= 4
    assert report["policy_payload"]["question_limit_policy"]
    assert report["policy_payload"]["group_boost_policy"]
    assert report["policy_payload"]["domain_boost_policy"]
    assert report["policy_payload"]["strategy_boost_policy"]
    assert report["policy_payload"]["seed_fit_policy"]
    assert report["policy_payload"]["reward_policy"]
    seed_fit = report["policy_payload"]["seed_fit_policy"][0]
    reward = report["policy_payload"]["reward_policy"][0]
    assert seed_fit["candidate_type"] == "role_view_seed_fit_policy"
    assert seed_fit["seed_key"] == "seed.career.role_pressure"
    assert seed_fit["suggested_action"] == "review_seed_question_fit"
    assert reward["candidate_type"] == "role_view_reward_policy"
    assert reward["suggested_action"] == "boost_question_candidate"
    assert reward["question_key"] == "q_career_structure"
    assert all(row["runtime_allowed"] is False for row in report["candidates"])
    assert "NO_RUNTIME_ROLE_VIEW_POLICY_MUTATION" in report["guardrails"]


def test_v20_role_view_policy_candidate_artifact_status_and_write(tmp_path: Path) -> None:
    store = LocalJsonlStore(runtime_dir=tmp_path)
    before = read_role_view_policy_candidate_artifact(output_dir=tmp_path / "training" / "role_view_policy_candidates")
    for index in range(3):
        record_role_question_click(
            input_id=f"role.policy.write.{index}",
            source_role="guest",
            question={
                "question_key": "q_guest_entry",
                "domain": "career",
                "role_view_level": "entry",
                "question_strategy": "guest_entry_question",
                "question_group": "entry",
                "action_type": "answer_helpful",
            },
            store=store,
        )
    written = write_role_view_policy_candidate_artifact(store=store)

    assert before["status"] == "not_built"
    assert written["version"] == "v20.role_view_policy_candidate_artifact_write.v1"
    assert written["status"] == "written"
    assert written["candidate_count"] >= 1
    assert Path(written["latest_path"]).exists()


def test_v20_role_view_policy_candidate_endpoint_is_declared() -> None:
    server_text = read_v20_text("server.py")

    assert "/api/v20/learning/role-view-policy-candidates" in server_text
    assert "build_role_view_policy_candidate_report" in server_text
