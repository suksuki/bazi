from __future__ import annotations

import pytest

from v17_rebirth.testing.practitioner_benchmarks import (
    PRACTITIONER_BENCHMARK_CASES,
    PRACTITIONER_FIRE_WATER_GENGXU_BINGWU,
    PRACTITIONER_METAL_MIX_GENGZI_BINGWU,
    PRACTITIONER_METAL_MIX_XINCHOU_YIWEI,
    practitioner_case_ids,
    practitioner_dynamic_families,
    practitioner_dynamic_row,
    practitioner_relation_families,
    practitioner_relation_row,
    run_practitioner_case,
)


pytestmark = [pytest.mark.regression, pytest.mark.benchmark]


@pytest.mark.parametrize("case", PRACTITIONER_BENCHMARK_CASES, ids=practitioner_case_ids())
def test_practitioner_benchmark_catalog_emits_expected_families_and_axes(case) -> None:
    run = run_practitioner_case(case)

    assert run.total > 0.0
    assert run.top
    assert case.audit_focus
    assert case.reviewer_note

    relation_families = practitioner_relation_families(run)
    dynamic_families = practitioner_dynamic_families(run)

    for family_key in case.expected_relation_families:
        assert family_key in relation_families
    for family_key in case.expected_dynamic_families:
        assert family_key in dynamic_families
    for family_key in case.forbidden_relation_families:
        assert family_key not in relation_families
        assert family_key not in dynamic_families
    for god in case.expected_top_contains:
        assert god in run.top
    if case.expected_leader:
        assert run.top[0] == case.expected_leader


def test_practitioner_gengzi_case_preserves_sanhe_without_false_sanhui() -> None:
    run = run_practitioner_case(PRACTITIONER_METAL_MIX_GENGZI_BINGWU)

    sanhe_row = practitioner_relation_row(run, "sanhe")
    chong_row = practitioner_dynamic_row(run, "chong")
    fusion_row = practitioner_dynamic_row(run, "stem_fusion_transform")

    assert isinstance(sanhe_row, dict)
    assert isinstance(chong_row, dict)
    assert isinstance(fusion_row, dict)

    assert float(sanhe_row.get("formation_ratio") or 0.0) >= 0.60
    assert "酉" in "".join(str(item) for item in (sanhe_row.get("members") or []))
    assert "丑" in "".join(str(item) for item in (sanhe_row.get("members") or []))
    assert float(chong_row.get("stability_delta_ratio") or 0.0) < 0.0
    assert float(fusion_row.get("energy_effect_ratio") or 0.0) > 0.0


def test_practitioner_xinchou_case_keeps_qisha_as_absolute_axis() -> None:
    run = run_practitioner_case(PRACTITIONER_METAL_MIX_XINCHOU_YIWEI)

    sanhe_row = practitioner_relation_row(run, "sanhe")
    xing_row = practitioner_dynamic_row(run, "xing")

    assert isinstance(sanhe_row, dict)
    assert isinstance(xing_row, dict)

    assert float(sanhe_row.get("formation_ratio") or 0.0) == pytest.approx(1.0, abs=1e-6)
    assert run.scores["七杀"] > run.scores["正官"] * 5
    assert run.scores["七杀"] > 100.0
    assert float(xing_row.get("stability_delta_ratio") or 0.0) < 0.0


def test_practitioner_fire_water_case_keeps_parallel_fire_and_water_routes() -> None:
    run = run_practitioner_case(PRACTITIONER_FIRE_WATER_GENGXU_BINGWU)

    sanhe_row = practitioner_relation_row(run, "sanhe")
    banhe_row = practitioner_relation_row(run, "banhe_muwang")
    sanhe_dynamic = practitioner_dynamic_row(run, "sanhe")
    banhe_dynamic = practitioner_dynamic_row(run, "banhe_muwang")

    assert isinstance(sanhe_row, dict)
    assert isinstance(banhe_row, dict)
    assert isinstance(sanhe_dynamic, dict)
    assert isinstance(banhe_dynamic, dict)

    assert float(sanhe_row.get("formation_ratio") or 0.0) > float(banhe_row.get("formation_ratio") or 0.0)
    assert float(sanhe_dynamic.get("energy_effect_ratio") or 0.0) > float(banhe_dynamic.get("energy_effect_ratio") or 0.0)
    assert float(banhe_row.get("formation_ratio") or 0.0) > 0.40
    assert float(banhe_dynamic.get("stability_delta_ratio") or 0.0) > 0.0
