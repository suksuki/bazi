"""L1 atomic plugin: grave (墓库) — channel lock and burst when unlocked."""
from __future__ import annotations

from typing import Any, Dict

from app.core.rules.junction import EnergyVaultStatus


def run_grave(
    *,
    base_abs: float,
    unlocked: bool,
    burst_multiplier: float,
) -> Dict[str, Any]:
    """墓库通道：锁定态 φ→0；冲开等解锁态 Abs_burst = base_abs * burst_multiplier。

    burst_multiplier 来自 `resolve_physics_settings`（如 GRAVE_BURST_MULTIPLIER），不在此写死。
    """
    base = max(0.0, float(base_abs or 0.0))
    mult = max(0.0, float(burst_multiplier or 0.0))
    if not unlocked:
        return {
            "effect": "grave",
            "phi_work": 0.0,
            "abs_burst": 0.0,
            "abs_base": round(base, 4),
            "energy_vault_status": EnergyVaultStatus.LOCKED.value,
            "vector": "tomb_channel",
        }
    return {
        "effect": "grave",
        "phi_work": 1.0,
        "abs_burst": round(base * mult, 4),
        "abs_base": round(base, 4),
        "energy_vault_status": EnergyVaultStatus.ACTIVE.value,
        "vector": "tomb_channel",
    }
