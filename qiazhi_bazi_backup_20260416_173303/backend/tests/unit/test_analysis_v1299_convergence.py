from __future__ import annotations

from unittest.mock import MagicMock

from app.services.analysis_service import (
    _core_dimensions_covered_for_convergence,
    _read_global_tension,
)


def test_read_global_tension_uses_meta_field() -> None:
    assert _read_global_tension({"meta": {"global_conflict_tension": 0.15}}) == 0.15
    assert _read_global_tension({"meta": {}}) == 1.0


def test_core_dimensions_covered_verified_facts() -> None:
    orch = MagicMock()
    orch.vf_tags = []
    b = {"verified_fact_lines": ["a", "b"]}
    assert _core_dimensions_covered_for_convergence(bundle=b, orchestration=orch) is True


def test_core_dimensions_from_hub_tags() -> None:
    orch = MagicMock()
    orch.vf_tags = ["VF1", "VF2"]
    assert _core_dimensions_covered_for_convergence(bundle={}, orchestration=orch) is True
