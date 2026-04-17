from __future__ import annotations

from app.logic.brain.decision_hub import (
    conflict_matches_ledger_patterns,
    conflict_pattern_signature,
    merge_silent_arbiter_into_assertion_tree,
    should_auto_resolve,
)


def test_should_auto_resolve_requires_low_weight_and_ledger_match() -> None:
    c = {"kind": "clash", "detail": "子午冲在月日"}
    assert should_auto_resolve(c, conflict_weight=0.8, gold_pattern_keys={"clash:子午"}) == "USER"
    assert should_auto_resolve(c, conflict_weight=0.5, gold_pattern_keys=set()) == "USER"
    assert should_auto_resolve(c, conflict_weight=0.5, gold_pattern_keys={"clash:子午"}) == "AUTO_LLM"


def test_should_auto_resolve_with_sink_enqueues_and_returns_queued() -> None:
    c = {"kind": "clash", "detail": "子午冲在月日"}
    sink: dict = {}
    assert (
        should_auto_resolve(
            c,
            conflict_weight=0.5,
            gold_pattern_keys={"clash:子午"},
            physics_meta_sink=sink,
        )
        == "AUTO_LLM_QUEUED"
    )
    q = sink.get("pending_arbitration_queue_v1")
    assert isinstance(q, list) and len(q) == 1
    assert q[0]["conflict"]["detail"] == "子午冲在月日"


def test_conflict_pattern_signature_stable() -> None:
    assert "子午" in conflict_pattern_signature({"kind": "CLASH", "detail": " 子午冲 "})


def test_conflict_matches_ledger_patterns() -> None:
    c = {"kind": "clash", "detail": "寅巳穿害"}
    assert conflict_matches_ledger_patterns(c, {"harm:寅巳", "other"})
    assert not conflict_matches_ledger_patterns(c, {"clash:子午"})


def test_merge_silent_arbiter_appends_law_and_history() -> None:
    base = {"protocol": "assertion_tree.v1", "root_id": "root", "nodes": [], "edges": []}
    out = merge_silent_arbiter_into_assertion_tree(
        base,
        plugin_id="classical.blind_school.v1",
        reason="黄金样本对齐",
        conflict_signature="clash|子午冲",
    )
    assert any(n.get("node_type") == "LAW" for n in out.get("nodes") or [])
    hist = out.get("silent_arbiter_history_v1") or []
    assert len(hist) == 1
    assert hist[0].get("decision") == "classical.blind_school.v1"
    assert hist[0].get("route") == "AUTO_LLM"
