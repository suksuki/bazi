from __future__ import annotations

from scripts.v50_run_synthetic_training_alignment import run_alignment


def test_synthetic_validation_and_training_candidates_share_one_evidence_boundary() -> None:
    result = run_alignment()

    assert result["status"] == "PASS"
    assert all(row["passed"] for row in result["checks"])
    assert result["counts"]["manifest_suites"] == 7
    assert result["counts"]["active_work_cases"] == 10
    assert result["counts"]["active_matrix_cases"] == 17
    assert result["counts"]["candidate_contracts"] == 75
    assert result["counts"]["training_review_candidates"] == 24
    assert result["counts"]["expert_gold"] == 0
    assert result["formal_state_writes"] == 0
    assert result["weights_modified"] is False
    assert result["llm_used"] is False


def test_synthetic_alignment_is_deterministic() -> None:
    assert run_alignment() == run_alignment()
