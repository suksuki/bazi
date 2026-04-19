from __future__ import annotations

import json
from typing import Any

import pytest

from v17_rebirth.backend.api import stream_v17
from v17_rebirth.backend.logic.L1_atomic_ops.physics_kernel import PhysicsKernel


class _FakeBackend:
    def __init__(self) -> None:
        self.physics = {
            "sid": {
                "pending_decisions": [
                    {"id": "d1", "label": "方案A", "physical_impact": {"target_god": "七杀", "impact_ratio": 0.2}}
                ]
            }
        }
        self.events: list[dict] = []

    async def get_physics(self, session_id: str) -> dict:
        return dict(self.physics.get(session_id) or {})

    async def set_physics(self, session_id: str, tensor: dict) -> bool:
        self.physics[session_id] = dict(tensor)
        return True

    async def publish_action(self, _session_id: str, event: dict) -> None:
        self.events.append(dict(event))


def _decode_json_response(resp) -> dict:
    return json.loads(resp.body.decode("utf-8"))


async def _reject_vote(backend: _FakeBackend, monkeypatch: pytest.MonkeyPatch) -> dict:
    monkeypatch.setattr(stream_v17, "get_state_backend", lambda: backend)
    called = {"kernel": 0}

    async def _fake_dispatch(**_kwargs) -> bool:
        called["kernel"] += 1
        return True

    monkeypatch.setattr(PhysicsKernel, "dispatch_perturbation", _fake_dispatch)
    resp = await stream_v17.v17_action(
        {
            "v17_origin": "v17_rebirth",
            "signal": "ACTION_TAKEN",
            "session_id": "sid",
            "decision_id": "d1",
            "action": "方案A",
            "status": "REJECTED",
        }
    )
    body = _decode_json_response(resp)
    return {"body": body, "called": called, "backend": backend}


def test_rejected_vote_skips_physics_kernel(monkeypatch: pytest.MonkeyPatch) -> None:
    import asyncio

    backend = _FakeBackend()
    result = asyncio.run(_reject_vote(backend, monkeypatch))

    assert result["body"]["signal"] == "VOTE_REJECTED"
    assert result["called"]["kernel"] == 0
    assert backend.physics["sid"]["pending_decisions"][0]["status"] == "REJECTED"


async def _batch_vote(backend: _FakeBackend, monkeypatch: pytest.MonkeyPatch) -> dict:
    monkeypatch.setattr(stream_v17, "get_state_backend", lambda: backend)
    called: dict[str, Any] = {"kernel": 0, "targets": []}

    async def _fake_dispatch(**kwargs: Any) -> bool:
        called["kernel"] += 1
        payload = kwargs.get("payload", {})
        called["targets"].append(
            (
                str(payload.get("decision_id", "")),
                str(payload.get("target_god", "")),
                payload.get("physical_impact", {}).get("impact_ratio") if isinstance(payload.get("physical_impact"), dict) else None,
            )
        )
        return True

    monkeypatch.setattr(PhysicsKernel, "dispatch_perturbation", _fake_dispatch)
    resp = await stream_v17.v17_action(
        {
            "v17_origin": "v17_rebirth",
            "signal": "ACTION_TAKEN",
            "session_id": "sid",
            "decision_ids": ["d1", "d2"],
            "action": "方案A",
            "status": "APPROVED",
            "physical_impact": {"target_god": "七杀", "impact_ratio": 0.99},
        }
    )
    body = _decode_json_response(resp)
    return {"body": body, "called": called, "backend": backend}


def test_batch_vote_applies_each_decision(monkeypatch: pytest.MonkeyPatch) -> None:
    import asyncio

    backend = _FakeBackend()
    backend.physics["sid"]["pending_decisions"] = [
        {"id": "d1", "label": "方案A", "physical_impact": {"target_god": "七杀", "impact_ratio": 0.2}},
        {"id": "d2", "label": "方案B", "physical_impact": {"target_god": "正官", "impact_ratio": 0.2}},
    ]
    result = asyncio.run(_batch_vote(backend, monkeypatch))

    assert result["body"]["ok"] is True
    assert result["body"]["signal"] == "ACTION_TAKEN"
    assert result["called"]["kernel"] == 2
    assert {row[0] for row in result["called"]["targets"]} == {"d1", "d2"}
    assert {row[1] for row in result["called"]["targets"]} == {"七杀", "正官"}
    assert {row[2] for row in result["called"]["targets"]} == {0.2}
    assert backend.physics["sid"]["pending_decisions"][0]["status"] == "APPROVED"
    assert backend.physics["sid"]["pending_decisions"][1]["status"] == "APPROVED"
