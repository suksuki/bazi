from __future__ import annotations

from fastapi.testclient import TestClient

from v40.admin.app import ADMIN_PREFIX, create_admin_app
from v40.api.app import API_PREFIX, create_app
from v40.project import build_project_status


def test_project_status_reports_realtime_completion_domains() -> None:
    status = build_project_status(
        lab_summary={
            "counts": {
                "runtime_records": 3,
                "training_label_events": 4,
                "local_overlays": 2,
                "training_examples": 2,
                "training_example_replays": 2,
                "training_replay_batches": 1,
                "global_weight_versions": 1,
                "evaluation_batches": 1,
            }
        }
    )

    assert status["current_phase"] >= 34
    assert status["overall_completion_percent"] >= 60
    assert status["can_auto_continue"] is True
    assert len(status["domains"]) == 4
    assert any(domain["key"] == "training_validation" for domain in status["domains"])
    assert status["runtime_evidence_counts"]["training_replay_batches"] == 1
    assert "global_weight_versions" in status["runtime_evidence_counts"]
    assert status["next_mainline_tasks"][0].startswith("P69-")
    assert status["boundary"] == "project_status_observes_v40_progress_without_mutating_runtime_or_weights"


def test_project_status_api_is_readonly_and_admin_exposes_live_panel() -> None:
    api_client = TestClient(create_app())
    response = api_client.get(f"{API_PREFIX}/project/status")

    assert response.status_code == 200
    body = response.json()
    assert body["status"]["current_phase"] >= 34
    assert body["writes_v30_state"] is False
    assert body["writes_v40_production"] is False

    admin_client = TestClient(create_admin_app())
    page = admin_client.get(ADMIN_PREFIX)
    assert page.status_code == 200
    assert "V40 Completion" in page.text
    assert "/admin/v40/api/project-status" in page.text
    assert "overall_completion_percent" in page.text
    assert "setInterval(load, 15000)" in page.text


def test_admin_project_status_proxy_points_to_v40_runtime_status() -> None:
    source = create_admin_app()
    client = TestClient(source)

    health = client.get(f"{ADMIN_PREFIX}/health")
    assert health.status_code == 200
    page = client.get(ADMIN_PREFIX)
    assert "project-status" in page.text
