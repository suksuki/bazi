from __future__ import annotations

from app.skills.prompts_registry import (
    SCENE_ARCHITECT,
    SCENE_PROPHET,
    output_purge_directive,
    route_final_verdict_scene,
    scene_system_directive,
)


def _base_metadata() -> dict:
    return {
        "flow_state": "ready",
        "pillars": {
            "year": {"stem": "甲", "branch": "子"},
            "month": {"stem": "丙", "branch": "寅"},
            "day": {"stem": "戊", "branch": "午"},
            "hour": {"stem": "庚", "branch": "申"},
        },
        "conflict_matrix": {"points": []},
        "persistence_layer": {"interrupt_request": {}},
        "verdict_anchor_layer": {},
    }


def test_final_verdict_e2e_scene_architect_when_structure_missing() -> None:
    routed = route_final_verdict_scene(_base_metadata())
    assert routed.get("scene") == SCENE_ARCHITECT
    assert bool(routed.get("requires_internal_probe")) is True
    assert "请先完成格局定性" in str(routed.get("internal_probe_query") or "")
    sys_msg = scene_system_directive(str(routed.get("scene") or ""))
    assert "SCENE_ARCHITECT" in sys_msg


def test_final_verdict_e2e_scene_prophet_with_pure_four_part_constraints() -> None:
    md = _base_metadata()
    md["verdict_anchor_layer"] = {"structural_tags": ["财格"]}
    routed = route_final_verdict_scene(md)
    assert routed.get("scene") == SCENE_PROPHET

    sys_prompt = scene_system_directive(SCENE_PROPHET)
    assert "【裁断】" in sys_prompt and "【证据】" in sys_prompt and "【行】" in sys_prompt and "【禁】" in sys_prompt
    assert "气象意象集" in sys_prompt
    assert "来源、格式或计算过程" in sys_prompt
    assert "禁止输出任何关于系统状态、流程说明、免责声明或对照提示的文字" in output_purge_directive()

