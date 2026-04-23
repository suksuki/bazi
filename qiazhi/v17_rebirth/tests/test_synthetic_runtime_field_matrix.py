from __future__ import annotations

import pytest

from v17_rebirth.backend.logic.core_engine.pillar_graph_kernel import build_six_pillar_graph
from v17_rebirth.testing.synthetic_lab import (
    RUNTIME_BANHE_INTERRUPTION,
    RUNTIME_HAI_FLOW_TRIGGER,
    RUNTIME_HAI_LUCK_BACKGROUND,
    RUNTIME_HAI_NATAL_BASELINE,
    RUNTIME_LIUHE_FLOW_TRIGGER,
    RUNTIME_LIUHE_LUCK_BACKGROUND,
    RUNTIME_LIUHE_NATAL_BASELINE,
    RUNTIME_SANHUI_RESONANCE,
    relation_dynamics_row,
    relation_row,
    run_case,
)


pytestmark = [pytest.mark.regression, pytest.mark.synthetic]


def test_runtime_field_matrix_luck_background_outweighs_flow_trigger_for_liuhe() -> None:
    luck_run = run_case(RUNTIME_LIUHE_LUCK_BACKGROUND)
    flow_run = run_case(RUNTIME_LIUHE_FLOW_TRIGGER)

    luck_row = relation_row(luck_run, "liuhe")
    flow_row = relation_row(flow_run, "liuhe")
    luck_dynamic = relation_dynamics_row(luck_run, "liuhe")
    flow_dynamic = relation_dynamics_row(flow_run, "liuhe")

    assert isinstance(luck_row, dict)
    assert isinstance(flow_row, dict)
    assert isinstance(luck_dynamic, dict)
    assert isinstance(flow_dynamic, dict)

    assert float(luck_row.get("formation_percent") or 0.0) > float(flow_row.get("formation_percent") or 0.0)
    assert float(luck_dynamic.get("energy_effect_ratio") or 0.0) > float(flow_dynamic.get("energy_effect_ratio") or 0.0)
    assert list(luck_dynamic.get("pillars") or []) == ["luck", "year"]
    assert list(flow_dynamic.get("pillars") or []) == ["flow", "year"]


def test_runtime_field_matrix_natal_outweighs_external_trigger_for_liuhe() -> None:
    natal_run = run_case(RUNTIME_LIUHE_NATAL_BASELINE)
    luck_run = run_case(RUNTIME_LIUHE_LUCK_BACKGROUND)
    flow_run = run_case(RUNTIME_LIUHE_FLOW_TRIGGER)

    natal_row = relation_row(natal_run, "liuhe")
    luck_row = relation_row(luck_run, "liuhe")
    flow_row = relation_row(flow_run, "liuhe")
    natal_dynamic = relation_dynamics_row(natal_run, "liuhe")
    luck_dynamic = relation_dynamics_row(luck_run, "liuhe")
    flow_dynamic = relation_dynamics_row(flow_run, "liuhe")

    assert isinstance(natal_row, dict)
    assert isinstance(luck_row, dict)
    assert isinstance(flow_row, dict)
    assert isinstance(natal_dynamic, dict)
    assert isinstance(luck_dynamic, dict)
    assert isinstance(flow_dynamic, dict)

    assert float(natal_row.get("formation_percent") or 0.0) > float(luck_row.get("formation_percent") or 0.0)
    assert float(luck_row.get("formation_percent") or 0.0) > float(flow_row.get("formation_percent") or 0.0)
    assert float(natal_dynamic.get("stability_delta_ratio") or 0.0) > float(luck_dynamic.get("stability_delta_ratio") or 0.0)
    assert float(luck_dynamic.get("stability_delta_ratio") or 0.0) > float(flow_dynamic.get("stability_delta_ratio") or 0.0)


def test_runtime_field_matrix_luck_background_outweighs_flow_trigger_for_hai() -> None:
    luck_run = run_case(RUNTIME_HAI_LUCK_BACKGROUND)
    flow_run = run_case(RUNTIME_HAI_FLOW_TRIGGER)

    luck_dynamic = relation_dynamics_row(luck_run, "hai")
    flow_dynamic = relation_dynamics_row(flow_run, "hai")

    assert isinstance(luck_dynamic, dict)
    assert isinstance(flow_dynamic, dict)

    assert float(luck_dynamic.get("energy_effect_ratio") or 0.0) > float(flow_dynamic.get("energy_effect_ratio") or 0.0)
    assert float(luck_dynamic.get("stability_delta_ratio") or 0.0) < 0.0
    assert float(flow_dynamic.get("stability_delta_ratio") or 0.0) < 0.0


