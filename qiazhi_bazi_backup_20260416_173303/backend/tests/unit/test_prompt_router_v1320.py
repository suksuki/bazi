from __future__ import annotations

from app.skills.prompts_registry import (
    SCENE_ARCHITECT,
    SCENE_ARBITER,
    SCENE_PROPHET,
    output_purge_directive,
    route_final_verdict_scene,
    scene_system_directive,
)


def _base_metadata() -> dict:
    return {
        "flow_state": "ready",
        "conflict_matrix": {"points": []},
        "verdict_anchor_layer": {},
        "persistence_layer": {"interrupt_request": {}},
        "pillars": {
            "year": {"stem": "甲", "branch": "子"},
            "month": {"stem": "丙", "branch": "寅"},
            "day": {"stem": "戊", "branch": "午"},
            "hour": {"stem": "庚", "branch": "申"},
        },
    }


def test_prompt_router_routes_to_arbiter_when_conflicts_pending() -> None:
    md = _base_metadata()
    md["conflict_matrix"] = {"points": [{"detail": "寅申冲"}]}
    out = route_final_verdict_scene(md)
    assert out["scene"] == SCENE_ARBITER


def test_prompt_router_routes_to_architect_when_structure_missing() -> None:
    md = _base_metadata()
    out = route_final_verdict_scene(md)
    assert out["scene"] == SCENE_ARCHITECT
    assert out["requires_internal_probe"] is True
    assert "格局定性" in str(out["internal_probe_query"])


def test_prompt_router_routes_to_prophet_when_structure_ready() -> None:
    md = _base_metadata()
    md["verdict_anchor_layer"] = {"structural_tags": ["财格"]}
    out = route_final_verdict_scene(md)
    assert out["scene"] == SCENE_PROPHET


def test_scene_prophet_hard_constraint_and_output_purging() -> None:
    sys_msg = scene_system_directive(SCENE_PROPHET)
    assert "【裁断】" in sys_msg and "【证据】" in sys_msg and "【行】" in sys_msg and "【禁】" in sys_msg
    assert "气象意象集" in sys_msg
    assert "来源、格式或计算过程" in sys_msg
    assert "禁止输出任何关于系统状态、流程说明、免责声明或对照提示的文字" in output_purge_directive()

