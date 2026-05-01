from __future__ import annotations

from fastapi.testclient import TestClient

from v20.ops.status import system_status_report
from v20.server import app


def test_v20_system_status_aggregates_core_contracts_read_only() -> None:
    report = system_status_report()

    assert report["status"] == "ok"
    assert report["runtime_mutation"] is False
    assert report["storage_table_count"] == 6
    assert report["sync_readiness"]["status"] == "ready_for_manual_sync"
    assert report["redis_validation"]["ok"] is True
    assert report["knowledge_catalog_status"] == "ready"
    assert report["knowledge_unit_count"] >= 12
    assert report["knowledge_source_catalog_status"] == "ready"
    assert report["knowledge_coverage_status"] == "pass"
    assert report["knowledge_gap_count"] == 0
    assert report["knowledge_release_status"] == "ready_for_release_review"
    assert report["v19_knowledge_migration_status"] == "audit_ready"
    assert report["v19_knowledge_candidate_count"] >= 50
    assert report["knowledge_draft_import_status"] == "preview_ready"
    assert report["knowledge_draft_candidate_count"] >= 50
    assert report["knowledge_review_queue_status"] == "ready"
    assert report["knowledge_review_domain_count"] >= 10
    assert report["knowledge_first_wave_packet_status"] == "ready"
    assert report["knowledge_first_wave_domain_count"] >= 5
    assert report["access_role_count"] == 4
    assert report["test_area_count"] >= 7
    assert report["learning_status"] == "ready_for_dry_run"
    assert report["learning_run_plan_status"] == "ready_for_dry_run"
    assert report["learning_target_case_count"] == 518_400
    assert set(report["policy_surfaces"]) >= {
        "question_ranking",
        "knowledge_retrieval",
        "confidence_calibration",
        "policy_review",
        "registries",
    }


def test_v20_system_status_endpoint_is_safe_for_monitoring() -> None:
    client = TestClient(app)
    response = client.get("/api/v20/system/status")

    assert response.status_code == 200
    data = response.json()
    assert data["runtime_mutation"] is False
    assert "NO_SECRET_VALUES_RENDERED" in data["guardrails"]
    assert data["dependency_readiness"]["runtime_mutation"] is False
    assert data["sync_readiness"]["runtime_mutation"] is False
