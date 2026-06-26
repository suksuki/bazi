from __future__ import annotations

from v30.knowledge.v20_reference_registry import (
    list_v20_reference_assets,
    summarize_v20_reference_registry,
)


def test_v20_reference_registry_lists_m3_assets_without_runtime_import() -> None:
    assets = list_v20_reference_assets()
    asset_ids = {asset.asset_id for asset in assets}
    assert "v30.m3.reference.v20_expanded_knowledge_units" in asset_ids
    assert "v30.m3.reference.v20_structure_mechanism_units" in asset_ids
    assert "v30.m3.reference.v20_structure_dynamics_graph_v2" in asset_ids
    assert "v30.m3.reference.v20_structure_knowledge_coverage" in asset_ids
    assert "v30.m3.reference.v20_rule_portrait_batch" in asset_ids
    assert all(asset.v20_paths for asset in assets)
    assert all(asset.required_v30_contracts for asset in assets)
    assert all("no_v20_runtime_import" in asset.migration_boundary for asset in assets)


def test_v20_reference_registry_requires_v30_contract_adaptation() -> None:
    summary = summarize_v20_reference_registry()
    assert summary["version"] == "v30.v20_reference_registry_for_m3.v1"
    assert summary["asset_count"] >= 6
    assert set(summary["required_v30_contracts"]) >= {
        "KnowledgeRulePortraitUnit",
        "FeatureEvidence",
        "RuleEvidenceSpec",
        "DynamicGraphPath",
        "SyntheticTrainingSignal",
        "KnowledgeSourceFamily",
    }
    assert summary["boundary"] == "v20_assets_are_reference_inputs_v30_runtime_contracts_remain_authoritative"
