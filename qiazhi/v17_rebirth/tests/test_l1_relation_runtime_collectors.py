from __future__ import annotations

from typing import Any, Dict, List

from v17_rebirth.backend.logic.L1_atomic_ops.relation_penalty_families import (
    collect_penalty_relation_deltas,
)
from v17_rebirth.backend.logic.L1_atomic_ops.relation_special_families import (
    collect_control_relation_deltas,
    collect_stem_fusion_relation_deltas,
)
from v17_rebirth.backend.logic.L1_atomic_ops.relation_structured_families import (
    collect_structured_relation_family_deltas,
)


def _apply_branch_delta(
    *,
    branch: str,
    branch_scope_totals: Dict[str, float],
    relation_element: str,
    magnitude: float,
    out: Dict[str, float],
) -> None:
    out[branch] = out.get(branch, 0.0) + magnitude * float(branch_scope_totals.get(branch, 1.0))


def _apply_stem_element_delta(
    *,
    target_element: str,
    magnitude: float,
    rooted_static: Dict[str, float],
    out: Dict[str, float],
) -> None:
    out[target_element] = out.get(target_element, 0.0) + magnitude


def _append_trace(
    relation_traces: List[Dict[str, Any]],
    kind: str,
    members: List[str],
    pillars: List[str],
    intensity: float,
    relation_element: str = "",
    **kwargs: Any,
) -> None:
    relation_traces.append(
        {
            "kind": kind,
            "members": list(members),
            "pillars": list(pillars),
            "intensity": intensity,
            "relation_element": relation_element,
            **kwargs,
        }
    )


def test_structured_relation_family_collector_handles_sanhe() -> None:
    traces: List[Dict[str, Any]] = []
    deltas: Dict[str, float] = {}

    collect_structured_relation_family_deltas(
        sanhe_hits=[
            {
                "group": ["寅", "午", "戌"],
                "matched_branches": ["寅", "午", "戌"],
                "pillars": ["year", "month", "hour"],
                "strength": 1.2,
                "duplicate_bonus": 0.1,
                "pivot_branch": "午",
                "tomb_branch": "戌",
                "role_map": {"寅": "starter", "午": "pivot", "戌": "tomb"},
                "branch_counts": {"寅": 1, "午": 1, "戌": 1},
            }
        ],
        sanhui_hits=[],
        banhe_hits=[],
        gonghe_hits=[],
        liuhe_hits=[],
        anhe_hits=[],
        conflicted_branches=set(),
        conflict_events=[],
        four_pillars={"year": "甲寅", "month": "丙午", "day": "戊子", "hour": "庚戌"},
        luck_pillar="",
        flow_pillar="",
        branch_scope_totals={"寅": 1.0, "午": 1.0, "戌": 1.0},
        relation_delta_raw=deltas,
        relation_traces=traces,
        branch_hidden={"午": [("丁", 1.0)]},
        stem_element_map={"丁": "火"},
        banhe_pair_to_element={},
        gonghe_pair_to_element={},
        liuhe_pair_to_element={},
        pillars_group_closeness=lambda pillars: 0.82,
        relation_factor_bundle=lambda **kwargs: {"effective_family_factor": 1.6, "visible_support_strength": 0.7},
        relation_conflict_damping=lambda **kwargs: 0.95,
        relation_root_intensity=lambda **kwargs: 1.5,
        relation_duplicate_bonus=lambda counts, roles: (0.0, {}),
        relation_duplicate_role_bonus=lambda role: 0.2 if role == "pivot" else 0.1,
        relation_apply_branch_delta=_apply_branch_delta,
        relation_dominant_hidden_stem=lambda **kwargs: "丁",
        append_relation_trace=_append_trace,
    )

    assert set(deltas) == {"寅", "午", "戌"}
    assert traces and traces[0]["kind"] == "sanhe"
    assert traces[0]["relation_element"] == "火"


