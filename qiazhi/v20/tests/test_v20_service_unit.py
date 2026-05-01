from __future__ import annotations

from fastapi.testclient import TestClient

from v20.ops.service_unit import service_unit_manifest
from v20.server import app


def test_v20_linux_service_unit_manifest_is_systemd_without_secrets(monkeypatch) -> None:
    monkeypatch.setenv("V20_ENV", "linux_0_13")
    manifest = service_unit_manifest("linux_0_13")

    assert manifest["unit_type"] == "systemd"
    assert "ExecStart=/usr/bin/env python3.12 -m uvicorn v20.server:app" in manifest["unit"]
    assert "V20_ENV=linux_0_13" in manifest["unit"]
    assert manifest["health_check"] == "http://0.13:9020/health"
    assert manifest["runtime_mutation"] is False
    assert "NO_SECRET_VALUES_RENDERED" in manifest["guardrails"]


def test_v20_macos_service_unit_manifest_is_foreground_command() -> None:
    manifest = service_unit_manifest("local_macos")

    assert manifest["unit_type"] == "foreground_command"
    assert "./v20/scripts/start_macos.sh" in manifest["unit"]
    assert manifest["ui_url"] == "http://127.0.0.1:9020/v20/ui/"


def test_v20_service_unit_endpoint_is_read_only() -> None:
    client = TestClient(app)
    linux = client.get("/api/v20/ops/service-unit/linux_0_13").json()
    local = client.get("/api/v20/ops/service-unit/local_macos").json()

    assert linux["runtime_mutation"] is False
    assert linux["unit_type"] == "systemd"
    assert local["unit_type"] == "foreground_command"
