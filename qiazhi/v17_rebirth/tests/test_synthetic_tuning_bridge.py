from __future__ import annotations

from dataclasses import replace

from v17_rebirth.testing.practitioner_benchmarks import (
    PRACTITIONER_BENCHMARK_CASES,
    PRACTITIONER_METAL_MIX_GENGZI_BINGWU,
)
from v17_rebirth.testing.synthetic_tuning_bridge import (
    audit_practitioner_case,
    build_parameter_candidate_plan,
    build_tuning_bridge_report,
)


def test_tuning_bridge_reports_green_benchmark_state() -> None:
    report = build_tuning_bridge_report(PRACTITIONER_BENCHMARK_CASES)

    assert report["protocol"] == "v17.synthetic_tuning_bridge.v1"
    assert report["benchmark_count"] >= 3
    assert report["synthetic_catalog_size"] > report["benchmark_count"]
    assert report["passed_count"] + report["failed_count"] == report["benchmark_count"]
    assert "learning_loop_state" in report


def test_tuning_bridge_maps_benchmark_failure_to_parameter_family_and_cases() -> None:
    broken = replace(
        PRACTITIONER_METAL_MIX_GENGZI_BINGWU,
        expected_relation_families=("sanhui",),
        forbidden_relation_families=("sanhe",),
        expected_leader="偏印",
    )

    audit = audit_practitioner_case(broken)

    assert audit.passed is False
    families = {issue.parameter_family for issue in audit.issues}
    assert "relation_formation.sanhui" in families
    assert "relation_gate.sanhe" in families
    assert "authority.leader_axis" in families
    assert audit.suggested_synthetic_cases


def test_parameter_candidate_plan_is_manual_and_case_backed() -> None:
    plan = build_parameter_candidate_plan(
        {
            "relation_formation.sanhe": 2,
            "authority.leader_axis": 1,
        }
    )

    assert [row["parameter_family"] for row in plan] == [
        "relation_formation.sanhe",
        "authority.leader_axis",
    ]
    assert all(row["safety_gate"] == "manual_review_required" for row in plan)
    assert plan[0]["recommended_action"] == "review_relation_family_factor_and_visibility_gate"
    assert plan[0]["synthetic_cases"]
