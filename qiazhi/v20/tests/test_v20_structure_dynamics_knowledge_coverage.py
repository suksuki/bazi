from __future__ import annotations

from v20.validation.structure_dynamics_knowledge_coverage import build_structure_dynamics_knowledge_coverage_report


def test_v20_structure_dynamics_knowledge_coverage_covers_current_path_scope() -> None:
    report = build_structure_dynamics_knowledge_coverage_report()

    assert report["version"] == "v20.structure_dynamics_knowledge_coverage.v1"
    assert report["status"] == "covered_current_scope"
    assert report["observed_label_count"] >= 9
    assert report["unsupported_count"] == 0
    assert report["full_knowledge_unit_count"] >= report["observed_label_count"]
    assert set(report["covered_labels"]) >= {
        "食神制杀",
        "伤官制杀",
        "输出制官杀",
        "食伤生财",
        "财生官/财滋杀",
        "官印/杀印相生",
        "印制食伤",
        "比劫夺财",
        "财破印",
    }
    assert all(row["mechanism_unit_supported"] for row in report["coverage_rows"])
    assert all(row["full_knowledge_unit_supported"] for row in report["coverage_rows"])
    assert "FULL_518K_COVERAGE_REQUIRES_CORPUS_REPLAY" in report["guardrails"]
