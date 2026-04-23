from __future__ import annotations

from v17_rebirth.testing.synthetic_batch_lab import (
    DEFAULT_SYNTHETIC_BATCH_CASES,
    SyntheticBatchCase,
    build_synthetic_batch_report,
    run_batch_case,
)


def test_default_synthetic_batch_lab_runs_green() -> None:
    report = build_synthetic_batch_report()

    assert report["protocol"] == "v17.synthetic_batch_lab.v1"
    assert report["case_count"] == len(DEFAULT_SYNTHETIC_BATCH_CASES)
    assert report["failed_count"] == 0
    assert report["passed_count"] == report["case_count"]
    assert report["parameter_candidate_plan"] == []
    assert report["learning_loop_state"] == "batch_green_no_parameter_adjustment"


def test_batch_case_exposes_relation_and_dynamic_families() -> None:
    case = next(item for item in DEFAULT_SYNTHETIC_BATCH_CASES if item.case_id == "batch.relation.sanhui.wood.full")
    run = run_batch_case(case)

    assert run.passed is True
    assert "sanhui" in run.relation_families
    assert run.total > 0.0
    assert run.top


def test_batch_lab_maps_failures_to_parameter_candidate_plan() -> None:
    broken = SyntheticBatchCase(
        case_id="batch.failure.demo",
        description="故意要求一个不存在的三会，验证异常映射到调参候选。",
        four_pillars={"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
        luck_pillar="庚子",
        flow_pillar="丙午",
        expected_relation_families=("sanhui",),
        forbidden_relation_families=("sanhe",),
    )
    report = build_synthetic_batch_report((broken,))

    assert report["failed_count"] == 1
    families = set(report["parameter_family_counts"])
    assert "relation_formation.sanhui" in families
    assert "relation_gate.sanhe" in families
    assert report["parameter_candidate_plan"]
    assert report["parameter_experiments"]
    assert all(item["application_mode"] == "dry_run_plan_only" for item in report["parameter_experiments"])

