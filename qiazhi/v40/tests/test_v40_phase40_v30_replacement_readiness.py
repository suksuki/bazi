from __future__ import annotations

from fastapi.testclient import TestClient

from v40.api.app import API_PREFIX, create_app
from v40.project import build_v30_replacement_readiness


def _ready_lab_summary() -> dict[str, object]:
    return {
        "counts": {
            "shadow_compare_runs": 3,
            "evaluation_batches": 2,
            "release_readiness": 2,
            "training_examples": 2,
            "training_example_replays": 2,
            "training_replay_batches": 1,
            "global_weight_versions": 1,
            "weight_activation_reviews": 1,
        }
    }


def test_v30_replacement_readiness_candidate_ready_when_all_gates_pass() -> None:
    readiness = build_v30_replacement_readiness(
        lab_summary=_ready_lab_summary(),
        surface_readiness={"beta_status": "ready"},
    )

    assert readiness["status"] == "candidate_ready"
    assert readiness["readiness_percent"] == 100
    assert readiness["ready_gate_count"] == readiness["gate_count"]
    assert "真实命例质量判断" in readiness["requires_human_signoff"]
    assert readiness["boundary"] == "v30_replacement_readiness_observes_v40_evidence_without_mutation"


def test_v30_replacement_readiness_needs_evidence_when_shadow_compare_is_missing() -> None:
    lab_summary = _ready_lab_summary()
    lab_summary["counts"]["shadow_compare_runs"] = 1

    readiness = build_v30_replacement_readiness(
        lab_summary=lab_summary,
        surface_readiness={"beta_status": "ready"},
    )

    shadow_gate = next(gate for gate in readiness["gates"] if gate["key"] == "shadow_compare_batch")
    assert readiness["status"] == "needs_evidence"
    assert readiness["readiness_percent"] < 100
    assert shadow_gate["ready"] is False


def test_v30_replacement_readiness_api_is_readonly() -> None:
    client = TestClient(create_app())

    response = client.get(f"{API_PREFIX}/project/v30-replacement-readiness")

    assert response.status_code == 200
    body = response.json()
    assert body["readiness"]["version"] == "v40.v30_replacement_readiness.v1"
    assert body["writes_v30_state"] is False
    assert body["writes_v40_production"] is False
    assert body["boundary"] == "v30_replacement_readiness_reads_v40_evidence_without_mutation"


def test_phase40_project_status_advances_replacement_track() -> None:
    status = TestClient(create_app()).get(f"{API_PREFIX}/project/status").json()["status"]
    replacement = next(domain for domain in status["domains"] if domain["key"] == "v30_replacement")

    assert status["current_phase"] >= 40
    assert replacement["completion_percent"] >= 70
    assert status["overall_completion_percent"] >= 81
