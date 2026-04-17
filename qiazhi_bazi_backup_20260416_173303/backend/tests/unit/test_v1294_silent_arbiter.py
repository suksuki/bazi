from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict

import pytest

from app.services.helpers import v1294_silent_arbiter as mod


@pytest.mark.asyncio
async def test_maybe_apply_v1294_clears_interrupt_and_merges_tree(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_batch(**kwargs: Any) -> Dict[str, Any]:
        items = kwargs.get("items") or []
        return {
            "results": [
                {"index": i, "decision": "plugin.a", "reason": "测试批量", "certainty": "CONFIDENT"}
                for i in range(len(items))
            ],
            "audit": {
                "messages": [{"role": "user", "content": "batch"}],
                "raw_response": "[]",
            },
            "raw": "[]",
        }

    monkeypatch.setattr(mod, "invoke_batch_conflict_arbiter_llm", _fake_batch)

    def _fake_matching(_s: Any, _c: Any) -> tuple[set[str], str]:
        return ({"clash:子午"}, "Based on GOLD Set #1 (HTN snapshot #99)")

    monkeypatch.setattr(mod, "load_gold_arbiter_matching", _fake_matching)
    monkeypatch.setattr(mod, "persist_arbitration_log_to_snapshot", lambda *_a, **_k: 1)

    @contextmanager
    def _fake_session_scope():
        yield None

    monkeypatch.setattr("app.db.session.session_scope", _fake_session_scope)

    out: Dict[str, Any] = {
        "metadata": {
            "flow_state": "probe_waiting",
            "conflict_matrix": {"points": [{"kind": "clash", "detail": "子午冲"}]},
            "verdict_anchor_layer": {},
        },
        "physics_tensor": {
            "meta": {
                "global_entropy": {"value": 0.4},
                "decision_inbox_v1": {
                    "match_scores": [
                        {"plugin_id": "plugin.a", "score": 0.9},
                        {"plugin_id": "plugin.b", "score": 0.89},
                    ]
                },
            }
        },
        "assertion_tree": {"protocol": "assertion_tree.v1", "root_id": "root", "nodes": [], "edges": []},
        "active_probing": {
            "reason_code": "M3_HIGH_TENSION_PENDING",
            "interrupt": {"interrupt_id": "x"},
            "block_mode": True,
        },
        "interrupt_request": {"state": "pending"},
    }

    class _Dummy:
        pass

    got = await mod.maybe_apply_v1294_silent_arbiter_to_analyze_clash(
        out=out,
        session_id=1,
        lang="zh",
        client=_Dummy(),
    )

    assert got["interrupt_request"] == {}
    assert got["active_probing"]["reason_code"] == "M3_AUTO_ARBITER_SILENT"
    tree = got["assertion_tree"]
    assert isinstance(tree.get("silent_arbiter_history_v1"), list)
    assert len(tree["silent_arbiter_history_v1"]) >= 1
    meta = got["physics_tensor"]["meta"]
    assert isinstance(meta.get("silent_arbiter_history_v1"), list)
    feed = meta.get("arbitration_audit_feed_v1")
    assert isinstance(feed, list) and len(feed) >= 1
    assert "GOLD" in str(feed[-1].get("gold_badge") or "")
    ctx = feed[-1].get("conflict_context") or {}
    assert "global_entropy" in str(ctx)
    scores_after = (meta.get("decision_inbox_v1") or {}).get("match_scores") or []
    assert scores_after == []
    assert meta.get("auto_llm_default_accept_plugin_ids_v1") == ["plugin.a"]


@pytest.mark.asyncio
async def test_maybe_apply_v1294_uncertain_skips_silent(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_batch(**kwargs: Any) -> Dict[str, Any]:
        items = kwargs.get("items") or []
        return {
            "results": [
                {"index": i, "decision": "plugin.a", "reason": "x", "certainty": "UNCERTAIN" if i == 0 else "CONFIDENT"}
                for i in range(len(items))
            ],
            "audit": {"messages": [], "raw_response": "[]"},
            "raw": "[]",
        }

    monkeypatch.setattr(mod, "invoke_batch_conflict_arbiter_llm", _fake_batch)

    def _fake_matching(_s: Any, _c: Any) -> tuple[set[str], str]:
        return ({"clash:子午"}, "GOLD")

    monkeypatch.setattr(mod, "load_gold_arbiter_matching", _fake_matching)

    @contextmanager
    def _fake_session_scope():
        yield None

    monkeypatch.setattr("app.db.session.session_scope", _fake_session_scope)

    out: Dict[str, Any] = {
        "metadata": {
            "flow_state": "probe_waiting",
            "conflict_matrix": {"points": [{"kind": "clash", "detail": "子午冲"}, {"kind": "clash", "detail": "寅巳害"}]},
        },
        "physics_tensor": {
            "meta": {
                "global_entropy": {"value": 0.4},
                "pending_arbitration_queue_v1": [{"conflict": {"kind": "clash", "detail": "子午冲"}}],
                "decision_inbox_v1": {
                    "match_scores": [
                        {"plugin_id": "plugin.a", "score": 0.9},
                        {"plugin_id": "plugin.b", "score": 0.89},
                    ]
                },
            }
        },
        "assertion_tree": {"protocol": "assertion_tree.v1", "root_id": "root", "nodes": [], "edges": []},
        "active_probing": {"reason_code": "M3_HIGH_TENSION_PENDING", "interrupt": {"interrupt_id": "x"}},
        "interrupt_request": {"state": "pending"},
    }

    class _Dummy:
        pass

    got = await mod.maybe_apply_v1294_silent_arbiter_to_analyze_clash(out=out, session_id=None, lang="zh", client=_Dummy())
    assert got["interrupt_request"] == {"state": "pending"}
    assert got["active_probing"]["reason_code"] == "M3_HIGH_TENSION_PENDING"
    meta = got["physics_tensor"]["meta"]
    assert meta.get("auto_llm_default_accept_plugin_ids_v1") is None
