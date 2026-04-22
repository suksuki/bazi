from __future__ import annotations

import pytest

from v17_rebirth.testing.synthetic_lab import (
    L0_FLOATING_PEER,
    L0_ROOTED_PEER,
    L1_SANHE_DAY_VISIBLE,
    L1_SANHE_MONTH_VISIBLE,
    L1_SANHE_NO_VISIBLE,
    L1_SANHUI_MONTH_VISIBLE,
    MASTER_BRANCH_CLUSTER,
    SYNTHETIC_CASES,
    case_ids,
    relation_row,
    run_case,
    score_of,
)


pytestmark = [pytest.mark.regression, pytest.mark.synthetic]


@pytest.mark.parametrize("case", SYNTHETIC_CASES, ids=case_ids())
def test_synthetic_case_catalog_executes_and_emits_expected_families(case) -> None:
    run = run_case(case)

    assert run.total > 0.0
    assert run.top

    if case.expected_relation_families:
        families = {
            str(row.get("family_key") or "")
            for row in (run.meta.get("relation_formation_summary") or [])
            if isinstance(row, dict)
        }
        for family_key in case.expected_relation_families:
            assert family_key in families
    if case.expected_dynamic_families:
        families = {
            str(row.get("family_key") or "")
            for row in (run.meta.get("relation_dynamics_summary") or [])
            if isinstance(row, dict)
        }
        for family_key in case.expected_dynamic_families:
            assert family_key in families


def test_static_basis_matrix_keeps_rooted_peer_above_floating_peer() -> None:
    floating_run = run_case(L0_FLOATING_PEER)
    rooted_run = run_case(L0_ROOTED_PEER)

    assert score_of(rooted_run, "比肩") > score_of(floating_run, "比肩")
    assert score_of(rooted_run, "比肩") > score_of(floating_run, "食神")


def test_relation_visibility_matrix_preserves_no_day_month_ordering() -> None:
    no_visible_run = run_case(L1_SANHE_NO_VISIBLE)
    day_visible_run = run_case(L1_SANHE_DAY_VISIBLE)
    month_visible_run = run_case(L1_SANHE_MONTH_VISIBLE)
    sanhui_month_run = run_case(L1_SANHUI_MONTH_VISIBLE)

    no_visible_row = relation_row(no_visible_run, "sanhe")
    day_visible_row = relation_row(day_visible_run, "sanhe")
    month_visible_row = relation_row(month_visible_run, "sanhe")
    sanhui_row = relation_row(sanhui_month_run, "sanhui")

    assert isinstance(no_visible_row, dict)
    assert isinstance(day_visible_row, dict)
    assert isinstance(month_visible_row, dict)
    assert isinstance(sanhui_row, dict)

    assert float(month_visible_row.get("family_factor") or 0.0) == pytest.approx(5.0, abs=0.05)
    assert float(sanhui_row.get("family_factor") or 0.0) == pytest.approx(10.0, abs=0.05)
    assert float(day_visible_row.get("family_factor") or 0.0) > float(no_visible_row.get("family_factor") or 0.0)
    assert float(month_visible_row.get("family_factor") or 0.0) > float(day_visible_row.get("family_factor") or 0.0)
    assert float(month_visible_row.get("visible_support_strength") or 0.0) > float(day_visible_row.get("visible_support_strength") or 0.0) > 0.0


def test_master_branch_cluster_reports_parallel_relation_summaries() -> None:
    run = run_case(MASTER_BRANCH_CLUSTER)

    sanhe_row = relation_row(run, "sanhe")
    banhe_row = relation_row(run, "banhe_muwang")
    sanhui_row = relation_row(run, "sanhui")

    assert isinstance(sanhe_row, dict)
    assert isinstance(banhe_row, dict)
    assert isinstance(sanhui_row, dict)

    assert "午中神+30%" in list(sanhe_row.get("duplicate_notes") or [])
    assert float(sanhe_row.get("formation_percent") or 0.0) > float(banhe_row.get("formation_percent") or 0.0)
    assert "七杀100%" in " ".join(str(item) for item in (banhe_row.get("projection_preview") or []))
    assert str(sanhui_row.get("status") or "") in {"候选未全", "受扰成局", "成局"}
    assert "基准x" in str(sanhe_row.get("summary") or "")
