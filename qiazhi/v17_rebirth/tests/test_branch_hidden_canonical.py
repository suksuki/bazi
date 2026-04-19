from __future__ import annotations

from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import BRANCH_HIDDEN


def test_pure_qi_branches_use_single_hidden_stem() -> None:
    assert BRANCH_HIDDEN["子"] == [("癸", 1.0)]
    assert BRANCH_HIDDEN["卯"] == [("乙", 1.0)]
    assert BRANCH_HIDDEN["酉"] == [("辛", 1.0)]


def test_mixed_branches_keep_main_middle_residual_layout() -> None:
    assert BRANCH_HIDDEN["丑"] == [("己", 0.6), ("癸", 0.2), ("辛", 0.2)]
    assert BRANCH_HIDDEN["巳"] == [("丙", 0.7), ("庚", 0.2), ("戊", 0.1)]
    assert BRANCH_HIDDEN["未"] == [("己", 0.6), ("丁", 0.2), ("乙", 0.2)]
