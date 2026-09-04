from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from abu_v60.api.identity import router as identity_router
from abu_v60.api.mingli import router as mingli_router
from abu_v60.api.mingli_narration import router as mingli_narration_router
from abu_v60.api.mingli_stage import router as mingli_stage_router
from abu_v60.api.public_experience import router as public_experience_router
from abu_v60.api.system import router as system_router
from abu_v60.settings import settings
from abu_v60.system_manifest import PRODUCT_VERSION

app = FastAPI(
    title="Abu Knows V60",
    version=PRODUCT_VERSION,
)
app.include_router(system_router)
app.include_router(identity_router)
app.include_router(mingli_router)
app.include_router(mingli_narration_router)
app.include_router(mingli_stage_router)
app.include_router(public_experience_router)

if settings.internal_surfaces_enabled:
    from abu_v60.api.mingli_synthetic_lab import router as mingli_synthetic_lab_router

    app.include_router(mingli_synthetic_lab_router)


def _web_cache_control(path: str) -> str | None:
    if path in {"/", "/experience"}:
        return "private, no-store, max-age=0, must-revalidate"
    if path.startswith("/assets/"):
        return "public, max-age=31536000, immutable"
    return None


@app.middleware("http")
async def apply_web_cache_policy(request: Request, call_next):
    response = await call_next(request)
    cache_control = _web_cache_control(request.url.path)
    if cache_control is not None and response.status_code < 400:
        response.headers["Cache-Control"] = cache_control
    return response


_repo_root = Path(__file__).resolve().parents[3]
_web_dist = _repo_root / "web" / "dist"

if _web_dist.exists():
    app.mount("/assets", StaticFiles(directory=_web_dist / "assets"), name="web-assets")

    @app.get("/", include_in_schema=False)
    @app.get("/experience", include_in_schema=False)
    def experience() -> FileResponse:
        return FileResponse(_web_dist / "index.html")
