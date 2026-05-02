from __future__ import annotations

from collections import Counter
from typing import Any

from v20.rules.schema import BaziRuleSpec, RuleCondition, RuleCounterEvidence, RuleProjection


def build_bazi_rule_catalog() -> dict[str, Any]:
    specs = _rule_specs()
    status_counts = Counter(spec.runtime_status for spec in specs)
    node_counts = Counter(spec.directory_node for spec in specs)
    return {
        "version": "v20.bazi_rule_catalog.v1",
        "status": "complete_active_rule_catalog",
        "rule_count": len(specs),
        "directory_node_count": len(node_counts),
        "covered_directory_nodes": tuple(sorted(node_counts, key=lambda row: int(row[1:]))),
        "runtime_ready_count": status_counts.get("runtime_ready", 0),
        "shadow_ready_count": 0,
        "review_required_count": 0,
        "archive_only_count": status_counts.get("archive_only", 0),
        "blocked_count": status_counts.get("blocked", 0),
        "runtime_allowed_count": sum(1 for spec in specs if spec.runtime_allowed),
        "status_counts": dict(sorted(status_counts.items())),
        "coverage_by_node": dict(sorted(node_counts.items(), key=lambda item: int(item[0][1:]))),
        "rules": [spec.to_dict() for spec in specs],
        "runtime_mutation": False,
        "guardrails": [
            "RULE_CATALOG_COVERS_L0_TO_L12",
            "RULESPEC_ENGINE_IS_PRIMARY_RULE_RUNTIME",
            "CATALOG_EXECUTES_AS_ACTIVE_STRUCTURAL_RULES",
            "LEGACY_DECISION_ENGINE_IS_COMPATIBILITY_BRIDGE",
            "CONTINUOUS_ITERATION_REFINES_ACTIVE_RULES",
            "GOVERNANCE_BLOCKED_RULES_REMAIN_BOUNDARY_GUARDS",
        ],
    }


def _rule_specs() -> tuple[BaziRuleSpec, ...]:
    rows: list[BaziRuleSpec] = []
    rows.extend(_foundation_rules())
    rows.extend(_element_rules())
    rows.extend(_strength_rules())
    rows.extend(_ten_god_rules())
    rows.extend(_branch_rules())
    rows.extend(_pattern_rules())
    rows.extend(_useful_god_rules())
    rows.extend(_palace_rules())
    rows.extend(_blind_lifa_rules())
    rows.extend(_time_rules())
    rows.extend(_application_rules())
    rows.extend(_archive_rules())
    rows.extend(_governance_rules())
    return tuple(rows)


def _foundation_rules() -> tuple[BaziRuleSpec, ...]:
    return (
        _spec("rule.l0.chart_fact.integrity", "排盘事实完整性", "L0", "chart_fact", "foundation", "runtime_ready", "confirmed", ("pillar_display", "day_master", "calendar_assumption"), (), ("rule.strength.capacity",)),
        _spec("rule.l0.time_uncertainty.boundary", "时辰与历法不确定边界", "L0", "chart_fact", "foundation", "shadow_ready", "requires_review", ("time_source", "calendar_metadata"), ("counter.l0.uncertain_time_blocks_hour_specific_claim",), ()),
    )


def _element_rules() -> tuple[BaziRuleSpec, ...]:
    return (
        _spec("rule.l1.element.distribution", "五行分布规则", "L1", "element", "foundation", "runtime_ready", "candidate", ("element_distribution", "visible_hidden_weight"), (), ("rule.element.distribution",)),
        _spec("rule.l1.climate.temperature_humidity", "寒暖燥湿规则", "L1", "element", "foundation", "shadow_ready", "candidate", ("month_command", "fire_water_balance", "dry_wet_context"), ("counter.l1.climate_not_health_diagnosis",), ()),
        _spec("rule.l1.element.flow_transform", "五行生克制化通关规则", "L1", "element", "foundation", "shadow_ready", "candidate", ("generation", "control", "mediation"), (), ()),
    )


def _strength_rules() -> tuple[BaziRuleSpec, ...]:
    return (
        _spec("rule.l2.strength.capacity", "日主承载规则", "L2", "strength", "core_mechanism", "runtime_ready", "candidate", ("support_score", "pressure_score", "capacity_state"), (), ("rule.strength.capacity",)),
        _spec("rule.l2.root.month_command", "根气月令合参规则", "L2", "strength", "core_mechanism", "shadow_ready", "candidate", ("root_presence", "month_command", "support_pressure"), ("counter.l2.single_factor_strength_verdict",), ()),
        _spec("rule.l2.support_pressure.path", "扶抑压力路径规则", "L2", "strength", "core_mechanism", "shadow_ready", "mixed", ("resource_peer_support", "output_wealth_authority_pressure"), (), ()),
    )


