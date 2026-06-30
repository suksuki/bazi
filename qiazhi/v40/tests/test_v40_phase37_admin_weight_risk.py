from __future__ import annotations

from fastapi.testclient import TestClient

from v40.admin.app import ADMIN_PREFIX, _build_weight_risk_summary, create_admin_app


def test_admin_weight_risk_summary_links_readiness_and_rollback() -> None:
    summary = _build_weight_risk_summary(
        {
            "weights": [
                {
                    "weight_version_id": "weight.ready",
                    "source_training_run_id": "train.ready",
                    "release_gate_id": "readiness.ready",
                    "active": False,
                    "rollback_version_id": "weight.previous",
                },
                {
                    "weight_version_id": "weight.review",
                    "source_training_run_id": "train.review",
                    "release_gate_id": "gate.unlinked",
                    "active": False,
                    "rollback_version_id": "",
                },
                {
                    "weight_version_id": "weight.blocked",
                    "source_training_run_id": "train.blocked",
                    "release_gate_id": "readiness.rejected",
                    "active": False,
                    "rollback_version_id": "weight.previous",
                },
            ]
        },
        {
            "readiness": [
                {"readiness_id": "readiness.ready", "recommendation": "approve"},
                {"readiness_id": "readiness.rejected", "recommendation": "reject"},
            ]
        },
    )

    assert summary["candidate_count"] == 3
    assert summary["ready_count"] == 1
    assert summary["review_count"] == 1
    assert summary["blocked_count"] == 1
    review = next(record for record in summary["records"] if record["weight_version_id"] == "weight.review")
    assert "release_gate_id 未匹配 release_readiness" in review["reasons"]
    assert "缺少 rollback_version_id" in review["reasons"]


def test_admin_weight_risk_endpoint_is_readonly(monkeypatch) -> None:
    def fake_fetch(path: str) -> dict[str, object]:
        if path.startswith("/api/v40/weights/candidates"):
            return {
                "weights": [
                    {
                        "weight_version_id": "weight.endpoint",
                        "source_training_run_id": "train.endpoint",
                        "release_gate_id": "readiness.endpoint",
                        "active": False,
                        "rollback_version_id": "weight.previous",
                    }
                ]
            }
        if path.startswith("/api/v40/release-readiness"):
            return {"readiness": [{"readiness_id": "readiness.endpoint", "recommendation": "approve"}]}
        raise AssertionError(path)

    monkeypatch.setattr("v40.admin.app._fetch_json", fake_fetch)
    client = TestClient(create_admin_app())

    response = client.get(f"{ADMIN_PREFIX}/api/weight-risk")

    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["ready_count"] == 1
    assert body["writes_v40_production"] is False
    assert body["boundary"] == "admin_weight_risk_reads_candidate_weight_and_readiness_without_activation"


def test_admin_console_exposes_candidate_risk_panel() -> None:
    page = TestClient(create_admin_app()).get(ADMIN_PREFIX)

    assert page.status_code == 200
    assert "Candidate Risk" in page.text
    assert "/admin/v40/api/weight-risk" in page.text
    assert "source · rollback" in page.text
