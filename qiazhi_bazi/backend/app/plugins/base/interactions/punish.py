"""L1 atomic plugin: punish (刑) — internal friction torque on Abs."""
from __future__ import annotations

from typing import Dict, Literal

PunishMode = Literal["sanxing", "zixing"]


def run_punish(
    *,
    source_abs: float,
    target_abs: float,
    friction_coeff: float,
    mode: PunishMode = "sanxing",
) -> Dict[str, float | str]:
    """Static Abs loss from torsional coupling between two nodes (三刑边或自刑对).

    Coefficients come from DB `physics_interaction_params`, not literals here.
    """
    src = max(0.0, float(source_abs or 0.0))
    tgt = max(0.0, float(target_abs or 0.0))
    k = max(0.0, float(friction_coeff or 0.0))
    coupling = min(src, tgt)
    loss = coupling * k
    return {
        "effect": "punish",
        "mode": mode,
        "abs_loss": round(loss, 4),
        "abs_gain": 0.0,
        "vector": "torsional_friction",
    }
