"""Rule junction: bridge L1 facts to L2 semantic routers."""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict


class EnergyVaultStatus(str, Enum):
    """墓库 / 合局等通道态：独立记账下的做功门控（L2 可读）。"""

    ACTIVE = "ACTIVE"
    LOCKED = "LOCKED"
    AGGREGATED = "AGGREGATED"


def detect_universal_flags(*, metadata: Dict[str, Any], physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    axes = ((physics_tensor or {}).get("deity_energy_axes") or {}) if isinstance(physics_tensor, dict) else {}
    shangguan_abs = float((((axes or {}).get("伤官") or {}).get("absolute_energy", 0.0) or 0.0))
    zhengguan_abs = float((((axes or {}).get("正官") or {}).get("absolute_energy", 0.0) or 0.0))
    active = shangguan_abs > 0.0 and zhengguan_abs > 0.0
    control_energy = min(shangguan_abs, zhengguan_abs) if active else 0.0
    shangguan_jian_guan = active and control_energy > 0.0

    return {
        "SHANG_GUAN_JIAN_GUAN": bool(shangguan_jian_guan),
        "shangguan_abs": round(shangguan_abs, 4),
        "zhengguan_abs": round(zhengguan_abs, 4),
        "control_energy": round(control_energy, 4),
        "source": "L1_Junction",
    }

