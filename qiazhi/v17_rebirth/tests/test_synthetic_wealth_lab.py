from __future__ import annotations

import pytest

from v17_rebirth.testing.synthetic_tuning_bridge import build_tuning_bridge_report
from v17_rebirth.testing.synthetic_wealth_lab import (
    SYNTHETIC_WEALTH_CASES,
    build_synthetic_wealth_report,
    run_wealth_case,
)


pytestmark = [pytest.mark.regression, pytest.mark.synthetic]


@pytest.mark.parametrize("case", SYNTHETIC_WEALTH_CASES, ids=lambda case: case.case_id)
def test_synthetic_wealth_cases_hold_expected_path_contracts(case) -> None:
    run = run_wealth_case(case)

    assert run.passed, [item.to_dict() for item in run.anomalies]
    assert run.wealth_code["contract"] == "v17.topic.wealth_code.v1"
    assert "topic.wealth_code.path.calibration" in run.wealth_code["learning_hooks"]
    assert run.case.parameter_family.startswith("topic.wealth_code.")


def test_synthetic_wealth_report_exports_learning_families() -> None:
    report = build_synthetic_wealth_report()

    assert report["protocol"] == "v17.synthetic_wealth_lab.v1"
    assert report["case_count"] == len(SYNTHETIC_WEALTH_CASES)
    assert report["failed_count"] == 0
    assert report["parameter_family_counts"] == {}
    assert report["learning_loop_state"] == "wealth_synthetic_cases_green_collect_more_feedback"


def test_tuning_bridge_catalog_includes_wealth_synthetic_cases() -> None:
    report = build_tuning_bridge_report(cases=[])

    assert report["synthetic_catalog_size"] >= len(SYNTHETIC_WEALTH_CASES)
