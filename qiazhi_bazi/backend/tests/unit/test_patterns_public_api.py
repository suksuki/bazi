"""V7.3：``/api/v1/patterns/reload`` 与 ``/evaluate`` 纯 JSON 路由。"""
from __future__ import annotations

from fastapi import FastAPI
from starlette.testclient import TestClient

from app.api.v1.patterns import router as patterns_public_router


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(patterns_public_router, prefix="/api")
    return TestClient(app)


def test_patterns_reload_returns_ok_and_sha256() -> None:
    r = _client().post("/api/v1/patterns/reload")
    assert r.status_code == 200
    ct = (r.headers.get("content-type") or "").lower()
    assert "application/json" in ct
    j = r.json()
    assert j.get("status") == "ok"
    assert isinstance(j.get("sha256"), str) and len(j["sha256"]) == 64


def test_patterns_evaluate_returns_rows_or_signature_error() -> None:
    r = _client().post(
        "/api/v1/patterns/evaluate",
        json={"physics_tensor": {"deity_scores": {"比肩": 1.0}}, "metadata": {}},
    )
    assert r.status_code == 200
    assert "application/json" in (r.headers.get("content-type") or "").lower()
    j = r.json()
    assert j.get("status") in ("ok", "SIGNATURE_ERROR")
    if j.get("status") == "ok":
        assert isinstance(j.get("rows"), list)
