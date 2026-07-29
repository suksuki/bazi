from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from abu_v60.db import database_health, engine
from abu_v60.media import runtime_media_manifest
from abu_v60.observability import RuntimeIntegrityService
from abu_v60.system_manifest import (
    ENTRY_EXPERIENCE,
    FOUNDATION_VERSION,
    PRIMARY_WORLD_ID,
    runtime_manifest,
)

router = APIRouter(prefix="/api/v60", tags=["system"])
runtime_integrity = RuntimeIntegrityService()


@router.get("/health")
def health() -> dict[str, object]:
    database = database_health(expected_foundation_version=FOUNDATION_VERSION)
    return {
        "status": "ready" if database["status"] == "ready" else "degraded",
        "database": database,
    }


@router.get("/system/manifest")
def system_manifest() -> dict[str, object]:
    return runtime_manifest()


@router.get("/system/runtime-status")
def runtime_status() -> dict[str, object]:
    return runtime_integrity.inspect(engine)


@router.get("/bootstrap")
def bootstrap() -> dict[str, object]:
    with engine.connect() as connection:
        row = (
            connection.execute(
                text(
                    "SELECT world_ref, world_version, branch, current_epoch, current_tick "
                    "FROM world.worlds WHERE world_ref = :world_ref"
                ),
                {"world_ref": PRIMARY_WORLD_ID},
            )
            .mappings()
            .one()
        )
        available_life_trees = connection.execute(
            text("SELECT count(*) FROM dream.life_trees"),
        ).scalar_one()
    return {
        "manifest": runtime_manifest(),
        "media": runtime_media_manifest(),
        "world": dict(row),
        "experience": {
            "state": "FIRST_SLICE_READY" if available_life_trees else "FOUNDATION_READY",
            "entry": ENTRY_EXPERIENCE,
            "available_life_trees": available_life_trees,
            "unavailable_reason": None if available_life_trees else "NO_V60_CASE_PROJECTION_YET",
        },
    }
