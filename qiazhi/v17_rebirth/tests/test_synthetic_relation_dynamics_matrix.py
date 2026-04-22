from __future__ import annotations

import pytest

from v17_rebirth.testing.synthetic_lab import (
    L1_ANHE_BASELINE,
    L1_CHONG_BASELINE,
    L1_HAI_BASELINE,
    L1_KE_BASELINE,
    L1_PO_BASELINE,
    L1_XING_BASELINE,
    relation_dynamics_row,
    run_case,
)


pytestmark = [pytest.mark.regression, pytest.mark.synthetic]


def test_relation_dynamics_matrix_preserves_axis_semantics() -> None:
    chong_row = relation_dynamics_row(run_case(L1_CHONG_BASELINE), "chong")
    hai_row = relation_dynamics_row(run_case(L1_HAI_BASELINE), "hai")
    po_row = relation_dynamics_row(run_case(L1_PO_BASELINE), "po")
    ke_row = relation_dynamics_row(run_case(L1_KE_BASELINE), "ke")

    assert isinstance(chong_row, dict)
    assert isinstance(hai_row, dict)
    assert isinstance(po_row, dict)
    assert isinstance(ke_row, dict)

    assert str(chong_row.get("energy_axis") or "") == "激发"
    assert str(hai_row.get("energy_axis") or "") == "暗损"
    assert str(po_row.get("energy_axis") or "") == "解构"
    assert str(ke_row.get("energy_axis") or "") == "压制转移"


def test_relation_dynamics_matrix_preserves_expected_stability_sign() -> None:
    chong_row = relation_dynamics_row(run_case(L1_CHONG_BASELINE), "chong")
    hai_row = relation_dynamics_row(run_case(L1_HAI_BASELINE), "hai")
    po_row = relation_dynamics_row(run_case(L1_PO_BASELINE), "po")
    ke_row = relation_dynamics_row(run_case(L1_KE_BASELINE), "ke")

    assert float(chong_row.get("stability_delta_ratio") or 0.0) < 0.0
    assert float(hai_row.get("stability_delta_ratio") or 0.0) < 0.0
    assert float(po_row.get("stability_delta_ratio") or 0.0) < 0.0
    assert float(ke_row.get("stability_delta_ratio") or 0.0) < 0.0

    assert float(chong_row.get("energy_effect_ratio") or 0.0) > float(hai_row.get("energy_effect_ratio") or 0.0)
    assert float(po_row.get("energy_effect_ratio") or 0.0) > float(hai_row.get("energy_effect_ratio") or 0.0)


def test_relation_dynamics_matrix_covers_binding_and_internal_loss_axes() -> None:
    anhe_row = relation_dynamics_row(run_case(L1_ANHE_BASELINE), "anhe")
    xing_row = relation_dynamics_row(run_case(L1_XING_BASELINE), "xing")

    assert isinstance(anhe_row, dict)
    assert isinstance(xing_row, dict)

    assert str(anhe_row.get("energy_axis") or "") == "绑定"
    assert float(anhe_row.get("stability_delta_ratio") or 0.0) > 0.0
    assert float(anhe_row.get("free_energy_lock_ratio") or 0.0) > 0.0

    assert str(xing_row.get("energy_axis") or "") == "内耗"
    assert float(xing_row.get("stability_delta_ratio") or 0.0) < 0.0
    assert "有效输出" in str(xing_row.get("note") or "")
