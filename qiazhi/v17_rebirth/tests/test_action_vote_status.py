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


async def _plan_action(
    backend: _FakeBackend,
    monkeypatch: pytest.MonkeyPatch,
    signal: str,
    **payload: Any,
) -> dict:
    monkeypatch.setattr(stream_v17, "get_state_backend", lambda: backend)
    called: dict[str, Any] = {"kernel": 0}

    async def _fake_dispatch(**_kwargs: Any) -> bool:
        called["kernel"] += 1
        return True

    monkeypatch.setattr(PhysicsKernel, "dispatch_perturbation", _fake_dispatch)
    resp = await stream_v17.v17_action(
        {
            "v17_origin": "v17_rebirth",
            "signal": signal,
            "session_id": "sid",
            "status": "APPROVED",
            **payload,
        },
    )
    return {
        "body": _decode_json_response(resp),
        "called": called,
        "backend": backend,
    }


def _get_plan_status(backend: _FakeBackend) -> str:
    queue = backend.physics.get("sid", {}).get("decision_brain_state", {}).get("plan_queue", [])
    if not queue:
        return ""
    return str(queue[0].get("status") or "").strip()


def _get_plan_meta(backend: _FakeBackend) -> dict[str, Any]:
    queue = backend.physics.get("sid", {}).get("decision_brain_state", {}).get("plan_queue", [])
    if not queue:
        return {}
    raw = queue[0].get("meta")
    return dict(raw) if isinstance(raw, dict) else {}


def test_plan_approve_triggers_physics_and_commits(monkeypatch: pytest.MonkeyPatch) -> None:
    import asyncio

    backend = _FakeBackend()
    backend.physics["sid"]["pending_decisions"] = [
        {"id": "p1", "label": "方案A", "physical_impact": {"target_god": "七杀", "impact_ratio": 0.2}},
        {"id": "p2", "label": "方案B", "physical_impact": {"target_god": "正官", "impact_ratio": 0.1}},
    ]

    result = asyncio.run(
        _plan_action(
            backend=backend,
            monkeypatch=monkeypatch,
            signal="PLAN_APPROVE",
            decision_ids=["p1", "p2"],
            action="测试方案",
            anchor="test-anchor",
        ),
    )

    assert result["body"]["ok"] is True
    assert result["body"]["plan_signal"] == "PLAN_APPROVE"
    assert result["called"]["kernel"] == 2
    assert backend.physics["sid"]["pending_decisions"][0]["status"] == "APPROVED"
    assert backend.physics["sid"]["pending_decisions"][1]["status"] == "APPROVED"
    assert _get_plan_status(backend) == "COMMITTED"
    plan_meta = _get_plan_meta(backend)
    decision_trace = plan_meta.get("decision_trace")
    assert isinstance(decision_trace, list)
    assert {str(item.get("decision_id") or "") for item in decision_trace} >= {"p1", "p2"}


def test_plan_approve_preserves_kernel_runtime_writeback(monkeypatch: pytest.MonkeyPatch) -> None:
    import asyncio

    backend = _FakeBackend()
    backend.physics["sid"]["ten_gods_runtime"] = {"七杀": 8.5, "正官": 13.17}
    backend.physics["sid"]["ten_gods_base_l0"] = {"七杀": 8.5, "正官": 13.17}
    backend.physics["sid"]["pending_decisions"] = [
        {"id": "p1", "label": "方案A", "physical_impact": {"target_god": "七杀", "impact_ratio": 0.2}},
    ]

    monkeypatch.setattr(stream_v17, "get_state_backend", lambda: backend)

    async def _fake_dispatch(**_kwargs: Any) -> bool:
        tensor = dict(backend.physics["sid"])
        tensor["ten_gods_runtime"] = {"七杀": 10.2, "正官": 13.17}
        tensor["ten_gods_absolute"] = {"七杀": 10.2, "正官": 13.17}
        tensor["ten_gods_absolute_intensity"] = {"七杀": 10.2, "正官": 13.17}
        tensor["deity_scores"] = {"七杀": 10.2, "正官": 13.17}
        backend.physics["sid"] = tensor
        return True

    monkeypatch.setattr(PhysicsKernel, "dispatch_perturbation", _fake_dispatch)
    resp = asyncio.run(
        stream_v17.v17_action(
            {
                "v17_origin": "v17_rebirth",
                "signal": "PLAN_APPROVE",
                "session_id": "sid",
                "status": "APPROVED",
                "decision_ids": ["p1"],
                "action": "测试方案",
            }
        )
    )
    body = _decode_json_response(resp)

    assert body["ok"] is True
    assert backend.physics["sid"]["ten_gods_runtime"]["七杀"] == 10.2
    assert backend.physics["sid"]["pending_decisions"][0]["status"] == "APPROVED"
    assert _get_plan_status(backend) == "COMMITTED"


