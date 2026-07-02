from __future__ import annotations

from fastapi.testclient import TestClient

from v40.api.app import create_app


def test_v40_ui_exposes_practitioner_calibration_without_admin_controls() -> None:
    client = TestClient(create_app())

    response = client.get("/v40/ui")

    assert response.status_code == 200
    assert 'id="roleKey"' not in response.text
    assert 'data-role="practitioner"' in response.text
    assert "专业视角" in response.text
    assert "practitioner-lens-action" in response.text
    assert "renderLens" in response.text
    assert "data-lens-action" in response.text
    assert "主分支、证据和校准动作" in response.text
    assert "production weight" not in response.text
    assert "/admin/v40" not in response.text
