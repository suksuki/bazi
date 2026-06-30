from __future__ import annotations

from fastapi.testclient import TestClient

from v40.api.app import create_app


def test_v40_ui_exposes_practitioner_calibration_without_admin_controls() -> None:
    client = TestClient(create_app())

    response = client.get("/v40/ui")

    assert response.status_code == 200
    assert 'id="roleKey"' in response.text
    assert 'value="practitioner"' in response.text
    assert "命理师校准" in response.text
    assert "practitioner-lens-action" in response.text
    assert "renderPractitionerPanel" in response.text
    assert "data-calibration-action" in response.text
    assert "只影响本次读盘" in response.text
    assert "production weight" not in response.text
    assert "/admin/v40" not in response.text