def test_plan_approve_untargeted_rows_consume_context(monkeypatch: pytest.MonkeyPatch) -> None:
    import asyncio

    backend = _FakeBackend()
    backend.physics["sid"]["pending_decisions"] = [
        {
            "id": "p1",
            "label": "状态机节律",
            "plugin_id": "l1.physics.op_status",
            "title": "日主处于病位，作为上下文观察。",
            "physical_impact": {"impact_ratio": 0.015},
        },
    ]

    result = asyncio.run(
        _plan_action(
            backend=backend,
            monkeypatch=monkeypatch,
            signal="PLAN_APPROVE",
            decision_ids=["p1"],
            action="处理上下文",
            anchor="context-anchor",
        ),
    )

    assert result["body"]["ok"] is True
    assert result["body"]["signal"] == "CONTEXT_CONSUMED"
    assert result["called"]["kernel"] == 0
    assert backend.physics["sid"]["pending_decisions"][0]["status"] == "CONSUMED_CONTEXT"
    assert _get_plan_status(backend) == "COMMITTED"


def test_plan_reject_only_marks_decisions_and_no_physics(monkeypatch: pytest.MonkeyPatch) -> None:
    import asyncio

    backend = _FakeBackend()
    backend.physics["sid"]["pending_decisions"] = [
        {"id": "p1", "label": "方案A", "physical_impact": {"target_god": "七杀", "impact_ratio": 0.2}},
    ]

    result = asyncio.run(
        _plan_action(
            backend=backend,
            monkeypatch=monkeypatch,
            signal="PLAN_REJECT",
            decision_ids=["p1"],
            action="测试否决",
            anchor="test-anchor",
            status="REJECTED",
        ),
    )

    assert result["body"]["ok"] is True
    assert result["body"]["signal"] in {"VOTE_REJECTED", "VOTE_WITHDRAWN"}
    assert result["called"]["kernel"] == 0
    assert backend.physics["sid"]["pending_decisions"][0]["status"] == "REJECTED"


def test_plan_routing_claim_on_system_path() -> None:
    rows = [
        {
            "label": "安全路径",
            "physical_impact": {"target_god": "正官", "impact_ratio": 0.1},
            "exclusivity_key": "k1",
        }
    ]
    route = stream_v17._decision_route_reason({}, rows)
    claim = route.get("routing_claim")
    assert isinstance(claim, dict)
    assert route["routing"] == "system"
    assert claim.get("severity") == "P3"
    assert str(claim.get("routing_reason") or "").strip()


def test_plan_routing_claim_with_explicit_user_route() -> None:
    rows = [
        {
            "label": "高风险",
            "physical_impact": {"target_god": "七杀", "impact_ratio": 0.05},
            "exclusivity_key": "k1",
        }
    ]
    route = stream_v17._decision_route_reason({"routing": "user"}, rows)
    claim = route.get("routing_claim")
    assert route["routing"] == "user"
    assert isinstance(claim, dict)
    assert claim.get("severity") == "P1"
    assert float(claim.get("confidence", 0.0)) >= 0.86


def test_plan_escalate_stays_await_review(monkeypatch: pytest.MonkeyPatch) -> None:
    import asyncio

    backend = _FakeBackend()
    backend.physics["sid"]["pending_decisions"] = [
        {"id": "p1", "label": "方案A", "physical_impact": {"target_god": "七杀", "impact_ratio": 0.2}},
    ]

    result = asyncio.run(
        _plan_action(
            backend=backend,
            monkeypatch=monkeypatch,
            signal="PLAN_ESCALATE",
            decision_ids=["p1"],
            action="测试升档",
            anchor="test-anchor",
            status="PENDING",
        ),
    )

    assert result["body"]["ok"] is True
    assert result["called"]["kernel"] == 0
    assert backend.physics["sid"]["pending_decisions"][0]["status"] == "AWAIT_REVIEW"
    assert _get_plan_status(backend) == "AWAIT_REVIEW"


def test_plan_withdraw_rejects_and_marks_terminal(monkeypatch: pytest.MonkeyPatch) -> None:
    import asyncio

    backend = _FakeBackend()
    backend.physics["sid"]["pending_decisions"] = [
        {"id": "p1", "label": "方案A", "physical_impact": {"target_god": "七杀", "impact_ratio": 0.2}},
    ]

    result = asyncio.run(
        _plan_action(
            backend=backend,
            monkeypatch=monkeypatch,
            signal="PLAN_WITHDRAW",
            decision_ids=["p1"],
            action="测试撤回",
            anchor="test-anchor",
            status="WITHDRAW",
        ),
    )

    assert result["body"]["ok"] is True
    assert result["called"]["kernel"] == 0
    assert backend.physics["sid"]["pending_decisions"][0]["status"] == "REJECTED"
    assert _get_plan_status(backend) == "REJECTED"


