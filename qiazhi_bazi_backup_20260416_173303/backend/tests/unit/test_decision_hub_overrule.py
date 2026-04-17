from __future__ import annotations

import pytest

from app.logic.brain.decision_hub import (
    apply_arbitration_overrule_to_client_bundle,
    build_arbitration_audit_entry,
    merge_silent_arbiter_into_assertion_tree,
)


def test_apply_arbitration_overrule_removes_law_and_sets_probe_waiting() -> None:
    audit_id = "arb-unit-test-01"
    merged = merge_silent_arbiter_into_assertion_tree(
        {"nodes": [], "edges": []},
        plugin_id="plugin_a",
        reason="unit",
        conflict_signature="sig",
        audit_bundle={"arbitration_audit_id": audit_id, "arbitration_theme": "A VS B"},
    )
    law_id = str((merged.get("silent_arbiter_history_v1") or [{}])[-1].get("law_node_id") or "")
    assert law_id
    entry = build_arbitration_audit_entry(
        conflict_name="c",
        conflict_context={"protocol": "arbitration_conflict_context.v1"},
        messages=[{"role": "user", "content": "hi"}],
        raw_response="{}",
        decision_plugin_id="plugin_a",
        reason="r",
        gold_badge="GOLD",
        law_node_id=law_id,
        rollback_interrupt={"interrupt_id": "i1", "reason_code": "M3", "state": "consumed"},
        rollback_flow_state="probe_waiting",
        entry_id=audit_id,
    )
    feed = [entry]
    out = apply_arbitration_overrule_to_client_bundle(
        audit_id=audit_id,
        assertion_tree=merged,
        metadata={"flow_state": "unknown", "persistence_layer": {}},
        arbitration_audit_feed=feed,
        physics_meta={"silent_arbiter_history_v1": [{"arbitration_audit_id": audit_id}], "arbitration_audit_feed_v1": feed},
    )
    tree = out["assertion_tree"]
    assert not any(str(n.get("node_id")) == law_id for n in (tree.get("nodes") or []) if isinstance(n, dict))
    md = out["metadata"]
    assert str(md.get("flow_state") or "") == "probe_waiting"
    pl = md.get("persistence_layer") or {}
    ir = pl.get("interrupt_request") or {}
    assert ir.get("state") == "pending"
    assert ir.get("interrupt_id") == "i1"
    marked = [x for x in out["physics_meta_patch"].get("arbitration_audit_feed_v1") or [] if x.get("id") == audit_id]
    assert marked and marked[0].get("overruled") is True


def test_apply_arbitration_overrule_unknown_audit_raises() -> None:
    with pytest.raises(LookupError):
        apply_arbitration_overrule_to_client_bundle(
            audit_id="missing",
            assertion_tree={"nodes": [], "edges": []},
            metadata={},
            arbitration_audit_feed=[],
        )
