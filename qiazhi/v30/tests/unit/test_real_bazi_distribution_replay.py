from __future__ import annotations

from v30.validation.real_bazi_distribution_replay import (
    REAL_BAZI_DISTRIBUTION_REPLAY_VERSION,
    build_real_bazi_distribution_replay,
    run_real_bazi_distribution_replay,
)


def test_rbd_s111_distribution_replay_passes_lightweight_real_case_and_518k_sample() -> None:
    result = run_real_bazi_distribution_replay(real_case_limit=8, sample_518k_limit=8)

    assert result["version"] == REAL_BAZI_DISTRIBUTION_REPLAY_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "rbd_s111_distribution_replay_ready"
    assert result["real_case_summary"]["ready_case_count"] == 8
    assert result["sample_518k_summary"]["ready_case_count"] == 8
    assert result["real_case_summary"]["min_quality_ready_domain_count"] == 5
    assert result["sample_518k_summary"]["min_quality_ready_domain_count"] == 5
    assert result["sample_518k_summary"]["min_admin_claim_count"] >= 45
    assert result["sample_518k_summary"]["min_admin_path_count"] >= 8
    assert result["sample_518k_summary"]["min_admin_portrait_count"] >= 20
    assert result["real_case_summary"]["generic_language_hit_count"] == 0
    assert result["sample_518k_summary"]["customer_internal_leak_count"] == 0
    assert result["policy_boundary"]["full_518k_required"] is False
    assert result["next_mainline_selection"]["task_id"] == "RBD-S1.12"
    quality_check = next(row for row in result["checks"] if row["check_id"] == "core_claim_quality_replay_ready")
    assert quality_check["passed"] is True


def test_rbd_s111_distribution_replay_blocks_if_s110_acceptance_is_missing() -> None:
    product = {
        "version": "v30.real_bazi_product_reading_acceptance.v1",
        "status": "blocked",
        "decision": {
            "product_reading_acceptance_ready": False,
            "decision_status": "rbd_s110_product_reading_blocked",
        },
    }
    real_case = {"suite_id": "v30.synthetic.real_case_calibration_pack", "passed": True, "case_count": 8, "results": []}
    result = build_real_bazi_distribution_replay(
        product_acceptance=product,
        real_case_synthetic=real_case,
        real_case_limit=8,
        sample_518k_limit=8,
    )

    assert result["status"] == "blocked"
    assert result["decision"]["decision_status"] == "rbd_s111_distribution_replay_blocked"
    assert "s110_product_acceptance_ready" in result["decision"]["failed_check_ids"]
    assert result["decision"]["full_518k_required"] is False
