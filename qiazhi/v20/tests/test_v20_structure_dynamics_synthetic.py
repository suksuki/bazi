from __future__ import annotations

from v20.validation.structure_dynamics_synthetic import (
    STRUCTURE_DYNAMICS_SYNTHETIC_CASES,
    run_structure_dynamics_synthetic_suite,
)


def test_v20_structure_dynamics_synthetic_suite_validates_v2_paths() -> None:
    report = run_structure_dynamics_synthetic_suite()

    assert report["version"] == "v20.structure_dynamics_synthetic.v1"
    assert report["ok"] is True
    assert report["case_count"] == len(STRUCTURE_DYNAMICS_SYNTHETIC_CASES)
    assert report["case_count"] >= 20
    assert report["pass_rate"] == 1.0
    assert report["quality_scores"]["dynamic_path_consistency"] == 1.0
    assert report["quality_scores"]["semantic_candidate_precision"] == 1.0
    assert "SDE_V2_VALIDATES_PATH_BEFORE_LEGACY_SWITCH" in report["guardrails"]


def test_v20_structure_dynamics_synthetic_suite_covers_adjacent_patterns() -> None:
    report = run_structure_dynamics_synthetic_suite()
    labels = {
        row["observed"]["label"]
        for row in report["results"]
    }
    path_text = " ".join(
        " ".join(row["observed"]["node_labels"])
        for row in report["results"]
    )

    assert {"食神制杀", "伤官制杀", "财生官/财滋杀", "官印/杀印相生", "印星承身", "比劫承身"}.issubset(labels)
    assert "丁食神" in path_text
    assert "丙伤官" in path_text
    assert "庚正财" in path_text
    assert "辛七杀" in path_text
    assert any("财破印" in row["observed"]["semantic_labels"] for row in report["results"])
    assert any("比劫夺财" in row["observed"]["semantic_labels"] for row in report["results"])
    assert any("印制食伤" in row["observed"]["semantic_labels"] for row in report["results"])
    assert any("印星承身" in row["observed"]["semantic_labels"] for row in report["results"])
    assert any("比劫承身" in row["observed"]["semantic_labels"] for row in report["results"])
    time_relations = {
        relation_type
        for row in report["results"]
        for relation_type in row["observed"]["time_relation_blockers"]
    }
    assert {"clash", "break", "punishment"}.issubset(time_relations)
