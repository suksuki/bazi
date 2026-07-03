from __future__ import annotations

from pathlib import Path

from v40.contracts.base import Topic
from v40.contracts.chart import ZiweiChartFacts
from v40.contracts.signal import SignalSource
from v40.enrichment import EXPLANATION_ONLY_SOURCE_REFS, build_sidecar_enrichment_signals
from v40.engines import build_native_bazi_runtime
from v40.project import build_module_migration_status, build_project_status
from v40.synthetic import load_synthetic_seeds


ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / "data" / "synthetic" / "native_bazi_seeds.json"


def _seed():
    return load_synthetic_seeds(SEED_PATH)[0]


def _ziwei_facts() -> ZiweiChartFacts:
    return ZiweiChartFacts(
        chart_id="ziwei.phase68.001",
        life_palace="命宫在寅",
        body_palace="身宫在申",
        palaces={"官禄": {"stars": ["紫微", "天府"]}, "迁移": {"stars": ["七杀"]}},
        major_stars={"官禄": ["紫微", "天府"], "迁移": ["七杀"]},
        annual_transformations={"禄": "官禄", "忌": "交友"},
        domain_lenses={"career": "事业旁路更关注平台、职责边界和外部机会承接。"},
    )


def test_phase68_runtime_adds_knowledge_portrait_and_ziwei_enrichment_sidecars() -> None:
    seed = _seed()
    runtime = build_native_bazi_runtime(
        request_id="request.phase68.enrichment",
        reading_id="reading.phase68.enrichment",
        chart=seed.chart_facts,
        ziwei_chart=_ziwei_facts(),
        user_question="今年事业如何？",
        topic=Topic.CAREER,
        role_key="practitioner",
    )

    assert runtime.signal_registry is not None
    source_refs = {signal.source_ref for signal in runtime.signal_registry.signals}

    assert "knowledge_card_enrichment_v1" in source_refs
    assert "portrait_signal_enrichment_v1" in source_refs
    assert "ziwei_sidecar_enrichment_v1" in source_refs
    assert all(not signal.decision_authority for signal in runtime.signal_registry.signals)
    assert all(not signal.chart_fact_mutation_allowed for signal in runtime.signal_registry.signals)


def test_phase68_decision_input_excludes_explanation_only_enrichment_but_keeps_portrait_signal() -> None:
    seed = _seed()
    runtime = build_native_bazi_runtime(
        request_id="request.phase68.decision",
        reading_id="reading.phase68.decision",
        chart=seed.chart_facts,
        ziwei_chart=_ziwei_facts(),
        user_question="事业适合稳定发展还是转型突破？",
        topic=Topic.CAREER,
        role_key="user",
    )

    assert runtime.decision_input is not None
    decision_refs = {signal.source_ref for signal in runtime.decision_input.signals}

    assert "portrait_signal_enrichment_v1" in decision_refs
    assert decision_refs.isdisjoint(EXPLANATION_ONLY_SOURCE_REFS)
    assert all(signal.source != SignalSource.ZIWEI_ENGINE for signal in runtime.decision_input.signals)


def test_phase68_enrichment_builder_keeps_boundaries_and_trainable_refs() -> None:
    seed = _seed()
    runtime = build_native_bazi_runtime(
        request_id="request.phase68.builder",
        reading_id="reading.phase68.builder",
        chart=seed.chart_facts,
        ziwei_chart=_ziwei_facts(),
        topic=Topic.CAREER,
        role_key="practitioner",
    )
    assert runtime.engine_result is not None
    bazi_result = next(result for result in runtime.engine_result.results if result.engine.value == "bazi")
    ziwei_result = next(result for result in runtime.engine_result.results if result.engine.value == "ziwei")

    signals = build_sidecar_enrichment_signals(
        reading_id="reading.phase68.builder.direct",
        bazi_signals=bazi_result.signals,
        ziwei_signals=ziwei_result.signals,
    )

    assert {signal.source_ref for signal in signals} >= {
        "knowledge_card_enrichment_v1",
        "portrait_signal_enrichment_v1",
        "ziwei_sidecar_enrichment_v1",
    }
    knowledge = next(signal for signal in signals if signal.source_ref == "knowledge_card_enrichment_v1")
    portrait = next(signal for signal in signals if signal.source_ref == "portrait_signal_enrichment_v1")
    ziwei = next(signal for signal in signals if signal.source_ref == "ziwei_sidecar_enrichment_v1")
    assert "explanation_basis" in " ".join(knowledge.trainable_targets)
    assert "portrait_weight" in " ".join(portrait.trainable_targets)
    assert ziwei.source == SignalSource.ZIWEI_ENGINE


def test_phase68_docs_status_and_module_map_track_sidecar_enrichment() -> None:
    doc = Path("qiazhi/v40/docs/V40_PHASE68_SIDECAR_ENRICHMENT.md").read_text(encoding="utf-8")
    readme = Path("qiazhi/v40/README.md").read_text(encoding="utf-8")
    status = build_project_status()
    modules = build_module_migration_status()
    module_map = {row["key"]: row for row in modules["modules"]}

    assert "Knowledge Portrait Ziwei Sidecar Enrichment" in doc
    assert "docs/V40_PHASE68_SIDECAR_ENRICHMENT.md" in readme
    assert status["current_phase"] == 74
    assert status["current_phase_name"] == "Mainline Completion Audit And Next Plan"
    assert any(row["range"] == "67" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "68" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "69" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "70" and row["status"] == "complete" for row in status["phase_groups"])
    assert status["next_mainline_tasks"][0] == "QA-19: live LLM report/conversation acceptance on selected real cases"
    assert module_map["knowledge_cards"]["current_state"] == "v40_native_v1_explanation_sidecar_ready"
    assert module_map["portrait_signals"]["current_state"] == "v40_native_v1_low_weight_signal_ready"
    assert module_map["ziwei_sidecar"]["current_state"] == "v40_sidecar_v1_enriched"