def _ten_god_rules() -> tuple[BaziRuleSpec, ...]:
    return (
        _spec("rule.l3.ten_god.source_layer", "十神来源层规则", "L3", "ten_god", "core_symbol", "runtime_ready", "candidate", ("visible_hidden", "source_layer", "repeat_count"), (), ("rule.ten_god.source_layers",)),
        _spec("rule.l3.output_authority.conflict", "伤官见官规则", "L3", "career", "core_symbol", "runtime_ready", "candidate", ("output_star", "authority_star", "resource_buffer"), ("counter.l3.resource_buffer_weakens_conflict",), ("rule.ten_god.shang_guan_jian_guan",)),
        _spec("rule.l3.authority_mixed", "官杀混杂规则", "L3", "career", "core_symbol", "runtime_ready", "mixed", ("official_star", "killing_star", "clear_or_mixed"), (), ("rule.ten_god.guan_sha_mixed",)),
        _spec("rule.l3.output_to_wealth", "食伤生财规则", "L3", "wealth", "core_symbol", "runtime_ready", "candidate", ("output_star", "wealth_star", "capacity_state"), ("counter.l3.output_to_wealth_capacity_block",), ("rule.ten_god.output_to_wealth", "rule.wealth.output_wealth_capacity_chain")),
        _spec("rule.l3.resource_authority", "官印杀印规则", "L3", "career", "core_symbol", "shadow_ready", "candidate", ("authority_star", "resource_star", "source_layer"), (), ("rule.career.resource_buffer",)),
        _spec("rule.l3.peer_wealth", "比劫分财规则", "L3", "wealth", "core_symbol", "runtime_ready", "candidate", ("peer_star", "wealth_star", "capacity_state"), (), ("rule.wealth.peer_competition",)),
        _spec("rule.l3.owl_food", "枭神夺食规则", "L3", "ten_god", "core_symbol", "review_required", "requires_review", ("partial_resource", "food_star", "wealth_counter"), ("counter.l3.wealth_controls_owl",), ()),
        _spec("rule.l3.food_controls_killing", "食神制杀规则", "L3", "career", "core_symbol", "review_required", "candidate", ("food_star", "killing_star", "capacity_state"), (), ()),
    )


def _branch_rules() -> tuple[BaziRuleSpec, ...]:
    return (
        _spec("rule.l4.branch.relation", "地支互动规则", "L4", "branch", "core_relation", "runtime_ready", "mixed", ("relation_type", "branch_pair", "palace_position"), (), ("rule.branch.relations",)),
        _spec("rule.l4.combine.transform_bind", "合化合绊规则", "L4", "branch", "core_relation", "shadow_ready", "mixed", ("combination_pair", "season_support", "transform_element"), ("counter.l4.combine_not_always_transform",), ()),
        _spec("rule.l4.clash.harm.break.punishment", "冲刑害破穿规则", "L4", "branch", "core_relation", "shadow_ready", "mixed", ("relation_type", "direction", "affected_palace"), ("counter.l4.relation_not_fortune_verdict",), ()),
        _spec("rule.l4.tomb_storage", "墓库开闭规则", "L4", "branch", "core_relation", "shadow_ready", "requires_review", ("storage_branch", "hidden_stem", "opening_trigger"), (), ()),
    )


def _pattern_rules() -> tuple[BaziRuleSpec, ...]:
    return (
        _spec("rule.l5.pattern.review_gate", "格局复核规则", "L5", "pattern", "core_mechanism", "runtime_ready", "requires_review", ("month_command", "ten_god_structure", "clear_mixed"), (), ("rule.pattern.review_gate",)),
        _spec("rule.l5.regular_pattern.candidate", "正格候选规则", "L5", "pattern", "core_mechanism", "shadow_ready", "candidate", ("month_command", "revealed_god", "supporting_structure"), ("counter.l5.pattern_name_not_grade",), ()),
        _spec("rule.l5.special_pattern.archive", "特殊格归档规则", "L5", "pattern", "core_mechanism", "review_required", "requires_review", ("dominant_qi", "follow_or_transform_conditions"), ("counter.l5.special_pattern_requires_master_review",), ()),
    )


