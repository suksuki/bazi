from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from abu_v60.api.dream import router as dream_router
from abu_v60.api.experience import router as experience_router
from abu_v60.api.identity import router as identity_router
from abu_v60.api.mingli import router as mingli_router
from abu_v60.api.mingli_narration import router as mingli_narration_router
from abu_v60.api.mingli_stage import router as mingli_stage_router
from abu_v60.api.system import router as system_router
from abu_v60.runtime import world_runtime_worker
from abu_v60.system_manifest import PRODUCT_VERSION


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await world_runtime_worker.start()
    try:
        yield
    finally:
        await world_runtime_worker.stop()


app = FastAPI(
    title="Abu Knows V60",
    version=PRODUCT_VERSION,
    lifespan=lifespan,
)
app.include_router(system_router)
app.include_router(identity_router)
app.include_router(mingli_router)
app.include_router(mingli_narration_router)
app.include_router(mingli_stage_router)
app.include_router(experience_router)
app.include_router(dream_router)


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
