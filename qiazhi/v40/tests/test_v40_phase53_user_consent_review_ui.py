from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from v40.api.app import API_PREFIX, create_app
from v40.contracts.base import Topic
from v40.project import build_project_status
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


def test_phase53_user_ui_wires_review_after_report_without_internal_leakage() -> None:
    html = TestClient(create_app()).get("/v40/ui").text

    assert "命理师复核" in html
    assert "授权复核" in html
    assert "reviewSurface" in html
    assert "renderReviewInvite(runtime)" in html
    assert "resetReviewSurface();" in html
    assert "/api/v40/consent/grants" in html
    assert "/api/v40/practitioner/review-requests" in html
    assert "submitPractitionerReview" in html

    for token in [
        "ConsentGrant",
        "AnonymizedCaseView",
        "PractitionerReviewRequest",
        "TrainingLabelEvent",
        "consent_grant",
        "role_key",
        "role_context",
        "/admin/v40",
        "provider",
        "model",
        "debug",
        "telemetry",
    ]:
        assert token not in html


def test_phase53_review_api_chain_matches_user_ui_payload_shape() -> None:
    client = TestClient(create_app())
    reading_id = "reading.phase53.ui.chain.001"
    runtime = _runtime(client, reading_id)

    grant_response = client.post(
        f"{API_PREFIX}/consent/grants",
        json={
            "grant_id": "ui-review-grant-phase53-001",
            "reading_id": reading_id,
            "granted_by_role": "user",
            "allow_practitioner_review": True,
            "allow_training_use": True,
            "note": "用户在报告页授权命理师复核",
            "persist": False,
        },
    )
    assert grant_response.status_code == 200
    grant = grant_response.json()["consent_grant"]

    review_response = client.post(
        f"{API_PREFIX}/practitioner/review-requests",
        json={
            "review_request_id": "ui-review-request-phase53-001",
            "runtime": runtime,
            "consent_grant": grant,
            "requested_topic": Topic.CAREER.value,
            "requested_by_role": "user",
            "note": "用户授权后发送脱敏摘要给命理师复核",
            "persist": False,
        },
    )

    assert review_response.status_code == 200
    body = review_response.json()
    assert body["queue_item"]["status"] == "queued"
    assert body["raw_runtime_returned"] is False
    assert body["chart_facts_returned"] is False
    assert body["writes_v40_production"] is False


def test_phase53_docs_and_project_status_track_user_consent_review_ui() -> None:
    doc = Path("qiazhi/v40/docs/V40_PHASE53_USER_CONSENT_REVIEW_UI.md").read_text(encoding="utf-8")
    spec = Path("qiazhi/v40/docs/V40_SPEC.md").read_text(encoding="utf-8")
    readme = Path("qiazhi/v40/README.md").read_text(encoding="utf-8")
    ui_spec = Path("qiazhi/v40/docs/V40_UI_PRODUCT_FLOW_SPEC.md").read_text(encoding="utf-8")
    status = build_project_status()

    assert "User Consent Review UI" in doc
    assert "授权复核" in doc
    assert "2026-07-02 Phase 53" in spec
    assert "docs/V40_PHASE53_USER_CONSENT_REVIEW_UI.md" in readme
    assert "User-side practitioner review authorization is wired" in ui_spec
    assert status["current_phase"] == 66
    assert status["current_phase_name"] == "Domain Verdict Adapters"
    assert any(row["range"] == "52" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "53" and row["status"] == "complete" for row in status["phase_groups"])
    assert "P66-1: Domain Verdict Adapters" in status["next_mainline_tasks"]
