from __future__ import annotations

from v20.ops.service_unit import service_unit_manifest
from v20.server import app


def _endpoint(path: str, method: str = "GET"):
    method = method.upper()
    for route in app.routes:
        if getattr(route, "path", "") == path and method in getattr(route, "methods", set()):
            return route.endpoint
    raise AssertionError(f"route not found: {method} {path}")


def test_v20_linux_service_unit_manifest_is_systemd_without_secrets(monkeypatch) -> None:
    monkeypatch.setenv("V20_ENV", "linux_0_13")
    manifest = service_unit_manifest("linux_0_13")

    assert manifest["unit_type"] == "systemd"
    assert "ExecStart=" in manifest["unit"]
    assert "/v20/scripts/start_linux.sh" in manifest["unit"]
    assert "V20_ENV=linux_0_13" in manifest["unit"]
    assert manifest["service_script"] == "./v20/scripts/service_linux.sh"
    assert manifest["background_commands"]["status"] == "./v20/scripts/service_linux.sh status"
    assert manifest["health_check"] == "http://0.13:9020/health"
    assert manifest["runtime_mutation"] is False
    assert "NO_SECRET_VALUES_RENDERED" in manifest["guardrails"]


def test_v20_macos_service_unit_manifest_is_launchd_and_background_script() -> None:
    manifest = service_unit_manifest("local_macos")

    assert manifest["unit_type"] == "launchd"
    assert "com.qiazhi.v20.local" in manifest["unit"]
    assert "start_macos.sh" in manifest["unit"]
    assert manifest["service_script"] == "./v20/scripts/service_macos.sh"
    assert manifest["background_commands"]["start"] == "./v20/scripts/service_macos.sh start"
    assert manifest["ui_url"] == "http://127.0.0.1:9020/v20/ui/"


def test_v20_service_unit_endpoint_is_read_only() -> None:
    linux = _endpoint("/api/v20/ops/service-unit/{profile_name}")("linux_0_13")
    local = _endpoint("/api/v20/ops/service-unit/{profile_name}")("local_macos")

    assert linux["runtime_mutation"] is False
    assert linux["unit_type"] == "systemd"
    assert local["unit_type"] == "launchd"
