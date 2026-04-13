"""V9.0 Admin：冲突法典 ``conflict_manifest.json`` 读写 / 重载 / 备份 / 回滚。"""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.api.admin_auth import admin_token_guard
from app.services import conflict_manifest_admin as cfma
from app.services.recommendation_service import invalidate_recommendation_cache

router = APIRouter(prefix="/v1/admin/conflict", tags=["admin-conflict"])


class ConflictManifestUpdateBody(BaseModel):
    manifest: Dict[str, Any]


@router.get("/manifest")
def get_conflict_manifest(_: None = Depends(admin_token_guard)) -> JSONResponse:
    data = cfma.read_conflict_manifest_from_disk()
    return JSONResponse(content={"ok": True, "manifest": data, "sha256": cfma.manifest_sha256(data)})


@router.post("/reload")
def post_conflict_manifest_reload(_: None = Depends(admin_token_guard)) -> JSONResponse:
    data = cfma.read_conflict_manifest_from_disk()
    return JSONResponse(content={"ok": True, "reloaded": True, "status": "ok", "sha256": cfma.manifest_sha256(data)})


@router.put("/update")
def put_conflict_manifest(body: ConflictManifestUpdateBody, _: None = Depends(admin_token_guard)) -> JSONResponse:
    info = cfma.write_conflict_manifest_with_backup(body.manifest)
    invalidate_recommendation_cache()
    return JSONResponse(content={"ok": True, **info})


@router.get("/manifest-backups")
def list_manifest_backups(_: None = Depends(admin_token_guard)) -> JSONResponse:
    return JSONResponse(content={"ok": True, "backups": cfma.list_timestamped_manifest_backups()})


@router.post("/restore-latest")
def post_restore_latest_manifest(_: None = Depends(admin_token_guard)) -> JSONResponse:
    out = cfma.restore_latest_manifest_backup()
    invalidate_recommendation_cache()
    return JSONResponse(content=out)
