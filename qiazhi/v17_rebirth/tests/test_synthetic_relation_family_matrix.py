from __future__ import annotations

import pytest

from v17_rebirth.testing.synthetic_lab import (
    L1_BANHE_MUWANG,
    L1_BANHE_SHENGWANG,
    L1_GONGHE_BASELINE,
    L1_LIUHE_BASELINE,
    L1_STEM_FUSION_RUNTIME,
    relation_dynamics_row,
    relation_row,
    run_case,
)


pytestmark = [pytest.mark.regression, pytest.mark.synthetic]


def test_relation_family_matrix_preserves_expected_base_factor_order() -> None:
    liuhe_run = run_case(L1_LIUHE_BASELINE)
    shengwang_run = run_case(L1_BANHE_SHENGWANG)
    muwang_run = run_case(L1_BANHE_MUWANG)
    gonghe_run = run_case(L1_GONGHE_BASELINE)

    liuhe_row = relation_row(liuhe_run, "liuhe")
    shengwang_row = relation_row(shengwang_run, "banhe_shengwang")
    muwang_row = relation_row(muwang_run, "banhe_muwang")
    gonghe_row = relation_row(gonghe_run, "gonghe")

    assert isinstance(liuhe_row, dict)
    assert isinstance(shengwang_row, dict)
    assert isinstance(muwang_row, dict)
    assert isinstance(gonghe_row, dict)

    assert float(shengwang_row.get("family_factor") or 0.0) == pytest.approx(1.45, abs=0.05)
    assert float(muwang_row.get("family_factor") or 0.0) == pytest.approx(1.28, abs=0.05)
    assert float(liuhe_row.get("family_factor") or 0.0) == pytest.approx(1.22, abs=0.05)
    assert float(gonghe_row.get("family_factor") or 0.0) == pytest.approx(1.12, abs=0.05)

    assert float(shengwang_row.get("family_factor") or 0.0) > float(muwang_row.get("family_factor") or 0.0)
    assert float(muwang_row.get("family_factor") or 0.0) > float(liuhe_row.get("family_factor") or 0.0)
    assert float(liuhe_row.get("family_factor") or 0.0) > float(gonghe_row.get("family_factor") or 0.0)


def test_relation_family_matrix_exposes_status_and_projection_variation() -> None:
    shengwang_run = run_case(L1_BANHE_SHENGWANG)
    muwang_run = run_case(L1_BANHE_MUWANG)
    gonghe_run = run_case(L1_GONGHE_BASELINE)

    shengwang_row = relation_row(shengwang_run, "banhe_shengwang")
    muwang_row = relation_row(muwang_run, "banhe_muwang")
    gonghe_row = relation_row(gonghe_run, "gonghe")

    assert isinstance(shengwang_row, dict)
    assert isinstance(muwang_row, dict)
    assert isinstance(gonghe_row, dict)

    assert str(shengwang_row.get("status") or "") in {"弱成局", "成局", "受扰成局"}
    assert str(muwang_row.get("status") or "") in {"弱成局", "成局", "受扰成局"}
    assert str(gonghe_row.get("status") or "") in {"弱成局", "成局", "受扰成局"}
    assert "金" in str(shengwang_row.get("summary") or "")
    assert "金" in str(muwang_row.get("summary") or "")
    assert "金" in str(gonghe_row.get("summary") or "")


def test_stem_fusion_runtime_case_enters_relation_dynamics_not_only_formation() -> None:
    run = run_case(L1_STEM_FUSION_RUNTIME)

    fusion_dynamic = relation_dynamics_row(run, "stem_fusion_transform")
    assert isinstance(fusion_dynamic, dict)
    assert str(fusion_dynamic.get("energy_axis") or "") == "转化"
    assert float(fusion_dynamic.get("stability_delta_ratio") or 0.0) > 0.0

    visible_rows = [row for row in (run.meta.get("relation_visible_bonuses") or []) if isinstance(row, dict)]
    fusion_visible = next((row for row in visible_rows if str(row.get("family_key") or "") == "stem_fusion_transform"), None)
    assert isinstance(fusion_visible, dict)
    assert float(fusion_visible.get("bonus_total") or 0.0) > 0.0