def test_penalty_relation_family_collector_handles_chong_and_xing() -> None:
    traces: List[Dict[str, Any]] = []
    deltas: Dict[str, float] = {}

    collect_penalty_relation_deltas(
        chong_hits=[{"pair": ["子", "午"], "pillars": ["day", "flow"]}],
        hai_hits=[],
        po_hits=[],
        xing_hits=[{"branches": ["丑", "戌"], "edge": ["month", "hour"]}],
        branch_scope_totals={"子": 1.0, "午": 1.0, "丑": 1.0, "戌": 1.0},
        relation_delta_raw=deltas,
        relation_traces=traces,
        pillars_group_closeness=lambda pillars: 0.8,
        get_penalty_value=lambda key, default: default,
        relation_apply_branch_delta=_apply_branch_delta,
        append_relation_trace=_append_trace,
        penalty_chong_default=0.5,
        penalty_hai_default=0.3,
        penalty_po_default=0.25,
        penalty_xing_default=0.4,
    )

    assert deltas["子"] < 0 and deltas["午"] < 0
    assert deltas["丑"] < 0 and deltas["戌"] < 0
    assert {trace["kind"] for trace in traces} == {"chong", "xing"}


def test_control_relation_family_collector_records_ke_trace() -> None:
    traces: List[Dict[str, Any]] = []
    deltas: Dict[str, float] = {}

    collect_control_relation_deltas(
        branches={"month": "寅", "day": "辰"},
        branch_element_map={"寅": "木", "辰": "土"},
        control_adj_scope_pairs=(("month", "day"),),
        branch_scope_totals={"寅": 1.0, "辰": 1.0},
        relation_delta_raw=deltas,
        relation_traces=traces,
        pillar_pair_closeness=lambda a, b: 0.75,
        controls_element=lambda src, dst: src == "木" and dst == "土",
        get_l0_val=lambda key, default: default,
        relation_apply_branch_delta=_apply_branch_delta,
        append_relation_trace=_append_trace,
        control_bonus_default=0.4,
        control_penalty_default=0.2,
    )

    assert deltas["寅"] > 0
    assert deltas["辰"] < 0
    assert traces[0]["kind"] == "ke"
    assert traces[0]["relation_element"] == "木克土"


def test_stem_fusion_relation_family_collector_handles_transform_and_stuck() -> None:
    traces: List[Dict[str, Any]] = []
    deltas: Dict[str, float] = {}

    cases = collect_stem_fusion_relation_deltas(
        stems={"year": "甲", "month": "己"},
        branches={"year": "子", "month": "丑"},
        static_rooted={"甲": 1.0, "己": 1.0},
        relation_delta_raw=deltas,
        relation_traces=traces,
        detect_stem_fusion_cases=lambda stems, branches: [
            {
                "mode": "transformed",
                "hua_element": "earth",
                "branch_root_ratio": 0.6,
                "visible_support_strength": 0.7,
                "support_score": 0.65,
                "interference_score": 0.1,
                "manifestation_mode": "明化",
                "support_origin": "month",
                "pillars": ["year", "month"],
                "stems": ["甲", "己"],
            },
            {
                "mode": "stuck",
                "hua_element": "earth",
                "branch_root_ratio": 0.2,
                "visible_support_strength": 0.1,
                "support_score": 0.22,
                "interference_score": 0.5,
                "manifestation_mode": "暗化",
                "support_origin": "year",
                "pillars": ["month", "day"],
                "stems": ["乙", "庚"],
            },
        ],
        pillars_group_closeness=lambda pillars: 0.8,
        get_l0_val=lambda key, default: default,
        relation_apply_stem_element_delta=_apply_stem_element_delta,
        append_relation_trace=_append_trace,
        element_en_to_cn={"earth": "土"},
        stem_element_map={"乙": "木", "庚": "金"},
        bonus_anhe_default=0.3,
        penalty_po_default=0.25,
    )

    assert len(cases) == 2
    assert deltas["土"] > 0
    assert deltas["木"] < 0 and deltas["金"] < 0
    assert {trace["kind"] for trace in traces} == {"stem_fusion_transform", "stem_fusion_stuck"}
