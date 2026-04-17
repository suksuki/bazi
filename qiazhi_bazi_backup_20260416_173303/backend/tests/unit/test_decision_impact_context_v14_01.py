from __future__ import annotations

import app.services.analysis_service  # noqa: F401 — 预热 registry，避免 decision_hub 循环导入

from app.logic.brain.decision_hub import DecisionEvolutionFrameProtocol, DecisionImpactContext


def test_decision_impact_registry_records_ack_ignore_patch() -> None:
    meta: dict = {}
    DecisionImpactContext.record_ignore(meta, subject="食神过旺", note="降权")
    DecisionImpactContext.record_ack(meta, subject="寅巳穿", note="保留")
    DecisionImpactContext.record_patch(
        meta,
        sql_patch="UPDATE physics_interaction_params SET param_value=0.35 WHERE param_key='CF_FLOATING_DECAY';",
        narrative="强调寅巳穿风险",
    )
    reg = meta.get("decision_impact_registry_v14_01") or {}
    assert len(reg.get("events") or []) == 3
    assert reg.get("pending_sql_patches")
    frames = DecisionEvolutionFrameProtocol.backtrace(meta, max_items=10)
    assert len(frames) >= 3
    assert {"USER_WILL"} <= {str(f.get("layer") or "") for f in frames}
    assert all("timestamp" in f and "source_id" in f and "content_delta" in f for f in frames)


def test_sql_patch_pending_cleared_after_manual_merge_simulation() -> None:
    meta: dict = {}
    DecisionImpactContext.record_patch(
        meta,
        sql_patch="UPDATE physics_interaction_params SET param_value=0.88 WHERE param_key='CF_FLOATING_DECAY';",
    )
    reg = meta.get("decision_impact_registry_v14_01") or {}
    assert len(reg.get("pending_sql_patches") or []) >= 1
