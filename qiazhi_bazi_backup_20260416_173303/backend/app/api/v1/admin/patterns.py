"""V6.6–V6.7 Admin：L2 格局法典读取 / 热更新 / 预览 / 备份列表 / 回滚。

生产环境（`QIAZHI_ENV`/`ENV` ∈ production|prod|live）下 **`QIAZHI_ADMIN_TOKEN` 必填**，
且禁止使用默认开发令牌；逻辑见 `admin_auth.admin_token_guard`。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.api.admin_auth import admin_token_guard
from app.api.contracts import AnalyzeSeedRequest, BlindSchoolFeatureFlags
from app.core.scanner import Scanner
from app.schemas.bazi_metadata import BaziMetadata, ConflictMatrix, FlowState
from app.services import pattern_manifest_admin as pma
from app.services.bazi_engine import get_bazi, get_timeline_snapshot
from app.services.orchestrator_service import OrchestratorService
from app.services.recommendation_service import invalidate_recommendation_cache

router = APIRouter(prefix="/v1/admin/patterns", tags=["admin-patterns"])


class PatternManifestUpdateBody(BaseModel):
    manifest: Dict[str, Any]


class PatternPreviewBody(BaseModel):
    physics_tensor: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


@router.get("/manifest")
def get_pattern_manifest(_: None = Depends(admin_token_guard)) -> JSONResponse:
    """返回磁盘当前法典全量（与 `UniversalPatternEngine` 默认读取路径一致）。"""
    data = pma.read_pattern_manifest_from_disk()
    return JSONResponse(content={"ok": True, "manifest": data, "sha256": pma.manifest_sha256(data)})


@router.post("/reload")
def post_pattern_manifest_reload(_: None = Depends(admin_token_guard)) -> JSONResponse:
    """重新从磁盘读取并返回指纹；引擎侧每次 `UniversalPatternEngine()` 已会读盘，本接口用于运维确认落盘。"""
    data = pma.read_pattern_manifest_from_disk()
    return JSONResponse(
        content={"ok": True, "reloaded": True, "status": "ok", "sha256": pma.manifest_sha256(data)},
    )


@router.put("/update")
def put_pattern_manifest(body: PatternManifestUpdateBody, _: None = Depends(admin_token_guard)) -> JSONResponse:
    """全量覆盖写入 `pattern_manifest.json`；写入前生成 `pattern_manifest.YYYYMMDD_HHMMSS.json.bak`。"""
    info = pma.write_pattern_manifest_with_backup(body.manifest)
    invalidate_recommendation_cache()
    return JSONResponse(content={"ok": True, **info})


@router.get("/manifest-backups")
def list_manifest_backups(_: None = Depends(admin_token_guard)) -> JSONResponse:
    """列出时间戳备份（新→旧），供运维核对。"""
    return JSONResponse(content={"ok": True, "backups": pma.list_timestamped_manifest_backups()})


@router.post("/restore-latest")
def post_restore_latest_manifest(_: None = Depends(admin_token_guard)) -> JSONResponse:
    """将 mtime 最新的时间戳备份写回主法典（写回前再为当前主文件打一条备份）。"""
    out = pma.restore_latest_manifest_backup()
    invalidate_recommendation_cache()
    return JSONResponse(content=out)


@router.post("/preview")
def post_pattern_preview(body: PatternPreviewBody, _: None = Depends(admin_token_guard)) -> JSONResponse:
    """调试：对给定 `physics_tensor` 跑一次 L2 manifest 引擎（不落库）。"""
    rows = pma.preview_evaluate_rows(dict(body.physics_tensor or {}), dict(body.metadata or {}))
    return JSONResponse(content={"ok": True, "rows": rows})


@router.post("/collision-preview")
def post_collision_preview(body: AnalyzeSeedRequest, _: None = Depends(admin_token_guard)) -> JSONResponse:
    """
    模拟八字（生日+时刻+历法）→ 排盘 → 物理引擎 → L2 格局逐条碰撞结果。
    无 LLM；供 Admin「因果调试台」列表实时着色。
    """
    try:
        pillars = get_bazi(body.date, body.time, body.calendar)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"日期格式错误: {e}") from e
    try:
        timeline = get_timeline_snapshot(
            body.date,
            body.time,
            body.calendar,
            1 if body.gender == "male" else 0,
            body.reference_year,
        )
    except Exception as e:  # noqa: BLE001 — 排盘依赖缺失时给出可读错误
        raise HTTPException(status_code=400, detail=f"大运/流年快照失败: {e}") from e

    timeline_out: Dict[str, Any] = dict(timeline) if isinstance(timeline, dict) else {}
    eo = body.external_overrides if isinstance(getattr(body, "external_overrides", None), dict) else {}
    liu = str(timeline_out.get("liunian") or "")
    dy = str(timeline_out.get("dayun") or "")
    if eo.get("liunian_ganzhi"):
        liu = str(eo["liunian_ganzhi"]).strip()
        timeline_out["liunian"] = liu
    if eo.get("dayun_ganzhi"):
        dy = str(eo["dayun_ganzhi"]).strip()
        timeline_out["dayun"] = dy
    temporal_ctx: Dict[str, Any] = {
        "reference_year": body.reference_year,
        "liunian_ganzhi": liu or None,
        "dayun_ganzhi": dy or None,
    }

    matrix = Scanner().scan(pillars)
    points = list(matrix.points)
    blind_flags = (
        body.blind_school_features.model_dump()
        if body.blind_school_features
        else BlindSchoolFeatureFlags().model_dump()
    )
    if blind_flags.get("enable_pierce_harm", True) and "classical.blind_school.v1" in (body.enabled_plugins or []):
        from app.plugins.blind_school.mangpai_engine import scan_six_harm_points

        points.extend(scan_six_harm_points(pillars))

    metadata_obj = BaziMetadata(
        pillars=pillars,
        conflict_matrix=ConflictMatrix(points=points),
        flow_state=FlowState.UNKNOWN,
        notes="admin collision preview",
        temporal_context=temporal_ctx,
    )
    physics_cfg = body.physics_config.model_dump(exclude_none=True) if body.physics_config else {}
    loop_out = OrchestratorService.run_internal_loop(
        metadata_obj=metadata_obj,
        enabled_plugins=list(body.enabled_plugins or []),
        blind_school_features=blind_flags,
        physics_config=physics_cfg,
        session_id=None,
        dayun=dy or None,
        liunian=liu or None,
    )
    md_after = loop_out["metadata"]
    pt = loop_out["physics_tensor"]
    rows = pma.preview_evaluate_rows(dict(pt or {}), md_after.model_dump())
    return JSONResponse(
        content={
            "ok": True,
            "rows": rows,
            "physics_tensor": pt,
            "timeline": timeline_out,
            "pillars": pillars.model_dump(),
        },
    )
