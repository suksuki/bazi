from __future__ import annotations

from pathlib import Path

from v20.learning.orchestrator_memory_training import build_orchestrator_memory_training_report
from v20.learning.orchestrator_policy_candidates import build_orchestrator_policy_candidate_report
from v20.learning.orchestrator_policy_replay import (
    build_orchestrator_policy_replay_report,
    read_orchestrator_policy_replay_artifact,
    write_orchestrator_policy_replay_artifact,
)
from v20.learning.orchestrator_policy_versioning import (
    build_orchestrator_policy_version_candidate,
    read_orchestrator_policy_version_candidate_artifact,
    write_orchestrator_policy_version_candidate_artifact,
)
from v20.learning.training_iteration import run_training_iteration
from v20.storage.local_jsonl import LocalJsonlStore
import v20.learning.training_iteration as training_iteration


def test_v20_orchestrator_policy_version_candidate_locks_review_only_payload() -> None:
    report = _candidate_report()
    version = build_orchestrator_policy_version_candidate(candidate_report=report)

    assert version["version"] == "v20.orchestrator_policy_version_candidate.v1"
    assert version["status"] == "ready_for_replay"
    assert version["candidate_policy_version"].startswith("v20.orchestrator_policy.candidate.")
    assert version["runtime_allowed"] is True
    assert version["policy_payload"]["mainline_arbitration_weight_policy"]
    assert version["policy_payload"]["question_focus_policy"]
    assert version["policy_payload"]["brain_memory_policy"]
    assert "source_policy_observability_input_summary" in version
    assert "source_candidate_quality_summary" in version
    assert version["source_quality_scoring_policy"]["version"] == "v20.orchestrator_policy_candidate_quality_policy.v1"
    assert all("quality_score" in row and "quality_rank" in row and "quality_policy_version" in row for rows in version["policy_payload"].values() for row in rows)
    assert "AUTO_ITERATION_VERSION_CANDIDATE" in version["guardrails"]


def test_v20_orchestrator_policy_replay_compares_baseline_and_candidate_without_runtime_use() -> None:
    version = build_orchestrator_policy_version_candidate(candidate_report=_candidate_report())
    replay = build_orchestrator_policy_replay_report(policy_version_candidate=version)

    assert replay["version"] == "v20.orchestrator_policy_replay_report.v1"
    assert replay["status"] == "ready_for_fast_iteration"
    assert replay["comparison_count"] >= 3
    assert replay["replay_result"]["eligible_for_runtime"] is True
    assert all(row["baseline_action"] == "keep_current_runtime_policy" for row in replay["comparisons"])
    assert all(row["runtime_allowed"] is True for row in replay["comparisons"])
    assert all(row["requires_human_review"] is False for row in replay["comparisons"])
    assert "AUTO_ITERATION_REPLAY_RESULT" in replay["guardrails"]


def test_v20_orchestrator_policy_replay_consumes_question_source_policy_rows() -> None:
    version = build_orchestrator_policy_version_candidate(candidate_report=_candidate_report_with_question_source())
    replay = build_orchestrator_policy_replay_report(policy_version_candidate=version)

    source_rows = [
        row for row in replay["comparisons"]
        if row["policy_key"] == "question_source_graph_quality_policy"
    ]
    assert source_rows
    assert source_rows[0]["candidate_action"] == "increase_source_quality_prior"
    assert source_rows[0]["expected_effect"] == "may_change_source_quality_weight_after_approval"


