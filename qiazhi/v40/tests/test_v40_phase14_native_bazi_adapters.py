from __future__ import annotations

from pathlib import Path

from v40.contracts.base import EngineKey, EngineMode, Topic
from v40.contracts.engine import EngineRunRequest
from v40.engines import build_native_bazi_runtime, run_native_bazi_engine
from v40.engines.bazi_adapters import build_branch_relation_profile, build_ten_god_profile
from v40.synthetic import load_synthetic_seeds


ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / "data" / "synthetic" / "native_bazi_seeds.json"


def test_ten_god_adapter_builds_visible_stem_profile() -> None:
    seed = load_synthetic_seeds(SEED_PATH)[0]

    profile = build_ten_god_profile(seed.chart_facts)

    assert profile["day_stem"] == "丙"
    assert profile["counts"]["偏印"] == 1
    assert profile["counts"]["食神"] == 1
    assert profile["counts"]["正财"] == 1
    assert profile["wealth_count"] == 1
    assert len(profile["rows"]) == 3


def test_branch_relation_adapter_keeps_original_and_timing_relations() -> None:
    seed = load_synthetic_seeds(SEED_PATH)[0]

    profile = build_branch_relation_profile(seed.chart_facts)
    labels = [
        row["label"]
        for row in [*profile["relations"], *profile["timing_relations"]]
    ]

    assert "子午冲" in labels
    assert profile["clash_count"] >= 1
    assert isinstance(profile["harmony_count"], int)


def test_native_bazi_engine_exposes_adapter_facts_features_and_domain_signals() -> None:
    seed = load_synthetic_seeds(SEED_PATH)[0]
    result = run_native_bazi_engine(
        engine_request=EngineRunRequest(
            request_id="engine.phase14.001",
            reading_id="reading.phase14.001",
            engine=EngineKey.BAZI,
            mode=EngineMode.SIGNAL_SIDECAR,
            topic=Topic.CAREER,
        ),
        chart=seed.chart_facts,
    )

    fact_ids = {str(row["fact_id"]) for row in result.facts}
    feature_ids = {str(row["feature_id"]) for row in result.features}
    signal_topics = {signal.topic for signal in result.signals}

    assert result.engine_version == "v40.bazi_native.adapter.v1"
    assert "adapter.ten_god_profile" in fact_ids
    assert "adapter.branch_relations" in fact_ids
    assert "feature.ten_god_counts" in feature_ids
    assert "feature.branch_relation_counts" in feature_ids
    assert Topic.WEALTH in signal_topics
    assert Topic.RELATIONSHIP in signal_topics
    assert Topic.HEALTH in signal_topics


def test_wealth_question_uses_wealth_signal_as_primary_runtime_topic() -> None:
    seed = load_synthetic_seeds(SEED_PATH)[1]

    runtime = build_native_bazi_runtime(
        request_id="request.phase14.wealth",
        reading_id="reading.phase14.wealth",
        chart=seed.chart_facts,
        user_question=seed.question,
        topic=Topic.WEALTH,
        role_key="user",
    )

    assert runtime.verdicts[0].topic == Topic.WEALTH
    assert runtime.product_projection is not None
    assert runtime.product_projection.verdict_cards[0].topic == Topic.WEALTH
    assert any("wealth" in ref for ref in runtime.verdicts[0].evidence_refs)
    assert runtime.product_projection.branch_cards == []
