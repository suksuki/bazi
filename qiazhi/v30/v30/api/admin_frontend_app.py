from __future__ import annotations

import os
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlencode

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles


ADMIN_FRONTEND_PORT = int(os.getenv("V30_ADMIN_FRONTEND_PORT", "9031"))
DEFAULT_RUNTIME_API_BASE_URL = "http://127.0.0.1:9030"
ROOT = Path(__file__).resolve().parents[2]
ADMIN_FRONTEND_DIR = ROOT / "admin_frontend"


def runtime_api_base_url() -> str:
    return os.getenv("V30_RUNTIME_API_BASE_URL", DEFAULT_RUNTIME_API_BASE_URL).rstrip("/")


def create_admin_frontend_app() -> FastAPI:
    app = FastAPI(title="Qiazhi V30 Admin Console", version="30.0.0a0-admin")
    app.mount("/admin/assets", StaticFiles(directory=str(ADMIN_FRONTEND_DIR)), name="admin-assets")

    @app.middleware("http")
    async def _admin_no_cache_middleware(request: Request, call_next):
        response = await call_next(request)
        if request.url.path == "/" or request.url.path.startswith("/admin"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

    @app.get("/")
    def admin_index_root() -> FileResponse:
        return FileResponse(str(ADMIN_FRONTEND_DIR / "index.html"))

    @app.get("/admin")
    def admin_index() -> FileResponse:
        return FileResponse(str(ADMIN_FRONTEND_DIR / "index.html"))

    @app.get("/admin/")
    def admin_index_slash() -> FileResponse:
        return FileResponse(str(ADMIN_FRONTEND_DIR / "index.html"))

    @app.get("/v30")
    def runtime_v30_redirect() -> RedirectResponse:
        return RedirectResponse(f"{runtime_api_base_url()}/v30")

    @app.get("/v30/ui")
    def runtime_ui_redirect(request: Request) -> RedirectResponse:
        suffix = _query_suffix(request)
        return RedirectResponse(f"{runtime_api_base_url()}/v30/ui{suffix}")

    @app.api_route("/api/v30/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    async def proxy_runtime_api(path: str, request: Request) -> Response:
        return await _proxy_request(request, f"/api/v30/{path}")

    @app.api_route("/api/admin/v30/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    async def proxy_admin_api(path: str, request: Request) -> Response:
        return await _proxy_request(request, f"/api/admin/v30/{path}")

    @app.get("/health")
    def admin_frontend_health() -> dict[str, object]:
        return {
            "ok": True,
            "service": "qiazhi-v30-admin-frontend",
            "port": ADMIN_FRONTEND_PORT,
            "runtime_api_base_url": runtime_api_base_url(),
            "admin_index": "/admin",
            "runtime_proxy": ["/api/v30/*", "/api/admin/v30/*"],
            "boundary": "admin_frontend_serves_control_plane_ui_and_proxies_runtime_api_without_mutating_chart_facts",
        }

    return app


async def _proxy_request(request: Request, target_path: str) -> Response:
    query = _query_suffix(request)
    target_url = f"{runtime_api_base_url()}{target_path}{query}"
    body = await request.body()
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in {"host", "content-length", "connection", "accept-encoding"}
    }
    upstream = urllib.request.Request(
        target_url,
        data=body if body else None,
        method=request.method,
        headers=headers,
    )
    try:
        with urllib.request.urlopen(upstream, timeout=180) as response:
            content = response.read()
            status_code = response.status
            response_headers = dict(response.headers.items())
    except urllib.error.HTTPError as exc:
        content = exc.read()
        status_code = exc.code
        response_headers = dict(exc.headers.items())
    except urllib.error.URLError as exc:
        return Response(
            content=f'{{"error":"runtime_api_unavailable","detail":"{str(exc.reason)}"}}',
            status_code=502,
            media_type="application/json",
        )
    return Response(
        content=content,
        status_code=status_code,
        media_type=response_headers.get("content-type", "application/octet-stream"),
        headers=_public_proxy_headers(response_headers),
    )


def _query_suffix(request: Request) -> str:
    if not request.query_params:
        return ""
    return f"?{urlencode(list(request.query_params.multi_items()))}"


def _public_proxy_headers(headers: dict[str, str]) -> dict[str, str]:
    blocked = {"content-length", "content-encoding", "transfer-encoding", "connection"}
    return {key: value for key, value in headers.items() if key.lower() not in blocked}


app = create_admin_frontend_app()
