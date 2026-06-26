from __future__ import annotations

from pathlib import Path

from v20.learning.orchestrator_policy_candidates import (
    build_orchestrator_policy_candidate_report,
    read_orchestrator_policy_candidate_artifact,
    write_orchestrator_policy_candidate_artifact,
)
from v20.learning.orchestrator_memory_training import build_orchestrator_memory_training_report
from v20.learning.training_iteration import run_training_iteration
from v20.storage.local_jsonl import LocalJsonlStore
import v20.learning.training_iteration as training_iteration


def test_v20_orchestrator_policy_candidates_convert_memory_training_to_review_only_policy_drafts() -> None:
    memory_report = build_orchestrator_memory_training_report(
        signals=(
            _memory_signal(1, "accept_primary"),
            _memory_signal(2, "accept_primary"),
            _memory_signal(3, "switch_to_supporting"),
        )
    )
    report = build_orchestrator_policy_candidate_report(memory_training_report=memory_report)
    by_type = {row["candidate_type"]: row for row in report["candidates"]}

    assert report["version"] == "v20.orchestrator_policy_candidate_report.v1"
    assert report["status"] == "ready_for_fast_iteration"
    assert report["runtime_mutation"] is False
    assert report["policy_observability_input_summary"]["version"] == "v20.orchestrator_policy_candidate_observability_input.v1"
    assert report["quality_scoring_policy"]["version"] == "v20.orchestrator_policy_candidate_quality_policy.v1"
    assert report["quality_scoring_policy"]["thresholds"]["high_quality_min"] == 0.72
    assert report["candidate_quality_summary"]["version"] == "v20.orchestrator_policy_candidate_quality_summary.v1"
    assert report["candidate_quality_summary"]["quality_policy_version"] == report["quality_scoring_policy"]["version"]
    assert report["candidate_quality_summary"]["candidate_count"] == report["candidate_count"]
    assert [row["quality_rank"] for row in report["candidates"]] == list(range(1, report["candidate_count"] + 1))
    assert all("quality_score" in row and "quality_band" in row and row["quality_policy_version"] == report["quality_scoring_policy"]["version"] for row in report["candidates"])
    assert by_type["mainline_arbitration_weight_policy"]["suggested_action"] == "increase_primary_stability_weight"
    assert by_type["question_focus_policy"]["suggested_action"] == "review_domain_question_focus_boost"
    assert by_type["brain_memory_policy"]["suggested_action"] == "keep_time_layer_missing_as_review_boundary"
    assert all(row["runtime_allowed"] is True for row in report["candidates"])
    assert report["review_artifact"]["review_status"] == "auto_recorded"
    assert "AUTO_ITERATION_POLICY_CANDIDATE" in report["guardrails"]
    assert "POLICY_OBSERVABILITY_RECOMMENDATIONS_CAN_FEED_NEXT_CANDIDATE" in report["guardrails"]
    assert "CANDIDATE_QUALITY_SCORE_IS_RANKING_ONLY" in report["guardrails"]


def test_v20_orchestrator_policy_candidates_imports_question_source_training_proposals() -> None:
    memory_report = build_orchestrator_memory_training_report(
        signals=(
            _memory_signal(1, "accept_primary"),
            _memory_signal(2, "accept_primary"),
            _memory_signal(3, "accept_primary"),
        )
    )
    source_training_report = {
        "version": "v20.question_source_training_report.v1",
        "status": "ready",
        "training_proposals": [
            {
                "target": "question_source_graph_quality_policy",
                "source_key": "source.guest.008",
                "suggested_action": "increase_source_quality_prior",
                "sample_count": 6,
                "average_graph_score": 0.36,
                "average_question_score": 0.27,
                "status": "candidate_from_offline_training",
            }
        ],
    }
    report = build_orchestrator_policy_candidate_report(
        memory_training_report=memory_report,
        question_source_training_report=source_training_report,
    )
    by_type = {row["candidate_type"]: row for row in report["candidates"]}

    assert "question_source_graph_quality_policy" in by_type
    source_candidate = by_type["question_source_graph_quality_policy"]
    assert source_candidate["source_key"] == "source.guest.008"
    assert source_candidate["sample_count"] == 6
    assert source_candidate["average_graph_score"] == 0.36
    assert source_candidate["average_question_score"] == 0.27
    assert source_candidate["runtime_allowed"] is True