def test_runtime_field_matrix_natal_harm_outweighs_external_harm() -> None:
    natal_run = run_case(RUNTIME_HAI_NATAL_BASELINE)
    luck_run = run_case(RUNTIME_HAI_LUCK_BACKGROUND)
    flow_run = run_case(RUNTIME_HAI_FLOW_TRIGGER)

    natal_dynamic = relation_dynamics_row(natal_run, "hai")
    luck_dynamic = relation_dynamics_row(luck_run, "hai")
    flow_dynamic = relation_dynamics_row(flow_run, "hai")

    assert isinstance(natal_dynamic, dict)
    assert isinstance(luck_dynamic, dict)
    assert isinstance(flow_dynamic, dict)

    assert float(natal_dynamic.get("energy_effect_ratio") or 0.0) > float(luck_dynamic.get("energy_effect_ratio") or 0.0)
    assert float(luck_dynamic.get("energy_effect_ratio") or 0.0) > float(flow_dynamic.get("energy_effect_ratio") or 0.0)
    assert abs(float(natal_dynamic.get("stability_delta_ratio") or 0.0)) > abs(float(luck_dynamic.get("stability_delta_ratio") or 0.0))
    assert abs(float(luck_dynamic.get("stability_delta_ratio") or 0.0)) > abs(float(flow_dynamic.get("stability_delta_ratio") or 0.0))


def test_runtime_field_matrix_graph_metadata_keeps_background_and_trigger_roles_distinct() -> None:
    luck_graph = build_six_pillar_graph(
        four_pillars=RUNTIME_LIUHE_LUCK_BACKGROUND.four_pillars,
        luck_pillar=RUNTIME_LIUHE_LUCK_BACKGROUND.luck_pillar,
        flow_pillar="",
    )
    flow_graph = build_six_pillar_graph(
        four_pillars=RUNTIME_LIUHE_FLOW_TRIGGER.four_pillars,
        luck_pillar="",
        flow_pillar=RUNTIME_LIUHE_FLOW_TRIGGER.flow_pillar,
    )

    luck_edge = {(edge.source, edge.target): edge for edge in luck_graph.edges}[("luck_branch", "year_branch")]
    flow_edge = {(edge.source, edge.target): edge for edge in flow_graph.edges}[("flow_branch", "year_branch")]

    assert float(luck_edge.weight) > float(flow_edge.weight)
    assert luck_edge.metadata.get("runtime_role") == "background_field"
    assert flow_edge.metadata.get("runtime_role") == "yearly_perturbation"
    assert luck_edge.metadata.get("coupling_mode") == "background_periphery"
    assert flow_edge.metadata.get("coupling_mode") == "peripheral_trigger"


def test_runtime_field_matrix_resonance_strengthens_structured_family() -> None:
    resonance_run = run_case(RUNTIME_SANHUI_RESONANCE)
    sanhui_row = relation_row(resonance_run, "sanhui")
    sanhui_dynamic = relation_dynamics_row(resonance_run, "sanhui")

    assert isinstance(sanhui_row, dict)
    assert isinstance(sanhui_dynamic, dict)

    assert float(sanhui_row.get("formation_percent") or 0.0) >= 90.0
    assert str(sanhui_row.get("status") or "") in {"强成局", "受扰成局"}
    assert float(sanhui_dynamic.get("stability_delta_ratio") or 0.0) > 0.0
    assert set(sanhui_dynamic.get("pillars") or []) >= {"year", "month", "day", "luck", "flow"}


def test_runtime_field_matrix_interruption_preserves_family_but_surfaces_breakers() -> None:
    interruption_run = run_case(RUNTIME_BANHE_INTERRUPTION)
    banhe_row = relation_row(interruption_run, "banhe_muwang")
    chong_dynamic = relation_dynamics_row(interruption_run, "chong")
    po_dynamic = relation_dynamics_row(interruption_run, "po")

    assert isinstance(banhe_row, dict)
    assert isinstance(chong_dynamic, dict)
    assert isinstance(po_dynamic, dict)

    assert float(banhe_row.get("formation_percent") or 0.0) > 0.0
    assert float(chong_dynamic.get("stability_delta_ratio") or 0.0) < 0.0
    assert float(po_dynamic.get("stability_delta_ratio") or 0.0) < 0.0
