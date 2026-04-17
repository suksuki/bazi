"""V13.03：物理锚点、插件权力等级、二段跳闭合。"""

from __future__ import annotations

from app.logic.brain.decision_hub import (
    apply_physical_sanity_check,
    apply_plugin_authority_tiers,
    maybe_two_stage_fact_closure,
)
from app.core.plugins.registry import plugin_authority_level


def test_plugin_authority_level_core_highest() -> None:
    assert plugin_authority_level("sys.core.physics") == 5
    assert plugin_authority_level("base.chronos") == 4
    assert plugin_authority_level("classical.blind_school.v1") == 3


def test_apply_plugin_authority_tiers_keeps_only_max_level() -> None:
    scores = [
        {"plugin_id": "modern.wealth_risk.v1", "score": 0.99, "authority_level": 2},
        {"plugin_id": "classical.blind_school.v1", "score": 0.5, "authority_level": 3},
    ]
    out = apply_plugin_authority_tiers(scores, physics_meta_sink={})
    assert len(out) == 1
    assert out[0]["plugin_id"] == "classical.blind_school.v1"


def test_apply_physical_sanity_check_rejects_large_deviation() -> None:
    pt = {
        "deity_energy_axes": {
            "比肩": {"absolute_energy": 10.0, "polarity": "STRONG_POSITIVE"},
            "七杀": {"absolute_energy": 0.1, "polarity": "STRONG_NEGATIVE"},
        },
        "meta": {},
    }
    scores = [{"plugin_id": "classical.blind_school.v1", "score": 0.9, "authority_level": 3}]
    meta: dict = {}
    out = apply_physical_sanity_check(
        [{"kind": "clash", "detail": "子午"}],
        physics_tensor=pt,
        match_scores=scores,
        physics_meta_sink=meta,
        deviation_threshold=0.4,
    )
    assert out == []
    assert any(x.get("kind") == "SILENT_REJECT" for x in (meta.get("physics_autonomy_log_v1") or []))


def test_two_stage_fact_closure_collapses_after_cycles() -> None:
    pt: dict = {"meta": {}}
    md = {"conflict_matrix": {"points": [{"kind": "clash", "detail": "子午冲"}]}}
    scores = [
        {"plugin_id": "classical.blind_school.v1", "score": 0.62, "authority_level": 3},
        {"plugin_id": "classical.wangshuai.v1", "score": 0.58, "authority_level": 3},
    ]
    out1 = maybe_two_stage_fact_closure(metadata=md, physics_tensor=pt, match_scores=scores)
    assert len(out1) == 2
    out2 = maybe_two_stage_fact_closure(metadata=md, physics_tensor=pt, match_scores=out1)
    assert len(out2) == 1
    assert pt["meta"].get("global_conflict_tension") == 0.0
    assert pt["meta"].get("v1303_two_stage_auto_closure_v1") is True
