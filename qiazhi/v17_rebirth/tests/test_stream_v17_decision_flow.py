from __future__ import annotations

from v17_rebirth.backend.api import stream_v17_decision_flow as decision_flow


def test_safe_plan_ids_dedup_and_cast() -> None:
    assert decision_flow.safe_plan_ids(["a", "b", "a", 0, None, ""]) == ["a", "b"]
    assert decision_flow.safe_plan_ids("x") == ["x"]
    assert decision_flow.safe_plan_ids(None) == []


def test_decision_route_reason_explicit_route() -> None:
    rows = [
        {"id": "d1", "label": "伤官见官", "physical_impact": {"impact_ratio": 0.12, "target_god": "正官"}},
    ]
    route = decision_flow.decision_route_reason(
        {"routing": "llm"},
        rows,
        plan_auto_approve_max_count=4,
        plan_auto_approve_max_ratio=0.2,
        plan_auto_approve_max_sum=1.0,
    )
    assert route["routing"] == "llm"
    assert route["routing_policy"] == "explicit_payload_routing"
    assert "explicit" in route["routing_reason"]


def test_seed_plan_from_payload_builds_plan_and_trace() -> None:
    rows = [
        {
            "id": "x",
            "label": "三合成局",
            "source": "test-plugin",
            "physical_impact": {"impact_ratio": 0.33, "target_god": "七杀"},
            "priority": 0.2,
        }
    ]
    plan = decision_flow.seed_plan_from_payload(
        {
            "action": "test",
            "routing": "system",
            "decision_ids": ["x"],
            "source": "manual",
        },
        session_id="session-1",
        rows=rows,
        signal="PLAN_SUBMIT",
        auto_approve_max=8,
        plan_auto_count=8,
    )

    assert plan.plan_id
    assert plan.session_id == "session-1"
    assert plan.routing == "system"
    assert plan.status in {"AWAIT_REVIEW", "APPROVED"}
    assert plan.meta.get("decision_trace_contract") == "v17.decision.trace.v1"
    assert plan.meta.get("decision_trace", [])
