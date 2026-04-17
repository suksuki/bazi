"""L1 子算子：合局 / 合绊 — 对锁定能量项施加 η（读 L1_OP_CONN_ETA）。"""
from __future__ import annotations

from typing import Any, Dict

OP_ID = "L1_OP_CONN"


def apply_eta(delta: Dict[str, Any], eta: float) -> Dict[str, Any]:
    out = dict(delta)
    e = max(0.0, min(3.0, float(eta or 0.0)))
    locked = float(out.get("abs_locked") or 0.0) * e
    out["abs_locked"] = round(locked, 4)
    out["l1_op_connection_eta"] = round(e, 4)
    return out
