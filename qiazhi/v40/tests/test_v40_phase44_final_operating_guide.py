from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from v40.api.app import API_PREFIX, create_app


def test_phase44_final_operating_guide_documents_handoff_boundaries() -> None:
    guide = Path("qiazhi/v40/docs/V40_PHASE44_FINAL_OPERATING_GUIDE.md").read_text(encoding="utf-8")

    assert "http://127.0.0.1:9040" in guide
    assert "http://127.0.0.1:9041/admin/v40" in guide
    assert "GET /api/v40/project/production-smoke" in guide
    assert "真实命例质量判断" in guide
    assert "剩余 2% 是人工验收和切换窗口" in guide


def test_phase44_project_status_marks_automatic_boundary_before_user_acceptance() -> None:
    status = TestClient(create_app()).get(f"{API_PREFIX}/project/status").json()["status"]

    assert status["current_phase"] >= 44
    assert status["overall_completion_percent"] >= 98
    assert status["next_mainline_tasks"][0].startswith("TRAIN-16")
    assert any(group["status"] == "requires_user" for group in status["phase_groups"])
