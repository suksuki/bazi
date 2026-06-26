from __future__ import annotations

from v30.validation.stage_a_evidence_review import (
    STAGE_A_EVIDENCE_REVIEW_VERSION,
    build_stage_a_evidence_review,
)


def _stage_a(*, passed: bool = True, external_release_allowed: bool = False) -> dict[str, object]:
    return {
        "version": "v30.stage_a_release_gate_execution.v1",
        "status": "completed" if passed else "blocked",
        "decision": {
            "stage_a_release_gates_passed": passed,
            "decision_status": "rel_s3_stage_a_gates_passed" if passed else "blocked",
            "gate_count": 4,
            "executed_gate_count": 4,
            "passed_gate_count": 4 if passed else 3,
            "failed_gate_ids": [] if passed else ["synthetic_all"],
            "missing_gate_ids": [],
            "external_release_allowed": external_release_allowed,
        },
        "policy_boundary": {
            "full_pytest_run": False,
            "live_llm_smoke_run": False,
            "real_env_smoke_run": False,
            "full_518k_run": False,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
        },
        "gate_summaries": [
            {
                "gate_id": "controlled_release_readiness",
                "executed": True,
                "passed": True,
                "status": "completed",
                "summary": {"case_count": 0, "passed_count": 0},
            },
            {
                "gate_id": "synthetic_all",
                "executed": True,
                "passed": passed,
                "status": "passed" if passed else "failed",
                "summary": {"case_count": 38, "passed_count": 38 if passed else 37},
            },
            {
                "gate_id": "518k_sample",
                "executed": True,
                "passed": True,
                "status": "eligible",
                "summary": {
                    "case_count": 8,
                    "run_id": "v30.518k.sample.test",
                    "artifact_uri": "artifacts/sample.json",
                    "index_uri": "artifacts/sample.index.json",
                    "artifact_record_id": "sample-record",
                    "artifact_search_backend": "json_fallback",
                },
            },
            {
                "gate_id": "518k_shard",
                "executed": True,
                "passed": True,
                "status": "eligible",
                "summary": {
                    "case_count": 16,
                    "run_id": "v30.518k.shard.test",
                    "artifact_uri": "artifacts/shard.json",
                    "index_uri": "artifacts/shard.index.json",
                    "artifact_record_id": "shard-record",
                    "artifact_search_backend": "json_fallback",
                },
            },
        ],
    }


def test_rel_s4_reviews_stage_a_evidence_and_holds_release() -> None:
    result = build_stage_a_evidence_review(stage_a_execution=_stage_a())

    assert result["version"] == STAGE_A_EVIDENCE_REVIEW_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "rel_s4_stage_a_evidence_review_complete_external_release_held"
    assert result["decision"]["controlled_trial_readiness_confirmed"] is True
    assert result["decision"]["external_release_allowed"] is False
    assert result["decision"]["return_to_core_module_mainline"] is True
    assert result["decision"]["additional_heavy_live_gate_authorization_recommended"] is False
    assert result["external_release_hold"]["additional_authorization_required_for_external_release"] is True
    assert result["policy_boundary"]["full_pytest_run"] is False
    assert result["policy_boundary"]["policy_pointer_promotion_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "MCR3"


def test_rel_s4_blocks_missing_required_gate() -> None:
    payload = _stage_a()
    payload["gate_summaries"] = payload["gate_summaries"][:-1]  # type: ignore[index]
    result = build_stage_a_evidence_review(stage_a_execution=payload)

    assert result["status"] == "blocked"
    assert result["decision"]["decision_status"] == "rel_s4_stage_a_evidence_review_blocked"
    assert "required_stage_a_gate_missing" in result["decision"]["blockers"]
    assert "518k_shard" in result["decision"]["missing_required_gate_ids"]
    assert result["next_mainline_selection"]["task_id"] == "REL-S4-FR"


def test_rel_s4_blocks_unexpected_external_release_permission() -> None:
    result = build_stage_a_evidence_review(stage_a_execution=_stage_a(external_release_allowed=True))

    assert result["status"] == "blocked"
    assert "unexpected_external_release_permission" in result["decision"]["blockers"]
    assert result["decision"]["external_release_allowed"] is False
