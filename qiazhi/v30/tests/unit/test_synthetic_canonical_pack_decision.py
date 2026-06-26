from __future__ import annotations

from v30.validation import (
    SYNTHETIC_CANONICAL_BAZI_CALIBRATION_CASES,
    run_synthetic_canonical_pack_decision,
    run_synthetic_tier,
)
from v30.validation.synthetic_canonical_pack_decision import (
    REQUIRED_EXPANSION_FAMILIES,
    SYNTHETIC_CANONICAL_PACK_DECISION_VERSION,
    build_synthetic_canonical_pack_decision,
)


def test_scal_s2_expanded_canonical_pack_decision_ready() -> None:
    result = run_synthetic_canonical_pack_decision()

    assert result["version"] == SYNTHETIC_CANONICAL_PACK_DECISION_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "scal_s2_expanded_canonical_pack_cadence_ready"
    assert result["decision"]["case_count"] == len(SYNTHETIC_CANONICAL_BAZI_CALIBRATION_CASES)
    assert result["decision"]["case_count"] >= 16
    assert result["decision"]["covered_family_count"] == len(REQUIRED_EXPANSION_FAMILIES)
    assert result["decision"]["routine_cadence_ready"] is True
    assert result["decision"]["missing_families"] == {}
    assert result["policy_boundary"]["uses_real_person_truth"] is False
    assert result["policy_boundary"]["chart_fact_mutation_allowed"] is False
    assert result["policy_boundary"]["auto_apply_training_allowed"] is False
    assert result["policy_boundary"]["policy_pointer_promotion_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "SCAL-S3"


def test_scal_s2_canonical_tier_expanded_cases_pass() -> None:
    result = run_synthetic_tier("synthetic_canonical_bazi_calibration")

    assert result.passed
    assert result.case_count >= 16
    case_ids = {row.case_id for row in result.results}
    for family_id in REQUIRED_EXPANSION_FAMILIES:
        assert any(family_id in case_id for case_id in case_ids)


def test_scal_s2_blocks_missing_expansion_family() -> None:
    result = build_synthetic_canonical_pack_decision(
        canonical_review={
            "version": "v30.synthetic_canonical_bazi_calibration_review.v1",
            "status": "completed",
            "decision": {
                "synthetic_canonical_calibration_ready": True,
                "decision_status": "scal_s1_synthetic_canonical_calibration_ready",
                "case_count": 6,
                "passed_case_count": 6,
                "queued_item_count": 0,
            },
            "policy_boundary": {
                "uses_real_person_truth": False,
                "chart_fact_mutation_allowed": False,
                "auto_apply_training_allowed": False,
                "policy_pointer_promotion_allowed": False,
            },
            "case_rows": [
                {
                    "case_id": "v30.synthetic.canonical_bazi.wealth_flow_geng_001",
                    "passed": True,
                }
            ],
        }
    )

    assert result["status"] == "blocked"
    assert result["decision"]["decision_status"] == "scal_s2_expanded_canonical_pack_blocked"
    assert "required_expansion_families_covered" in result["decision"]["failed_check_ids"]
    assert result["policy_boundary"]["chart_fact_mutation_allowed"] is False
