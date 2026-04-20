from __future__ import annotations

from fastapi import FastAPI

from v17_rebirth.backend.api.admin_v17 import router as admin_router
from v17_rebirth.backend.api.stream_v17_endpoints import router as stream_router

app = FastAPI(title="V17 Rebirth API", version="17.2")
app.include_router(stream_router)
app.include_router(admin_router)


@app.get("/health")
async def health() -> dict:
    return {"ok": True, "service": "v17_rebirth"}
