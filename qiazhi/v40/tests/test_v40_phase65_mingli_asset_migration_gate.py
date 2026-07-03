from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from v40.api.app import API_PREFIX, create_app
from v40.contracts.base import AssertionLevel, Polarity, Topic
from v40.contracts.manifest import contract_manifest
from v40.migration import (
    MingliAssetMigrationStatus,
    MingliAssetTargetType,
    MingliAssetType,
    MigratedMingliAsset,
    build_mingli_asset_migration_gate,
)
from v40.project import build_module_migration_status, build_project_status


def _asset(
    asset_id: str = "v30.asset.rule.career.001",
    *,
    status: MingliAssetMigrationStatus = MingliAssetMigrationStatus.SIDECAR,
    target: MingliAssetTargetType = MingliAssetTargetType.RUNTIME_SIGNAL,
) -> MigratedMingliAsset:
    return MigratedMingliAsset(
        asset_id=asset_id,
        source_v30_module="diagnosis/rule_matcher",
        source_ref="career.rules:stable_or_breakthrough",
        asset_type=MingliAssetType.DIAGNOSIS_RULE,
        target_v40_type=target,
        topic=Topic.CAREER,
        domain="career",
        claim_key="career.stable_or_breakthrough",
        claim="事业判断应先看压力能否被资质、平台和稳定交付承接。",
        evidence_refs=["adapter.fact_engine_pro", "v30.rule.career.stable_or_breakthrough"],
        default_confidence=0.66,
        strength=0.64,
        polarity=Polarity.SUPPORT,
        assertion_hint=AssertionLevel.SUPPORTED,
        max_assertion_level=AssertionLevel.SUPPORTED,
        forbidden_user_claims=["保证升职", "一定转型成功"],
        allowed_roles=["user", "practitioner", "admin", "lab"],
        user_visible=True,
        required_tests=["phase65_asset_gate_smoke"],
        migration_status=status,
    )


def test_phase65_migrated_asset_rejects_raw_v30_runtime_references() -> None:
    with pytest.raises(ValueError, match="raw V30 runtime"):
        MigratedMingliAsset(
            asset_id="v30.asset.bad.raw.001",
            source_v30_module="diagnosis/rule_matcher",
            asset_type=MingliAssetType.DIAGNOSIS_RULE,
            topic=Topic.CAREER,
            claim="坏资产不应携带 V30 runtime 路径。",
            evidence_refs=["v30.rule.bad"],
            migration_status=MingliAssetMigrationStatus.SIDECAR,
            raw_v30_runtime_path="/tmp/v30/runtime.json",
        )


def test_phase65_gate_converts_sidecar_asset_to_runtime_signal_without_authority() -> None:
    gate = build_mingli_asset_migration_gate(
        gate_id="gate.phase65.001",
        reading_id="reading.phase65.001",
        assets=[_asset()],
    )

    assert gate.asset_count == 1
    assert gate.signal_count == 1
    assert gate.accepted_asset_ids == ["v30.asset.rule.career.001"]
    assert gate.blocked_asset_ids == []
    assert gate.writes_v30_state is False
    assert gate.writes_v40_production is False
    signal = gate.signals[0]
    assert signal.source_ref.startswith("v30_asset:diagnosis/rule_matcher")
    assert signal.topic == Topic.CAREER
    assert signal.decision_authority is False
    assert signal.chart_fact_mutation_allowed is False
    assert "claim_score.career.stable_or_breakthrough" in signal.trainable_targets
    assert "user" in signal.role_visibility


def test_phase65_gate_blocks_draft_and_non_signal_assets_with_reasons() -> None:
    draft = _asset("v30.asset.rule.draft.001", status=MingliAssetMigrationStatus.DRAFT)
    knowledge = _asset(
        "v30.asset.knowledge.001",
        status=MingliAssetMigrationStatus.SIDECAR,
        target=MingliAssetTargetType.KNOWLEDGE_CARD,
    )

    gate = build_mingli_asset_migration_gate(
        gate_id="gate.phase65.blocked.001",
        reading_id="reading.phase65.blocked.001",
        assets=[draft, knowledge],
    )

    assert gate.accepted_asset_ids == []
    assert gate.blocked_asset_ids == ["v30.asset.rule.draft.001", "v30.asset.knowledge.001"]
    assert "migration_status_draft_not_runnable" in gate.blocked_reasons["v30.asset.rule.draft.001"]
    assert "target_knowledge_card_not_runtime_signal_v1" in gate.blocked_reasons["v30.asset.knowledge.001"]


def test_phase65_asset_gate_api_returns_signals_without_persistence() -> None:
    client = TestClient(create_app())
    asset = _asset()

    response = client.post(
        f"{API_PREFIX}/migration/mingli-assets/gate",
        json={
            "gate_id": "gate.phase65.api.001",
            "reading_id": "reading.phase65.api.001",
            "assets": [asset.model_dump(mode="json")],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["persisted"] is False
    assert body["writes_v30_state"] is False
    assert body["writes_v40_production"] is False
    assert body["gate"]["signal_count"] == 1
    assert body["signals"][0]["claim_key"] == "career.stable_or_breakthrough"


def test_phase65_manifest_module_status_and_project_status_track_asset_gate() -> None:
    doc = Path("qiazhi/v40/docs/V40_PHASE65_V30_MINGLI_ASSET_MIGRATION_GATE.md").read_text(encoding="utf-8")
    readme = Path("qiazhi/v40/README.md").read_text(encoding="utf-8")
    manifest = contract_manifest()
    module_status = build_module_migration_status()
    project_status = build_project_status()

    assert "MigratedMingliAsset" in manifest["migration"]
    assert "MingliAssetMigrationGateResult" in manifest["migration"]
    assert "docs/V40_PHASE65_V30_MINGLI_ASSET_MIGRATION_GATE.md" in readme
    assert "plain JSON asset -> RuntimeSignal sidecar" in doc
    asset_gate = next(row for row in module_status["modules"] if row["key"] == "asset_migration_gate")
    assert asset_gate["current_state"] == "v40_native_v1_sidecar_ready"
    assert project_status["current_phase"] == 73
    assert project_status["current_phase_name"] == "Real Case Acceptance Pack"
    assert any(row["range"] == "64" and row["status"] == "complete" for row in project_status["phase_groups"])
    assert any(row["range"] == "65" and row["status"] == "complete" for row in project_status["phase_groups"])
    assert project_status["next_mainline_tasks"][0] == "QA-19: live LLM report/conversation acceptance on selected real cases"
