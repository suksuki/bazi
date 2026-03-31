"""qiazhi_core FastAPI 入口（MVP）。"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

_ROOT = Path(__file__).resolve().parents[2]
for p in (_ROOT, _ROOT / "legacy", _ROOT / "qiazhi"):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)

from qiazhi.api.router import router as qiazhi_router
from qiazhi_core.database.session import init_db

app = FastAPI(title="Qiazhi-Bazi API", version="0.2.0-mvp")
app.include_router(qiazhi_router, prefix="/api/qiazhi")

_cors = os.environ.get("QIAZHI_CORS_ORIGINS", "http://localhost:3000")
_origins = [o.strip() for o in _cors.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/qiazhi")
def qiazhi_entry():
    origin = os.environ.get("QIAZHI_FRONTEND_ORIGIN", "").strip()
    if origin:
        return RedirectResponse(url=f"{origin.rstrip('/')}/qiazhi", status_code=307)
    return JSONResponse({"name": "Qiazhi-Bazi", "api": "/api/qiazhi/health"})
