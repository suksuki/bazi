from __future__ import annotations

from v20.validation.structure_dynamics_legacy_v2_switch import build_structure_dynamics_legacy_v2_switch_report


def test_v20_structure_dynamics_legacy_v2_switch_report_is_explainable() -> None:
    report = build_structure_dynamics_legacy_v2_switch_report()

    assert report["version"] == "v20.structure_dynamics_legacy_v2_switch.v1"
    assert report["status"] == "switch_ready_primary"
    assert report["case_count"] >= 20
    assert report["unexplained_conflict_count"] == 0
    assert report["explainable_count"] == report["case_count"]
    assert report["switch_policy"]["recommended_runtime_field"] == "primary_dynamic_chain"
    assert report["switch_policy"]["runtime_primary"] == "primary_dynamic_chain"
    assert report["switch_policy"]["keep_legacy_field"] == "debug_only"
    assert report["comparisons"]
