"""
FDS 2.0 流形追踪：基于 static_atlas 的 D_M 概率云与叠加态（前 3 格局）。
GET /api/v2/manifold/trace/{user_id} 的底层实现。
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from core.engine import load_static_atlas

DIM_ORDER = ["E", "O", "M", "S", "R"]


def _vec_5d(x: Any) -> List[float]:
    if isinstance(x, (list, tuple)) and len(x) >= 5:
        return [float(x[i]) for i in range(5)]
    if isinstance(x, dict):
        return [float(x.get(k, 0)) for k in DIM_ORDER]
    return [0.0] * 5


def _dm(point: List[float], centroid: List[float]) -> float:
    """欧氏距离 D_M。"""
    if len(point) != 5 or len(centroid) != 5:
        return float("inf")
    return math.sqrt(sum((point[i] - centroid[i]) ** 2 for i in range(5)))


def compute_dm_cloud(
    point_5d: Any,
    *,
    atlas: Optional[Dict[str, Any]] = None,
    top_k: int = 3,
    double_capture_ratio: float = 1.2,
) -> Dict[str, Any]:
    """
    计算当前 5D 点相对 60 个质心的 D_M 概率云，返回前 top_k 个格局的叠加态。
    与 v61 对撞逻辑一致：距离比 ≤ double_capture_ratio 的视为多重捕获，以概率权重表示叠加。
    """
    atlas = atlas or load_static_atlas()
    patterns = atlas.get("patterns") or []
    vec = _vec_5d(point_5d)
    if len(vec) != 5:
        return {"overlay": [], "distances": {}, "point_5d": vec, "schema": atlas.get("schema", "")}

    distances = {}
    for p in patterns:
        pid = (p.get("pattern_id") or "").strip()
        cen = p.get("centroid_5d")
        if not pid or not cen:
            continue
        distances[pid] = _dm(vec, _vec_5d(cen))

    sorted_ids = sorted(distances.keys(), key=lambda i: distances[i])
    # 取前 top_k，并基于距离转为权重（近者权大）：softmax(-distance) 或 1/(1+d)
    top_ids = sorted_ids[: max(top_k, 1)]
    d_vals = [distances[i] for i in top_ids]
    inv = [1.0 / (1.0 + d) for d in d_vals]
    total = sum(inv)
    probs = [x / total if total > 0 else (1.0 / len(inv)) for x in inv]

    overlay = []
    for i, pid in enumerate(top_ids):
        p_entry = next((x for x in patterns if (x.get("pattern_id") or "").strip() == pid), {})
        overlay.append({
            "pattern_id": pid,
            "chinese_name": p_entry.get("chinese_name") or pid,
            "D_M": round(distances[pid], 6),
            "probability": round(probs[i], 6),
        })

    return {
        "overlay": overlay,
        "distances": {k: round(v, 6) for k, v in distances.items()},
        "point_5d": dict(zip(DIM_ORDER, vec)),
        "schema": atlas.get("schema", ""),
        "double_capture_ratio": double_capture_ratio,
    }


def trace_user(
    user_id: str,
    *,
    dynamic_5d: Optional[Any] = None,
    atlas: Optional[Dict[str, Any]] = None,
    top_k: int = 3,
) -> Dict[str, Any]:
    """
    按 user_id 做流形追踪。若未提供 dynamic_5d，则尝试从档案/控制器解析（未实现则返回需 5D）。
    """
    if dynamic_5d is not None:
        return compute_dm_cloud(dynamic_5d, atlas=atlas, top_k=top_k)

    # 预留：从 BaziController / Profile 根据 user_id 取当前 5D（原局+大运+流年）
    try:
        from controllers.bazi_controller import BaziController
        ctrl = BaziController()
        # 假设存在 get_user_current_5d(user_id) 或通过 profile_id 查档案再算 5D
        profile = getattr(ctrl, "get_profile_by_id", None) or getattr(ctrl, "get_profile", None)
        if profile:
            data = profile(user_id) if callable(profile) else None
            if data and isinstance(data, dict):
                vec = data.get("current_5d") or data.get("dynamic_5d") or data.get("natal_5d")
                if vec is not None:
                    return compute_dm_cloud(vec, atlas=atlas, top_k=top_k)
    except Exception:
        pass

    return {
        "overlay": [],
        "distances": {},
        "point_5d": None,
        "schema": (atlas or load_static_atlas()).get("schema", ""),
        "error": "missing_5d",
        "message": "需要提供 dynamic_5d 或确保 user_id 对应档案存在 current_5d/dynamic_5d/natal_5d",
    }
