"""V7.3：公开 Pattern JSON 端点（与 Admin ``/v1/admin/patterns`` 分离，固定 JSONResponse）。"""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse

from app.services.pattern_service import PatternService

router = APIRouter(prefix="/v1/patterns", tags=["patterns"])


@router.post("/reload")
def post_patterns_reload() -> JSONResponse:
    """运维/联调：重新读取磁盘法典指纹（不写盘）。``{"status":"ok","sha256":"..."}`` 或 SIGNATURE_ERROR。"""
    return JSONResponse(content=PatternService.reload_fingerprint())


@router.post("/evaluate")
def post_patterns_evaluate(payload: Dict[str, Any] = Body(default_factory=dict)) -> JSONResponse:
    """对给定 physics_tensor 跑一次 L2 manifest 引擎（不落库）。空 body 等价 ``{}``。"""
    pt = dict(payload.get("physics_tensor") or {})
    md = dict(payload.get("metadata") or {})
    return JSONResponse(content=PatternService.evaluate_rows(pt, md))
