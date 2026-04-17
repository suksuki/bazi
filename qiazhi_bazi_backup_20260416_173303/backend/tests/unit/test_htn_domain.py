from __future__ import annotations

from app.logic.brain.htn_domain import HTN_DOMAIN, evaluate_htn_tasks, plan_htn_route


def test_htn_domain_shape() -> None:
    assert HTN_DOMAIN["ROOT_GOAL"] == "FINAL_VERDICT"
    assert "TASKS" in HTN_DOMAIN
    assert "OBSERVE" in HTN_DOMAIN["TASKS"]


def test_evaluate_htn_tasks_ordered() -> None:
    out = evaluate_htn_tasks(
        {
            "has_raw_data": True,
            "has_clash_matrix": True,
            "logic_gap_detected": True,
            "introspection_clear": False,
        }
    )
    assert out == ["OBSERVE", "AUDIT", "PROBE"]


def test_plan_htn_route_probe_status() -> None:
    p = plan_htn_route(
        {
            "has_raw_data": True,
            "has_clash_matrix": True,
            "logic_gap_detected": True,
            "introspection_clear": False,
            "will_assimilated": False,
        }
    )
    assert p["goal"] == "终局裁决 v2.0"
    assert "[PROBE]" in list(p["plan"])
    assert any(str(x).endswith("(pending)") for x in list(p["plan"]))
    assert "等待裁决者指令" in str(p["status"])
