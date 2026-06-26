from __future__ import annotations

from pathlib import Path

from v20.learning.orchestrator_memory_training import (
    build_orchestrator_memory_training_report,
    read_orchestrator_memory_training_artifact,
    write_orchestrator_memory_training_artifact,
)
import v20.learning.training_iteration as training_iteration
from v20.learning.training_iteration import run_training_iteration
from v20.storage.local_jsonl import LocalJsonlStore


def test_v20_orchestrator_memory_training_aggregates_mainline_and_domain_signals(tmp_path: Path) -> None:
    store = LocalJsonlStore(runtime_dir=tmp_path)
    for index, direction in enumerate(("accept_primary", "accept_primary", "switch_to_supporting")):
        store.append_record("orchestrator_memory_ledger", _memory_signal(index, direction=direction))

    report = build_orchestrator_memory_training_report(store=store)
    mainline = report["mainline_summaries"][0]
    domain = report["domain_summaries"][0]

    assert report["version"] == "v20.orchestrator_memory_training_report.v1"
    assert report["status"] == "ready"
    assert report["memory_signal_count"] == 3
    assert report["compiled_signal_count"] == 3
    assert mainline["primary_mainline_key"] == "mainline.career.guan_shang_yin"
    assert mainline["direction_counts"]["accept_primary"] == 2
    assert mainline["review_candidate"] is True
    assert domain["domain"] == "career"
    assert domain["signal_count"] == 3
    assert report["training_proposals"][0]["target"] == "mainline_arbitration_weight_policy"
    assert report["runtime_mutation"] is False
    assert "NO_RUNTIME_MAINLINE_MUTATION" in report["guardrails"]


def test_v20_orchestrator_memory_training_accepts_runtime_signal_rows_without_ledger() -> None:
    report = build_orchestrator_memory_training_report(
        signals=(
            _memory_signal(1, direction="switch_to_supporting"),
            _memory_signal(2, direction="evidence_insufficient"),
        )
    )

    assert report["record_count"] == 0
    assert report["memory_signal_count"] == 2
    assert report["mainline_summaries"][0]["direction_counts"]["switch_to_supporting"] == 1
    assert report["runtime_mutation"] is False


def test_v20_orchestrator_memory_training_write_and_status(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    store = LocalJsonlStore(runtime_dir=tmp_path)
    store.append_record("orchestrator_memory_ledger", _memory_signal(1, direction="accept_primary"))

    written = write_orchestrator_memory_training_artifact(store=store)
    status = read_orchestrator_memory_training_artifact()

    assert written["status"] == "written"
    assert written["memory_signal_count"] == 1
    assert status["version"] == "v20.orchestrator_memory_training_report.v1"
    assert status["memory_signal_count"] == 1
    assert status["runtime_mutation"] is False


def test_v20_training_iteration_includes_orchestrator_memory_phase(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    _stub_training_iteration(monkeypatch)
    report = run_training_iteration(include_rule_batch=False, dynamic_case_limit=1, rule_iteration_limit=1)

    assert "orchestrator_memory_training" in report["results"]
    assert report["results"]["orchestrator_memory_training"]["status"] == "not_enough_data"
    assert report["runtime_mutation"] is False


def _stub_training_iteration(monkeypatch) -> None:
    def report(name: str) -> dict[str, object]:
        return {"version": f"test.{name}.v1", "status": "ready", "runtime_mutation": False}

    monkeypatch.setattr(training_iteration, "run_dynamic_decision_training_batch", lambda **_: report("dynamic"))
    monkeypatch.setattr(training_iteration, "build_practitioner_calibration_training_report", lambda **_: report("practitioner"))
    monkeypatch.setattr(training_iteration, "build_arbitration_loop_report", lambda **_: report("arbitration"))
    monkeypatch.setattr(training_iteration, "build_question_ranking_learning_report", lambda **_: report("question"))
    monkeypatch.setattr(training_iteration, "build_rule_synthetic_training_report", lambda *_, **__: report("synthetic"))
    monkeypatch.setattr(training_iteration, "build_knowledge_rule_review_overlay", lambda *_, **__: report("overlay"))
    monkeypatch.setattr(training_iteration, "build_rule_subcondition_split_report", lambda **_: report("subcondition"))
    monkeypatch.setattr(training_iteration, "build_decision_registry_iteration_report", lambda **_: report("registry"))
    monkeypatch.setattr(training_iteration, "build_decision_training_plan", lambda: report("plan"))


def _memory_signal(index: int, *, direction: str) -> dict[str, object]:
    return {
        "version": "v20.orchestrator_brain_memory_signal.v1",
        "status": "active",
        "memory_key": f"brain.memory.test.{index}",
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
