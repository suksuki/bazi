"""L1 atomic plugin: pierce/harm interaction."""
from __future__ import annotations

from typing import Dict


def run_pierce(*, source_abs: float, target_abs: float, penetration_ratio: float = 0.45) -> Dict[str, float | str]:
    src = max(0.0, float(source_abs or 0.0))
    tgt = max(0.0, float(target_abs or 0.0))
    ratio = min(1.0, max(0.0, float(penetration_ratio or 0.0)))
    damage = min(src, tgt) * ratio
    return {
        "effect": "pierce",
        "abs_loss": round(damage, 4),
        "abs_gain": 0.0,
        "vector": "penetration",
    }