def test_v20_orchestrator_policy_version_and_replay_artifacts(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    store = LocalJsonlStore(runtime_dir=tmp_path)
    for index in range(3):
        store.append_record("orchestrator_memory_ledger", _memory_signal(index, "accept_primary"))

    version_written = write_orchestrator_policy_version_candidate_artifact(store=store)
    replay_written = write_orchestrator_policy_replay_artifact(store=store)
    version_status = read_orchestrator_policy_version_candidate_artifact()
    replay_status = read_orchestrator_policy_replay_artifact()

    assert version_written["status"] == "written"
    assert replay_written["status"] == "written"
    assert version_status["version"] == "v20.orchestrator_policy_version_candidate.v1"
    assert replay_status["version"] == "v20.orchestrator_policy_replay_report.v1"
    assert version_status["runtime_mutation"] is False
    assert replay_status["runtime_mutation"] is False


def test_v20_training_iteration_includes_policy_version_and_replay_phases(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    _stub_training_iteration(monkeypatch)
    report = run_training_iteration(include_rule_batch=False)

    assert "orchestrator_policy_version_candidate" in report["results"]
    assert "orchestrator_policy_replay" in report["results"]
    assert report["results"]["orchestrator_policy_version_candidate"]["status"] == "ready_for_replay"
    assert report["results"]["orchestrator_policy_replay"]["status"] == "ready_for_fast_iteration"
    assert report["orchestrator_policy_learning_summary"]["version"] == "v20.training_iteration_orchestrator_policy_learning_summary.v1"
    assert "version_switch_event_count" in report["orchestrator_policy_learning_summary"]
    assert "ORCHESTRATOR_POLICY_RECOMMENDATIONS_ARE_READ_ONLY" in report["guardrails"]
    assert report["runtime_mutation"] is False


def _candidate_report() -> dict[str, object]:
    memory = build_orchestrator_memory_training_report(
        signals=(
            _memory_signal(1, "accept_primary"),
            _memory_signal(2, "accept_primary"),
            _memory_signal(3, "switch_to_supporting"),
        )
    )
    return build_orchestrator_policy_candidate_report(memory_training_report=memory)


def _candidate_report_with_question_source() -> dict[str, object]:
    memory = build_orchestrator_memory_training_report(
        signals=(
            _memory_signal(1, "accept_primary"),
            _memory_signal(2, "accept_primary"),
            _memory_signal(3, "accept_primary"),
        )
    )
    source_report = {
        "version": "v20.question_source_training_report.v1",
        "status": "ready",
        "training_proposals": [
            {
                "target": "question_source_graph_quality_policy",
                "source_key": "source.qa.001",
                "suggested_action": "increase_source_quality_prior",
                "sample_count": 7,
                "average_graph_score": 0.42,
                "average_question_score": 0.31,
            }
        ],
    }
    return build_orchestrator_policy_candidate_report(
        memory_training_report=memory,
        question_source_training_report=source_report,
    )


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
        "coordination_status": "需复核",
        "signals": [
            {
                "signal_type": "practitioner_structured_choice",
                "domain": "career",
                "direction": direction,
                "target": "orchestrator.mainline_arbitration_memory",
                "strength": 0.9,
                "allowed_use": "offline_orchestrator_memory_training",
            }
        ],
        "runtime_mutation": False,
    }


def _stub_training_iteration(monkeypatch) -> None:
    candidate_report = _candidate_report()
    version = build_orchestrator_policy_version_candidate(candidate_report=candidate_report)
    replay = build_orchestrator_policy_replay_report(policy_version_candidate=version)

    def ready(name: str) -> dict[str, object]:
        return {"version": f"test.{name}.v1", "status": "ready", "runtime_mutation": False}

    monkeypatch.setattr(training_iteration, "run_dynamic_decision_training_batch", lambda **_: ready("dynamic"))
    monkeypatch.setattr(training_iteration, "build_practitioner_calibration_training_report", lambda **_: ready("practitioner"))
    monkeypatch.setattr(training_iteration, "build_orchestrator_memory_training_report", lambda **_: build_orchestrator_memory_training_report(signals=(_memory_signal(1, "accept_primary"), _memory_signal(2, "accept_primary"), _memory_signal(3, "switch_to_supporting"))))
    monkeypatch.setattr(training_iteration, "build_orchestrator_policy_candidate_report", lambda **_: candidate_report)
    monkeypatch.setattr(training_iteration, "build_orchestrator_policy_version_candidate", lambda **_: version)
    monkeypatch.setattr(training_iteration, "build_orchestrator_policy_replay_report", lambda **_: replay)
    monkeypatch.setattr(training_iteration, "build_arbitration_loop_report", lambda **_: ready("arbitration"))
    monkeypatch.setattr(training_iteration, "build_question_ranking_learning_report", lambda **_: ready("question"))
    monkeypatch.setattr(training_iteration, "build_rule_synthetic_training_report", lambda *_, **__: ready("synthetic"))
    monkeypatch.setattr(training_iteration, "build_knowledge_rule_review_overlay", lambda *_, **__: ready("overlay"))
    monkeypatch.setattr(training_iteration, "build_rule_subcondition_split_report", lambda **_: ready("subcondition"))
    monkeypatch.setattr(training_iteration, "build_decision_registry_iteration_report", lambda **_: ready("registry"))
    monkeypatch.setattr(training_iteration, "build_decision_training_plan", lambda: ready("plan"))
