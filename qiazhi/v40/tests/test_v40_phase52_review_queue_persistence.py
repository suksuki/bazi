from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from v40.api.app import API_PREFIX, create_app
from v40.contracts.base import Topic
from v40.project import build_project_status
from v40.storage import V40PostgresRepository, resolve_v40_database_config
from v40.synthetic import load_synthetic_seeds


ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / "data" / "synthetic" / "native_bazi_seeds.json"


def _runtime(client: TestClient, reading_id: str) -> dict[str, object]:
    seed = load_synthetic_seeds(SEED_PATH)[0]
    response = client.post(
        f"{API_PREFIX}/readings/native-report",
        json={
            "request_id": f"request.{reading_id}",
            "reading_id": reading_id,
            "chart_facts": seed.chart_facts.model_dump(mode="json"),
            "user_question": seed.question,
            "topic": Topic.CAREER.value,
            "execution_mode": "local",
            "persist": False,
        },
    )
    assert response.status_code == 200
    return response.json()["runtime"]


def test_phase52_schema_repository_and_api_support_review_queue_persistence() -> None:
    schema = Path("qiazhi/v40/deploy/postgres_v40_schema.sql").read_text(encoding="utf-8")
    repository = Path("qiazhi/v40/v40/storage/postgres.py").read_text(encoding="utf-8")
    app_source = Path("qiazhi/v40/v40/api/app.py").read_text(encoding="utf-8")

    for table in [
        "v40_consent_grants",
        "v40_practitioner_review_requests",
        "v40_practitioner_review_queue",
        "v40_practitioner_review_results",
    ]:
        assert table in schema
        assert table in repository

    assert "idx_v40_consent_grants_reading" in schema
    assert "idx_v40_practitioner_review_queue_status" in schema
    assert "save_consent_grant" in repository
    assert "list_consent_grants" in repository
    assert "save_practitioner_review_request" in repository
    assert "list_practitioner_review_queue" in repository
    assert "assign_practitioner_review_queue_item" in repository
    assert "save_practitioner_review_result" in repository
    assert "/practitioner/review-queue/assign" in app_source
    assert "writes_v40_production" in app_source
    assert "v30_practitioner_review" not in schema
    assert "v30_practitioner_review" not in repository


def test_phase52_persist_false_keeps_review_queue_lightweight() -> None:
    client = TestClient(create_app())
    runtime = _runtime(client, "reading.phase52.lightweight.001")
    consent = client.post(
        f"{API_PREFIX}/consent/grants",
        json={"grant_id": "consent.phase52.lightweight.001", "reading_id": runtime["reading_id"], "persist": False},
    ).json()["consent_grant"]

    response = client.post(
        f"{API_PREFIX}/practitioner/review-requests",
        json={
            "review_request_id": "review.phase52.lightweight.001",
            "runtime": runtime,
            "consent_grant": consent,
            "requested_topic": Topic.CAREER.value,
            "persist": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["persisted"] is False
    assert body["queue_item"]["status"] == "queued"
    assert body["raw_runtime_returned"] is False
    assert body["chart_facts_returned"] is False
    assert body["writes_v40_production"] is False


def test_phase52_persisted_review_queue_round_trip_when_repository_configured() -> None:
    if resolve_v40_database_config() is None:
        pytest.skip("V40_DATABASE_URL is not configured")

    client = TestClient(create_app())
    reading_id = "reading.phase52.persisted.001"
    runtime = _runtime(client, reading_id)

    consent_response = client.post(
        f"{API_PREFIX}/consent/grants",
        json={"grant_id": "consent.phase52.persisted.001", "reading_id": reading_id, "persist": True},
    )
    assert consent_response.status_code == 200
    assert consent_response.json()["persisted"] is True
    consent = consent_response.json()["consent_grant"]

    review_response = client.post(
        f"{API_PREFIX}/practitioner/review-requests",
        json={
            "review_request_id": "review.phase52.persisted.001",
            "runtime": runtime,
            "consent_grant": consent,
            "requested_topic": Topic.CAREER.value,
            "persist": True,
        },
    )
    assert review_response.status_code == 200
    assert review_response.json()["persisted"] is True
    queue_item = review_response.json()["queue_item"]

    listed = client.get(f"{API_PREFIX}/practitioner/review-queue?status=queued&limit=20").json()
    assert listed["persisted_queue_available"] is True
    assert any(row["queue_item_id"] == queue_item["queue_item_id"] for row in listed["queue_items"])

    assigned = client.post(
        f"{API_PREFIX}/practitioner/review-queue/assign",
        json={"queue_item_id": queue_item["queue_item_id"], "practitioner_ref": "practitioner:phase52"},
    )
    assert assigned.status_code == 200
    assert assigned.json()["queue_item"]["status"] == "assigned"
    assert assigned.json()["queue_item"]["assigned_to_practitioner_ref"] == "practitioner:phase52"
    assert assigned.json()["changes_verdict"] is False

    review_request = review_response.json()["review_request"]
    signal_id = review_request["case_view"]["source_signal_ids"][0]
    result_response = client.post(
        f"{API_PREFIX}/practitioner/review-results",
        json={
            "result_id": "result.phase52.persisted.001",
            "review_request": review_request,
            "decision": "supports",
            "selected_signal_ids": [signal_id],
            "advice_notes": ["持久化审阅支持当前事业主线"],
            "persist": True,
        },
    )
    assert result_response.status_code == 200
    assert result_response.json()["persisted"] is True
    assert result_response.json()["training_label_persisted"] is True

    repository = V40PostgresRepository.from_env()
    labels = repository.list_training_label_events(reading_id=reading_id, limit=20)
    assert any(row["event_id"] == "label:review:result.phase52.persisted.001" for row in labels)


def test_phase52_docs_and_project_status_track_review_persistence() -> None:
    doc = Path("qiazhi/v40/docs/V40_PHASE52_REVIEW_QUEUE_PERSISTENCE.md").read_text(encoding="utf-8")
    spec = Path("qiazhi/v40/docs/V40_SPEC.md").read_text(encoding="utf-8")
    readme = Path("qiazhi/v40/README.md").read_text(encoding="utf-8")
    status = build_project_status()

    assert "Review Queue Persistence And Assignment" in doc
    assert "v40_practitioner_review_queue" in doc
    assert "POST /api/v40/practitioner/review-queue/assign" in spec
    assert "2026-07-01 Phase 52" in spec
    assert "docs/V40_PHASE52_REVIEW_QUEUE_PERSISTENCE.md" in readme
    assert status["current_phase"] == 61
    assert status["current_phase_name"] == "UI Flow Clean Rebuild"
    assert any(row["range"] == "51" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "52" and row["status"] == "complete" for row in status["phase_groups"])
