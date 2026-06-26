from __future__ import annotations

from v20.validation.structure_dynamics_path_distribution import build_structure_dynamics_path_distribution


def test_v20_structure_dynamics_path_distribution_covers_counters_and_time_blockers() -> None:
    report = build_structure_dynamics_path_distribution()

    assert report["version"] == "v20.structure_dynamics_path_distribution.v1"
    assert report["status"] == "ready"
    assert report["case_count"] >= 20
    assert report["counterexample_coverage"]["status"] == "covered"
    assert set(report["counterexample_coverage"]["covered_labels"]) >= {"财破印", "比劫夺财", "印制食伤"}
    assert report["time_blocker_coverage"]["status"] == "covered"
    assert "clash" in report["time_blocker_coverage"]["covered_types"]
    assert report["label_distribution"]
