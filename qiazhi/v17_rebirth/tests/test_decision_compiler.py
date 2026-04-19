from __future__ import annotations

from v17_rebirth.backend.plugins.spec import ArbiterType
from v17_rebirth.backend.logic.L1_atomic_ops.l1_meta_hydration import _manifest_hits_to_decision_rows
from v17_rebirth.backend.plugins.spec import V17Fact
from v17_rebirth.backend.services.plugin_display import plugin_display_profile
from v17_rebirth.backend.services.decision_compiler import compile_decision_arbitration, compile_modifier_proposals, compile_pending_decisions
from v17_rebirth.backend.services.target_god_resolver import infer_target_god_from_text, resolve_target_god


def test_compile_pending_decisions_backfills_target_god_from_physical_impact() -> None:
    rows = compile_pending_decisions(
        facts=[],
        spec_decisions=[],
        existing_rows=[
            {
                "id": "d1",
                "source": "l1.physics.op_branch_liuchong",
                "label": "六冲",
                "title": "检测到地支六冲",
                "priority": 0.8,
                "physical_impact": {
                    "target_god": "七杀",
                    "impact_ratio": 0.12,
                    "significance_weight": 1.0,
                },
            }
        ],
    )
    assert rows
    assert rows[0]["target_god"] == "七杀"
    assert rows[0]["physical_impact"]["target_god"] == "七杀"


def test_manifest_hits_rows_use_last_facts_as_title() -> None:
    rows = _manifest_hits_to_decision_rows(
        {
            "l1.physics.op_branch_liuchong": {
                "plugin_id": "l1.physics.op_branch_liuchong",
                "label": "六冲",
                "priority": 0.72,
                "activated": True,
                "last_facts": ["检测到地支六冲 [戌辰]：局部结构对撞。"],
            }
        }
    )
    assert len(rows) == 1
    assert rows[0]["label"] == "六冲"
    assert "六冲" in rows[0]["title"]


def test_compile_pending_decisions_infers_hint_from_fact_meta() -> None:
    rows = compile_pending_decisions(
        facts=[
            V17Fact(
                plugin_id="l1.physics.op_branch_liuhe",
                text="检测到地支六合 [午未]：资源稳定绑定，正财 能级提升 15%。",
                causal_tier=4,
                priority=0.78,
                meta={"impact_ratio": 0.15, "target_god": "正财"},
            )
        ],
        spec_decisions=[],
        existing_rows=[],
    )
    assert len(rows) == 1
    assert rows[0]["label"] == "六合"
    assert rows[0]["target_god"] == "正财"


def test_infer_target_god_from_text_detects_embedded_ten_god() -> None:
    assert infer_target_god_from_text("资源稳定绑定，正财 能级提升 15%。") == "正财"


def test_compile_pending_decisions_infers_target_god_from_title_text() -> None:
    rows = compile_pending_decisions(
        facts=[],
        spec_decisions=[],
        existing_rows=[
            {
                "id": "d2",
                "source": "l1.physics.op_branch_liuhe",
                "label": "六合",
                "title": "检测到地支六合：资源稳定绑定，正财 能级提升 15%。",
                "priority": 0.78,
            }
        ],
    )
    assert len(rows) == 1
    assert rows[0]["target_god"] == "正财"
    assert rows[0]["physical_impact"]["target_god"] == "正财"


def test_resolve_target_god_from_branch_and_day_master() -> None:
    resolved = resolve_target_god(
        title="检测到地支六合 [午未]：资源稳定绑定。",
        plugin_id="l1.physics.op_branch_liuhe",
        physics_tensor={
            "four_pillars": {"day": "壬戌"},
            "day_master_stem": "壬",
        },
    )
    assert resolved == "正财"


def test_compile_pending_decisions_uses_physics_tensor_for_dynamic_target() -> None:
    rows = compile_pending_decisions(
        facts=[],
        spec_decisions=[],
        existing_rows=[
            {
                "id": "d3",
                "source": "l1.physics.op_branch_liuhe",
                "plugin_id": "l1.physics.op_branch_liuhe",
                "label": "六合",
                "title": "检测到地支六合 [午未]：资源稳定绑定。",
                "priority": 0.78,
            }
        ],
        physics_tensor={
            "four_pillars": {"day": "壬戌"},
            "day_master_stem": "壬",
        },
    )
    assert len(rows) == 1
    assert rows[0]["target_god"] == "正财"


def test_compile_decision_arbitration_splits_manual_and_llm() -> None:
    arbitration = compile_decision_arbitration(
        facts=[],
        spec_decisions=[],
        existing_rows=[
            {
                "id": "manual_1",
                "source": "l1.physics.op_branch_liuhe",
                "label": "六合",
                "title": "检测到地支六合 [午未]：资源稳定绑定，正财 能级提升 15%。",
                "priority": 0.78,
                "target_god": "正财",
                "physical_impact": {"target_god": "正财", "impact_ratio": 0.15},
            },
            {
                "id": "llm_1",
                "source": "classical.wangshuai.v1",
                "label": "状态机节律",
                "title": "日主 壬 位处「墓」位，抗性系数 1.0。",
                "priority": 0.85,
                "physical_impact": {},
            },
        ],
    )
    assert len(arbitration["manual_decisions"]) == 1
    assert arbitration["manual_decisions"][0]["label"] == "六合"
    assert arbitration["manual_decisions"][0]["arbitration_trace"] == "六合协同 -> L? -> 手动"
    assert len(arbitration["llm_arbitration_context"]) == 1
    assert arbitration["llm_arbitration_context"][0]["label"] == "状态机节律"
    assert arbitration["llm_arbitration_context"][0]["arbitration_trace"] == "旺衰框架 -> L? -> LLM"
    assert arbitration["llm_arbitration_context"][0]["llm_resolution_policy"] == "context_only"
    assert arbitration["llm_arbitration_context"][0]["llm_resolution_state"] == "pending_context"
    assert arbitration["llm_arbitration_context"][0]["llm_resolution_result"] == "consume_context"
    assert arbitration["llm_arbitration_context"][0]["llm_terminal_state"] == "consume_context"


