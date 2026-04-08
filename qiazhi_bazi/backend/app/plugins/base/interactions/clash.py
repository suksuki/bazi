"""L1 atomic plugin: clash interaction."""
from __future__ import annotations

from typing import Dict


def run_clash(*, source_abs: float, target_abs: float, intensity: float = 1.0) -> Dict[str, float | str]:
    src = max(0.0, float(source_abs or 0.0))
    tgt = max(0.0, float(target_abs or 0.0))
    k = max(0.0, float(intensity or 0.0))
    exchange = min(src, tgt) * 0.35 * k
    return {
        "effect": "clash",
        "abs_loss": round(exchange, 4),
        "abs_gain": round(exchange * 0.2, 4),
        "vector": "repulsion",
    }

