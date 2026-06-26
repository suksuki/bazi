from __future__ import annotations

from v30.validation.targeted_calibration_validation_gate import build_targeted_calibration_validation_gate


def _ready_candidate_review() -> dict[str, object]:
    return {
        "version": "v30.targeted_calibration_candidate_review.v1",
        "review_id": "unit-f3",
        "decision": {"targeted_calibration_review_ready": True},
        "candidate_summary": {
            "candidate_count": 4,
            "families": ["structure_policy", "rule_policy", "question_policy", "answer_policy"],
        },
    }


def test_targeted_calibration_validation_gate_ready() -> None:
    gate = build_targeted_calibration_validation_gate(
        candidate_review=_ready_candidate_review(),
        synthetic_all={
            "suite_id": "v30.synthetic.all",
            "passed": True,
            "case_count": 95,
            "passed_count": 95,
            "failed_count": 0,
        },
        corpus_sample={
            "run_id": "v30.518k.sample.unit",
            "mode": "sample",
            "case_count": 8,
            "promotion_signal": "eligible",
            "failure_clusters": [],
            "artifact_record_id": "v30.518k.artifact.unit",
            "artifact_search_backend": "json_fallback",
        },
        gate_id="unit-f3",
    )

    assert gate["version"] == "v30.targeted_calibration_validation_gate.v1"
    assert gate["decision"]["validation_gate_ready"] is True
    assert gate["decision"]["policy_pointer_review_allowed"] is True
    assert gate["decision"]["policy_pointer_promotion_allowed"] is False
    assert gate["policy_boundary"]["chart_fact_mutation_allowed"] is False
    assert gate["synthetic_all_summary"]["passed_count"] == 95
    assert gate["corpus_518k_sample_summary"]["case_count"] == 8
    assert gate["next_mainline_selection"]["task_id"] == "F4"


def test_targeted_calibration_validation_gate_blocks_missing_evidence() -> None:
    gate = build_targeted_calibration_validation_gate(
        candidate_review={
            "version": "v30.targeted_calibration_candidate_review.v1",
            "decision": {"targeted_calibration_review_ready": False},
        },
        synthetic_all={
            "suite_id": "v30.synthetic.all",
            "passed": False,
            "case_count": 0,
            "passed_count": 0,
            "failed_count": 0,
        },
        corpus_sample={
            "run_id": "",
            "mode": "sample",
            "case_count": 0,
            "promotion_signal": "",
        },
    )

    assert gate["decision"]["validation_gate_ready"] is False
    assert "f2_candidate_review_not_ready" in gate["decision"]["blockers"]
    assert "synthetic_all_failed" in gate["decision"]["blockers"]
    assert "518k_sample_not_eligible" in gate["decision"]["blockers"]
    assert gate["next_mainline_selection"]["task_id"] == "F3"