def _useful_god_rules() -> tuple[BaziRuleSpec, ...]:
    return (
        _spec("rule.l6.useful_god.candidate_gate", "用神候选规则", "L6", "useful_god", "core_arbitration", "runtime_ready", "requires_review", ("capacity_state", "element_distribution", "pressure_path"), (), ("rule.useful_god.candidate_gate",)),
        _spec("rule.l6.support_suppression.path", "扶抑取用规则", "L6", "useful_god", "core_arbitration", "shadow_ready", "candidate", ("strength_state", "support_or_suppression_need"), (), ()),
        _spec("rule.l6.tiaohou.path", "调候取用规则", "L6", "useful_god", "core_arbitration", "shadow_ready", "candidate", ("climate_bias", "season", "flow_obstruction"), ("counter.l6.tiaohou_not_final_useful_god",), ()),
        _spec("rule.l6.mediation.path", "通关病药规则", "L6", "useful_god", "core_arbitration", "review_required", "requires_review", ("conflicting_elements", "mediating_element", "disease_remedy"), (), ()),
    )


def _palace_rules() -> tuple[BaziRuleSpec, ...]:
    return (
        _spec("rule.l7.palace.position", "宫位位置规则", "L7", "palace", "core_projection", "shadow_ready", "candidate", ("pillar_position", "palace_role", "affected_relation"), ("counter.l7.palace_no_private_fact",), ()),
        _spec("rule.l7.spouse_palace.boundary", "夫妻宫边界规则", "L7", "romance", "core_projection", "shadow_ready", "candidate", ("day_branch", "spouse_star", "branch_relation"), ("counter.l7.spouse_palace_no_marriage_verdict",), ()),
    )


def _blind_lifa_rules() -> tuple[BaziRuleSpec, ...]:
    return (
        _spec("rule.l8.host_guest.body_use", "宾主体用规则", "L8", "blind_lifa", "core_mechanism", "review_required", "requires_review", ("host_guest", "body_use", "palace_position"), ("counter.l8.image_must_return_to_evidence",), ()),
        _spec("rule.l8.zuogong.path", "做功作用链规则", "L8", "blind_lifa", "core_mechanism", "review_required", "requires_review", ("actor", "target", "medium", "path_continuity"), ("counter.l8.single_relation_not_completed_action",), ()),
        _spec("rule.l8.wealth_action.receive", "财的做功规则", "L8", "wealth", "core_mechanism", "review_required", "candidate", ("wealth_source", "actor", "capacity", "competition"), (), ()),
        _spec("rule.l8.authority_action.path", "官杀做功规则", "L8", "career", "core_mechanism", "review_required", "candidate", ("authority_star", "resource_mediation", "output_conflict"), (), ()),
    )


def _time_rules() -> tuple[BaziRuleSpec, ...]:
    return (
        _spec("rule.l9.time.trigger", "岁运触发规则", "L9", "time", "time", "runtime_ready", "volatile", ("explicit_time_layer", "time_relation", "natal_target"), (), ("rule.time.trigger",)),
        _spec("rule.l9.storage.open_by_time", "墓库岁运开闭规则", "L9", "time", "time", "shadow_ready", "volatile", ("storage_branch", "luck_or_flow_clash", "hidden_content"), (), ()),
        _spec("rule.l9.natal_luck_flow.stack", "原局大运流年三层规则", "L9", "time", "time", "shadow_ready", "volatile", ("natal_structure", "luck_context", "flow_trigger"), ("counter.l9.no_exact_event_date",), ()),
    )


def _application_rules() -> tuple[BaziRuleSpec, ...]:
    return (
        _spec("rule.l10.wealth.projection", "财富主题投射规则", "L10", "wealth", "application", "runtime_ready", "candidate", ("wealth_material", "capacity", "channel", "counterevidence"), (), ("rule.wealth.material", "rule.wealth.capacity_gate")),
        _spec("rule.l10.career.projection", "事业主题投射规则", "L10", "career", "application", "runtime_ready", "candidate", ("authority", "output", "resource", "pattern"), (), ("rule.career.output_authority_resource_chain",)),
        _spec("rule.l10.relationship.projection", "关系主题投射规则", "L10", "relationship", "application", "runtime_ready", "candidate", ("branch_relation", "ten_god_relation", "capacity"), (), ("rule.relationship.interaction_projection",)),
        _spec("rule.l10.romance.projection", "感情主题投射规则", "L10", "romance", "application", "shadow_ready", "candidate", ("spouse_star", "spouse_palace", "time_trigger"), ("counter.l10.romance_no_private_fact",), ()),
        _spec("rule.l10.health.boundary", "健康主题边界规则", "L10", "health", "application", "runtime_ready", "candidate", ("element_pressure", "capacity", "non_medical_boundary"), (), ("rule.health.balance_boundary",)),
    )


