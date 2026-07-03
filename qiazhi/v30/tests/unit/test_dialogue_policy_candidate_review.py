from __future__ import annotations

from pathlib import Path

from v30.config import V30Settings
from v30.training import (
    DIALOGUE_POLICY_CANDIDATE_REVIEW_VERSION,
    compile_dialogue_question_policy_candidate,
    run_dialogue_policy_candidate_review,
    run_dialogue_training_calibration_loop,
)
from v30.validation.dialogue_policy_candidate_review import (
    DIALOGUE_POLICY_CANDIDATE_REVIEW_VALIDATION_VERSION,
    run_dialogue_policy_candidate_review_validation,
)


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


def test_dialogue_policy_candidate_review_compiles_and_replays_candidate(tmp_path: Path) -> None:
    review = run_dialogue_policy_candidate_review(
        run_id="dtc2-unit",
        sample_limit=8,
        persist=True,
        settings=_settings(tmp_path),
    )

    assert review["version"] == DIALOGUE_POLICY_CANDIDATE_REVIEW_VERSION
    assert review["status"] == "completed"
    assert review["decision"]["decision_status"] == "dtc2_dialogue_policy_candidate_review_ready"
    assert review["decision"]["policy_pointer_write_allowed"] is False
    assert review["decision"]["chart_fact_mutation_allowed"] is False
    assert review["candidate_payload"]["auto_apply_allowed"] is False
    assert review["candidate_payload"]["policy_pointer_promotion_allowed"] is False

    comparison = review["question_policy_comparison"]
    assert comparison["version"] == "v30.question_policy_comparison.v1"
    assert comparison["candidate_id"] == "dtc2-unit.question_policy.candidate"
    assert comparison["weighted_delta_count"] > 0
    assert comparison["artifact_uri"]
    assert Path(str(comparison["artifact_uri"])).exists()
    assert review["review_summary"]["training_sample_count"] >= 1


def test_dialogue_policy_candidate_review_validation_keeps_policy_boundaries_safe(tmp_path: Path) -> None:
    validation = run_dialogue_policy_candidate_review_validation(
        run_id="dtc2-validation",
        sample_limit=8,
        persist=True,
        settings=_settings(tmp_path),
    )

    assert validation["version"] == DIALOGUE_POLICY_CANDIDATE_REVIEW_VALIDATION_VERSION
    assert validation["status"] == "completed"
    assert validation["decision"]["dialogue_policy_candidate_review_ready"] is True
    assert validation["decision"]["policy_pointer_write_allowed"] is False
    assert validation["decision"]["auto_apply_training_allowed"] is False
    assert validation["policy_boundary"]["policy_pointer_promotion_allowed"] is False


def test_compile_dialogue_question_policy_candidate_uses_dtc1_training_evidence() -> None:
    loop = run_dialogue_training_calibration_loop(run_id="dtc2-compile")
    candidate = compile_dialogue_question_policy_candidate(loop, run_id="dtc2-compile")

    assert candidate["version"] == "v30.dialogue_policy_compiled_candidate.v1"
    assert candidate["requires_operator_review"] is True
    assert candidate["chart_fact_mutation_allowed"] is False
    assert candidate["evidence_routes"]
    weights = candidate["weights"]
    assert "topic_weights" in weights
    assert "question_weights" in weights
