from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from v40.api.app import API_PREFIX, create_app
from v40.contracts.base import Topic
from v40.project import build_project_status
from v40.synthetic import load_synthetic_seeds


ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / "data" / "synthetic" / "native_bazi_seeds.json"


def _runtime() -> dict[str, object]:
    client = TestClient(create_app())
    seed = load_synthetic_seeds(SEED_PATH)[0]
    response = client.post(
        f"{API_PREFIX}/readings/native-report",
        json={
            "request_id": "request.phase51.review.001",
            "reading_id": "reading.phase51.review.001",
            "chart_facts": seed.chart_facts.model_dump(mode="json"),
            "user_question": seed.question,
            "topic": Topic.CAREER.value,
            "execution_mode": "local",
            "persist": False,
        },
    )
    assert response.status_code == 200
    return response.json()["runtime"]


def test_consent_review_request_returns_anonymized_case_view_without_raw_runtime() -> None:
    client = TestClient(create_app())
    runtime = _runtime()

    consent_response = client.post(
        f"{API_PREFIX}/consent/grants",
        json={
            "grant_id": "consent.phase51.001",
            "reading_id": runtime["reading_id"],
            "granted_by_role": "user",
            "allow_practitioner_review": True,
            "allow_training_use": True,
        },
    )
    assert consent_response.status_code == 200
    consent = consent_response.json()["consent_grant"]

    review_response = client.post(
        f"{API_PREFIX}/practitioner/review-requests",
        json={
            "review_request_id": "review.phase51.001",
            "runtime": runtime,
            "consent_grant": consent,
            "requested_topic": Topic.CAREER.value,
            "requested_by_role": "user",
            "note": "希望命理师复核事业建议",
        },
    )

    assert review_response.status_code == 200
    body = review_response.json()
    assert body["raw_runtime_returned"] is False
    assert body["chart_facts_returned"] is False
    case_view = body["review_request"]["case_view"]
    assert case_view["chart_facts_included"] is False
    assert case_view["raw_runtime_included"] is False
    assert "birth_datetime" in case_view["hidden_user_fields"]
    assert case_view["verdict_summaries"]
    assert body["queue_item"]["review_request_id"] == "review.phase51.001"
    assert "year_stem" not in str(case_view)
    assert "day_stem" not in str(case_view)
    assert "current_luck" not in str(case_view)
    assert body["writes_v30_state"] is False
    assert body["writes_v40_production"] is False


def test_review_request_rejects_missing_practitioner_review_consent() -> None:
    client = TestClient(create_app())
    runtime = _runtime()
    consent_response = client.post(
        f"{API_PREFIX}/consent/grants",
        json={
            "grant_id": "consent.phase51.no-review",
            "reading_id": runtime["reading_id"],
            "allow_practitioner_review": False,
            "allow_training_use": True,
        },
    )
    assert consent_response.status_code == 200

    review_response = client.post(
        f"{API_PREFIX}/practitioner/review-requests",
        json={
            "review_request_id": "review.phase51.no-review",
            "runtime": runtime,
            "consent_grant": consent_response.json()["consent_grant"],
            "requested_topic": Topic.CAREER.value,
        },
    )

    assert review_response.status_code == 422
    assert "does not allow practitioner review" in review_response.json()["detail"]


def test_practitioner_review_result_creates_local_training_label_only() -> None:
    client = TestClient(create_app())
    runtime = _runtime()
    consent = client.post(
        f"{API_PREFIX}/consent/grants",
        json={"grant_id": "consent.phase51.result", "reading_id": runtime["reading_id"]},
    ).json()["consent_grant"]
    review_request = client.post(
        f"{API_PREFIX}/practitioner/review-requests",
        json={
            "review_request_id": "review.phase51.result",
            "runtime": runtime,
            "consent_grant": consent,
            "requested_topic": Topic.CAREER.value,
        },
    ).json()["review_request"]
    signal_id = review_request["case_view"]["source_signal_ids"][0]

    result_response = client.post(
        f"{API_PREFIX}/practitioner/review-results",
        json={
            "result_id": "result.phase51.001",
            "review_request": review_request,
            "reviewer_role": "practitioner",
            "decision": "supports",
            "selected_signal_ids": [signal_id],
            "advice_notes": ["事业建议应优先落到平台资源与职责承接"],
            "probe_suggestions": ["当前平台资源是否稳定？"],
        },
    )

    assert result_response.status_code == 200
    body = result_response.json()
    event = body["training_label_events"][0]
    assert event["source"] == "practitioner_selection"
    assert event["local_only"] is True
    assert event["target_ids"] == [signal_id]
    assert body["changes_verdict"] is False
    assert body["changes_chart_facts"] is False
    assert body["writes_v40_production"] is False
    assert body["writes_v30_state"] is False


def test_phase51_docs_and_project_status_track_consent_review_queue() -> None:
    doc = Path("qiazhi/v40/docs/V40_PHASE51_CONSENT_REVIEW_QUEUE.md").read_text(encoding="utf-8")
    spec = Path("qiazhi/v40/docs/V40_SPEC.md").read_text(encoding="utf-8")
    readme = Path("qiazhi/v40/README.md").read_text(encoding="utf-8")
    status = build_project_status()

    assert "ConsentGrant And Practitioner Review Queue" in doc
    assert "AnonymizedCaseView" in doc
    assert "POST /api/v40/practitioner/review-results" in doc
    assert "2026-07-01 Phase 51" in spec
    assert "docs/V40_PHASE51_CONSENT_REVIEW_QUEUE.md" in readme
    assert status["current_phase"] == 61
    assert status["current_phase_name"] == "UI Flow Clean Rebuild"
    assert any(row["range"] == "50" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "51" and row["status"] == "complete" for row in status["phase_groups"])
