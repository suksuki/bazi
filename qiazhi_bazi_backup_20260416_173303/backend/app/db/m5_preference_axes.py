"""V13.06：从 HTN 快照推断 M5 偏好轴（古法格局 vs 现代意象 / 权力等级峰值）。"""
from __future__ import annotations

from typing import Any, List, Optional, Sequence, Tuple

from app.core.plugins.registry import plugin_authority_level


def _collect_plugin_ids(obj: Any, out: Optional[List[str]] = None) -> List[str]:
    if out is None:
        out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "plugin_id" and isinstance(v, str) and v.strip():
                out.append(v.strip())
            _collect_plugin_ids(v, out)
    elif isinstance(obj, list):
        for x in obj:
            _collect_plugin_ids(x, out)
    return out


def infer_m5_preference_axes(snapshot_payload: Any) -> Tuple[str, Optional[int]]:
    """
    返回 ``(logic_school_axis, authority_scope_peak)``。

    - ``logic_school_axis``: CLASSICAL_GRID | MODERN_IMAGERY | MIXED | UNKNOWN
    - ``authority_scope_peak``: 快照载荷中出现过的 plugin_id 的最高 ``plugin_authority_level``；无则 None。
    """
    ids = _collect_plugin_ids(snapshot_payload or {})
    if not ids:
        return "UNKNOWN", None
    dedup = list(dict.fromkeys(ids))
    peaks = [plugin_authority_level(p) for p in dedup]
    peak = max(peaks) if peaks else None
    classical = sum(1 for p in dedup if str(p).startswith("classical."))
    modern = sum(1 for p in dedup if str(p).startswith("modern."))
    if classical > 0 and modern == 0:
        axis = "CLASSICAL_GRID"
    elif modern > 0 and classical == 0:
        axis = "MODERN_IMAGERY"
    elif classical > 0 and modern > 0:
        axis = "MIXED"
    else:
        axis = "UNKNOWN"
    return axis, peak
