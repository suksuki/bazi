from __future__ import annotations

from fastapi.testclient import TestClient

from v40.admin.app import ADMIN_PREFIX, create_admin_app


def test_admin_console_surfaces_training_feedback_closed_loop() -> None:
    client = TestClient(create_admin_app())

    response = client.get(ADMIN_PREFIX)

    assert response.status_code == 200
    assert "Training Feedback" in response.text
    assert "closed loop" in response.text
    assert "training_label_events" in response.text
    assert "local_overlays" in response.text
    assert "training_examples" in response.text
    assert "latest_training_examples" in response.text
    assert "latest_local_overlays" in response.text
    assert "production write" not in response.text
