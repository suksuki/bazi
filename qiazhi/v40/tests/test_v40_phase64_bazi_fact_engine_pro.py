from __future__ import annotations

from pathlib import Path

from v40.contracts.base import EngineKey, EngineMode, Topic
from v40.contracts.engine import EngineRunRequest
from v40.engines import build_native_bazi_runtime, run_native_bazi_engine
from v40.engines.bazi_adapters import build_fact_engine_pro_profile
from v40.project import build_project_status
from v40.synthetic import load_synthetic_seeds


ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / "data" / "synthetic" / "native_bazi_seeds.json"


def test_phase64_fact_engine_pro_builds_hidden_stems_root_and_month_authority() -> None:
    seed = load_synthetic_seeds(SEED_PATH)[0]

    profile = build_fact_engine_pro_profile(seed.chart_facts)

    assert profile["profile_id"] == "bazi_fact_engine_pro.v1"
    assert profile["fact_training_allowed"] is False
    assert any(row["branch"] == "辰" and row["stem"] == "戊" for row in profile["hidden_stems"])
    assert profile["hidden_ten_god_counts"]["正印"] > 0
    assert profile["root_profile"]["day_master_has_root"] is True
    assert profile["root_profile"]["root_score"] > 0.3
    assert profile["month_profile"]["month_branch"] == "辰"
    assert profile["month_profile"]["relation_to_day"] == "output"


def test_phase64_fact_engine_pro_detects_advanced_branch_relations() -> None:
    seed = load_synthetic_seeds(SEED_PATH)[0]

    profile = build_fact_engine_pro_profile(seed.chart_facts)
    relation_labels = {row["label"] for row in profile["advanced_branch_relations"]["relations"]}
    counts = profile["advanced_branch_relations"]["counts"]

    assert "卯辰害" in relation_labels
    assert "卯午破" in relation_labels
    assert "申子辰水局" in relation_labels
    assert counts["harm"] >= 1
    assert counts["break"] >= 1
    assert counts["three_harmony"] >= 1


def test_phase64_native_bazi_runtime_exposes_pro_facts_features_and_signals() -> None:
    seed = load_synthetic_seeds(SEED_PATH)[0]
    result = run_native_bazi_engine(
        engine_request=EngineRunRequest(
            request_id="engine.phase64.001",
            reading_id="reading.phase64.001",
            engine=EngineKey.BAZI,
            mode=EngineMode.SIGNAL_SIDECAR,
            topic=Topic.CAREER,
        ),
        chart=seed.chart_facts,
    )

    fact_ids = {str(row["fact_id"]) for row in result.facts}
    feature_ids = {str(row["feature_id"]) for row in result.features}
    signal_refs = {signal.source_ref for signal in result.signals}

    assert "adapter.fact_engine_pro" in fact_ids
    assert "adapter.hidden_stems" in fact_ids
    assert "feature.hidden_ten_god_counts" in feature_ids
    assert "feature.root_profile" in feature_ids
    assert "feature.month_authority" in feature_ids
    assert "feature.advanced_branch_relation_counts" in feature_ids
    assert "native_bazi_fact_engine_pro" in signal_refs


def test_phase64_decision_runtime_consumes_pro_facts_without_mutating_chart_facts() -> None:
    seed = load_synthetic_seeds(SEED_PATH)[1]

    runtime = build_native_bazi_runtime(
        request_id="request.phase64.wealth",
        reading_id="reading.phase64.wealth",
        chart=seed.chart_facts,
        user_question=seed.question,
        topic=Topic.WEALTH,
        role_key="user",
    )

    assert runtime.chart_fact_mutation_allowed is False
    assert runtime.verdicts[0].topic == Topic.WEALTH
    assert any("adapter.fact_engine_pro" in ref for ref in runtime.verdicts[0].evidence_refs)
    assert runtime.engine_result is not None
    assert runtime.engine_result.results[0].engine_version == "v40.bazi_native.adapter.v1"


def test_phase64_project_status_tracks_fact_engine_pro_mainline() -> None:
    doc = Path("qiazhi/v40/docs/V40_PHASE64_BAZI_FACT_ENGINE_PRO.md").read_text(encoding="utf-8")
    readme = Path("qiazhi/v40/README.md").read_text(encoding="utf-8")
    status = build_project_status()

    assert "Bazi Fact Engine Pro V1" in doc
    assert "docs/V40_PHASE64_BAZI_FACT_ENGINE_PRO.md" in readme
    assert status["current_phase"] == 65
    assert status["current_phase_name"] == "V30 Mingli Asset Migration Gate"
    assert any(row["range"] == "63" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "64" and row["status"] == "complete" for row in status["phase_groups"])
    assert status["next_mainline_tasks"][0] == "P65-1: V30 Mingli Asset Migration Gate"
