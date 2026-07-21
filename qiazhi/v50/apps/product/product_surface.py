from __future__ import annotations

import logging
import mimetypes
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from product.legacy_usage import LegacyUsageStore, legacy_route_key
from product.product_store import ProductStore


STATIC_DIR = Path(__file__).resolve().parent / "static" / "l5"
EXPERIENCE_STATIC_DIR = Path(__file__).resolve().parent / "static" / "experience"
LOGGER = logging.getLogger(__name__)

mimetypes.add_type("image/webp", ".webp")


def register_product_surface(
    app: FastAPI,
    *,
    store: ProductStore,
    legacy_usage_store: LegacyUsageStore,
) -> None:
    @app.get("/abu-theater", include_in_schema=False)
    def abu_theater_entry() -> RedirectResponse:
        return RedirectResponse(
            url="/experience-static/internal-tools/abu-says-mingli-s0-v12/index.html",
            status_code=307,
        )

    @app.get("/experience-static/prototypes/abu-says-mingli-s0/index.html", include_in_schema=False)
    @app.get("/experience-static/prototypes/abu-says-mingli-s0-v11/index.html", include_in_schema=False)
    @app.get("/experience-static/prototypes/abu-says-mingli-s0-v12/index.html", include_in_schema=False)
    def legacy_abu_theater_entry() -> RedirectResponse:
        return RedirectResponse(url="/abu-theater", status_code=308)

    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="product-assets")
    app.mount("/experience-static", StaticFiles(directory=EXPERIENCE_STATIC_DIR), name="experience-static")

    @app.middleware("http")
    async def trace_legacy_runtime_usage(request: Request, call_next):
        response = await call_next(request)
        route_key = legacy_route_key(request.url.path)
        if route_key:
            try:
                legacy_usage_store.record(route_key=route_key, method=request.method)
            except Exception:  # noqa: BLE001 - observability must never interrupt the product.
                LOGGER.exception("legacy_runtime_usage_record_failed")
        return response

    @app.get("/", include_in_schema=False)
    def product_entry() -> RedirectResponse:
        return RedirectResponse(url="/abu-theater", status_code=307)

    @app.get("/app", include_in_schema=False)
    def product_index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/experience", include_in_schema=False)
    @app.get("/experience/", include_in_schema=False)
    def experience_index() -> FileResponse:
        return FileResponse(EXPERIENCE_STATIC_DIR / "index.html")

    @app.get("/theater", include_in_schema=False)
    @app.get("/theater/studio", include_in_schema=False)
    def theater_index() -> FileResponse:
        return FileResponse(STATIC_DIR / "theater.html")

    @app.get("/visual-alpha", include_in_schema=False)
    def retired_visual_alpha_route() -> RedirectResponse:
        return RedirectResponse(url="/app", status_code=308)

    @app.get("/app.js", include_in_schema=False)
    def product_javascript() -> FileResponse:
        return FileResponse(STATIC_DIR / "app.js", media_type="application/javascript")

    @app.get("/styles.css", include_in_schema=False)
    def product_styles() -> FileResponse:
        return FileResponse(STATIC_DIR / "styles.css", media_type="text/css")

    @app.get("/theater.js", include_in_schema=False)
    def theater_javascript() -> FileResponse:
        return FileResponse(STATIC_DIR / "theater.js", media_type="application/javascript")

    @app.get("/theater.css", include_in_schema=False)
    def theater_styles() -> FileResponse:
        return FileResponse(STATIC_DIR / "theater.css", media_type="text/css")

    @app.get("/favicon.ico", include_in_schema=False)
    def product_favicon() -> FileResponse:
        return FileResponse(STATIC_DIR / "assets" / "deepbazi_symbol.png", media_type="image/png")

    @app.get("/health", include_in_schema=False)
    def product_health() -> dict[str, object]:
        return {
            "status": "ok",
            "product": "deepbazi_v50",
            "cognitive_core": "llm_mingli_agent",
            "storage": store.storage_name,
        }
