"""V8.3 Admin：调候法典 ``climate_manifest.json`` 读取 / 热更新 / 重载指纹 / 备份列表 / 回滚。"""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.api.admin_auth import admin_token_guard
from app.services import climate_manifest_admin as cma
from app.services.recommendation_service import invalidate_recommendation_cache

router = APIRouter(prefix="/v1/admin/climate", tags=["admin-climate"])


class ClimateManifestUpdateBody(BaseModel):
    manifest: Dict[str, Any]


@router.get("/manifest")
def get_climate_manifest(_: None = Depends(admin_token_guard)) -> JSONResponse:
    """返回磁盘当前调候法典全量与规范 SHA256（与 ``climate_adjuster_v1`` 读取路径一致）。"""
    data = cma.read_climate_manifest_from_disk()
    return JSONResponse(content={"ok": True, "manifest": data, "sha256": cma.manifest_sha256(data)})


@router.post("/reload")
def post_climate_manifest_reload(_: None = Depends(admin_token_guard)) -> JSONResponse:
    """重新从磁盘读取并返回指纹；物理引擎每次推断均读盘，本接口供运维确认落盘。"""
    data = cma.read_climate_manifest_from_disk()
    return JSONResponse(
        content={"ok": True, "reloaded": True, "status": "ok", "sha256": cma.manifest_sha256(data)},
    )


@router.put("/update")
def put_climate_manifest(body: ClimateManifestUpdateBody, _: None = Depends(admin_token_guard)) -> JSONResponse:
    """全量覆盖写入 ``climate_manifest.json``；写入前打时间戳备份，并刷新同目录 ``climate_manifest.sha256``。"""
    info = cma.write_climate_manifest_with_backup(body.manifest)
    invalidate_recommendation_cache()
    return JSONResponse(content={"ok": True, **info})


@router.get("/manifest-backups")
def list_manifest_backups(_: None = Depends(admin_token_guard)) -> JSONResponse:
    return JSONResponse(content={"ok": True, "backups": cma.list_timestamped_manifest_backups()})


@router.post("/restore-latest")
def post_restore_latest_manifest(_: None = Depends(admin_token_guard)) -> JSONResponse:
    out = cma.restore_latest_manifest_backup()
    invalidate_recommendation_cache()
    return JSONResponse(content=out)