def test_plan_approve_idempotent_no_duplicate_kernel_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    import asyncio

    backend = _FakeBackend()
    backend.physics["sid"]["pending_decisions"] = [
        {
            "id": "p1",
            "label": "方案A",
            "status": "APPROVED",
            "physical_impact": {"target_god": "七杀", "impact_ratio": 0.2},
        }
    ]

    result = asyncio.run(
        _plan_action(
            backend=backend,
            monkeypatch=monkeypatch,
            signal="PLAN_APPROVE",
            decision_ids=["p1"],
            action="测试幂等",
            anchor="test-anchor",
        ),
    )

    assert result["body"]["ok"] is True
    assert result["body"]["signal"] == "VOTE_IGNORED"
    assert result["called"]["kernel"] == 0
    assert "skip duplicate" in str(result["body"].get("detail", ""))


def test_plan_submit_auto_executes_when_system_routing(monkeypatch: pytest.MonkeyPatch) -> None:
    import asyncio

    backend = _FakeBackend()
    backend.physics["sid"]["pending_decisions"] = [
        {"id": "p1", "label": "方案A", "physical_impact": {"target_god": "七杀", "impact_ratio": 0.06}},
        {"id": "p2", "label": "方案B", "physical_impact": {"target_god": "正官", "impact_ratio": -0.05}},
    ]

    result = asyncio.run(
        _plan_action(
            backend=backend,
            monkeypatch=monkeypatch,
            signal="PLAN_SUBMIT",
            decision_ids=["p1", "p2"],
            action="自动提交",
            anchor="auto-anchor",
            status="APPROVED",
        ),
    )

    assert result["body"]["ok"] is True
    assert result["body"]["plan_signal"] == "PLAN_SUBMIT"
    assert result["called"]["kernel"] == 2
    assert backend.physics["sid"]["pending_decisions"][0]["status"] == "APPROVED"
    assert backend.physics["sid"]["pending_decisions"][1]["status"] == "APPROVED"
    assert _get_plan_status(backend) == "COMMITTED"


def test_plan_submit_llm_routing_generates_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    import asyncio

    backend = _FakeBackend()
    backend.physics["sid"]["pending_decisions"] = [
        {
            "id": "p1",
            "label": "方案A",
            "physical_impact": {"target_god": "七杀", "impact_ratio": 0.20},
            "priority": 0.7,
        }
    ]

    result = asyncio.run(
        _plan_action(
            backend=backend,
            monkeypatch=monkeypatch,
            signal="PLAN_SUBMIT",
            decision_ids=["p1"],
            action="LLM 路由用例",
            anchor="llm-anchor",
            status="PENDING",
        ),
    )

    assert result["body"]["ok"] is True
    assert result["body"]["signal"] == "PLAN_SUBMIT"
    assert result["called"]["kernel"] == 0
    assert result["body"].get("llm_review_prompt")
    assert "LLM 路由用例" in str(result["body"].get("llm_review_prompt") or "")
    assert _get_plan_status(backend) == "AWAIT_REVIEW"
    assert _get_plan_meta(backend).get("llm_review_prompt")
    assert isinstance(_get_plan_meta(backend).get("decision_trace"), list)


def test_plan_submit_manual_route_stays_review(monkeypatch: pytest.MonkeyPatch) -> None:
    import asyncio

    backend = _FakeBackend()
    backend.physics["sid"]["pending_decisions"] = [
        {"id": "p1", "label": "方案A", "physical_impact": {"target_god": "七杀", "impact_ratio": 0.75}},
    ]

    result = asyncio.run(
        _plan_action(
            backend=backend,
            monkeypatch=monkeypatch,
            signal="PLAN_SUBMIT",
            decision_ids=["p1"],
            action="手工提交",
            anchor="manual-anchor",
            status="PENDING",
            routing="user",
        ),
    )

    assert result["body"]["ok"] is True
    assert result["called"]["kernel"] == 0
    assert backend.physics["sid"]["pending_decisions"][0]["status"] == "AWAIT_REVIEW"
    assert _get_plan_status(backend) == "AWAIT_REVIEW"


def test_plan_approve_without_verdict_publishes_physics_sync(monkeypatch: pytest.MonkeyPatch) -> None:
    import asyncio

    backend = _FakeBackend()
    backend.physics["sid"]["pending_decisions"] = [
        {"id": "p1", "label": "方案A", "physical_impact": {"target_god": "七杀", "impact_ratio": 0.06}},
    ]

    result = asyncio.run(
        _plan_action(
            backend=backend,
            monkeypatch=monkeypatch,
            signal="PLAN_APPROVE",
            decision_ids=["p1"],
            action="同步验证",
            anchor="sync-anchor",
            request_verdict=False,
        ),
    )

    assert result["body"]["ok"] is True
    assert backend.events, "expected backend publish_action to be called"
    last_event = backend.events[-1]
    assert last_event.get("signal") == "PHYSICS_SYNC"
    assert last_event.get("request_verdict") is False
    assert isinstance(last_event.get("payload"), dict)
    assert (last_event.get("payload") or {}).get("type") == "PHYSICS_SYNC"
