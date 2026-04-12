"""
Qiazhi-Bazi 后端入口。

在仓库根目录执行::

    cd qiazhi_bazi/backend
    uvicorn main:app --reload --host 0.0.0.0 --port 8001

或::

    PYTHONPATH=qiazhi_bazi/backend uvicorn main:app --reload --host 0.0.0.0 --port 8001
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# 保证 `app` 包可导入
_BACKEND = Path(__file__).resolve().parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.api.router import router as api_router
from app.api.admin import router as admin_router
from app.api.audit_router import router as audit_router
from app.db.session import init_db
from app.plugins.base_physics.manifest_loader import load_l1_physics_manifest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

_logger = logging.getLogger(__name__)

app = FastAPI(title="Qiazhi-Bazi API", version="1.0.0-mvp")
app.include_router(api_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(audit_router, prefix="/api")

_cors = os.environ.get("QIAZHI_CORS_ORIGINS", "")
_env_origins = [o.strip() for o in _cors.split(",") if o.strip()]
_extra_origins = [o.strip() for o in (os.environ.get("QIAZHI_CORS_EXTRA_ORIGINS") or "").split(",") if o.strip()]
_default_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "https://dblife.com",
    "https://www.dblife.com",
]
_merged = _default_origins + _env_origins + _extra_origins
_seen: set[str] = set()
_origins: list[str] = []
for _o in _merged:
    _k = _o.lower()
    if _k not in _seen:
        _seen.add(_k)
        _origins.append(_o)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_startup_state = {
    "db_init_ok": False,
    "db_init_error": "",
}


@app.on_event("startup")
def _startup() -> None:
    try:
        init_db()
        _startup_state["db_init_ok"] = True
        _startup_state["db_init_error"] = ""
    except Exception as e:  # noqa: BLE001
        # 不因 DATABASE_URL 错/库未起而拒绝绑定端口：机房页可改连、/ready 反映 DB 状态。
        _logger.warning(
            "[startup] init_db failed — serving in degraded mode (fix DATABASE_URL or use admin Init/Migrate): %s",
            e,
        )
        _startup_state["db_init_ok"] = False
        _startup_state["db_init_error"] = str(e)
    try:
        load_l1_physics_manifest()
    except Exception as e:  # noqa: BLE001
        print(f"[startup] l1_physics_manifest load failed: {e}")
        raise


@app.get("/health")
def health() -> dict:
    return {"service": "qiazhi-bazi-backend", "ok": True, "kind": "liveness"}


@app.get("/ready")
def ready() -> dict:
    return {
        "service": "qiazhi-bazi-backend",
        "ok": bool(_startup_state["db_init_ok"]),
        "kind": "readiness",
        "checks": {
            "db_init": {
                "ok": bool(_startup_state["db_init_ok"]),
                "error": _startup_state["db_init_error"] or None,
            }
        },
    }
