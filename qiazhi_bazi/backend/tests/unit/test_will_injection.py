"""Will Injection 与叙事刷新阈值纯函数测试。"""
from __future__ import annotations

from app.schemas.bazi_metadata import (
    BaziMetadata,
    ConflictMatrix,
    FlowState,
    FourPillars,
    HistoryContext,
    PersistenceConfirmedPhysicsWill,
    PersistenceLayer,
    StemBranchPair,
)
from app.services.helpers.will_injection import (
    UPDATE_PHYSICS_PARAM,
    collect_will_physics_param_merges,
    inject_user_decisions,
    narrative_refresh_needed,
    snapshot_energy_state,
    temporal_will_stale_warnings,
    will_temporal_anchor_blocks_injection,
)


def _pillars() -> FourPillars:
    return FourPillars(
        year=StemBranchPair(stem="甲", branch="子"),
        month=StemBranchPair(stem="丙", branch="寅"),
        day=StemBranchPair(stem="戊", branch="辰"),
        hour=StemBranchPair(stem="庚", branch="午"),
    )


def test_collect_merges_from_persistence_confirmed_verdicts():
    md = BaziMetadata(
        pillars=_pillars(),
        conflict_matrix=ConflictMatrix(points=[]),
        flow_state=FlowState.UNKNOWN,
        persistence_layer=PersistenceLayer(
            confirmed_verdicts=[
                PersistenceConfirmedPhysicsWill(
                    kinds=[UPDATE_PHYSICS_PARAM],
                    payload={"L1_OP_PROD_ETA": 1.11, "root_decay_lambda": 0.55},
                )
            ],
        ),
    )
    phys, inter = collect_will_physics_param_merges(md)
    assert phys.get("L1_OP_PROD_ETA") == 1.11
    assert inter.get("root_decay_lambda") == 0.55


def test_inject_user_decisions_mutates_physics_config():
    md = BaziMetadata(
        pillars=_pillars(),
        conflict_matrix=ConflictMatrix(points=[]),
        flow_state=FlowState.UNKNOWN,
        persistence_layer=PersistenceLayer(
            confirmed_verdicts=[
                PersistenceConfirmedPhysicsWill(
                    kinds=[UPDATE_PHYSICS_PARAM],
                    payload={"CLIMATE_INTENSITY": 1.05},
                )
            ],
        ),
    )
    cfg: dict = {"WEIGHT_LUCK": 0.5}
    out = inject_user_decisions(md, cfg)
    assert out["applied"] is True
    assert cfg["CLIMATE_INTENSITY"] == 1.05


def test_narrative_refresh_entropy_relative_gt_5pct():
    before = snapshot_energy_state({"meta": {"global_entropy": 0.4}, "deity_scores": {"比肩": 0.5, "正印": 0.5}})
    after = snapshot_energy_state({"meta": {"global_entropy": 0.5}, "deity_scores": {"比肩": 0.5, "正印": 0.5}})
    assert narrative_refresh_needed(before, after) is True


def test_narrative_refresh_tier_jump():
    before = {"global_entropy": 0.2, "deity_tiers": {"比肩": "偏弱", "正印": "中庸"}}
    after = {"global_entropy": 0.2, "deity_tiers": {"比肩": "中庸", "正印": "中庸"}}
    assert narrative_refresh_needed(before, after) is True


def test_narrative_refresh_abs_t3_to_t4():
    before = {"global_entropy": 0.2, "deity_tiers": {}, "deity_abs_tiers": {"正官": "Abs_T3"}}
    after = {"global_entropy": 0.2, "deity_tiers": {}, "deity_abs_tiers": {"正官": "Abs_T4"}}
    assert narrative_refresh_needed(before, after) is True


def test_narrative_refresh_false_when_stable():
    before = snapshot_energy_state({"meta": {"global_entropy": 0.4}, "deity_scores": {"比肩": 0.8, "正印": 0.2}})
    after = snapshot_energy_state({"meta": {"global_entropy": 0.41}, "deity_scores": {"比肩": 0.79, "正印": 0.21}})
    assert narrative_refresh_needed(before, after) is False


def test_inject_skipped_when_temporal_anchor_mismatch():
    md = BaziMetadata(
        pillars=_pillars(),
        conflict_matrix=ConflictMatrix(points=[]),
        flow_state=FlowState.UNKNOWN,
        temporal_context={"dayun_ganzhi": "丙寅"},
        persistence_layer=PersistenceLayer(
            will_temporal_anchor_dayun="甲子",
            confirmed_verdicts=[
                PersistenceConfirmedPhysicsWill(
                    kinds=[UPDATE_PHYSICS_PARAM],
                    payload={"CLIMATE_INTENSITY": 1.0},
                )
            ],
        ),
    )
    cfg: dict = {"WEIGHT_LUCK": 0.5}
    out = inject_user_decisions(md, cfg, request_dayun="丙寅")
    assert out["applied"] is False
    assert "CLIMATE_INTENSITY" not in cfg


def test_temporal_will_stale_when_dayun_mismatch():
    md = BaziMetadata(
        pillars=_pillars(),
        conflict_matrix=ConflictMatrix(points=[]),
        flow_state=FlowState.UNKNOWN,
        temporal_context={"dayun_ganzhi": "丙寅"},
        persistence_layer=PersistenceLayer(
            will_temporal_anchor_dayun="甲子",
            confirmed_verdicts=[
                PersistenceConfirmedPhysicsWill(
                    kinds=[UPDATE_PHYSICS_PARAM],
                    payload={"CLIMATE_INTENSITY": 1.0},
                )
            ],
        ),
    )
    w = temporal_will_stale_warnings(md, request_dayun=None)
    assert w and "[警告]" in w[0] and "甲子" in w[0] and "丙寅" in w[0]
    assert will_temporal_anchor_blocks_injection(md, request_dayun="丙寅") is True


def test_history_context_confirmed_verdicts_merge():
    from app.schemas.bazi_metadata import ConfirmedVerdictRecord

    md = BaziMetadata(
        pillars=_pillars(),
        conflict_matrix=ConflictMatrix(points=[]),
        flow_state=FlowState.UNKNOWN,
        history_context=HistoryContext(
            confirmed_verdicts=[
                ConfirmedVerdictRecord(
                    verdict_id="v1",
                    body_excerpt="x",
                    confirmed_at="",
                    decision_kinds=[UPDATE_PHYSICS_PARAM],
                    physics_param_payload={"through_stem_boost": 1.2},
                )
            ]
        ),
    )
    _p, inter = collect_will_physics_param_merges(md)
    assert inter.get("through_stem_boost") == 1.2
