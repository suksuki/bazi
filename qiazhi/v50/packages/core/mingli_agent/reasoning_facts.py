from __future__ import annotations

from typing import Any

from core.mingli_agent.context import MingliContextCompiler
from core.mingli_agent.contracts import ChartWorldInstance


def _reasoning_world_payload(world: ChartWorldInstance) -> dict[str, Any]:
    return MingliContextCompiler().compile(world=world, stage="pattern").payload

def _element_role_ledger(ledger: dict[str, Any]) -> dict[str, str]:
    day_master = ledger.get("day_master") or {}
    day_element = str(day_master.get("day_element") or day_master.get("element") or "")
    if not day_element:
        return {}
    generates = {"wood": "fire", "fire": "earth", "earth": "metal", "metal": "water", "water": "wood"}
    controls = {"wood": "earth", "earth": "water", "water": "fire", "fire": "metal", "metal": "wood"}
    generated_by = next((source for source, target in generates.items() if target == day_element), "")
    controlled_by = next((source for source, target in controls.items() if target == day_element), "")
    return {
        day_element: "比劫/同类",
        generates.get(day_element, ""): "食伤/输出",
        controls.get(day_element, ""): "财星/资源结果",
        controlled_by: "官杀/规则压力",
        generated_by: "印星/支持输入",
    }
