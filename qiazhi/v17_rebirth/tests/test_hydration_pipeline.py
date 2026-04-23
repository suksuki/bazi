from __future__ import annotations

from v17_rebirth.backend.logic.plugin_discovery import iter_all_plugin_specs
from v17_rebirth.backend.services.hydration_pipeline import (
    bucket_decision_records,
    build_plugin_governance_manifest,
)


def test_bucket_decision_records_splits_manual_system_and_llm() -> None:
    buckets = bucket_decision_records(
        [
            {"id": "m1", "arbiter_type": "user"},
            {"id": "s1", "arbiter_type": "system"},
            {"id": "l1", "arbiter_type": "llm"},
            {"id": "m2"},
        ]
    )

    assert buckets["protocol"] == "v17.hydration_pipeline.v1"
    assert buckets["bucket_counts"] == {"manual": 2, "system": 1, "llm": 1, "total": 4}
    assert [row["id"] for row in buckets["manual_decisions"]] == ["m1", "m2"]
    assert [row["id"] for row in buckets["auto_decisions"]] == ["s1", "l1"]
    assert buckets["decision_inbox_contract"] == "v17.decision.inbox.v2"


def test_plugin_governance_manifest_summarizes_discovered_specs() -> None:
    manifest = build_plugin_governance_manifest(iter_all_plugin_specs())

    assert manifest["protocol"] == "v17.hydration_pipeline.v1"
    assert manifest["plugin_count"] >= 80
    assert manifest["governance_class_counts"]["ziping_umbrella"] >= 1
    assert manifest["governance_class_counts"]["soft_bias_topic"] >= 1
    assert manifest["governance_class_counts"]["semantic_only_topic"] >= 1
    assert manifest["authority_level_counts"]["level_1_hard"] >= 1