def test_v20_orchestrator_policy_candidates_consume_policy_observability_recommendations() -> None:
    memory_report = build_orchestrator_memory_training_report(signals=(_memory_signal(1, "accept_primary"),))
    policy_report = {
        "version": "v20.orchestrator_policy_observability_training_report.v1",
        "status": "ready",
        "observation_count": 4,
        "candidate_consumed_ratio": 0.25,
        "fallback_ratio": 0.75,
        "trend_summary": {"status": "fallback_pressure"},
        "strategy_recommendations": [
            {
                "recommendation_key": "inspect_fallback_pressure",
                "recommendation_type": "rollback_watch",
                "suggested_action": "保留 baseline 回滚指针并检查候选覆盖面",
            }
        ],
    }

    report = build_orchestrator_policy_candidate_report(
        memory_training_report=memory_report,
        policy_observability_report=policy_report,
    )

    assert report["source_policy_observation_count"] == 4
    assert report["policy_observability_input_summary"]["status"] == "fallback_pressure"
    assert report["candidate_quality_summary"]["top_quality_score"] > 0
    assert any(
        row.get("source_recommendation_key") == "inspect_fallback_pressure"
        and row.get("suggested_action") == "increase_candidate_coverage_before_next_version"
        and row.get("quality_score", 0) > 0
        for row in report["candidates"]
    )


def test_v20_orchestrator_policy_candidate_artifact_write_and_status(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    store = LocalJsonlStore(runtime_dir=tmp_path)
    for index in range(3):
        store.append_record("orchestrator_memory_ledger", _memory_signal(index, "accept_primary"))

    written = write_orchestrator_policy_candidate_artifact(store=store)
    status = read_orchestrator_policy_candidate_artifact()

    assert written["status"] == "written"
    assert written["candidate_count"] >= 1
    assert status["version"] == "v20.orchestrator_policy_candidate_report.v1"
    assert status["candidate_count"] >= 1
    assert status["runtime_mutation"] is False


def test_v20_training_iteration_includes_orchestrator_policy_candidate_phase(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    _stub_training_iteration(monkeypatch)
    report = run_training_iteration(include_rule_batch=False)

    assert "orchestrator_memory_training" in report["results"]
    assert "orchestrator_policy_candidates" in report["results"]
    assert report["results"]["orchestrator_policy_candidates"]["status"] == "ready_for_fast_iteration"
    assert report["runtime_mutation"] is False


def _memory_signal(index: int, direction: str) -> dict[str, object]:
    return {
        "version": "v20.orchestrator_brain_memory_signal.v1",
        "status": "active",
        "memory_key": f"brain.memory.{index}",
        "primary_mainline_key": "mainline.career.guan_shang_yin",
        "primary_title": "伤官见官",
        "primary_domain": "career",
        "selected_question_key": "q_career_structure",
        "selected_question_domain": "career",
        "question_focus_status": "already_aligned",
        "coordination_status": "需复核",
        "coordination_flags": ["mainline_quality_review"],
        "signal_count": 1,
        "signals": [
            {
                "signal_key": f"brain.practitioner.{index}",
                "signal_type": "practitioner_structured_choice",
                "domain": "career",
                "target": "orchestrator.mainline_arbitration_memory",
                "direction": direction,
                "strength": 0.9,
                "allowed_use": "offline_orchestrator_memory_training",
                "runtime_rule_mutation": False,
            }
        ],
        "runtime_mutation": False,
    }


def _stub_training_iteration(monkeypatch) -> None:
    memory_report = build_orchestrator_memory_training_report(
        signals=(
            _memory_signal(1, "accept_primary"),
            _memory_signal(2, "accept_primary"),
            _memory_signal(3, "switch_to_supporting"),
        )
    )

    def ready(name: str) -> dict[str, object]:
        return {"version": f"test.{name}.v1", "status": "ready", "runtime_mutation": False}

    monkeypatch.setattr(training_iteration, "run_dynamic_decision_training_batch", lambda **_: ready("dynamic"))
    monkeypatch.setattr(training_iteration, "build_practitioner_calibration_training_report", lambda **_: ready("practitioner"))
    monkeypatch.setattr(training_iteration, "build_orchestrator_memory_training_report", lambda **_: memory_report)
    monkeypatch.setattr(training_iteration, "build_policy_observability_training_report", lambda **_: ready("policy_observability"))
    monkeypatch.setattr(training_iteration, "build_arbitration_loop_report", lambda **_: ready("arbitration"))
    monkeypatch.setattr(training_iteration, "build_question_ranking_learning_report", lambda **_: ready("question"))
    monkeypatch.setattr(training_iteration, "build_rule_synthetic_training_report", lambda *_, **__: ready("synthetic"))
    monkeypatch.setattr(training_iteration, "build_knowledge_rule_review_overlay", lambda *_, **__: ready("overlay"))
    monkeypatch.setattr(training_iteration, "build_rule_subcondition_split_report", lambda **_: ready("subcondition"))
    monkeypatch.setattr(training_iteration, "build_decision_registry_iteration_report", lambda **_: ready("registry"))
    monkeypatch.setattr(training_iteration, "build_decision_training_plan", lambda: ready("plan"))
