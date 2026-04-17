"""墓库（辰戌丑未）：对宫未全时闭库语义与 η_tomb（与全局墓库强度可解耦）。"""
from __future__ import annotations

from typing import Any, Dict, List

_TOMB_BRANCHES = frozenset({"辰", "戌", "丑", "未"})
_TOMB_OPPOSITE = {"辰": "戌", "戌": "辰", "丑": "未", "未": "丑"}


def resolve_tomb_eta(settings: Dict[str, float]) -> float:
    """墓库相关物理折损/闭锁强度系数，默认与 TOMB_LOCK_RATE 同量级、可单独覆盖。"""
    raw = settings.get("MANGPAI_ETA_TOMB", settings.get("TOMB_LOCK_RATE", 0.9))
    return float(max(0.0, min(1.0, float(raw))))


def tomb_vault_assertion_lines(metadata: Dict[str, Any]) -> List[str]:
    """
    墓库：若支在局中而「对宫冲支」不在局中，则无法形成辰戌冲/丑未冲 → 闭库。
    断言注入 result_logs 风格文案（由上层加 [MANGPAI_CHIP] 或纯断言）。
    """
    pillars = (metadata or {}).get("pillars") or {}
    if not isinstance(pillars, dict):
        return []
    branches: Dict[str, str] = {}
    for slot in ("year", "month", "day", "hour"):
        col = pillars.get(slot)
        if isinstance(col, dict) and col.get("branch"):
            branches[slot] = str(col["branch"])
        else:
            return []
    present = set(branches.values())
    lines: List[str] = []
    for tb in sorted(present & _TOMB_BRANCHES):
        opp = _TOMB_OPPOSITE.get(tb)
        if not opp or opp not in present:
            lines.append(f"墓库闭锁（{tb}）：对宫支未全，能量无法溢出。")
    return lines


def tomb_chip_logs(metadata: Dict[str, Any]) -> List[str]:
    return [f"[MANGPAI_CHIP] {line}" for line in tomb_vault_assertion_lines(metadata)]
