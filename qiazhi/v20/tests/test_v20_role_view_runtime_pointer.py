from __future__ import annotations

import json
from pathlib import Path

from v20.interaction.role_question_click import record_role_question_click
from v20.role_view.runtime_pointer import (
    build_role_view_runtime_pointer,
    write_role_view_runtime_pointer_activate_candidate,
    write_role_view_runtime_pointer_rollback,
)
from v20.storage.local_jsonl import LocalJsonlStore
from v20.tests.support_paths import read_v20_text


def test_v20_role_view_runtime_pointer_is_prefight_only_without_candidates(tmp_path: Path) -> None:
    pointer = build_role_view_runtime_pointer(store=LocalJsonlStore(runtime_dir=tmp_path))

    assert pointer["version"] == "v20.role_view_runtime_pointer.v1"
    assert pointer["status"] == "not_enough_data"
    assert pointer["active_policy_version"] == "v20.role_view_policy.v1"
    assert pointer["runtime_applied"] is False
    assert pointer["runtime_allowed"] is False
    assert pointer["blocking_gate"] == "not_enough_data"
    assert "ROLE_VIEW_RUNTIME_POINTER_FAST_ITERATION" in pointer["guardrails"]


def test_v20_role_view_runtime_pointer_applies_answer_governance_training_directly(tmp_path: Path) -> None:
    store = LocalJsonlStore(runtime_dir=tmp_path)
    training_dir = tmp_path / "training" / "answer_governance"
    training_dir.mkdir(parents=True, exist_ok=True)
    (training_dir / "latest.json").write_text(
        json.dumps(
            {
                "version": "v20.answer_governance_training_report.v1",
                "status": "ready",
                "average_quality_score": 1.0,
                "parameter_targets": {
                    "answer_guidance_weight": 0.014,
                    "role_answer_governance_weight": 0.012,
                    "prompt_context_budget_weight": 0.01,
                    "stream_answer_quality_weight": 0.012,
                },
                "stream_answer_governance_summary": {
                    "version": "v20.stream_answer_governance_summary.v1",
                    "average_quality_score": 1.0,
                    "sample_count": 2,
                    "weak_or_thin_count": 0,
                },
            }
        ),
        encoding="utf-8",
    )

    pointer = build_role_view_runtime_pointer(store=store)

    assert pointer["status"] == "answer_governance_active"
    assert pointer["runtime_allowed"] is True
    assert pointer["runtime_answer_governance_applied"] is True
    assert pointer["runtime_effect"] == "role_answer_governance_policy_active"
    rows = pointer["policy_payload"]["answer_governance_style_policy"]
    assert {row["source_role"] for row in rows} >= {"guest", "user", "analyst", "admin"}
    assert rows[0]["style_weight_delta"] == 0.012
    assert rows[0]["prompt_context_budget_delta"] == 0.01
    assert rows[0]["stream_answer_quality_delta"] == 0.012
    assert rows[0]["stream_average_quality_score"] == 1.0
    assert "ROLE_ANSWER_GOVERNANCE_TRAINING_APPLIES_DIRECTLY" in pointer["guardrails"]


def test_v20_role_view_runtime_pointer_exposes_replay_gate_for_seed_fit_candidate(tmp_path: Path) -> None:
    store = LocalJsonlStore(runtime_dir=tmp_path)
    for index in range(3):
        record_role_question_click(
            input_id=f"role.pointer.{index}",
            source_role="user",
            question={
                "question_key": "q_income_factors",
                "domain": "wealth",
                "role_view_level": "guided",
                "question_strategy": "guided_user_question",
                "question_group": "domain",
                "seed_source_key": "seed.wealth.opportunity_pressure",
            },
            store=store,
        )

    pointer = build_role_view_runtime_pointer(store=store)

    assert pointer["status"] == "candidate_replay_ready"
    assert pointer["candidate_count"] >= 1
    assert pointer["comparison_count"] >= 1
    assert pointer["policy_payload_counts"]["seed_fit_policy"] == 1
    assert pointer["replay_impact_summary"]["by_policy_key"]["seed_fit_policy"] == 1
    assert pointer["ab_test_summary"]["net_lift"] > 0
    assert pointer["replay_ab_test_summary"]["candidate_win"] is True
    assert pointer["calibration"]["version"] == "v20.role_view_policy_calibration_report.v1"
    assert pointer["calibration"]["suggested_thresholds"]["min_promotion_comparisons"] >= 3
    assert pointer["promotion_gate"]["status"] == "blocked"
    assert pointer["runtime_applied"] is False
    assert pointer["runtime_allowed"] is False
    assert pointer["runtime_effect"] == "baseline_role_view_policy_active"
    assert pointer["blocking_gate"]
    assert pointer["policy_payload"] == {}
    assert "ROLE_VIEW_POLICY_PROMOTION_REQUIRES_GATE" in pointer["guardrails"]


def test_v20_role_view_runtime_pointer_can_activate_and_rollback_after_promotion_gate(tmp_path: Path) -> None:
    store = LocalJsonlStore(runtime_dir=tmp_path)
    for index in range(4):
        record_role_question_click(
            input_id=f"role.pointer.activate.{index}",
            source_role="user",
            question={
                "question_key": "q_income_factors",
                "domain": "wealth",
                "role_view_level": "guided",
                "question_strategy": "guided_user_question",
                "question_group": "domain",
                "seed_source_key": "seed.wealth.opportunity_pressure",
            },
            store=store,
        )

    activation = write_role_view_runtime_pointer_activate_candidate(source_role="admin", reason="test activate", store=store)
    active_pointer = build_role_view_runtime_pointer(store=store)
    rollback = write_role_view_runtime_pointer_rollback(source_role="admin", reason="test rollback", store=store)
    rollback_pointer = build_role_view_runtime_pointer(store=store)

    assert activation["status"] == "candidate_active"
    assert activation["promotion_gate"]["eligible_for_runtime"] is True
    assert active_pointer["status"] == "candidate_active"
    assert active_pointer["runtime_applied"] is True
    assert active_pointer["runtime_allowed"] is True
    assert active_pointer["policy_payload"]
    assert rollback["status"] == "rolled_back"
    assert rollback_pointer["active_policy_version"] == "v20.role_view_policy.v1"
    assert rollback_pointer["runtime_applied"] is False
    assert rollback_pointer["policy_payload"] == {}


def test_v20_role_view_runtime_pointer_endpoint_is_declared() -> None:
    server_text = read_v20_text("server.py")

    assert "/api/v20/role-view/runtime-pointer" in server_text
    assert "/api/v20/admin/role-view/runtime-pointer/activate-candidate" in server_text
    assert "/api/v20/admin/role-view/runtime-pointer/rollback" in server_text
    assert "build_role_view_runtime_pointer" in server_text
    assert "write_role_view_runtime_pointer_activate_candidate" in server_text
