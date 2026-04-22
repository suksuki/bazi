from __future__ import annotations

from v17_rebirth.backend.logic.core_engine.god_ring_resolver_core import resolve_god_ring_core
from v17_rebirth.backend.logic.core_engine.pillar_graph_kernel import build_six_pillar_graph
from v17_rebirth.backend.logic.runtime_field_protocol import (
    ROOT_SCOPE_WEIGHTS,
    WORK_ORIGIN_SCOPE_FACTORS,
    runtime_field_prompt_lines,
    runtime_field_protocol_payload,
)


def test_runtime_field_prompt_lines_export_canonical_contract() -> None:
    rows = runtime_field_prompt_lines()
    joined = "\n".join(rows)
    assert "大运更像背景场" in joined
    assert "日柱/日支 > 月柱/月令 > 时柱 > 年柱" in joined
    assert "runtime_cascade" in joined


def test_build_six_pillar_graph_dynamic_edges_carry_runtime_metadata() -> None:
    graph = build_six_pillar_graph(
        four_pillars={"year": "壬寅", "month": "甲辰", "day": "丙子", "hour": "甲午"},
        luck_pillar="庚戌",
        flow_pillar="丙午",
    )
    by_pair = {(edge.source, edge.target): edge for edge in graph.edges}
    luck_day = by_pair[("luck_stem", "day_stem")]
    flow_month = by_pair[("flow_branch", "month_branch")]
    luck_flow = by_pair[("luck_branch", "flow_branch")]

    assert luck_day.metadata.get("coupling_mode") == "background_core"
    assert luck_day.metadata.get("runtime_role") == "background_field"
    assert luck_day.metadata.get("coupling_priority") == 1
    assert flow_month.metadata.get("coupling_mode") == "seasonal_trigger"
    assert flow_month.metadata.get("runtime_role") == "yearly_perturbation"
    assert luck_flow.metadata.get("coupling_mode") == "runtime_cascade"


def test_resolve_god_ring_core_exports_runtime_field_protocol_snapshot() -> None:
    result = resolve_god_ring_core(
        four_pillars={"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
        luck_pillar="庚子",
        flow_pillar="丙午",
        deity_scores={"伤官": 74.0, "食神": 53.0, "正官": 15.0, "七杀": 9.0},
        decision_rows=[],
    )
    graph_meta = result["graph_meta"]
    protocol = graph_meta["runtime_field_protocol"]
    dynamic_modes = graph_meta["dynamic_mode_profile"]

    assert protocol["anchor_priority_label"] == "日柱/日支 > 月柱/月令 > 时柱 > 年柱"
    assert protocol["root_scope_weights"]["luck"] == ROOT_SCOPE_WEIGHTS["luck"]
    assert protocol["work_origin_scope_factors"]["flow"] == WORK_ORIGIN_SCOPE_FACTORS["flow"]
    assert protocol["dynamic_edge_modes"]["luck->day"] == "background_core"
    assert dynamic_modes["background_core"]["count"] >= 2
    assert dynamic_modes["runtime_cascade"]["count"] >= 2


def test_runtime_field_protocol_payload_keeps_core_and_l0_roles_separate() -> None:
    payload = runtime_field_protocol_payload()
    assert payload["core_graph_position_weights"]["day"] > payload["core_graph_position_weights"]["flow"]
    assert payload["root_scope_weights"]["luck"] > payload["root_scope_weights"]["flow"]
    assert payload["work_origin_scope_factors"]["luck"] > payload["work_origin_scope_factors"]["flow"]
