from __future__ import annotations

from scripts.v50_run_cross_axis_metamorphic_suite import run_cross_axis_suite


def test_cross_axis_metamorphic_suite_changes_only_authorized_layers() -> None:
    report = run_cross_axis_suite()

    assert report["status"] == "passed"
    assert report["observed_data"]["test_count"] == 5
    assert report["observed_data"]["pass_count"] == 5
    assert report["observed_data"]["failures"] == []
    assert report["boundary_status"]["expected_contract_used"] is False
