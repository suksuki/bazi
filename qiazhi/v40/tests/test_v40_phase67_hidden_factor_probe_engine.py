from __future__ import annotations

from pathlib import Path

from v40.contracts.base import Topic
from v40.contracts.runtime import RuntimeResult
from v40.contracts.signal import SignalSource
from v40.engines import build_native_bazi_runtime
from v40.probes import (
    build_hidden_factor_answer_runtime_signal,
    build_hidden_factor_probe_candidates,
    build_probe_answer_result,
)
from v40.project import build_project_status
from v40.synthetic import load_synthetic_seeds


ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / "data" / "synthetic" / "native_bazi_seeds.json"


def _runtime() -> RuntimeResult:
    seed = load_synthetic_seeds(SEED_PATH)[0]
    return build_native_bazi_runtime(
        request_id="request.phase67.hidden",
        reading_id="reading.phase67.hidden",
        chart=seed.chart_facts,
        user_question="事业上有没有隐藏阻力？",
        topic=Topic.CAREER,
        role_key="user",
    )


def test_phase67_native_runtime_emits_goal_directed_hidden_factor_probe() -> None:
    runtime = _runtime()

    hidden_probes = [probe for probe in runtime.probes if probe.probe_id.startswith("probe:reading.phase67.hidden:hidden_factor")]

    assert hidden_probes
    probe = hidden_probes[0]
    assert probe.topic == Topic.HIDDEN_ATTRIBUTE
    assert probe.probe_type == "event"
    assert probe.target_verdict_ids
    assert probe.target_branch_ids
    assert probe.target_hidden_attribute_ids
    assert probe.expected_information_gain > probe.user_cost
    assert "暂不明显" in probe.options
    assert any("可训练" in row for row in probe.impact_preview)


def test_phase67_hidden_factor_probe_builder_ranks_uncertain_domain_focus() -> None:
    runtime = _runtime()

    probes = build_hidden_factor_probe_candidates(
        reading_id=runtime.reading_id,
        verdicts=runtime.verdicts,
        branches=runtime.branches,
        signals=runtime.decision_input.signals if runtime.decision_input else [],
        role_key="practitioner",
    )

    assert len(probes) == 1
    assert probes[0].topic == Topic.HIDDEN_ATTRIBUTE
    assert probes[0].ask_now is True
    assert Topic.HIDDEN_ATTRIBUTE in probes[0].target_domains
    assert "probe_voi" not in " ".join(probes[0].impact_preview)


def test_phase67_probe_answer_can_be_bound_back_as_runtime_signal_without_decision_authority() -> None:
    runtime = _runtime()
    probe = next(item for item in runtime.probes if item.topic == Topic.HIDDEN_ATTRIBUTE)
    result = build_probe_answer_result(
        answer_id="phase67-hidden-answer",
        runtime=runtime,
        probe_id=probe.probe_id,
        selected_option=probe.options[0],
        created_by_role="user",
    )

    signal = build_hidden_factor_answer_runtime_signal(result=result)

    assert signal.source == SignalSource.REALITY_PROBE
    assert signal.source_ref == "hidden_factor_probe_answer"
    assert signal.topic == Topic.HIDDEN_ATTRIBUTE
    assert result.answer_signal.signal_id in signal.evidence_refs
    assert result.hidden_attribute_update.update_id in signal.evidence_refs
    assert "signal_weight.reality_probe.hidden_attribute" in signal.trainable_targets
    assert signal.decision_authority is False
    assert signal.chart_fact_mutation_allowed is False


def test_phase67_docs_and_project_status_track_hidden_factor_probe_engine() -> None:
    doc = Path("qiazhi/v40/docs/V40_PHASE67_HIDDEN_FACTOR_PROBE_ENGINE.md").read_text(encoding="utf-8")
    readme = Path("qiazhi/v40/README.md").read_text(encoding="utf-8")
    status = build_project_status()

    assert "Hidden Factor Probe Engine" in doc
    assert "docs/V40_PHASE67_HIDDEN_FACTOR_PROBE_ENGINE.md" in readme
    assert status["current_phase"] == 73
    assert status["current_phase_name"] == "Real Case Acceptance Pack"
    assert any(row["range"] == "66" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "67" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "68" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "69" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "70" and row["status"] == "complete" for row in status["phase_groups"])
    assert status["next_mainline_tasks"][0] == "QA-19: live LLM report/conversation acceptance on selected real cases"
