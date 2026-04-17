from __future__ import annotations

import json
from contextlib import contextmanager

import pytest
from sqlalchemy.exc import OperationalError

from app.api import router as router_module
from app.api.contracts import ArbitrationOverruleRequest


def test_resume_pulse_history_degrades_on_db_error(monkeypatch: pytest.MonkeyPatch) -> None:
    @contextmanager
    def _broken_session_scope():
        raise OperationalError("SELECT …", {}, Exception("no such table: resume_pulse_history"))
        yield  # pragma: no cover

    monkeypatch.setattr(router_module, "session_scope", _broken_session_scope)
    resp = router_module.get_resume_pulse_history(571)
    assert resp.status_code == 503
    raw = resp.body
    if isinstance(raw, memoryview):
        raw = raw.tobytes()
    body = json.loads(raw.decode("utf-8"))
    assert body.get("ok") is False
    assert body.get("items") == []


def test_m5_gold_stats_degrades_instead_of_500(monkeypatch: pytest.MonkeyPatch) -> None:
    @contextmanager
    def _broken_session_scope():
        raise RuntimeError("db unavailable")
        yield  # pragma: no cover

    monkeypatch.setattr(router_module, "session_scope", _broken_session_scope)
    out = router_module.m5_gold_stats()
    assert out.get("ok") is True
    assert out.get("degraded") is True
    assert int(out.get("gold_total") or 0) == 0
    assert isinstance(out.get("top3_assimilated_seeds"), list)
    assert out.get("silent_arbiter_audit_events") == 0
    assert out.get("auto_arbitration_success_rate") is None


def test_arbitration_overrule_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    audit_id = "arb-router-test-1"
    law = "law-arbiter-router01"

    def _noop_persist(*_a, **_k):
        return None

    monkeypatch.setattr(router_module, "persist_arbitration_log_to_snapshot", _noop_persist)

    tree = {
        "nodes": [{"node_id": law, "node_type": "LAW", "text": "x", "evidence_refs": [f"silent_arbiter.law_node_id={law}"]}],
        "edges": [{"from": "root", "to": law, "label": "silent_arbiter"}],
        "silent_arbiter_history_v1": [{"arbitration_audit_id": audit_id, "law_node_id": law}],
    }
    feed = [
        {
            "protocol": "arbitration_audit.v1",
            "id": audit_id,
            "law_node_id": law,
            "rollback_interrupt": {"interrupt_id": "ir-1", "state": "cleared"},
            "overruled": False,
        }
    ]
    body = ArbitrationOverruleRequest(
        audit_id=audit_id,
        consultation_id=0,
        assertion_tree=tree,
        metadata={"flow_state": "unknown", "persistence_layer": {}},
        arbitration_audit_feed=feed,
        physics_meta={"arbitration_audit_feed_v1": feed, "silent_arbiter_history_v1": [{"arbitration_audit_id": audit_id}]},
    )
    out = router_module.arbitration_overrule(body)
    assert out.get("ok") is True
    assert str((out.get("metadata") or {}).get("flow_state") or "") == "probe_waiting"


@pytest.mark.asyncio
async def test_final_verdict_returns_409_on_probe_pending(monkeypatch: pytest.MonkeyPatch) -> None:
    body = router_module.FinalVerdictRequest(
        metadata={"flow_state": "probe_waiting"},
        physics_tensor={"meta": {"x": 1}, "abs_nodes": {}},
    )

    monkeypatch.setattr(router_module, "resolve_consensus_history", lambda **_: [])

    async def _raise_conflict(*args, **kwargs):
        raise PermissionError("PROBE_PENDING：需先完成主动追问确认，终判阶段已锁定。")

    monkeypatch.setattr(router_module, "generate_final_verdict", _raise_conflict)

    with pytest.raises(router_module.HTTPException) as exc:
        await router_module.final_verdict(body)
    assert exc.value.status_code == 409
    detail = exc.value.detail if isinstance(exc.value.detail, dict) else {}
    assert str(detail.get("code") or "") == "FINAL_VERDICT_FLOW_STATE_CONFLICT"


@pytest.mark.asyncio
async def test_orchestrator_resume_returns_ack_token(monkeypatch: pytest.MonkeyPatch) -> None:
    body = router_module.ResumeCalculationRequest(
        session_id=321,
        user_feedback={"answer": "确认冲突"},
        metadata={"flow_state": "probe_waiting"},
    )

    def _ok_resume(**kwargs):
        assert int(kwargs.get("session_id") or 0) == 321
        return {
            "session_id": 321,
            "resume_ack_token": "resume:ut-token",
            "metadata": {"flow_state": "ready"},
            "physics_tensor": {"meta": {}},
            "plugin_outputs": {},
            "semantic_label_bundle_v1": {},
            "verified_fact_lines": [],
            "verdict_skeleton": "",
            "requires_narrative_refresh": False,
            "pre_injection_deity_display": {},
            "active_probing": {},
            "interrupt_request": {"state": "resumed"},
            "resume_pulse": {},
            "brain_hub": {"confirmed_facts": [], "sacred_evidence_refs": []},
        }

    monkeypatch.setattr(router_module.OrchestratorService, "resume_calculation", staticmethod(_ok_resume))
    out = await router_module.orchestrator_resume(body)
    assert str(out.get("resume_ack_token") or "").startswith("resume:")
