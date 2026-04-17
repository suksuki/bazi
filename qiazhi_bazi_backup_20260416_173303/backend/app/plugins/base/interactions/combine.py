"""L1 atomic plugin: combine interaction."""
from __future__ import annotations

from typing import Dict


def run_combine(*, source_abs: float, target_abs: float, lock_ratio: float = 0.3) -> Dict[str, float | str]:
    src = max(0.0, float(source_abs or 0.0))
    tgt = max(0.0, float(target_abs or 0.0))
    ratio = min(1.0, max(0.0, float(lock_ratio or 0.0)))
    locked = min(src, tgt) * ratio
    return {
        "effect": "combine",
        "abs_loss": 0.0,
        "abs_locked": round(locked, 4),
        "vector": "binding",
    }

