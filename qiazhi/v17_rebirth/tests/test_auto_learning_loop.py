from __future__ import annotations

from v17_rebirth.testing.auto_learning_loop import run_auto_learning_cycle
from v17_rebirth.testing.parameter_sandbox import build_shadow_override, patched_v17_constants
from v17_rebirth.testing.synthetic_batch_lab import (
    SyntheticBatchCase,
    build_synthetic_batch_report,
)


def test_parameter_sandbox_temporarily_overrides_constants() -> None:
    override = build_shadow_override(
        parameter_path="L0_FOUNDATION.REL_FAMILY_FULL_CLEAN_SANHE",
        multiplier=1.01,
    )
    assert override

    with patched_v17_constants(override):
        inside = build_shadow_override(
            parameter_path="L0_FOUNDATION.REL_FAMILY_FULL_CLEAN_SANHE",
            multiplier=1.0,
        )
    outside = build_shadow_override(
        parameter_path="L0_FOUNDATION.REL_FAMILY_FULL_CLEAN_SANHE",
        multiplier=1.0,
    )

    path = "L0_FOUNDATION.REL_FAMILY_FULL_CLEAN_SANHE"
    assert inside[path] == override[path]
    assert outside[path] != override[path]


def test_auto_learning_cycle_is_safe_when_batch_is_green() -> None:
    report = run_auto_learning_cycle()

    assert report["protocol"] == "v17.auto_learning_loop.v1"
    assert report["state"] == "baseline_green_no_parameter_tuning"
    assert report["can_auto_apply"] is False
    assert report["shadow_experiments"] == []
    assert report["baseline"]["failed_count"] == 0


def test_batch_report_feeds_parameter_experiments_for_failures() -> None:
    broken = SyntheticBatchCase(
        case_id="batch.learning.failure",
        description="故意制造一个可归因失败。",
        four_pillars={"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
        expected_relation_families=("sanhui",),
    )
    report = build_synthetic_batch_report((broken,))

    assert report["failed_count"] == 1
    assert report["parameter_candidate_plan"]
    assert report["parameter_experiments"]
    assert report["parameter_experiments"][0]["application_mode"] == "dry_run_plan_only"

