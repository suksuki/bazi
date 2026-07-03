from __future__ import annotations

from pathlib import Path

from v40.contracts.base import AssertionLevel, Polarity, Topic
from v40.decision import build_domain_adapter_signals
from v40.engines import build_native_bazi_runtime
from v40.migration import (
    MingliAssetMigrationStatus,
    MingliAssetType,
    MigratedMingliAsset,
    build_mingli_asset_migration_gate,
)
from v40.project import build_project_status
from v40.synthetic import load_synthetic_seeds


ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / "data" / "synthetic" / "native_bazi_seeds.json"


def test_phase66_domain_adapter_enters_native_verdict_evidence() -> None:
    seed = load_synthetic_seeds(SEED_PATH)[0]

    runtime = build_native_bazi_runtime(
        request_id="request.phase66.career",
        reading_id="reading.phase66.career",
        chart=seed.chart_facts,
        user_question=seed.question,
        topic=Topic.CAREER,
        role_key="user",
    )

    assert runtime.decision_input is not None
    adapter_signals = [
        signal for signal in runtime.decision_input.signals if signal.source_ref == "domain_verdict_adapter"
    ]
    assert adapter_signals
    assert adapter_signals[0].topic == Topic.CAREER
    assert adapter_signals[0].decision_authority is False
    assert adapter_signals[0].chart_fact_mutation_allowed is False
    assert any("domain-adapter:career" in ref for ref in runtime.verdicts[0].evidence_refs)
    assert "domain_adapter.career.claim_score" in adapter_signals[0].trainable_targets


def test_phase66_domain_adapter_consumes_migrated_v30_asset_signal() -> None:
    asset = MigratedMingliAsset(
        asset_id="v30.asset.phase66.wealth.001",
        source_v30_module="diagnosis/path_engine",
        source_ref="wealth.path.resource_output",
        asset_type=MingliAssetType.PATH_RULE,
        topic=Topic.WEALTH,
        domain="wealth",
        claim_key="wealth.resource_output",
        claim="财运要看资源入口、输出方式和分配边界能否形成闭环。",
        evidence_refs=["adapter.fact_engine_pro", "v30.path.wealth.resource_output"],
        default_confidence=0.68,
        strength=0.66,
        polarity=Polarity.SUPPORT,
        assertion_hint=AssertionLevel.SUPPORTED,
        max_assertion_level=AssertionLevel.SUPPORTED,
        migration_status=MingliAssetMigrationStatus.SIDECAR,
        required_tests=["phase66_domain_adapter_smoke"],
        allowed_roles=["user", "practitioner", "admin", "lab"],
        user_visible=True,
    )
    gate = build_mingli_asset_migration_gate(
        gate_id="gate.phase66.wealth",
        reading_id="reading.phase66.wealth",
        assets=[asset],
    )

    adapter_signals = build_domain_adapter_signals(
        reading_id="reading.phase66.wealth",
        signals=gate.signals,
        topics=[Topic.WEALTH],
    )

    assert len(adapter_signals) == 1
    adapter = adapter_signals[0]
    assert adapter.claim_key == "domain_adapter.wealth"
    assert "资源入口" in adapter.claim
    assert adapter.source_ref == "domain_verdict_adapter"
    assert "migrated:reading.phase66.wealth:v30.asset.phase66.wealth.001" in adapter.evidence_refs


def test_phase66_project_status_tracks_domain_verdict_adapters() -> None:
    doc = Path("qiazhi/v40/docs/V40_PHASE66_DOMAIN_VERDICT_ADAPTERS.md").read_text(encoding="utf-8")
    readme = Path("qiazhi/v40/README.md").read_text(encoding="utf-8")
    status = build_project_status()

    assert "Domain Verdict Adapters" in doc
    assert "docs/V40_PHASE66_DOMAIN_VERDICT_ADAPTERS.md" in readme
    assert status["current_phase"] == 74
    assert status["current_phase_name"] == "Mainline Completion Audit And Next Plan"
    assert any(row["range"] == "65" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "66" and row["status"] == "complete" for row in status["phase_groups"])
    assert status["next_mainline_tasks"][0] == "QA-19: live LLM report/conversation acceptance on selected real cases"