def test_plugin_display_profile_prefers_human_readable_name() -> None:
    profile = plugin_display_profile(
        plugin_id="l1.physics.op_branch_sanhe",
        manifest={
            "Description": "地支三合/半合全十神通用协同性算法。",
            "Rationale": "量化合局中的能量聚变与资源绑定过程。",
        },
    )
    assert profile["display_name"] == "三合成局"
    assert "地支三合" in profile["display_definition"]
    assert "能量聚变" in profile["display_description"]


def test_compile_decision_arbitration_assigns_llm_auto_apply_policy_for_low_risk_targeted_item() -> None:
    arbitration = compile_decision_arbitration(
        facts=[],
        spec_decisions=[],
        existing_rows=[
            {
                "id": "llm_auto_1",
                "source": "classical.flow.report",
                "label": "流转报告",
                "title": "流转报告：正财 能级微调 6%，建议小幅收敛。",
                "priority": 0.62,
                "physical_impact": {"target_god": "正财", "impact_ratio": 0.06, "intensity_level": 2},
            }
        ],
    )
    assert arbitration["llm_arbitration_context"] == []
    assert arbitration["auto_resolutions"][0]["resolved_from_llm"] is True
    assert arbitration["auto_resolutions"][0]["llm_resolution_state"] == "collapsed_to_system"
    assert "LLM裁决" in arbitration["auto_resolutions"][0]["arbitration_trace"]


def test_compile_decision_arbitration_promotes_llm_suggest_only_item_to_manual() -> None:
    arbitration = compile_decision_arbitration(
        facts=[],
        spec_decisions=[],
        existing_rows=[
            {
                "id": "llm_suggest_1",
                "source": "classical.flow.review",
                "label": "边界复核报告",
                "title": "边界复核报告：七杀 目标明确，但仍需你确认执行边界。",
                "priority": 0.71,
                "physical_impact": {"target_god": "七杀", "impact_ratio": 0.12, "intensity_level": 3},
            }
        ],
    )
    assert arbitration["llm_arbitration_context"] == []
    assert arbitration["manual_decisions"][0]["resolved_from_llm"] is True
    assert arbitration["manual_decisions"][0]["llm_resolution_state"] == "promoted_to_manual"
    assert "LLM裁决" in arbitration["manual_decisions"][0]["arbitration_trace"]


def test_compile_decision_arbitration_does_not_reseed_manual_relation_into_llm() -> None:
    arbitration = compile_decision_arbitration(
        facts=[
            V17Fact(
                plugin_id="l1.physics.op_branch_liuhe",
                text="检测到地支六合 [午未]：资源稳定绑定，正财 能级提升 15%。",
                causal_tier=4,
                priority=0.78,
                meta={"impact_ratio": 0.15, "target_god": "正财"},
            )
        ],
        spec_decisions=[],
        existing_rows=[],
    )
    assert len(arbitration["manual_decisions"]) == 1
    assert arbitration["manual_decisions"][0]["label"] == "六合"
    assert arbitration["llm_arbitration_context"] == []


def test_compile_modifier_proposals_preserves_low_tier_system_auto_apply() -> None:
    proposals = compile_modifier_proposals(
        facts=[
            V17Fact(
                plugin_id="l0.physics.auto_boost",
                text="底层自动校正：七杀 能级提升 20%。",
                causal_tier=0,
                suggested_arbiter=ArbiterType.SYSTEM,
                meta={"impact_ratio": 0.2, "target_god": "七杀", "significance_weight": 1.0},
            )
        ],
        physics_tensor={"ten_gods_base_l0": {"七杀": 10.0}},
    )
    assert len(proposals) == 1
    assert proposals[0]["arbiter_type"] == "system"
    assert proposals[0]["target_god"] == "七杀"
    assert proposals[0]["impact_ratio"] == 0.2


def test_compile_modifier_proposals_demotes_nonzero_tier_system_to_user() -> None:
    proposals = compile_modifier_proposals(
        facts=[
            V17Fact(
                plugin_id="l2.structure.review",
                text="结构提示：正财 需要人工确认。",
                causal_tier=2,
                suggested_arbiter=ArbiterType.SYSTEM,
                meta={"impact_ratio": 0.15, "target_god": "正财"},
            )
        ],
        physics_tensor={"ten_gods_base_l0": {"正财": 10.0}},
    )
    assert len(proposals) == 1
    assert proposals[0]["arbiter_type"] == "user"


def test_compile_modifier_proposals_tracks_claim_id_for_conflict_join() -> None:
    proposals = compile_modifier_proposals(
        facts=[
            V17Fact(
                plugin_id="l1.physics.op_branch_liuhe",
                text="检测到地支六合：正财 能级提升 15%。",
                causal_tier=4,
                suggested_arbiter=ArbiterType.SYSTEM,
                meta={"impact_ratio": 0.15, "target_god": "正财"},
            )
        ],
        physics_tensor={"ten_gods_base_l0": {"正财": 10.0}},
    )
    assert proposals[0]["claim_id"] == "l1.physics.op_branch_liuhe_claim_0"
