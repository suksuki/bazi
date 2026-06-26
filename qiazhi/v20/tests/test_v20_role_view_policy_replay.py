from __future__ import annotations

from pathlib import Path

from v20.interaction.role_question_click import record_role_question_click
from v20.learning.role_view_policy_candidates import build_role_view_policy_candidate_report
from v20.learning.role_view_policy_replay import (
    build_role_view_policy_replay_report,
    read_role_view_policy_replay_artifact,
    write_role_view_policy_replay_artifact,
)
from v20.storage.local_jsonl import LocalJsonlStore
from v20.tests.support_paths import read_v20_text


def test_v20_role_view_policy_replay_compares_candidate_to_baseline(tmp_path: Path) -> None:
    store = LocalJsonlStore(runtime_dir=tmp_path)
    for index in range(3):
        record_role_question_click(
            input_id=f"role.replay.{index}",
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
    candidate = build_role_view_policy_candidate_report(store=store)
    replay = build_role_view_policy_replay_report(policy_candidate_report=candidate)

    assert replay["version"] == "v20.role_view_policy_replay_report.v1"
    assert replay["status"] == "ready_for_review"
    assert replay["comparison_count"] >= 4
    assert any(row["policy_key"] == "seed_fit_policy" for row in replay["comparisons"])
    assert any(row["policy_key"] == "reward_policy" for row in replay["comparisons"])
    assert any(row["expected_effect"] == "may_change_role_seed_question_priority_after_pointer" for row in replay["comparisons"])
    assert any(row["expected_effect"] == "may_change_question_priority_from_interaction_reward_after_pointer" for row in replay["comparisons"])
    assert replay["impact_summary"]["by_policy_key"]["seed_fit_policy"] == 1
    assert replay["impact_summary"]["by_policy_key"]["reward_policy"] == 1
    assert replay["impact_summary"]["offline_score_total"] > 0
    assert replay["impact_summary"]["by_source_role"]["analyst"] >= 1
    assert replay["ab_test_summary"]["version"] == "v20.role_view_policy_ab_replay_summary.v1"
    assert replay["ab_test_summary"]["candidate_win"] is True
    assert replay["ab_test_summary"]["net_lift"] > 0
    assert replay["ab_test_summary"]["risk_count"] == 0
    assert replay["ab_test_summary"]["by_role"]["analyst"]["net_lift"] > 0
    assert replay["ab_test_summary"]["by_policy_key"]["reward_policy"]["net_lift"] > 0
    assert replay["replay_result"]["positive_score_count"] >= 1
    assert replay["replay_result"]["ab_candidate_win"] is True
    assert replay["replay_result"]["ab_net_lift"] > 0
    assert replay["replay_result"]["eligible_for_runtime"] is False
    assert replay["replay_result"]["blocking_gate"] == "role_view_runtime_pointer_not_enabled"
    assert all(row["baseline_action"] == "keep_current_role_view_policy" for row in replay["comparisons"])
    assert all(row["ab_variant"] == "candidate" for row in replay["comparisons"])
    assert all(row["baseline_score"] == 0.0 for row in replay["comparisons"])
    assert all(row["runtime_allowed"] is False for row in replay["comparisons"])
    assert "ROLE_VIEW_REPLAY_IS_POLICY_DIFF_ONLY" in replay["guardrails"]
    assert "ROLE_VIEW_AB_REPLAY_IS_OFFLINE_ONLY" in replay["guardrails"]


def test_v20_role_view_policy_replay_artifact_status_and_write(tmp_path: Path) -> None:
    store = LocalJsonlStore(runtime_dir=tmp_path)
    before = read_role_view_policy_replay_artifact(output_dir=tmp_path / "training" / "role_view_policy_replay")
    for index in range(3):
        record_role_question_click(
            input_id=f"role.replay.write.{index}",
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
    written = write_role_view_policy_replay_artifact(store=store)

    assert before["status"] == "not_built"
    assert written["version"] == "v20.role_view_policy_replay_artifact_write.v1"
    assert written["status"] == "written"
    assert written["comparison_count"] >= 1
    assert Path(written["latest_path"]).exists()


def test_v20_role_view_policy_replay_endpoint_is_declared() -> None:
    server_text = read_v20_text("server.py")

    assert "/api/v20/learning/role-view-policy-replay" in server_text
    assert "build_role_view_policy_replay_report" in server_text
