from __future__ import annotations

from v17_rebirth.backend.plugins.spec import V17Fact
from v17_rebirth.backend.logic.L1_atomic_ops.l1_meta_hydration import hydrate_v17_physics_tensor
from v17_rebirth.backend.logic.plugin_discovery import collect_all_spec_facts
from v17_rebirth.backend.services.claim_protocol import compile_claims
from v17_rebirth.backend.services.conflict_detector import detect_claim_conflicts
from v17_rebirth.backend.services.decision_compiler import compile_modifier_proposals
from v17_rebirth.backend.services.physics_layers import settle_modifier_proposals


def test_hydration_populates_liu_po_and_stem_fusion_meta() -> None:
    pt = {
        "four_pillars": {
            "year": "甲子",
            "month": "己酉",
            "day": "甲辰",
            "hour": "庚酉",
        },
        "luck_pillar": "丙午",
        "flow_pillar": "丁未",
        "ten_gods_absolute_intensity": {"比肩": 22.0, "正财": 19.0, "正官": 11.0},
        "total_energy_index": 80.0,
    }

    hydrate_v17_physics_tensor(pt)
    meta = pt.get("meta") or {}
    iv2 = meta.get("interaction_v2") or {}

    assert "liu_po" in iv2
    assert isinstance(iv2["liu_po"], list)
    assert "stem_fusion_v1" in meta


def test_condition_plugins_emit_condition_metadata() -> None:
    pt = {
        "four_pillars": {
            "year": "甲子",
            "month": "己酉",
            "day": "甲辰",
            "hour": "庚酉",
        },
        "luck_pillar": "丙午",
        "flow_pillar": "丁未",
        "ten_gods_base_l0": {"比肩": 30.0, "正财": 28.0, "正官": 18.0, "七杀": 12.0},
        "ten_gods_runtime": {"比肩": 30.0, "正财": 28.0, "正官": 18.0, "七杀": 12.0},
        "energy_meta": {"month_command_god": "正财", "season_power": {"month_branch": "酉"}},
        "meta": {
            "interaction_v2": {
                "liu_chong": [{"pair": ["子", "午"], "pillars": ["year", "luck"]}],
                "liu_hai": [],
                "liu_po": [{"pair": ["子", "酉"], "pillars": ["year", "month"]}],
                "liu_he": [{"pair": ["辰", "酉"], "pillars": ["day", "month"]}],
                "san_he": [],
                "ban_he": [],
                "sanxing": [],
            },
            "stem_fusion_v1": {
                "cases": [
                    {
                        "stems": ["甲", "己"],
                        "mode": "transformed",
                        "hua_element": "earth",
                        "month_stem_supports": True,
                        "branch_hua_ratio": 0.25,
                    }
                ]
            },
            "plugin_conflicts": [{"conflict_id": "c1"}],
            "plugin_conflict_resolutions": [{"resolution_id": "r1"}],
        },
    }

    facts = collect_all_spec_facts(pt)
    by_plugin = {str(f.plugin_id or ""): f for f in facts}

    assert by_plugin["l1.physics.op_branch_liuhe"].meta.get("condition_state") in {"supported", "contested"}
    assert 0.0 <= float(by_plugin["l1.physics.op_branch_liuhe"].meta.get("match_ratio", 0.0) or 0.0) <= 1.0
    assert by_plugin["l1.physics.op_stem_fusion"].meta.get("condition_trigger") == "month_support"
    assert 0.0 <= float(by_plugin["l1.physics.op_stem_fusion"].meta.get("match_ratio", 0.0) or 0.0) <= 1.0
    assert by_plugin["classical.conflict_auditor.v1"].meta.get("conflict_count") == 1


def test_contested_relation_fact_does_not_produce_modifier_proposal() -> None:
    facts = [
        V17Fact(
            plugin_id="l1.physics.op_branch_liuhe",
            text="六合成立但受冲争夺。",
            causal_tier=4,
            priority=0.8,
            meta={
                "target_god": "正官",
                "condition_state": "contested",
                "condition_blockers": ["liu_chong"],
            },
        )
    ]
    proposals = compile_modifier_proposals(facts=facts, physics_tensor={})
    assert proposals == []


def test_pattern_candidates_enter_conflict_layer_as_exclusive_family() -> None:
    facts = [
        V17Fact(
            plugin_id="classical.pattern.axis.v1",
            text="格局轴线候选：比肩当前为最强主轴。",
            causal_tier=3,
            priority=0.77,
            meta={
                "claim_type": "pattern_candidate",
                "entity_scope": "pattern",
                "exclusivity_key": "pattern_family",
                "source_event": "pattern_family",
                "confidence": 0.77,
            },
        ),
        V17Fact(
            plugin_id="classical.pattern.finance_officer.v1",
            text="格局候选：财官双线并举。",
            causal_tier=3,
            priority=0.73,
            meta={
                "claim_type": "pattern_candidate",
                "entity_scope": "pattern",
                "exclusivity_key": "pattern_family",
                "source_event": "pattern_family",
                "confidence": 0.73,
            },
        ),
    ]
    claims = compile_claims(facts=facts, physics_tensor={})
    conflicts = detect_claim_conflicts(claims)
    assert any(str(row.get("conflict_type") or "") == "pattern_family_exclusive" for row in conflicts)


def test_match_ratio_scales_modifier_proposal() -> None:
    facts = [
        V17Fact(
            plugin_id="l2.risk.risk_matrix",
            text="检测到伤官见官。",
            causal_tier=2,
            priority=0.9,
            meta={
                "target_god": "正官",
                "impact_ratio": -0.4,
                "match_ratio": 0.6,
            },
        )
    ]
    proposals = compile_modifier_proposals(facts=facts, physics_tensor={})
    assert len(proposals) == 1
    assert proposals[0]["raw_impact_ratio"] == -0.4
    assert proposals[0]["match_ratio"] == 0.6
    assert proposals[0]["impact_ratio"] == -0.24


def test_settlement_recomputes_from_base_scores() -> None:
    runtime_scores = {"正官": 40.0}
    base_scores = {"正官": 10.0}
    proposals = [
        {
            "plugin_id": "l2.risk.risk_matrix",
            "target_god": "正官",
            "impact_ratio": -0.2,
            "match_ratio": 1.0,
            "significance_weight": 1.0,
            "arbiter_type": "system",
        }
    ]
    settled, ratio_totals, applied = settle_modifier_proposals(
        runtime_scores,
        proposals,
        base_scores=base_scores,
    )
    assert ratio_totals["正官"] == -0.2
    assert settled["正官"] == 8.0
    assert applied[0]["before"] == 10.0
    assert applied[0]["delta_abs"] == -2.0


def test_diagnostic_claim_without_explicit_match_ratio_is_not_forced_to_full_score() -> None:
    facts = [
        V17Fact(
            plugin_id="classical.climate_adjuster.v1",
            text="调候提示：当前月令主气落在 伤官。",
            causal_tier=3,
            priority=0.82,
            salience_weight=0.82,
            meta={},
        )
    ]
    claims = compile_claims(facts=facts, physics_tensor={})
    assert len(claims) == 1
    assert 0.35 <= float(claims[0]["match_ratio"]) < 1.0
