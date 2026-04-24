from __future__ import annotations

from v17_rebirth.backend.logic.plugin_discovery import iter_all_plugin_specs
from v17_rebirth.backend.services.hydration_pipeline import (
    append_algorithm_execution_stage,
    build_algorithm_execution_policy,
    bucket_decision_records,
    build_algorithm_execution_audit,
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


def test_algorithm_execution_audit_tracks_order_and_gate_visibility() -> None:
    meta: dict[str, object] = {}
    append_algorithm_execution_stage(meta, stage="geometry_built", label="几何关系建模")
    append_algorithm_execution_stage(meta, stage="base_runtime_ready", label="基线就绪")
    append_algorithm_execution_stage(meta, stage="plugin_manifest_ready", label="插件治理清单")
    append_algorithm_execution_stage(meta, stage="plugin_scan_completed", label="插件扫描")
    append_algorithm_execution_stage(meta, stage="claims_compiled", label="主张编译")
    append_algorithm_execution_stage(meta, stage="conflicts_routed", label="冲突路由")
    append_algorithm_execution_stage(meta, stage="modifier_settlement_completed", label="统一结算")
    append_algorithm_execution_stage(meta, stage="decision_buckets_ready", label="决策分桶")
    append_algorithm_execution_stage(meta, stage="flow_applied", label="流转平衡")
    append_algorithm_execution_stage(
        meta,
        stage="runtime_synced",
        label="运行态同步",
        sovereignty={
            "hard_authority_present": True,
            "authority_layer_protocol_present": True,
            "blind_theme_present": True,
        },
    )
    append_algorithm_execution_stage(meta, stage="meta_contract_built", label="元数据契约")

    audit = build_algorithm_execution_audit(meta.get("algorithm_execution_trace"))

    assert audit["protocol"] == "v17.algorithm_execution_audit.v1"
    assert audit["policy_protocol"] == "v17.algorithm_execution_policy.v1"
    assert audit["order_ok"] is True
    assert audit["critical_path_ok"] is True
    assert audit["gate_stage_ok"] is True
    assert audit["trace_coverage_ratio"] == 1.0
    assert audit["hard_authority_present"] is True
    assert audit["authority_layer_protocol_present"] is True
    assert audit["summary"] == "healthy"


def test_algorithm_execution_policy_declares_critical_path_and_gate_stage() -> None:
    policy = build_algorithm_execution_policy()

    assert policy["protocol"] == "v17.algorithm_execution_policy.v1"
    assert "geometry_built" in policy["critical_path"]
    assert "runtime_synced" in policy["gate_stages"]
    assert any(row["stage"] == "claims_compiled" for row in policy["stages"])


def test_algorithm_execution_audit_flags_dependency_violations() -> None:
    meta: dict[str, object] = {}
    append_algorithm_execution_stage(meta, stage="geometry_built", label="几何关系建模")
    append_algorithm_execution_stage(meta, stage="base_runtime_ready", label="基线就绪")
    append_algorithm_execution_stage(meta, stage="plugin_manifest_ready", label="插件治理清单")
    append_algorithm_execution_stage(meta, stage="plugin_scan_completed", label="插件扫描")
    append_algorithm_execution_stage(meta, stage="claims_compiled", label="主张编译")
    append_algorithm_execution_stage(meta, stage="modifier_settlement_completed", label="统一结算")

    audit = build_algorithm_execution_audit(meta.get("algorithm_execution_trace"))

    assert audit["critical_path_ok"] is False
    assert "conflicts_routed->modifier_settlement_completed" in audit["dependency_violations"]
    assert "modifier_settlement_completed" in audit["watch_stages"]
    assert audit["summary"] == "needs_review"
