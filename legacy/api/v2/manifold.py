"""
GET /api/v2/manifold/trace/{user_id}
流形追踪：实时计算用户当前在 60 个质心间的 D_M 概率云，返回前 3 格局叠加态。
"""
from __future__ import annotations

import json
from typing import Any, Optional

from fastapi import APIRouter, Query

from core.manifold_trace import trace_user

router = APIRouter(prefix="/manifold", tags=["manifold"])


@router.get("/trace/{user_id}")
def get_manifold_trace(
    user_id: str,
    dynamic_5d: Optional[str] = Query(None, description="可选，JSON 数组 [E,O,M,S,R] 或对象 {E,O,M,S,R}"),
    top_k: int = Query(3, ge=1, le=10),
) -> dict[str, Any]:
    """
    实时计算 user_id 对应状态在 60 个格局质心间的 D_M 概率云，
    返回前 top_k 个最接近格局的叠加态（默认 3），与双重捕获逻辑一致。
    """
    point = None
    if dynamic_5d:
        try:
            raw = json.loads(dynamic_5d)
            if isinstance(raw, list) and len(raw) >= 5:
                point = raw[:5]
            elif isinstance(raw, dict):
                point = [float(raw.get("E", 0)), float(raw.get("O", 0)), float(raw.get("M", 0)),
                         float(raw.get("S", 0)), float(raw.get("R", 0))]
        except (json.JSONDecodeError, TypeError):
            pass
    result = trace_user(user_id, dynamic_5d=point, top_k=top_k)
    return result
