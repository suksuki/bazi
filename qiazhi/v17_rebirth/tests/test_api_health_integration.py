"""集成：FastAPI 应用 /health（无外部 LLM）。"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from v17_rebirth.backend.api.app import app


@pytest.mark.integration
def test_health_ok() -> None:
    with TestClient(app) as client:
        r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True
    assert body.get("service") == "v17_rebirth"
