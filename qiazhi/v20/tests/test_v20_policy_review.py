from __future__ import annotations

from fastapi.testclient import TestClient

from v20.learning.policy_review import policy_review_manifest, review_policy_proposal
from v20.server import app


def test_v20_policy_review_manifest_defines_dry_run_flow() -> None:
    manifest = policy_review_manifest()

    assert manifest["runtime_mutation"] is False
    assert {"question_ranking", "knowledge_retrieval", "confidence_calibration"} <= set(manifest["supported_policy_types"])
    assert "activation_policy" in manifest["required_flow"]
    assert "ACTIVE_POLICY_ITERATION" in manifest["guardrails"]


def test_v20_policy_review_blocks_production_by_default() -> None:
    report = review_policy_proposal(
        policy_type="question_ranking",
        policy_payload={"domain_weights": {"wealth": 0.05}},
        source="unit_test",
    )

    assert report["runtime_mutation"] is False
    assert report["validation"]["ok"] is True
    assert report["artifact"]["production_eligible"] is True
    assert report["activation_policy"]["ok"] is True
    assert report["proposal"]["status"] == "draft"


def test_v20_policy_review_endpoint_is_guarded() -> None:
    client = TestClient(app)
    manifest = client.get("/api/v20/learning/policy-review").json()
    report = client.post(
        "/api/v20/learning/policy-review",
        json={
            "policy_type": "confidence_calibration",
            "policy_payload": {"domain_offsets": {"branch": 0.02}},
            "source": "endpoint_test",
        },
    ).json()

    assert manifest["runtime_mutation"] is False
    assert report["policy_type"] == "confidence_calibration"
    assert report["activation_policy"]["decision"] == "active"
    assert "POLICY_ACTIVATION_RECORDED" in report["guardrails"]
