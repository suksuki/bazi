from __future__ import annotations

from v30.validation import (
    SYNTHETIC_CANONICAL_BAZI_CALIBRATION_CASES,
    run_synthetic_canonical_bazi_calibration_review,
    run_synthetic_tier,
)
from v30.validation.synthetic_canonical_bazi_calibration_review import (
    SYNTHETIC_CANONICAL_BAZI_CALIBRATION_REVIEW_VERSION,
    build_synthetic_canonical_bazi_calibration_review,
)


def test_synthetic_canonical_bazi_calibration_tier_passes() -> None:
    result = run_synthetic_tier("synthetic_canonical_bazi_calibration")

    assert result.suite_id == "v30.synthetic.synthetic_canonical_bazi_calibration"
    assert result.case_count == len(SYNTHETIC_CANONICAL_BAZI_CALIBRATION_CASES)
    assert result.passed
    for row in result.results:
        quality = row.observed["real_bazi_diagnosis_quality"]
        assert quality["status"] == "ready"
        assert quality["rule_match_count"] >= 40
        assert quality["path_count"] >= 8
        assert quality["claim_count"] >= 55
        assert quality["generic_language_rate"] <= 0.2
        assert quality["untraceable_claim_count"] == 0
        assert quality["llm_generated_claim_count"] == 0
        assert quality["chart_fact_mutation_claim_count"] == 0
        assert quality["fixed_event_prediction_claim_count"] == 0


def test_scal_s1_synthetic_canonical_calibration_review_ready() -> None:
    result = run_synthetic_canonical_bazi_calibration_review()

    assert result["version"] == SYNTHETIC_CANONICAL_BAZI_CALIBRATION_REVIEW_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "scal_s1_synthetic_canonical_calibration_ready"
    assert result["decision"]["case_count"] == len(SYNTHETIC_CANONICAL_BAZI_CALIBRATION_CASES)
    assert result["decision"]["passed_case_count"] == len(SYNTHETIC_CANONICAL_BAZI_CALIBRATION_CASES)
    assert result["decision"]["queued_item_count"] == 0
    assert result["policy_boundary"]["uses_real_person_truth"] is False
    assert result["policy_boundary"]["chart_fact_mutation_allowed"] is False
    assert result["policy_boundary"]["auto_apply_training_allowed"] is False
    assert result["policy_boundary"]["policy_pointer_promotion_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "SCAL-S2"


def test_scal_s1_blocks_and_queues_failed_canonical_case() -> None:
    result = build_synthetic_canonical_bazi_calibration_review(
        synthetic_suite={
            "suite_id": "v30.synthetic.synthetic_canonical_bazi_calibration",
            "passed": False,
            "case_count": 1,
            "passed_count": 0,
            "failed_count": 1,
            "results": [
                {
                    "case_id": SYNTHETIC_CANONICAL_BAZI_CALIBRATION_CASES[0].case_id,
                    "passed": False,
                    "failures": ["rbd_domains_missing:wealth"],
                    "observed": {
                        "real_bazi_diagnosis_quality": {
                            "domain_claims": ["career"],
                            "rule_match_count": 10,
                            "path_count": 1,
                            "portrait_count": 2,
                            "claim_count": 3,
                            "generic_language_rate": 0.0,
                            "untraceable_claim_count": 0,
                            "llm_generated_claim_count": 0,
                            "chart_fact_mutation_claim_count": 0,
                            "fixed_event_prediction_claim_count": 0,
                            "customer_internal_leak_count": 0,
                        }
                    },
                }
            ],
        }
    )

    assert result["status"] == "blocked"
    assert result["decision"]["decision_status"] == "scal_s1_synthetic_canonical_calibration_blocked"
    assert result["decision"]["queued_item_count"] >= 1
    assert result["calibration_queue_items"][0]["chart_fact_mutation_allowed"] is False
    assert result["calibration_queue_items"][0]["policy_pointer_promotion_allowed"] is False
