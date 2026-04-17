"""L1 子算子：相克 / 穿破 / 刑耗 — 对 Abs 损耗项施加 η（读 L1_OP_DEST_ETA）。"""
from __future__ import annotations

from typing import Any, Dict

OP_ID = "L1_OP_DEST"


def apply_eta(delta: Dict[str, Any], eta: float) -> Dict[str, Any]:
    out = dict(delta)
    e = max(0.0, min(3.0, float(eta or 0.0)))
    loss = float(out.get("abs_loss") or 0.0) * e
    out["abs_loss"] = round(loss, 4)
    out["l1_op_destruction_eta"] = round(e, 4)
    torque = out.get("impact_torque")
    if torque is not None:
        try:
            out["impact_torque"] = round(float(torque) * e, 4)
        except (TypeError, ValueError):
            pass
    return out
