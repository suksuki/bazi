from __future__ import annotations

from fastapi import APIRouter

from abu_v60.db import database_health
from abu_v60.media import public_runtime_media_manifest
from abu_v60.system_manifest import (
    ENTRY_EXPERIENCE,
    FOUNDATION_VERSION,
    runtime_manifest,
)

router = APIRouter(prefix="/api/v60", tags=["system"])


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
    database = database_health(expected_foundation_version=FOUNDATION_VERSION)
    manifest = runtime_manifest()
    return {
        "status": "READY" if database["status"] == "ready" else "DEGRADED",
        "foundation_version": FOUNDATION_VERSION,
        "entry_experience": ENTRY_EXPERIENCE,
        "public_product_exposure": manifest["public_product_exposure"],
        "mingli_focused_runtime": manifest["mingli_focused_runtime"],
        "speech_runtime": manifest["speech_runtime"],
    }


@router.get("/bootstrap")
def bootstrap() -> dict[str, object]:
    return {
        "manifest": runtime_manifest(),
        "media": public_runtime_media_manifest(),
        "experience": {
            "state": "MINGLI_READY",
            "entry": ENTRY_EXPERIENCE,
            "unavailable_reason": None,
        },
    }
