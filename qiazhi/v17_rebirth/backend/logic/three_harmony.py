"""Readonly mirror: three-harmony combine signal."""
from __future__ import annotations

from typing import Dict, List


def run_three_harmony(*, source_abs: float, target_abs: float, lock_ratio: float = 0.3) -> Dict[str, float | str]:
    src = max(0.0, float(source_abs or 0.0))
    tgt = max(0.0, float(target_abs or 0.0))
    ratio = min(1.0, max(0.0, float(lock_ratio or 0.0)))
    locked = min(src, tgt) * ratio
    return {"effect": "combine", "abs_locked": round(locked, 4), "vector": "binding"}


def collect_v17_facts(deity_scores: Dict[str, float]) -> List[dict]:
    food = float(deity_scores.get("食神", 0.0))
    wealth = float(deity_scores.get("正财", 0.0) + deity_scores.get("偏财", 0.0))
    result = run_three_harmony(source_abs=food, target_abs=wealth, lock_ratio=0.32)
    locked = float(result.get("abs_locked", 0.0))
    if locked < 4.0:
        return []
    return [
        {
            "plugin": "three_harmony",
            "fact": f"三合协同增强，资源绑定强度约 {locked:.1f}。",
            "label": "将执行节奏拆分为两段，先稳态验证再扩张。",
            "priority": min(0.95, 0.55 + locked / 20.0),
        }
    ]
