from __future__ import annotations

from fastapi.testclient import TestClient

from v40.api.app import create_app


def test_v40_user_report_ui_serves_report_first_page() -> None:
    client = TestClient(create_app())

    response = client.get("/v40/ui")

    assert response.status_code == 200
    assert "掐指一算" in response.text
    assert "/api/v40/readings/native-report" in response.text
    assert "/api/v40/expression/provider/ollama" in response.text
    assert "execution_mode" in response.text
    assert "renderReport" in response.text
    assert "你想测什么" in response.text
    assert "这个判断像你吗" in response.text
    assert "Gemma4" not in response.text
    assert "192.168." not in response.text
    assert "测算结果" in response.text
