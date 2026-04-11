"""L1 子算子：相生通道 — 对 Abs 增益项施加 η（默认 1.0，读 L1_OP_PROD_ETA）。"""
from __future__ import annotations

from typing import Any, Dict

OP_ID = "L1_OP_PROD"


def apply_eta(delta: Dict[str, Any], eta: float) -> Dict[str, Any]:
    """放大/收缩 delta 中的 abs_gain；η  clamp 到 [0, 3] 防误配。"""
    out = dict(delta)
    e = max(0.0, min(3.0, float(eta or 0.0)))
    gain = float(out.get("abs_gain") or 0.0) * e
    out["abs_gain"] = round(gain, 4)
    out["l1_op_production_eta"] = round(e, 4)
    return out