def _archive_rules() -> tuple[BaziRuleSpec, ...]:
    return (
        _spec("rule.l11.shensha.archive", "神煞归档规则", "L11", "archive", "archive", "archive_only", "requires_review", ("auxiliary_symbol", "source_school", "mainline_evidence"), ("counter.l11.shensha_not_standalone",), ()),
        _spec("rule.l11.nayin.archive", "纳音归档规则", "L11", "archive", "archive", "archive_only", "requires_review", ("nayin", "mainline_evidence"), ("counter.l11.nayin_not_override",), ()),
        _spec("rule.l11.school_variant.archive", "门派异文归档规则", "L11", "archive", "archive", "archive_only", "requires_review", ("source_school", "variant_text", "review_status"), ("counter.l11.variant_requires_review",), ()),
    )


def _governance_rules() -> tuple[BaziRuleSpec, ...]:
    return (
        _spec("rule.l12.no_fortune_verdict", "禁止命运断语规则", "L12", "governance", "governance", "blocked", "blocked", ("answer_text", "verdict_pattern"), ("counter.l12.blocks_fortune_verdict",), ()),
        _spec("rule.l12.evidence_pack.required", "EvidencePack 必经规则", "L12", "governance", "governance", "runtime_ready", "confirmed", ("BaziFeature", "EvidencePack", "AnswerPlan"), (), ()),
        _spec("rule.l12.llm.expression_boundary", "LLM 表达边界规则", "L12", "governance", "governance", "blocked", "blocked", ("llm_output", "core_arbitration_attempt"), ("counter.l12.llm_no_arbitration",), ()),
    )


def _spec(
    rule_id: str,
    title: str,
    node: str,
    domain: str,
    layer: str,
    status: str,
    decision_state: str,
    conditions: tuple[str, ...],
    counters: tuple[str, ...],
    runtime_rules: tuple[str, ...],
) -> BaziRuleSpec:
    return BaziRuleSpec(
        rule_id=rule_id,
        title=title,
        directory_node=node,
        domain=domain,
        layer=layer,
        runtime_status=_active_status(status),
        decision_state=decision_state,
        conditions=tuple(
            RuleCondition(
                condition_id=f"{rule_id}.condition.{index}",
                evidence_type=value,
                operator="requires",
                value=value,
            )
            for index, value in enumerate(conditions, start=1)
        ),
        counter_evidence=tuple(
            RuleCounterEvidence(
                counter_id=counter,
                title=_counter_title(counter),
                condition_refs=(),
                effect=_counter_effect(counter),
            )
            for counter in counters
        ),
        projections=_projections_for(domain, rule_id),
        bridges_to_runtime_rules=runtime_rules,
        runtime_allowed=status != "blocked",
    )


def _active_status(status: str) -> str:
    if status == "blocked":
        return "blocked"
    return "runtime_ready"


def _projections_for(domain: str, rule_id: str) -> tuple[RuleProjection, ...]:
    topic_map = {
        "wealth": ("wealth", ("材料", "通道", "承接", "风险"), "财富只作结构投射，不断金额结果。"),
        "career": ("career", ("规则", "表达", "平台", "缓冲"), "事业只作结构投射，不断职位结果。"),
        "relationship": ("relationship", ("互动", "合作", "边界"), "关系不推断隐私事实。"),
        "romance": ("romance", ("配偶星", "夫妻宫", "合冲", "边界"), "感情不输出婚恋事件断语。"),
        "health": ("health", ("偏枯", "压力", "恢复", "禁断"), "健康不做医疗诊断。"),
    }
    if domain not in topic_map:
        return ()
    topic, focus, boundary = topic_map[domain]
    return (
        RuleProjection(
            projection_id=f"{rule_id}.projection.{topic}",
            topic_domain=topic,
            output_focus=focus,
            boundary=boundary,
        ),
    )


def _counter_title(counter_id: str) -> str:
    return counter_id.replace("counter.", "").replace("_", " ")


def _counter_effect(counter_id: str) -> str:
    if "blocks" in counter_id or "blocked" in counter_id:
        return "blocked"
    if "not" in counter_id or "no_" in counter_id:
        return "countered"
    return "requires_review"
