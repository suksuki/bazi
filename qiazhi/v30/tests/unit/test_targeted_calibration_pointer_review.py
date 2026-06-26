from __future__ import annotations

from pathlib import Path

from v30.config import V30Settings
from v30.policy import RuntimePointerStore
from v30.validation.targeted_calibration_pointer_review import build_targeted_calibration_pointer_review


def _settings(tmp_path: Path) -> V30Settings:
    return V30Settings(
        database_url=None,
        redis_url=None,
        redis_prefix="v30",
        runtime_dir=tmp_path / ".runtime",
        host="127.0.0.1",
        port=9030,
        env="test",
        repository="memory",
    )


def _ready_gate() -> dict[str, object]:
    return {
        "version": "v30.targeted_calibration_validation_gate.v1",
        "gate_id": "unit-f4",
        "decision": {"validation_gate_ready": True, "decision_status": "ready_for_policy_pointer_review"},
        "candidate_review_summary": {
            "candidate_count": 4,
            "families": ["structure_policy", "rule_policy", "question_policy", "answer_policy"],
        },
        "synthetic_all_summary": {"passed": True, "case_count": 95, "passed_count": 95},
        "corpus_518k_sample_summary": {
            "case_count": 8,
            "promotion_signal": "eligible",
            "artifact_record_id": "v30.518k.artifact.unit",
        },
    }


def test_targeted_calibration_pointer_review_ready(tmp_path: Path) -> None:
    review = build_targeted_calibration_pointer_review(
        validation_gate=_ready_gate(),
        store=RuntimePointerStore(_settings(tmp_path)),
        review_id="unit-f4",
    )

    assert review["version"] == "v30.targeted_calibration_pointer_review.v1"
    assert review["decision"]["pointer_review_ready"] is True
    assert review["decision"]["manual_pointer_decision_required"] is True
    assert review["decision"]["policy_pointer_promotion_allowed"] is False
    assert review["operator_boundary"]["automatic_pointer_write_allowed"] is False
    assert review["operator_boundary"]["chart_fact_mutation_allowed"] is False
    assert review["pointer_diff_summary"]["would_change_count"] >= 3
    assert review["next_mainline_selection"]["task_id"] == "F5"


def test_targeted_calibration_pointer_review_blocks_missing_gate(tmp_path: Path) -> None:
    review = build_targeted_calibration_pointer_review(
        validation_gate={
            "version": "v30.targeted_calibration_validation_gate.v1",
            "decision": {"validation_gate_ready": False},
            "candidate_review_summary": {"candidate_count": 0, "families": []},
            "synthetic_all_summary": {"case_count": 0, "passed_count": 0, "passed": False},
            "corpus_518k_sample_summary": {"case_count": 0, "promotion_signal": ""},
        },
        store=RuntimePointerStore(_settings(tmp_path)),
    )

    assert review["decision"]["pointer_review_ready"] is False
    assert "f3_validation_gate_not_ready" in review["decision"]["blockers"]
    assert "candidate_count_low" in review["decision"]["blockers"]
    assert "no_pointer_diff_to_review" in review["decision"]["blockers"]
    assert review["next_mainline_selection"]["task_id"] == "F4"
