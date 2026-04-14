"""V12.9: HTN 任务分层域 + Planner。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class TaskNode:
    name: str
    pre_conditions: Dict[str, str]


HTN_DOMAIN = {
    "ROOT_GOAL": "FINAL_VERDICT",
    "TASKS": {
        "OBSERVE": {"pre": "has_raw_data", "action": "M1_Scanner"},
        "AUDIT": {"pre": "has_clash_matrix", "action": "M2_Auditor"},
        "PROBE": {"pre": "logic_gap_detected", "action": "M3_Active_Probing"},
        "SYNTHESIS": {"pre": "introspection_clear", "action": "M4_LLM_Final"},
    },
}


def evaluate_htn_tasks(flags: Dict[str, bool]) -> List[str]:
    """按 HTN_DOMAIN 顺序返回当前可执行任务。"""
    f = flags if isinstance(flags, dict) else {}
    out: List[str] = []
    tasks = HTN_DOMAIN.get("TASKS") if isinstance(HTN_DOMAIN.get("TASKS"), dict) else {}
    for name in ("OBSERVE", "AUDIT", "PROBE", "SYNTHESIS"):
        row = tasks.get(name) if isinstance(tasks, dict) else None
        if not isinstance(row, dict):
            continue
        pre = str(row.get("pre") or "").strip()
        if pre and bool(f.get(pre)):
            out.append(name)
    return out


def plan_htn_route(blackboard_state: Dict[str, bool]) -> Dict[str, object]:
    """统一任务编排入口：根据黑板状态产出 plan/status。"""
    flags = blackboard_state if isinstance(blackboard_state, dict) else {}
    goal = "终局裁决 v2.0"
    full_order = ["OBSERVE", "PROBE", "AUDIT", "SYNTHESIS"]
    active = "OBSERVE"
    if flags.get("logic_gap_detected"):
        active = "PROBE"
        status = "正在执行 PROBE，等待裁决者指令。"
    elif flags.get("will_assimilated"):
        active = "SYNTHESIS"
        status = "意志已同化，推进 M4_Synthesis。"
    elif flags.get("has_clash_matrix"):
        active = "AUDIT"
        status = "冲突矩阵已就绪，执行 AUDIT。"
    elif flags.get("will_assimilated"):
        active = "SYNTHESIS"
        status = "意志已同化，推进 M4_Synthesis。"
    else:
        status = "执行 Observe/Audit 常规链路。"
    plan_render: List[str] = []
    for name in full_order:
        if name == active:
            plan_render.append(f"[{name}]")
        elif full_order.index(name) > full_order.index(active):
            plan_render.append(f"{name}(pending)")
        else:
            plan_render.append(name)
    seeds_matched = list(flags.get("seeds_matched") or []) if isinstance(flags.get("seeds_matched"), list) else []
    return {
        "goal": goal,
        "plan": plan_render,
        "active_task": active,
        "status": status,
        "lineage": "HTN_DRIVEN",
        "seeds_matched": [str(x) for x in seeds_matched if str(x).strip()],
    }


__all__ = ["TaskNode", "HTN_DOMAIN", "evaluate_htn_tasks", "plan_htn_route"]
