from __future__ import annotations

from v30.validation.frozen_core_calibration_review import (
    DEFAULT_REQUIRED_SIGNAL_IDS,
    build_frozen_core_calibration_review,
)


def test_frozen_core_calibration_review_ready_with_required_evidence() -> None:
    suite_results = {
        "m1_m2_bazi_calculation": {
            "suite_id": "v30.synthetic.m1_m2_bazi_calculation",
            "passed": True,
            "case_count": 12,
            "passed_count": 12,
            "failed_count": 0,
        },
        "m3_core_spine": {
            "suite_id": "v30.synthetic.m3_core_spine",
            "passed": True,
            "case_count": 8,
            "passed_count": 8,
            "failed_count": 0,
        },
    }
    signals = [
        {
            "signal_id": signal_id,
            "domain": "frozen_core",
            "signal_type": "coverage",
            "strength": 1.0,
            "source_case_ids": ["case"],
            "payload": {"boundary": "test_signal_trains_candidates_not_chart_facts"},
        }
        for signal_id in DEFAULT_REQUIRED_SIGNAL_IDS
    ]

    review = build_frozen_core_calibration_review(suite_results=suite_results, training_signals=signals)

    assert review["version"] == "v30.frozen_core_calibration_review.v1"
    assert review["decision"]["calibration_baseline_ready"] is True
    assert review["decision"]["core_reopen_required"] is False
    assert review["policy_boundary"]["policy_pointer_promotion_allowed"] is False
    assert review["policy_boundary"]["chart_fact_mutation_allowed"] is False
    assert review["training_signal_summary"]["required_signal_ready_count"] == len(DEFAULT_REQUIRED_SIGNAL_IDS)
    assert review["next_mainline_selection"]["task_id"] == "F2"


def test_frozen_core_calibration_review_blocks_missing_evidence() -> None:
    review = build_frozen_core_calibration_review(suite_results={}, training_signals=())

    assert review["decision"]["calibration_baseline_ready"] is False
    assert "frozen_core_calibration_tiers_not_run" in review["decision"]["blockers"]
    assert "required_training_signals_missing" in review["decision"]["blockers"]
    assert review["next_mainline_selection"]["task_id"] == "F1"
