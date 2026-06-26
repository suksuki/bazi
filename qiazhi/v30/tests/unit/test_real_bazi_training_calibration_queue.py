from __future__ import annotations

from v30.validation.real_bazi_training_calibration_queue import (
    REAL_BAZI_TRAINING_CALIBRATION_QUEUE_VERSION,
    build_real_bazi_training_calibration_queue,
    run_real_bazi_training_calibration_queue,
)


def test_rbd_s112_training_calibration_queue_ready() -> None:
    result = run_real_bazi_training_calibration_queue(real_case_limit=8, sample_518k_limit=8)

    assert result["version"] == REAL_BAZI_TRAINING_CALIBRATION_QUEUE_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "rbd_s112_training_calibration_queue_ready"
    assert result["decision"]["training_signal_count"] >= 4
    assert result["decision"]["queued_item_count"] >= 1
    assert result["policy_boundary"]["auto_apply_training_allowed"] is False
    assert result["policy_boundary"]["chart_fact_mutation_allowed"] is False
    assert result["policy_boundary"]["policy_pointer_promotion_allowed"] is False
    signal_ids = {signal["signal_id"] for signal in result["training_signals"]}
    assert {
        "v30.training_signal.rbd_product_reading_acceptance",
        "v30.training_signal.rbd_distribution_replay_quality",
        "v30.training_signal.rbd_domain_coverage",
        "v30.training_signal.rbd_projection_safety",
        "v30.training_signal.rbd_core_claim_quality",
    }.issubset(signal_ids)
    quality_signal = next(
        signal for signal in result["training_signals"]
        if signal["signal_id"] == "v30.training_signal.rbd_core_claim_quality"
    )
    assert quality_signal["strength"] == 1.0
    assert quality_signal["payload"]["required_quality_ready_domain_count"] == 5
    assert quality_signal["payload"]["min_quality_ready_domain_count"] == 5
    assert quality_signal["runtime_mutation_allowed"] is False
    assert quality_signal["chart_fact_mutation_allowed"] is False
    domains = {item["target_domain"] for item in result["calibration_queue_items"]}
    assert {"wealth", "health"} & domains
    for item in result["calibration_queue_items"]:
        assert item["runtime_mutation_allowed"] is False
        assert item["chart_fact_mutation_allowed"] is False
        assert item["policy_pointer_promotion_allowed"] is False
        assert item["evidence_case_ids"]
    assert result["next_mainline_selection"]["task_id"] == "RBD-S1.13"


def test_rbd_s112_blocks_if_distribution_replay_not_ready() -> None:
    result = build_real_bazi_training_calibration_queue(
        distribution_replay={
            "version": "v30.real_bazi_distribution_replay.v1",
            "status": "blocked",
            "decision": {
                "distribution_replay_ready": False,
                "decision_status": "rbd_s111_distribution_replay_blocked",
            },
            "real_case_summary": {},
            "sample_518k_summary": {},
            "real_case_rows": [],
            "sample_518k_rows": [],
        }
    )

    assert result["status"] == "blocked"
    assert result["decision"]["decision_status"] == "rbd_s112_training_calibration_queue_blocked"
    assert "s111_distribution_replay_ready" in result["decision"]["failed_check_ids"]
    assert result["decision"]["full_pytest_required"] is False
    assert result["decision"]["full_518k_required"] is False
    assert result["policy_boundary"]["chart_fact_mutation_allowed"] is False
