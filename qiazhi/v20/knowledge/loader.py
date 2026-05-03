from __future__ import annotations

import json
from itertools import chain
from pathlib import Path
from collections import OrderedDict
from collections.abc import Iterable

from v20.interaction.questions import QUESTION_LABELS
from v20.knowledge.schema import (
    KnowledgeAnswerGuidance,
    KnowledgePortraitMapping,
    KnowledgeQuestionMapping,
    KnowledgeRuleAtom,
    KnowledgeUnit,
)
from v20.knowledge.draft_import import _seed_paths


_DEFAULT_KNOWLEDGE_DRAFT_ROOT = Path(__file__).resolve().parents[2] / "docs" / "bazi_knowledge"


def default_knowledge_units() -> tuple[KnowledgeUnit, ...]:
    core_units = (
        KnowledgeUnit(
            "v20.core.strength_boundary",
            "Strength evidence boundary",
            "strength",
            "Day-master capacity should be explained through support, pressure, and uncertainty evidence.",
            "Use support score, pressure score, and source-layer evidence before naming any capacity tendency.",
            "Do not hard-judge strong or weak in Phase 1.",
            source_refs=("docs/v20.prestart.strength",),
            feature_hooks=("feature.strength",),
            question_hooks=("q_strength_assessment",),
            rule_atoms=(
                KnowledgeRuleAtom(
                    "strength.support_pressure.required",
                    "strength_evidence_gate",
                    "requires",
                    "support_score+pressure_score+source_layers",
                    "condition",
                    0.82,
                ),
            ),
            portrait_mappings=(
                KnowledgePortraitMapping(
                    "portrait.day_master_capacity",
                    "日主承载力",
                    "strength",
                    "围绕扶助、压力和来源层级判断日主承载状态。",
                    "warm",
                    from_rule_atoms=("strength.support_pressure.required",),
                    question_seeds=("这个八字日主偏强还是偏弱，适合先看什么？",),
                ),
            ),
            question_mappings=(
                KnowledgeQuestionMapping(
                    "q_strength_assessment",
                    "这个八字日主偏强还是偏弱，适合先看什么？",
                    "strength",
                    trigger_rule_atoms=("strength.support_pressure.required",),
                ),
            ),
            answer_guidance=(
                KnowledgeAnswerGuidance(
                    "answer.strength.boundary",
                    "strength",
                    "先解释扶助和压力来源，再说明是否需要命理师裁决。",
                    allowed_phrases=("扶助", "压力", "承载力", "待复核"),
                    forbidden_phrases=("一定身强", "一定身弱", "必然发财"),
                    boundary="Do not hard-judge strong or weak in Phase 1.",
                ),
            ),
        ),
        KnowledgeUnit(
            "v20.core.branch_relation_boundary",
            "Branch relation boundary",
            "branch",
            "Branch relations identify visible structural interactions and must be layer-aware.",
            "Name the relation type and branches; explain that relation names alone do not imply good or bad outcomes.",
            "Do not infer fortune from clash, harmony, punishment, harm, break, three harmony, or three meeting.",
            source_refs=("docs/v20.prestart.branch",),
            feature_hooks=("feature.branch",),
            question_hooks=("q_branch_relation_detail",),
            rule_atoms=(
                KnowledgeRuleAtom(
                    "branch.visible_relation.layer",
                    "branch_relation_gate",
                    "requires",
                    "relation_type+branches+source_layer",
                    "condition",
                    0.75,
                ),
            ),
            portrait_mappings=(
                KnowledgePortraitMapping(
                    "portrait.branch_interaction",
                    "地支互动层",
                    "branch",
                    "先说明冲合刑害会牵动哪一层结构，不直接定吉凶。",
                    "hot",
                    from_rule_atoms=("branch.visible_relation.layer",),
                    question_seeds=("地支互动会先影响哪一类事情？",),
                ),
            ),
            question_mappings=(
                KnowledgeQuestionMapping(
                    "q_branch_relation_detail",
                    "地支互动会先影响哪一类事情？",
                    "branch",
                    trigger_rule_atoms=("branch.visible_relation.layer",),
                ),
            ),
        ),
        KnowledgeUnit(
            "v20.core.time_layer_boundary",
            "Time layer boundary",
            "time",
            "Time layers can describe explicit luck or flow pillar interaction with the natal chart.",
            "Use only supplied time pillars, time ten-god labels, and time-to-natal relation hits as evidence.",
            "Do not infer exact dates, fixed events, guaranteed timing, or calendar facts that were not supplied.",
            source_refs=("docs/v20.prestart.time_layer",),
            feature_hooks=("feature.time",),
            question_hooks=("q_time_layer_context", "q_time_relation_triggers"),
            retrieval_tags=("time_layer", "flow_year", "luck"),
            rule_atoms=(
                KnowledgeRuleAtom(
                    "time.explicit_layer.required",
                    "time_layer_gate",
                    "requires",
                    "supplied_luck_or_flow_pillar+time_to_natal_relation",
                    "condition",
                    0.78,
                ),
            ),
            portrait_mappings=(
                KnowledgePortraitMapping(
                    "portrait.time_trigger",
                    "大运流年牵动",
                    "time",
                    "只把大运流年作为触发背景，回到原局结构判断牵动位置。",
                    "hot",
                    from_rule_atoms=("time.explicit_layer.required",),
                    question_seeds=("流年大运会先牵动原局哪一块？",),
                ),
            ),
            question_mappings=(
                KnowledgeQuestionMapping(
                    "q_time_relation_triggers",
                    "流年大运会先牵动原局哪一块？",
                    "time",
                    trigger_rule_atoms=("time.explicit_layer.required",),
                ),
            ),
        ),
        KnowledgeUnit(
            "v20.core.wealth_material_boundary",
            "Wealth material boundary",
            "wealth",
            "Wealth ten-god material can describe structural availability, source layer, and constraints.",
            "Use visible/hidden wealth ten-god evidence and relation context as structural material only.",
            "Do not predict wealth events, amounts, gains, losses, or timing.",
            source_refs=("docs/v20.prestart.wealth",),
            feature_hooks=("feature.wealth",),
            question_hooks=("q_income_stability",),
            rule_atoms=(
                KnowledgeRuleAtom(
                    "wealth.material.source_layer",
                    "wealth_material_gate",
                    "requires",
                    "visible_or_hidden_wealth+capacity+relation_context",
                    "condition",
                    0.74,
                ),
            ),
            portrait_mappings=(
                KnowledgePortraitMapping(
                    "portrait.wealth_structure",
                    "财星与收入结构",
                    "wealth",
                    "先看财星材料在哪里、能不能承载、有没有通道或限制。",
                    "hot",
                    from_rule_atoms=("wealth.material.source_layer",),
                    question_seeds=("财星能不能用，要先看日主承载还是结构通道？",),
                ),
            ),
            question_mappings=(
                KnowledgeQuestionMapping(
                    "q_income_stability",
                    "财星能不能用，要先看日主承载还是结构通道？",
                    "wealth",
                    trigger_rule_atoms=("wealth.material.source_layer",),
                ),
            ),
        ),
        KnowledgeUnit(
            "v20.applied.career_projection_boundary",
            "Career projection boundary",
            "career",
            "Career readings are applied-domain projections over ten-god, pattern, strength, and branch features.",
            "Use role structure, authority-output relation, and constraint/support paths only when source features are present.",
            "Do not predict promotion, job loss, salary, title, or guaranteed workplace events.",
            source_refs=("docs/v20.prestart.career",),
            feature_hooks=("feature.ten_god", "feature.pattern", "feature.strength", "feature.branch"),
            question_hooks=("q_career_structure",),
            retrieval_tags=("applied_domain", "career", "projection"),
            rule_atoms=(
                KnowledgeRuleAtom(
                    "career.authority_output.pressure",
                    "career_domain_projection",
                    "requires_any",
                    "authority_star|output_star|pattern|branch_interaction",
                    "domain_projection",
                    0.72,
                ),
            ),
            portrait_mappings=(
                KnowledgePortraitMapping(
                    "portrait.career_structure",
                    "事业角色与工作结构",
                    "career",
                    "用官杀、食伤、印星和格局材料判断事业表达、规则压力和缓冲。",
                    "warm",
                    from_rule_atoms=("career.authority_output.pressure",),
                    question_seeds=("伤官见官是否被印星缓冲？",),
                ),
            ),
            question_mappings=(
                KnowledgeQuestionMapping(
                    "q_career_structure",
                    "伤官见官是否被印星缓冲？",
                    "career",
                    trigger_rule_atoms=("career.authority_output.pressure",),
                ),
            ),
        ),
        KnowledgeUnit(
            "v20.applied.relationship_projection_boundary",
            "Relationship projection boundary",
            "relationship",
            "Relationship readings are applied-domain projections over interaction and ten-god structure.",
            "Use visible/hidden relation material and branch interaction as context for relationship questions.",
            "Do not predict marriage, divorce, partner identity, private partner facts, or guaranteed relationship events.",
            source_refs=("docs/v20.prestart.relationship",),
            feature_hooks=("feature.ten_god", "feature.branch", "feature.strength"),
            question_hooks=("q_relationship_structure",),
            retrieval_tags=("applied_domain", "relationship", "projection"),
            rule_atoms=(
                KnowledgeRuleAtom(
                    "relationship.interaction.structure",
                    "relationship_domain_projection",
                    "requires_any",
                    "branch_interaction|ten_god_relation|capacity_context",
                    "domain_projection",
                    0.68,
                ),
            ),
            portrait_mappings=(
                KnowledgePortraitMapping(
                    "portrait.relationship_structure",
                    "关系互动结构",
                    "relationship",
                    "用互动、约束、承接和十神关系解释关系主题边界。",
                    "cool",
                    from_rule_atoms=("relationship.interaction.structure",),
                    question_seeds=("关系结构里更明显的是互动、约束还是承接？",),
                ),
            ),
            question_mappings=(
                KnowledgeQuestionMapping(
                    "q_relationship_structure",
                    "关系结构里更明显的是互动、约束还是承接？",
                    "relationship",
                    trigger_rule_atoms=("relationship.interaction.structure",),
                ),
            ),
        ),
        KnowledgeUnit(
            "v20.applied.health_projection_boundary",
            "Health projection boundary",
            "health",
            "Health-adjacent readings are limited to five-element balance and stress-boundary context.",
            "Use strength, branch, and pattern features only to discuss structural balance boundaries.",
            "Do not diagnose, predict disease, recommend treatment, or replace medical advice.",
            source_refs=("docs/v20.prestart.health",),
            feature_hooks=("feature.strength", "feature.branch", "feature.pattern"),
            question_hooks=("q_health_balance_boundary",),
            retrieval_tags=("applied_domain", "health", "projection"),
            rule_atoms=(
                KnowledgeRuleAtom(
                    "health.balance.boundary",
                    "health_boundary_gate",
                    "requires",
                    "element_balance+stress_boundary+non_medical_language",
                    "safety_boundary",
                    0.86,
                    boundary="Do not diagnose, predict disease, recommend treatment, or replace medical advice.",
                ),
            ),
            portrait_mappings=(
                KnowledgePortraitMapping(
                    "portrait.health_balance_boundary",
                    "身心平衡边界",
                    "health",
                    "只讨论五行平衡和压力边界，不做医疗判断。",
                    "cool",
                    from_rule_atoms=("health.balance.boundary",),
                    question_seeds=("五行偏枯主要提示哪种平衡压力？",),
                ),
            ),
            question_mappings=(
                KnowledgeQuestionMapping(
                    "q_health_balance_boundary",
                    "五行偏枯主要提示哪种平衡压力？",
                    "health",
                    trigger_rule_atoms=("health.balance.boundary",),
                ),
            ),
        ),
        KnowledgeUnit(
            "v20.core.useful_god_gate",
            "Useful-god evidence gate",
            "useful_god",
            "Useful-god discussion requires candidate paths and explicit evidence gates.",
            "Explain whether support, output, constraint, or unresolved evidence paths are present.",
            "Do not state fixed favorable or unfavorable gods in Phase 1.",
            source_refs=("docs/v20.prestart.useful_god",),
            feature_hooks=("feature.useful_god",),
            question_hooks=("q_useful_god_candidates", "q_useful_god_evidence_gaps"),
            retrieval_tags=("candidate_path", "evidence_gate", "arbitration"),
            rule_atoms=(
                KnowledgeRuleAtom(
                    "useful_god.candidate_paths.required",
                    "useful_god_evidence_gate",
                    "requires",
                    "capacity+element_distribution+structural_pressure",
                    "candidate_gate",
                    0.8,
                ),
            ),
            portrait_mappings=(
                KnowledgePortraitMapping(
                    "portrait.useful_god_candidates",
                    "用神候选路径",
                    "useful_god",
                    "先列候选路径和证据缺口，不把候选直接定为喜忌。",
                    "warm",
                    from_rule_atoms=("useful_god.candidate_paths.required",),
                    question_seeds=("哪些用神路径可以作为候选？",),
                ),
            ),
            question_mappings=(
                KnowledgeQuestionMapping(
                    "q_useful_god_candidates",
                    "哪些用神路径可以作为候选？",
                    "useful_god",
                    trigger_rule_atoms=("useful_god.candidate_paths.required",),
                ),
            ),
        ),
        KnowledgeUnit(
            "v20.core.useful_god_candidate_paths",
            "Useful-god candidate paths",
            "useful_god",
            "Candidate paths are derived from capacity, element distribution, and structural pressure only.",
            "Name candidate path types such as support, release, channel, constraint, or evidence gap.",
            "Do not convert a candidate path into fixed favorable or unfavorable gods without validation.",
            source_refs=("docs/v20.useful_god_candidates",),
            feature_hooks=("feature.useful_god.candidate_paths",),
            question_hooks=("q_useful_god_candidates", "q_useful_god_evidence_gaps"),
            retrieval_tags=("candidate_path", "element_distribution", "strength_capacity"),
            rule_atoms=(
                KnowledgeRuleAtom(
                    "useful_god.paths.capacity_element_pressure",
                    "useful_god_path_gate",
                    "requires",
                    "capacity+element_distribution+pressure_path",
                    "candidate_gate",
                    0.79,
                ),
            ),
            portrait_mappings=(
                KnowledgePortraitMapping(
                    "portrait.useful_god_path_review",
                    "用神路径复核",
                    "useful_god",
                    "把扶助、泄秀、通关、制约等作为候选路径逐条复核。",
                    "warm",
                    from_rule_atoms=("useful_god.paths.capacity_element_pressure",),
                    question_seeds=("用神判断现在还缺哪类证据？",),
                ),
            ),
            question_mappings=(
                KnowledgeQuestionMapping(
                    "q_useful_god_evidence_gaps",
                    "用神判断现在还缺哪类证据？",
                    "useful_god",
                    trigger_rule_atoms=("useful_god.paths.capacity_element_pressure",),
                ),
            ),
        ),
        KnowledgeUnit(
            "v20.core.ten_god_boundary",
            "Ten-god interpretation boundary",
            "ten_god",
            "Ten-god labels describe relation type and source layer before any applied domain reading.",
            "Name whether the relation is visible or hidden, then keep it as structural material unless a verified feature connects it to a question.",
            "Do not convert ten-god labels directly into personality, career, money, relationship, or health conclusions.",
            source_refs=("docs/v20.prestart.ten_god",),
            feature_hooks=("feature.ten_god",),
            question_hooks=("q_ten_god_focus", "q_hidden_stem_role", "q_ten_god_metadata"),
            retrieval_tags=("visible", "hidden", "relation_label"),
            rule_atoms=(
                KnowledgeRuleAtom(
                    "ten_god.visible_hidden.layer",
                    "ten_god_layer_gate",
                    "requires",
                    "visible_or_hidden+relation_label+source_layer",
                    "condition",
                    0.76,
                ),
            ),
            portrait_mappings=(
                KnowledgePortraitMapping(
                    "portrait.ten_god_roles",
                    "十神角色分布",
                    "ten_god",
                    "先区分明透和藏干，再判断十神在主题里的结构作用。",
                    "warm",
                    from_rule_atoms=("ten_god.visible_hidden.layer",),
                    question_seeds=("藏干和明透分别承担什么结构作用？",),
                ),
            ),
            question_mappings=(
                KnowledgeQuestionMapping(
                    "q_hidden_stem_role",
                    "藏干和明透分别承担什么结构作用？",
                    "ten_god",
                    trigger_rule_atoms=("ten_god.visible_hidden.layer",),
                ),
            ),
        ),
        KnowledgeUnit(
            "v20.core.element_distribution_boundary",
            "Five-element distribution boundary",
            "element",
            "Five-element distribution describes structural balance, concentration, and gaps before applied readings.",
            "Use visible stems and hidden-stem weights to name distribution tendencies and evidence boundaries.",
            "Do not convert element imbalance directly into health diagnosis, fixed fortune, or guaranteed events.",
            source_refs=("docs/v20.prestart.element_distribution",),
            feature_hooks=("feature.element",),
            question_hooks=("q_element_balance", "q_element_support_pressure"),
            retrieval_tags=("five_element", "balance", "foundation"),
            rule_atoms=(
                KnowledgeRuleAtom(
                    "element.distribution.balance",
                    "element_distribution_gate",
                    "requires",
                    "visible_stems+hidden_stem_weights+support_pressure",
                    "condition",
                    0.73,
                ),
            ),
            portrait_mappings=(
                KnowledgePortraitMapping(
                    "portrait.element_balance",
                    "五行分布",
                    "element",
                    "先看五行集中、偏枯、支持和压力，再进入具体主题。",
                    "warm",
                    from_rule_atoms=("element.distribution.balance",),
                    question_seeds=("五行偏向会让这个盘更需要哪种平衡？",),
                ),
            ),
            question_mappings=(
                KnowledgeQuestionMapping(
                    "q_element_balance",
                    "五行偏向会让这个盘更需要哪种平衡？",
                    "element",
                    trigger_rule_atoms=("element.distribution.balance",),
                ),
            ),
        ),
        KnowledgeUnit(
            "v20.core.pattern_review_boundary",
            "Pattern review boundary",
            "pattern",
            "Pattern material is a review index that needs rule-path and evidence arbitration.",
            "Use pattern evidence to open a structured review path, not to name a final pattern prematurely.",
            "Do not declare a fixed pattern, grade, or outcome from a preliminary index.",
            source_refs=("docs/v20.prestart.pattern",),
            feature_hooks=("feature.pattern",),
            question_hooks=("q_pattern_structure",),
            retrieval_tags=("review_index", "arbitration", "rule_path"),
            rule_atoms=(
                KnowledgeRuleAtom(
                    "pattern.review.evidence_path",
                    "pattern_review_gate",
                    "requires",
                    "pattern_evidence+rule_path+arbitration",
                    "review_gate",
                    0.77,
                ),
            ),
            portrait_mappings=(
                KnowledgePortraitMapping(
                    "portrait.pattern_review",
                    "格局复核",
                    "pattern",
                    "把格局当作复核路径，不提前定格局等级或成败。",
                    "warm",
                    from_rule_atoms=("pattern.review.evidence_path",),
                    question_seeds=("格局和命格需要先复核哪条证据？",),
                ),
            ),
            question_mappings=(
                KnowledgeQuestionMapping(
                    "q_pattern_structure",
                    "格局和命格需要先复核哪条证据？",
                    "pattern",
                    trigger_rule_atoms=("pattern.review.evidence_path",),
                ),
            ),
        ),
        KnowledgeUnit(
            "v20.core.strength_root_month_command",
            "Strength root and month-command review",
            "strength",
            "Day-master capacity needs root, month-command seasonality, support, and pressure to be reviewed together.",
            "Use root presence, month-command support, support score, and pressure score before changing the strength lane.",
            "Do not decide strength from one visible stem or one ten-god label.",
            source_refs=("docs/v20.knowledge.strength_root_month_command",),
            feature_hooks=("feature.strength", "feature.element"),
            question_hooks=("q_strength_assessment",),
            retrieval_tags=("root", "month_command", "capacity", "strength"),
            rule_atoms=(
                KnowledgeRuleAtom(
                    "strength.root_month.capacity_review",
                    "strength_arbitration_gate",
                    "requires",
                    "root_presence+month_command+support_pressure",
                    "condition",
                    0.81,
                ),
            ),
            portrait_mappings=(
                KnowledgePortraitMapping(
                    "portrait.strength_root_review",
                    "日主根气与月令复核",
                    "strength",
                    "把根气、月令、扶助和压力放在一起复核日主承载力。",
                    "warm",
                    from_rule_atoms=("strength.root_month.capacity_review",),
                    question_seeds=("日主强弱要先看根气、月令还是扶助压力？",),
                ),
            ),
            question_mappings=(
                KnowledgeQuestionMapping(
                    "q_strength_assessment",
                    "日主强弱要先看根气、月令还是扶助压力？",
                    "strength",
                    trigger_rule_atoms=("strength.root_month.capacity_review",),
                ),
            ),
            answer_guidance=(
                KnowledgeAnswerGuidance(
                    "answer.strength.root_month",
                    "strength",
                    "先拆根气和月令，再合并扶助压力，最后给出待裁决状态。",
                    allowed_phrases=("根气", "月令", "扶助", "压力", "承载"),
                    forbidden_phrases=("单凭一个字就定身强", "单凭一个字就定身弱"),
                    boundary="Strength review must combine multiple evidence layers.",
                ),
            ),
        ),
        KnowledgeUnit(
            "v20.core.ten_god_source_priority",
            "Ten-god source priority",
            "ten_god",
            "Visible ten-gods, hidden ten-gods, and repeated roles should be weighed by source layer before applied reading.",
            "Separate visible stems, hidden stems, repeated roles, and relation to day-master before projecting meaning.",
            "Do not turn a repeated ten-god into a personality or life-event verdict.",
            source_refs=("docs/v20.knowledge.ten_god_source_priority",),
            feature_hooks=("feature.ten_god",),
            question_hooks=("q_ten_god_focus", "q_hidden_stem_role"),
            retrieval_tags=("visible_hidden", "source_priority", "ten_god"),
            rule_atoms=(
                KnowledgeRuleAtom(
                    "ten_god.source_priority.review",
                    "ten_god_source_priority_gate",
                    "requires",
                    "visible_hidden+repeat_count+day_master_relation",
                    "condition",
                    0.78,
                ),
            ),
            portrait_mappings=(
                KnowledgePortraitMapping(
                    "portrait.ten_god_source_priority",
                    "十神来源优先级",
                    "ten_god",
                    "明透、藏干和重复十神需要按来源层级分开判断。",
                    "warm",
                    from_rule_atoms=("ten_god.source_priority.review",),
                    question_seeds=("明透、藏干和重复十神，哪一层更该先看？",),
                ),
            ),
            question_mappings=(
                KnowledgeQuestionMapping(
                    "q_hidden_stem_role",
                    "明透、藏干和重复十神，哪一层更该先看？",
                    "ten_god",
                    trigger_rule_atoms=("ten_god.source_priority.review",),
                ),
            ),
        ),
        KnowledgeUnit(
            "v20.core.wealth_output_channel",
            "Output-to-wealth channel review",
            "wealth",
            "Wealth reading should distinguish visible wealth material from output-to-wealth channels and capacity to receive.",
            "Use wealth ten-god, food/hurting output, capacity state, and relation context to discuss channel quality.",
            "Do not convert channel visibility into guaranteed income or investment result.",
            source_refs=("docs/v20.knowledge.wealth_output_channel",),
            feature_hooks=("feature.wealth", "feature.ten_god", "feature.strength"),
            question_hooks=("q_income_factors", "q_income_stability"),
            retrieval_tags=("wealth", "output_to_wealth", "capacity"),
            rule_atoms=(
                KnowledgeRuleAtom(
                    "wealth.output_channel.capacity",
                    "wealth_channel_gate",
                    "requires",
                    "wealth_material+output_star+capacity_state",
                    "domain_projection",
                    0.77,
                ),
            ),
            portrait_mappings=(
                KnowledgePortraitMapping(
                    "portrait.wealth_output_channel",
                    "食伤转财通道",
                    "wealth",
                    "财运先分财星材料、食伤输出通道和日主承接力。",
                    "hot",
                    from_rule_atoms=("wealth.output_channel.capacity",),
                    question_seeds=("财运机会来自财星本身，还是食伤转财通道？",),
                ),
            ),
            question_mappings=(
                KnowledgeQuestionMapping(
                    "q_income_factors",
                    "财运机会来自财星本身，还是食伤转财通道？",
                    "wealth",
                    trigger_rule_atoms=("wealth.output_channel.capacity",),
                ),
            ),
        ),
        KnowledgeUnit(
            "v20.applied.career_authority_output_resource",
            "Career authority-output-resource arbitration",
            "career",
            "Career structure should arbitrate authority stars, output stars, resource buffering, and day-master capacity.",
            "Use official/killing, food/hurting, resource, pattern, and capacity evidence to decide the reading path.",
            "Do not predict promotion, demotion, job loss, or workplace conflict as fixed events.",
            source_refs=("docs/v20.knowledge.career_authority_output_resource",),
            feature_hooks=("feature.ten_god", "feature.pattern", "feature.strength", "feature.branch"),
            question_hooks=("q_career_structure",),
            retrieval_tags=("career", "authority", "output", "resource_buffer"),
            rule_atoms=(
                KnowledgeRuleAtom(
                    "career.authority_output_resource.arbitration",
                    "career_arbitration_gate",
                    "requires_any",
                    "authority_star+output_star+resource_star+capacity_state",
                    "domain_projection",
                    0.76,
                ),
            ),
            portrait_mappings=(
                KnowledgePortraitMapping(
                    "portrait.career_authority_output_resource",
                    "事业官伤印裁决",
                    "career",
                    "事业先看官杀规则压力、食伤表达和印星缓冲是否形成主线。",
                    "warm",
                    from_rule_atoms=("career.authority_output_resource.arbitration",),
                    question_seeds=("事业上先看规则压力、表达冲突，还是印星缓冲？",),
                ),
            ),
            question_mappings=(
                KnowledgeQuestionMapping(
                    "q_career_structure",
                    "事业上先看规则压力、表达冲突，还是印星缓冲？",
                    "career",
                    trigger_rule_atoms=("career.authority_output_resource.arbitration",),
                ),
            ),
        ),
        KnowledgeUnit(
            "v20.applied.relationship_branch_tengod",
            "Relationship branch and ten-god arbitration",
            "relationship",
            "Relationship projection should combine branch interaction, ten-god source layer, and capacity context.",
            "Use branch relation, visible or hidden ten-god material, and support/pressure context before asking applied questions.",
            "Do not infer marriage timing, partner facts, breakup, or private relationship events.",
            source_refs=("docs/v20.knowledge.relationship_branch_tengod",),
            feature_hooks=("feature.branch", "feature.ten_god", "feature.strength"),
            question_hooks=("q_relationship_structure",),
            retrieval_tags=("relationship", "branch_interaction", "ten_god"),
            rule_atoms=(
                KnowledgeRuleAtom(
                    "relationship.branch_tengod.arbitration",
                    "relationship_arbitration_gate",
                    "requires_any",
                    "branch_relation+ten_god_source_layer+capacity_context",
                    "domain_projection",
                    0.71,
                ),
            ),
            portrait_mappings=(
                KnowledgePortraitMapping(
                    "portrait.relationship_branch_tengod",
                    "关系地支与十神裁决",
                    "relationship",
                    "关系主题先看地支互动和十神来源，再判断互动、约束或承接。",
                    "cool",
                    from_rule_atoms=("relationship.branch_tengod.arbitration",),
                    question_seeds=("关系里先看地支互动，还是十神来源？",),
                ),
            ),
            question_mappings=(
                KnowledgeQuestionMapping(
                    "q_relationship_structure",
                    "关系里先看地支互动，还是十神来源？",
                    "relationship",
                    trigger_rule_atoms=("relationship.branch_tengod.arbitration",),
                ),
            ),
        ),
        KnowledgeUnit(
            "v20.core.element_extreme_boundary",
            "Five-element extreme boundary",
            "element",
            "Element concentration and absence should be treated as balance pressure before applied-domain projection.",
            "Use prominent, weak, missing, and support-pressure evidence to decide whether balance is a main topic.",
            "Do not convert element pressure into medical diagnosis or fixed fortune.",
            source_refs=("docs/v20.knowledge.element_extreme_boundary",),
            feature_hooks=("feature.element", "feature.strength"),
            question_hooks=("q_element_balance", "q_element_support_pressure"),
            retrieval_tags=("five_element", "extreme", "balance_pressure"),
            rule_atoms=(
                KnowledgeRuleAtom(
                    "element.extreme.balance_pressure",
                    "element_extreme_gate",
                    "requires",
                    "prominent_or_weak_element+support_pressure",
                    "condition",
                    0.75,
                ),
            ),
            portrait_mappings=(
                KnowledgePortraitMapping(
                    "portrait.element_extreme_pressure",
                    "五行偏枯压力",
                    "element",
                    "五行偏显或偏弱只作为平衡压力和取用候选的依据。",
                    "warm",
                    from_rule_atoms=("element.extreme.balance_pressure",),
                    question_seeds=("五行偏枯会让这个盘更需要哪种平衡？",),
                ),
            ),
            question_mappings=(
                KnowledgeQuestionMapping(
                    "q_element_support_pressure",
                    "五行偏枯会让这个盘更需要哪种平衡？",
                    "element",
                    trigger_rule_atoms=("element.extreme.balance_pressure",),
                ),
            ),
        ),
        KnowledgeUnit(
            "v20.applied.wealth_peer_competition",
            "Wealth peer-competition arbitration",
            "wealth",
            "When wealth material and peer stars appear together, wealth reading should review competition, sharing, and capacity before opportunity language.",
            "Use wealth stars, peer stars, day-master capacity, and channel evidence to decide whether the wealth topic is opportunity, pressure, or shared-resource review.",
            "Do not infer financial loss, debt, investment outcome, or specific income events from peer-wealth coexistence.",
            source_refs=("docs/v20.knowledge.wealth_peer_competition",),
            feature_hooks=("feature.wealth", "feature.ten_god", "feature.strength"),
            question_hooks=("q_income_factors", "q_income_stability"),
            retrieval_tags=("wealth", "peer_star", "competition", "capacity"),
            rule_atoms=(
                KnowledgeRuleAtom(
                    "wealth.peer_competition.capacity_review",
                    "wealth_peer_competition_gate",
                    "requires",
                    "wealth_star+peer_star+capacity_state",
                    "domain_projection",
                    0.74,
                ),
            ),
            portrait_mappings=(
                KnowledgePortraitMapping(
                    "portrait.wealth_peer_competition",
                    "财星与比劫竞争",
                    "wealth",
                    "财运主题要同时看财星材料、比劫竞争和日主承载力。",
                    "warm",
                    from_rule_atoms=("wealth.peer_competition.capacity_review",),
                    question_seeds=("财运上先看机会，还是先看比劫竞争和承载力？",),
                ),
            ),
            question_mappings=(
                KnowledgeQuestionMapping(
                    "q_income_stability",
                    "财运上先看机会，还是先看比劫竞争和承载力？",
                    "wealth",
                    trigger_rule_atoms=("wealth.peer_competition.capacity_review",),
                ),
            ),
        ),
        KnowledgeUnit(
            "v20.applied.career_resource_buffer",
            "Career resource-buffer review",
            "career",
            "Resource stars can buffer output-authority tension, but only after source layer and capacity are checked.",
            "Use authority star, output star, resource star, and source layer evidence to decide whether career pressure is conflict, learning, rule adaptation, or unresolved candidate.",
            "Do not promise promotion, exam success, leadership role, or workplace conflict resolution.",
            source_refs=("docs/v20.knowledge.career_resource_buffer",),
            feature_hooks=("feature.ten_god", "feature.strength", "feature.pattern"),
            question_hooks=("q_career_structure",),
            retrieval_tags=("career", "resource_star", "authority", "output"),
            rule_atoms=(
                KnowledgeRuleAtom(
                    "career.resource_buffer.source_layer",
                    "career_resource_buffer_gate",
                    "requires_any",
                    "authority_star+output_star+resource_star+source_layer",
                    "domain_projection",
                    0.75,
                ),
            ),
            portrait_mappings=(
                KnowledgePortraitMapping(
                    "portrait.career_resource_buffer",
                    "事业印星缓冲",
                    "career",
                    "事业压力如果见印星，要先判断它是缓冲、学习路径还是证据不足。",
                    "warm",
                    from_rule_atoms=("career.resource_buffer.source_layer",),
                    question_seeds=("事业压力中，印星能不能形成缓冲？",),
                ),
            ),
            question_mappings=(
                KnowledgeQuestionMapping(
                    "q_career_structure",
                    "事业压力中，印星能不能形成缓冲？",
                    "career",
                    trigger_rule_atoms=("career.resource_buffer.source_layer",),
                ),
            ),
        ),
        KnowledgeUnit(
            "v20.applied.relationship_spouse_star_context",
            "Relationship spouse-star context boundary",
            "relationship",
            "Relationship questions should separate spouse-star material, branch interaction, and capacity context before any applied interpretation.",
            "Use visible or hidden spouse-star material, branch relation, source layer, and support-pressure context as review material.",
            "Do not infer marriage timing, partner identity, breakup, affair, or private relationship facts.",
            source_refs=("docs/v20.knowledge.relationship_spouse_star_context",),
            feature_hooks=("feature.ten_god", "feature.branch", "feature.strength"),
            question_hooks=("q_relationship_structure",),
            retrieval_tags=("relationship", "spouse_star", "branch_interaction", "source_layer"),
            rule_atoms=(
                KnowledgeRuleAtom(
                    "relationship.spouse_star.context_review",
                    "relationship_spouse_star_gate",
                    "requires_any",
                    "spouse_star+branch_relation+source_layer+capacity_context",
                    "domain_projection",
                    0.72,
                ),
            ),
            portrait_mappings=(
                KnowledgePortraitMapping(
                    "portrait.relationship_spouse_star_context",
                    "关系星与互动层",
                    "relationship",
                    "关系主题先分关系星材料、地支互动和承接边界。",
                    "cool",
                    from_rule_atoms=("relationship.spouse_star.context_review",),
                    question_seeds=("关系主题先看关系星，还是先看地支互动？",),
                ),
            ),
            question_mappings=(
                KnowledgeQuestionMapping(
                    "q_relationship_structure",
                    "关系主题先看关系星，还是先看地支互动？",
                    "relationship",
                    trigger_rule_atoms=("relationship.spouse_star.context_review",),
                ),
            ),
        ),
    )
    return _merge_knowledge_units(
        core_units,
        _expanded_knowledge_units(),
        _draft_knowledge_units(),
    )


def _merge_knowledge_units(*groups: Iterable[KnowledgeUnit]) -> tuple[KnowledgeUnit, ...]:
    merged: OrderedDict[str, KnowledgeUnit] = OrderedDict()
    for group in groups:
        for unit in group:
            knowledge_id = str(unit.knowledge_id)
            if knowledge_id not in merged:
                merged[knowledge_id] = unit
    return tuple(merged.values())


def _draft_knowledge_units(*, source_root: Path | None = None) -> tuple[KnowledgeUnit, ...]:
    root = source_root or _DEFAULT_KNOWLEDGE_DRAFT_ROOT
    return tuple(
        chain.from_iterable(
            _draft_units_from_file(path)
            for path in _seed_paths(root)
        )
    )


def _draft_units_from_file(path: Path) -> tuple[KnowledgeUnit, ...]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return ()
    rows = payload.get("knowledge_drafts", ()) if isinstance(payload, dict) else ()
    units: list[KnowledgeUnit] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        unit = _knowledge_unit_from_draft_row(row, path=path, row_index=index)
        if unit is None:
            continue
        units.append(unit)
    return tuple(units)


def _knowledge_unit_from_draft_row(row: dict[str, object], *, path: Path, row_index: int) -> KnowledgeUnit | None:
    statement = str(row.get("statement", "")).strip()
    if not statement:
        return None
    knowledge_id = str(row.get("knowledge_id") or f"{path.stem}.draft.{row_index:03d}")
    raw_domain = str(row.get("domain") or "core_structure").strip() or "core_structure"
    domain = _normalize_runtime_domain(raw_domain)
    category = str(row.get("category") or "").strip().lower()
    title = str(row.get("title") or knowledge_id)
    raw_source_refs = tuple(str(item) for item in row.get("source_refs", ()) if str(item).strip())
    source_refs = raw_source_refs or (f"docs/{path.as_posix()}",)
    structured_facts = row.get("structured_facts") if isinstance(row.get("structured_facts"), dict) else {}
    conditions = row.get("conditions") if isinstance(row.get("conditions"), dict) else {}
    forbidden_usage = tuple(str(item) for item in row.get("forbidden_usage", ()) if str(item).strip())
    allowed_usage = tuple(str(item) for item in row.get("allowed_usage", ()) if str(item).strip())
    risk_level = str(row.get("risk_level") or "")
    feature_hooks = _derive_feature_hooks(domain=domain, category=category, structured_facts=structured_facts)
    question_hooks = _derive_question_hooks(
        domain=domain,
        category=category,
        statement=statement,
        structured_facts=structured_facts,
    )
    retrieval_tags = _derive_retrieval_tags(domain, category, structured_facts)
    atom_id = f"draft.{_slug_id(knowledge_id)}.gate"
    atom_value = _flatten_seed_conditions(structured_facts=structured_facts, conditions=conditions)
    atom_confidence = _seed_confidence(row.get("confidence_prior"))
    boundary = _derive_boundary(category=category, forbidden_usage=forbidden_usage, risk_level=risk_level)
    evidence_template = _derive_evidence_template(statement, structured_facts, category, allowed_usage, forbidden_usage)
    question_title = _derive_question_title(domain, category, title, statement)
    question_key = question_hooks[0]
    return KnowledgeUnit(
        knowledge_id,
        title,
        domain,
        statement,
        evidence_template,
        boundary,
        version="v20.knowledge_unit.draft_seed.v1",
        status="reviewed",
        source_refs=tuple(_ensure_non_empty(ref) for ref in source_refs),
        feature_hooks=tuple(dict.fromkeys(feature_hooks)),
        question_hooks=tuple(question_hooks),
        retrieval_tags=tuple(dict.fromkeys(retrieval_tags)),
        rule_atoms=(
            KnowledgeRuleAtom(
                atom_id,
                _rule_atom_type(category),
                "requires",
                atom_value,
                "condition",
                atom_confidence,
                boundary=boundary,
            ),
        ),
        portrait_mappings=(
            KnowledgePortraitMapping(
                f"portrait.{_slug_id(knowledge_id)}",
                _derive_portrait_label(domain, title),
                _portrait_domain(domain),
                evidence_template,
                "warm",
                from_rule_atoms=(atom_id,),
                question_seeds=(question_title,),
            ),
        ),
        question_mappings=(
            KnowledgeQuestionMapping(
                question_key,
                question_title,
                _portrait_domain(domain),
                trigger_rule_atoms=(atom_id,),
                role="draft_knowledge_entry",
            ),
        ),
        answer_guidance=(
            KnowledgeAnswerGuidance(
                f"answer.{_slug_id(knowledge_id)}",
                _portrait_domain(domain),
                evidence_template,
                allowed_phrases=_derive_allowed_phrases(statement),
                forbidden_phrases=_derive_forbidden_phrases(forbidden_usage),
                boundary=boundary,
            ),
        ),
        counterexamples=(),
        allowed_usage=allowed_usage or ("evidence_context", "feature_support", "question_support"),
        forbidden_usage=tuple(dict.fromkeys((*forbidden_usage, "direct_rule_truth"))),
    )


def _slug_id(value: str) -> str:
    safe = "".join(ch if (ch.isalnum() or ch == "_") else "_" for ch in value.lower())
    while "__" in safe:
        safe = safe.replace("__", "_")
    return safe.strip("_") or "draft_seed"


def _portrait_domain(domain: str) -> str:
    mapping = {
        "answer_expression": "pattern",
        "answer_style": "pattern",
        "relationship": "relationship",
        "richness": "pattern",
        "core_structure": "pattern",
        "ten_god": "ten_god",
        "strength": "strength",
        "pattern": "pattern",
        "wealth": "wealth",
        "career": "career",
        "health": "health",
        "blind": "pattern",
        "geo_context": "branch",
        "branch_advanced": "branch",
        "branch": "branch",
        "palace": "branch",
        "timing": "time",
        "luck_flow": "time",
        "calendar": "time",
        "interaction": "branch",
        "rule_db": "pattern",
        "calendar": "time",
        "luck_flow": "time",
        "five_element": "element",
        "lab": "pattern",
        "auxiliary_pillars": "time",
        "nayin": "element",
        "auxiliary_symbols": "ten_god",
        "branch_relation": "branch",
        "children": "relationship",
        "family": "relationship",
        "shensha": "ten_god",
    }
    return mapping.get(domain, "pattern")


def _normalize_runtime_domain(domain: str) -> str:
    mapping = {
        "core_structure": "pattern",
        "answer_expression": "pattern",
        "answer_style": "pattern",
        "relationship": "relationship",
        "interaction": "branch",
        "geo_context": "branch",
        "rule_db": "pattern",
        "blind": "pattern",
        "timing": "time",
        "auxiliary_pillars": "time",
        "branch_advanced": "branch",
        "palace": "branch",
        "luck_flow": "time",
        "calendar": "time",
        "auxiliary_symbols": "ten_god",
        "growth_phase": "time",
        "five_element": "element",
        "auxiliary_archive": "pattern",
        "special_pattern_boundary": "pattern",
        "special_pattern_detail": "pattern",
        "auxiliary_boundary": "pattern",
        # Archive-domain seeds from first-wave packs:
        # map to executable bazi projection domains so rule graph can reason without
        # a separate auxiliary domain adapter.
        "children": "relationship",
        "family": "relationship",
        "personality": "pattern",
        "lab": "pattern",
        "nayin": "element",
        "shensha": "ten_god",
    }
    normalized = str(domain).strip().lower()
    return mapping.get(normalized, normalized)


def _derive_feature_hooks(*, domain: str, category: str, structured_facts: dict[str, object]) -> tuple[str, ...]:
    hooks: list[str] = []
    for key in structured_facts:
        slug = _slug_id(str(key))
        if slug.startswith("feature_"):
            hooks.append(slug)
            continue
        if all(ch.isascii() and (ch.isalpha() or ch.isdigit() or ch == "_") for ch in slug) and slug:
            hooks.append(f"feature.{slug}")
    hooks.append(_domain_feature_hook(domain))
    if category:
        hooks.append(f"topic.{_slug_id(category)}")
    if category in {"ten_god_interaction", "ten_god_pathway", "ten_god", "ten_god_interaction_mechanism", "ten_god_pathway_mechanism"}:
        hooks.append("feature.ten_god")
    if category.startswith("blind_"):
        hooks.append("feature.pattern")
    if category.startswith("branch_"):
        hooks.append("feature.branch")
    if category.startswith("wealth_"):
        hooks.append("feature.wealth")
    if "answer" in category:
        hooks.append("feature.strength")
    if domain in {"career", "relationship", "health"}:
        hooks.extend(_applied_core_feature_anchors(domain))
    return tuple(dict.fromkeys(hook for hook in hooks if hook))


def _applied_core_feature_anchors(domain: str) -> tuple[str, ...]:
    try:
        from v20.answer.measurement_policy import feature_domains_for_applied_domain
    except Exception:
        return ()
    return tuple(
        f"feature.{source_domain}"
        for source_domain in feature_domains_for_applied_domain(domain)
        if source_domain
    )


def _derive_question_hooks(
    *,
    domain: str,
    category: str,
    statement: str,
    structured_facts: dict[str, object],
) -> tuple[str, ...]:
    question_hooks = list[str]()
    base = {
        "core_structure": ("q_structure_overview",),
        "strength": ("q_strength_assessment",),
        "pattern": ("q_pattern_structure",),
        "ten_god": ("q_ten_god_focus",),
        "branch": ("q_branch_relation_detail",),
        "time": ("q_time_layer_context",),
        "wealth": ("q_income_stability",),
        "career": ("q_career_structure",),
        "relationship": ("q_relationship_structure",),
        "health": ("q_health_balance_boundary",),
        "blind": ("q_pattern_structure",),
        "interaction": ("q_branch_relation_detail",),
        "rule_db": ("q_structure_overview",),
        "geo_context": ("q_structure_overview",),
        "luck_flow": ("q_time_relation_triggers",),
        "calendar": ("q_time_vs_natal_relation",),
    }
    question_hooks.extend(base.get(domain, ()))
    if not question_hooks:
        question_hooks.append("q_structure_overview")
    for key in structured_facts:
        if any(tok in str(key) for tok in ("wealth", "income", "财", "财星", "财运")):
            if "q_income_stability" not in question_hooks:
                question_hooks.append("q_income_stability")
        if any(tok in str(key) for tok in ("career", "事业", "官", "官星", "事业")):
            if "q_career_structure" not in question_hooks:
                question_hooks.append("q_career_structure")
        if any(tok in str(key) for tok in ("关系", "spouse", "婚", "伴")):
            if "q_relationship_structure" not in question_hooks:
                question_hooks.append("q_relationship_structure")
        if any(tok in str(key) for tok in ("用神", "useful_god")):
            if "q_useful_god_candidates" not in question_hooks:
                question_hooks.append("q_useful_god_candidates")
        if any(tok in str(key) for tok in ("时", "流", "运", "大运", "流年", "luck", "time", "timing")):
            if "q_time_relation_triggers" not in question_hooks:
                question_hooks.append("q_time_relation_triggers")
    if "answer" in category and "q_structure_overview" not in question_hooks:
        question_hooks.append("q_structure_overview")
    allowed_map = {
        "strength": ("q_strength_assessment",),
        "ten_god": ("q_ten_god_focus", "q_ten_god_metadata", "q_hidden_stem_role"),
        "useful_god": ("q_useful_god_candidates", "q_useful_god_evidence_gaps"),
        "element": ("q_element_balance", "q_element_support_pressure"),
        "branch": ("q_branch_relation_detail", "q_time_vs_natal_relation", "q_structure_overview"),
        "wealth": ("q_income_stability", "q_income_factors"),
        "pattern": ("q_pattern_structure",),
        "time": ("q_time_layer_context", "q_time_relation_triggers"),
        "career": ("q_career_structure",),
        "relationship": ("q_relationship_structure",),
        "health": ("q_health_balance_boundary",),
    }
    domain_allowed = set(allowed_map.get(domain, ("q_structure_overview",)))
    filtered = [hook for hook in question_hooks if hook in domain_allowed]
    if not filtered:
        filtered = [sorted(domain_allowed)[0]]
    return tuple(dict.fromkeys(filtered))


def _derive_retrieval_tags(domain: str, category: str, structured_facts: dict[str, object]) -> tuple[str, ...]:
    tags = ["seed", "draft_import"]
    tags.append(domain)
    if category:
        tags.append(category)
    if "blind" in category or domain == "blind":
        tags.append("blind_school")
    if "micro" in category or category.endswith("_mechanism"):
        tags.append("micro")
    if "macro" in category or category.startswith("qishi") or "climate" in category:
        tags.append("macro")
    if "interaction" in category:
        tags.append("interaction")
    for key in structured_facts:
        normalized_key = _slug_id(str(key))
        if normalized_key:
            tags.append(normalized_key)
    return tuple(dict.fromkeys(tag for tag in tags if tag))


def _derive_boundary(category: str, forbidden_usage: tuple[str, ...], risk_level: str) -> str:
    if forbidden_usage:
        boundary = "，".join(forbidden_usage[:4])
        if len(forbidden_usage) > 4:
            boundary += "..."
    else:
        boundary = "不输出命理标签化判断，不直接给出确定事件。"
    if risk_level in {"R1", "R2"}:
        boundary = f"{boundary}；{_risk_boundary(risk_level)}"
    if not boundary.strip():
        boundary = "不输出确定性结论，先做结构化边界说明。"
    if category:
        boundary = f"{boundary} | 类目: {category}"
    return boundary


def _derive_evidence_template(
    statement: str,
    structured_facts: dict[str, object],
    category: str,
    allowed_usage: tuple[str, ...],
    forbidden_usage: tuple[str, ...],
) -> str:
    if structured_facts:
        facts = "；".join(f"{key}:{value}" for key, value in list(structured_facts.items())[:3])
        if facts:
            return f"{statement} | 结构证据线索: {facts}"
    return f"{statement} | category={category or 'unspecified'}"


def _derive_question_title(domain: str, category: str, title: str, statement: str) -> str:
    hooks = _derive_question_hooks(
        domain=domain,
        category=category,
        statement=statement,
        structured_facts={},
    )
    base = (QUESTION_LABELS.get(hooks[0]) or "先看哪条结构线再回答？")
    return f"{title or '规则线索'}（{base}）"


def _derive_allowed_phrases(statement: str) -> tuple[str, ...]:
    words = ("结构", "关系", "依据", "边界", "复核", "先看")
    return tuple(word for word in words if word in str(statement))


def _derive_forbidden_phrases(forbidden_usage: tuple[str, ...]) -> tuple[str, ...]:
    base = {
        "prediction": "预测",
        "fortune": "财运结论",
        "good_bad_judgement": "是非判定",
        "rule_mutation": "改写规则",
        "career_prediction": "职业预测",
        "life_event_prediction": "人生事件判断",
        "unsupported_question": "越界问题",
    }
    collected = [
        word for key, word in base.items()
        for usage in forbidden_usage
        if key in usage
    ]
    collected.extend(("一定", "必然", "绝对", "注定"))
    return tuple(dict.fromkeys(collected))


def _domain_feature_hook(domain: str) -> str:
    return f"feature.{_slug_id(domain)}"


def _rule_atom_type(category: str) -> str:
    if "mechanism" in category:
        return "mechanism_gate"
    if "boundary" in category:
        return "boundary_gate"
    if "anchor" in category:
        return "anchor_gate"
    return "condition_gate"


def _seed_confidence(value: object) -> float:
    try:
        confidence = float(value)
    except Exception:
        return 0.7
    if not (0.0 <= confidence <= 1.0):
        confidence = max(0.0, min(1.0, confidence))
    return confidence


def _ensure_non_empty(ref: str) -> str:
    return str(ref).strip() or "docs/v20/unknown"


def _flatten_seed_conditions(structured_facts: dict[str, object], conditions: dict[str, object]) -> str:
    lines: list[str] = []
    if conditions:
        lines.append("conditions=" + "|".join(f"{key}:{_compact_value(value)}" for key, value in conditions.items()))
    if structured_facts:
        lines.append("facts=" + "|".join(f"{key}:{_compact_value(value)}" for key, value in structured_facts.items()))
    if not lines:
        return "draft_seed_condition"
    return "; ".join(lines)[:220]


def _compact_value(value: object) -> str:
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return ",".join(str(item) for item in value[:4])
    if isinstance(value, tuple):
        return ",".join(str(item) for item in value[:4])
    if isinstance(value, dict):
        keys = list(value.keys())[:4]
        return ",".join(str(key) for key in keys)
    return "obj"


def _risk_boundary(risk_level: str) -> str:
    if risk_level == "R2":
        return "高风险域，需严格禁止事件结论并保留观察边界。"
    if risk_level == "R1":
        return "中风险域，返回结构提示并保留可追溯证据边界。"
    return "低风险域，仍需以结构证据约束，不做确定结果。"


def _derive_portrait_label(domain: str, title: str) -> str:
    if domain in {"wealth", "career", "relationship", "health", "strength", "ten_god", "branch", "pattern", "core_structure", "time"}:
        return {"wealth": "财富结构画像", "career": "事业结构画像", "relationship": "关系结构画像", "health": "健康结构画像", "strength": "强弱结构画像", "ten_god": "十神结构画像", "branch": "地支互动结构画像", "pattern": "格局结构画像", "core_structure": "结构阅读画像", "time": "时间层结构画像"}.get(domain, title[:14])
    return f"{title[:18]}结构画像"


def _expanded_knowledge_units() -> tuple[KnowledgeUnit, ...]:
    return (
        _unit(
            "v20.macro.pattern.qishi_flow",
            "Macro qishi and structural flow",
            "pattern",
            "宏观先看全局气势、主客、流通和阻滞，再决定是否进入格局、用神或应用主题。",
            "Use season, dominant element, flow path, obstruction, and host-guest relation before naming a pattern.",
            "Do not name a high/low pattern or life outcome from broad qishi alone.",
            ("feature.pattern", "feature.element", "feature.strength"),
            ("q_pattern_structure", "q_element_balance"),
            ("macro", "qishi", "flow", "pattern"),
            "pattern.qishi.flow_gate",
            "pattern_macro_gate",
            "season+dominant_element+flow_path+obstruction",
            "portrait.pattern_qishi_flow",
            "全局气势与流通",
            "先看气势流向、阻滞点和主客关系，再进入细部裁决。",
            "q_pattern_structure",
            "全局气势先看流通，还是先看阻滞？",
        ),
        _unit(
            "v20.macro.element.temperature_humidity",
            "Temperature and humidity macro climate",
            "element",
            "寒暖燥湿是宏观气候，不等同于五行数量；它决定调候和结构舒展的优先级。",
            "Use month season, fire-water balance, dryness-wetness signs, and support pressure as climate evidence.",
            "Do not turn cold/heat/dry/wet into health diagnosis or fixed fortune.",
            ("feature.element", "feature.strength"),
            ("q_element_balance", "q_useful_god_candidates"),
            ("macro", "climate", "temperature", "humidity", "tiaohou"),
            "element.climate.temperature_humidity",
            "climate_gate",
            "season+fire_water_balance+dry_wet_evidence",
            "portrait.element_climate",
            "寒暖燥湿气候",
            "把寒暖燥湿作为调候和流通优先级，而不是直接断事。",
            "q_element_balance",
            "这个盘先看寒暖燥湿，还是先看五行数量？",
        ),
        _unit(
            "v20.macro.useful_god.tiaohou_path",
            "Tiaohou useful-god path",
            "useful_god",
            "调候路径处理季节气候偏性，和扶抑、通关、病药路径需要分开裁决。",
            "Separate climate adjustment, support-suppression, mediation, and disease-remedy candidate paths.",
            "Do not declare one fixed favorable god before comparing competing useful-god paths.",
            ("feature.useful_god", "feature.element", "feature.strength"),
            ("q_useful_god_candidates", "q_useful_god_evidence_gaps"),
            ("macro", "tiaohou", "useful_god", "path_arbitration"),
            "useful_god.tiaohou.path_gate",
            "useful_god_path_gate",
            "climate_bias+capacity_state+flow_obstruction",
            "portrait.useful_god_tiaohou",
            "调候用神路径",
            "把调候作为候选路径，与扶抑、通关、病药逐条比较。",
            "q_useful_god_candidates",
            "用神候选里，调候是不是优先路径？",
        ),
        _unit(
            "v20.macro.branch.palace_position",
            "Palace and position layer",
            "branch",
            "宫位位置决定结构落点，年/月/日/时不能混作同一层信息。",
            "Use pillar position, branch relation, hidden stem source, and affected domain as position evidence.",
            "Do not infer family facts, spouse facts, or exact events from palace position alone.",
            ("feature.branch", "feature.ten_god", "feature.time"),
            ("q_branch_relation_detail", "q_time_vs_natal_relation"),
            ("macro", "palace", "position", "pillar_layer"),
            "branch.palace.position_layer",
            "branch_position_gate",
            "pillar_position+branch_relation+hidden_stem_source",
            "portrait.branch_palace_position",
            "宫位落点层",
            "先分年、月、日、时位置，再判断关系牵动哪一层。",
            "q_branch_relation_detail",
            "这组地支关系落在哪个宫位层？",
        ),
        _unit(
            "v20.macro.time.original_luck_flow_stack",
            "Original-luck-flow stack",
            "time",
            "原局、大运、流年是三层栈：原局给结构，大运给阶段背景，流年给触发窗口。",
            "Use supplied natal, luck, and flow pillars as separate layers before checking hits and repeats.",
            "Do not infer exact dates or guaranteed events from a layer hit.",
            ("feature.time", "feature.branch", "feature.ten_god"),
            ("q_time_layer_context", "q_time_relation_triggers"),
            ("macro", "natal_luck_flow", "time_stack"),
            "time.natal_luck_flow.stack",
            "time_stack_gate",
            "natal_structure+luck_context+flow_trigger",
            "portrait.time_stack",
            "原局大运流年三层",
            "原局定结构，大运定阶段，流年只作触发背景。",
            "q_time_layer_context",
            "原局、大运、流年现在分别承担什么角色？",
        ),
        _unit(
            "v20.macro.pattern.blind_image_entry",
            "Blind-school image entry",
            "pattern",
            "盲派象法先取可见象、宫位象、十神象和动作象，再回到结构证据复核。",
            "Use visible image, palace image, ten-god image, and action image as clues, then require structural confirmation.",
            "Do not use image reading to bypass evidence, privacy boundaries, or deterministic event claims.",
            ("feature.pattern", "feature.branch", "feature.ten_god"),
            ("q_pattern_structure", "q_branch_relation_detail"),
            ("macro", "blind_school", "image_reading", "xiangfa"),
            "pattern.blind_image.entry",
            "blind_image_gate",
            "visible_image+palace_image+ten_god_image+structural_confirmation",
            "portrait.blind_image_entry",
            "盲派取象入口",
            "象法只作为入口线索，必须回到结构和证据复核。",
            "q_pattern_structure",
            "这个盘的象法入口来自宫位、十神还是动作？",
        ),
        _unit(
            "v20.micro.ten_god.full_role_set",
            "Full ten-god role set",
            "ten_god",
            "十神必须区分比肩、劫财、食神、伤官、偏财、正财、七杀、正官、偏印、正印的角色差异。",
            "Use role name, polarity, source layer, repeat count, and relation to day-master before applied reading.",
            "Do not collapse all wealth, authority, resource, peer, or output stars into one meaning.",
            ("feature.ten_god",),
            ("q_ten_god_focus", "q_hidden_stem_role"),
            ("micro", "ten_god", "role_set"),
            "ten_god.full_role_set.required",
            "ten_god_role_gate",
            "role_name+polarity+source_layer+repeat_count",
            "portrait.ten_god_full_roles",
            "十神细分角色",
            "十神先分正偏、显隐、重复和与日主关系，再进入主题。",
            "q_ten_god_focus",
            "十神里哪一个具体角色最该先复核？",
        ),
        _unit(
            "v20.micro.element.generate_control_transform",
            "Element generation-control-transform",
            "element",
            "五行不能只看数量，要看生、克、泄、耗、助、制化和通关能否形成路径。",
            "Use generation path, control path, release path, drain path, support path, and mediation evidence.",
            "Do not treat element count as the final balance decision.",
            ("feature.element", "feature.useful_god", "feature.strength"),
            ("q_element_support_pressure", "q_useful_god_candidates"),
            ("micro", "sheng_ke_zhi_hua", "mediation", "flow"),
            "element.generate_control.transform",
            "element_flow_gate",
            "generation+control+release+drain+support+mediation",
            "portrait.element_flow_transform",
            "五行生克制化",
            "五行以流通、制化和通关路径判断，不只看个数。",
            "q_element_support_pressure",
            "五行之间是流通、制约，还是需要通关？",
        ),
        _unit(
            "v20.micro.branch.tomb_storage_open_close",
            "Tomb-storage open-close",
            "branch",
            "辰戌丑未等墓库要看藏干、开合、冲刑引动和所藏十神，不宜直接定吉凶。",
            "Use tomb/storage branch, hidden stems, opening trigger, affected ten-god, and pillar position.",
            "Do not call a tomb/storage branch lucky or unlucky without trigger and content evidence.",
            ("feature.branch", "feature.ten_god", "feature.time"),
            ("q_branch_relation_detail", "q_time_relation_triggers"),
            ("micro", "tomb_storage", "muku", "open_close"),
            "branch.tomb_storage.open_close",
            "branch_storage_gate",
            "storage_branch+hidden_stem+opening_trigger+position",
            "portrait.branch_tomb_storage",
            "墓库开合",
            "墓库先看所藏、开合和引动位置，不直接断吉凶。",
            "q_branch_relation_detail",
            "墓库现在是藏、开，还是被时间层引动？",
        ),
        _unit(
            "v20.micro.branch.punishment_harm_break_pierce",
            "Punishment harm break and pierce",
            "branch",
            "刑、害、破、穿属于不同互动机制，要分开看方向、对象、宫位和是否有解。",
            "Use relation type, direction, involved branches, palace position, and mediating element evidence.",
            "Do not merge punishment, harm, break, and pierce into a generic bad outcome.",
            ("feature.branch", "feature.element", "feature.time"),
            ("q_branch_relation_detail",),
            ("micro", "xing_hai_po_chuan", "branch_mechanism"),
            "branch.punishment_harm_break_pierce",
            "branch_mechanism_gate",
            "relation_type+direction+branch_pair+mediation",
            "portrait.branch_mechanism",
            "刑害破穿机制",
            "把刑、害、破、穿拆成不同互动机制和落点。",
            "q_branch_relation_detail",
            "这组地支互动是刑、害、破、穿中的哪种机制？",
        ),
        _unit(
            "v20.micro.branch.combine_transform_bind",
            "Combination transform and binding",
            "branch",
            "合要区分合化、合绊、合动和合而不化，不能见合就当化。",
            "Use combination pair, season support, transformation element, obstruction, and source layer.",
            "Do not assume every combination transforms or produces a favorable result.",
            ("feature.branch", "feature.element", "feature.time"),
            ("q_branch_relation_detail", "q_element_balance"),
            ("micro", "combination", "transform", "binding"),
            "branch.combine.transform_bind",
            "branch_combination_gate",
            "combination_pair+season_support+transform_element+obstruction",
            "portrait.branch_combination",
            "合化与合绊",
            "见合先分合化、合绊、合动和合而不化。",
            "q_branch_relation_detail",
            "这组合是化、绊、动，还是合而不化？",
        ),
        _unit(
            "v20.micro.pattern.zuogong_path",
            "Zuogong action path",
            "pattern",
            "做功关注干支、十神、宫位之间是否形成可执行的作用链。",
            "Use actor, target, medium, path continuity, obstruction, and received result as action evidence.",
            "Do not treat one isolated relation as completed action or outcome.",
            ("feature.pattern", "feature.ten_god", "feature.branch", "feature.strength"),
            ("q_pattern_structure",),
            ("micro", "zuogong", "action_path", "blind_school"),
            "pattern.zuogong.action_path",
            "zuogong_gate",
            "actor+target+medium+path_continuity+obstruction",
            "portrait.zuogong_path",
            "做功作用链",
            "看谁对谁做功、通过什么做、是否被阻断和是否承接。",
            "q_pattern_structure",
            "这个盘的做功链条是谁在作用谁？",
        ),
        _unit(
            "v20.micro.wealth.zuogong_receive",
            "Wealth zuogong and receiving path",
            "wealth",
            "财的做功要看财从哪里来、谁去取、能否入主、是否被分夺或阻隔。",
            "Use wealth source, output channel, peer competition, capacity, and receiving position evidence.",
            "Do not predict income amount, gain, loss, or transaction outcome.",
            ("feature.wealth", "feature.ten_god", "feature.strength", "feature.branch"),
            ("q_income_factors", "q_income_stability"),
            ("micro", "zuogong", "wealth", "receive_path"),
            "wealth.zuogong.receive_path",
            "wealth_action_gate",
            "wealth_source+actor+channel+capacity+competition",
            "portrait.wealth_zuogong",
            "财的做功与承接",
            "财要看来源、通道、承接和分夺，不直接断钱数。",
            "q_income_factors",
            "财的作用链是财来就我，还是我去取财？",
        ),
        _unit(
            "v20.micro.career.authority_zuogong",
            "Authority zuogong path",
            "career",
            "官杀做功要看规则压力、平台约束、印星转化、食伤冲突和日主承接。",
            "Use authority star, output star, resource mediation, capacity, and branch position evidence.",
            "Do not predict job title, promotion, demotion, or legal outcome.",
            ("feature.ten_god", "feature.pattern", "feature.strength", "feature.branch"),
            ("q_career_structure",),
            ("micro", "zuogong", "authority", "career"),
            "career.authority.zuogong_path",
            "career_action_gate",
            "authority_star+output_star+resource_mediation+capacity",
            "portrait.career_authority_zuogong",
            "官杀做功路径",
            "事业看规则压力如何作用、是否被印化或被食伤冲击。",
            "q_career_structure",
            "官杀在这个盘里是在约束、成事，还是形成压力？",
        ),
        _unit(
            "v20.applied.study_exam_learning_path",
            "Study exam and learning path",
            "career",
            "学业考试主题先看印星、食伤、官杀规则、日主承载和时间层触发。",
            "Use resource star, output star, authority star, capacity, and explicit time context as evidence.",
            "Do not promise exam success, admission, ranking, certificate, or exact result.",
            ("feature.ten_god", "feature.strength", "feature.time", "feature.pattern"),
            ("q_career_structure", "q_time_layer_context"),
            ("application", "study", "exam", "resource_output_authority"),
            "career.study_exam.learning_path",
            "study_exam_gate",
            "resource_star+output_star+authority_star+capacity+time_context",
            "portrait.study_exam_path",
            "学业考试路径",
            "学业考试看印星吸收、食伤表达、规则压力和承载力。",
            "q_career_structure",
            "学业考试先看印星、食伤，还是官杀规则？",
        ),
        _unit(
            "v20.applied.family_parent_resource",
            "Family and parent-resource context",
            "relationship",
            "家庭父母主题以印星、年/月宫位、承接压力和互动关系作结构讨论。",
            "Use resource star, year-month position, branch interaction, and capacity pressure as evidence.",
            "Do not infer private family facts, parent health, death, divorce, or exact family events.",
            ("feature.ten_god", "feature.branch", "feature.strength"),
            ("q_relationship_structure", "q_hidden_stem_role"),
            ("application", "family", "parent", "resource_star"),
            "relationship.family_parent.resource_context",
            "family_context_gate",
            "resource_star+year_month_position+branch_interaction+capacity",
            "portrait.family_resource_context",
            "家庭印星与承接",
            "家庭主题先看印星、宫位和承接压力，不推断隐私事件。",
            "q_relationship_structure",
            "家庭主题先看印星来源，还是宫位互动？",
        ),
        _unit(
            "v20.applied.social_peer_network",
            "Social peer and network context",
            "relationship",
            "人际合作主题先看比劫、食伤表达、财官牵动和地支互动。",
            "Use peer stars, output stars, branch interaction, wealth-authority link, and capacity evidence.",
            "Do not infer betrayal, lawsuit, exact collaboration result, or private third-party facts.",
            ("feature.ten_god", "feature.branch", "feature.wealth", "feature.strength"),
            ("q_relationship_structure", "q_income_factors"),
            ("application", "social", "peer", "network"),
            "relationship.social_peer.network",
            "social_network_gate",
            "peer_star+output_star+branch_interaction+wealth_authority_link",
            "portrait.social_peer_network",
            "人际合作结构",
            "人际主题看比劫合作竞争、表达方式和资源分配边界。",
            "q_relationship_structure",
            "人际合作里先看比劫、食伤，还是地支互动？",
        ),
        _unit(
            "v20.applied.mobility_migration_branch_time",
            "Mobility and migration context",
            "time",
            "迁移变动主题要看驿动象、冲动宫位、时间层触发和原局承接。",
            "Use branch movement signs, palace position, time trigger, and receiving structure as evidence.",
            "Do not predict moving date, travel accident, immigration result, or guaranteed relocation.",
            ("feature.branch", "feature.time", "feature.strength"),
            ("q_time_layer_context", "q_branch_relation_detail"),
            ("application", "mobility", "migration", "movement"),
            "time.mobility.migration_context",
            "mobility_gate",
            "movement_sign+palace_position+time_trigger+receiving_structure",
            "portrait.mobility_context",
            "迁移变动结构",
            "迁移变动只看结构牵动和承接，不断具体地点和结果。",
            "q_time_layer_context",
            "迁移变动是原局动象，还是大运流年触发？",
        ),
        _unit(
            "v20.applied.asset_cashflow_structure",
            "Asset and cashflow structure",
            "wealth",
            "资产现金流主题要分财星材料、库藏、通道、风险约束和承接力。",
            "Use wealth material, storage branch, output channel, authority constraint, and capacity evidence.",
            "Do not predict asset price, debt amount, investment profit, or financial event timing.",
            ("feature.wealth", "feature.branch", "feature.ten_god", "feature.strength"),
            ("q_income_stability", "q_income_factors"),
            ("application", "asset", "cashflow", "storage"),
            "wealth.asset_cashflow.structure",
            "asset_cashflow_gate",
            "wealth_material+storage_branch+output_channel+constraint+capacity",
            "portrait.asset_cashflow",
            "资产现金流结构",
            "资产现金流要分材料、库藏、通道、约束和承接。",
            "q_income_stability",
            "财务结构先看现金流通道，还是库藏承接？",
        ),
        _unit(
            "v20.applied.health.rhythm_recovery_boundary",
            "Rhythm and recovery boundary",
            "health",
            "健康相邻主题只讨论作息节律、压力恢复和五行偏性，不进入诊断。",
            "Use element climate, support pressure, time rhythm, and branch stress as non-medical evidence.",
            "Do not diagnose disease, recommend treatment, predict onset, or replace medical advice.",
            ("feature.element", "feature.strength", "feature.time", "feature.branch"),
            ("q_health_balance_boundary", "q_element_support_pressure"),
            ("application", "rhythm", "recovery", "health_boundary"),
            "health.rhythm_recovery.boundary",
            "health_rhythm_gate",
            "element_climate+support_pressure+time_rhythm+branch_stress",
            "portrait.health_rhythm_recovery",
            "节律恢复边界",
            "只讨论压力节律和恢复边界，不做医疗判断。",
            "q_health_balance_boundary",
            "压力恢复先看五行气候，还是承载力边界？",
        ),
    )


def _unit(
    knowledge_id: str,
    title: str,
    domain: str,
    summary: str,
    evidence_template: str,
    boundary: str,
    feature_hooks: tuple[str, ...],
    question_hooks: tuple[str, ...],
    retrieval_tags: tuple[str, ...],
    atom_id: str,
    atom_type: str,
    atom_value: str,
    portrait_key: str,
    portrait_label: str,
    portrait_description: str,
    question_key: str,
    question_title: str,
) -> KnowledgeUnit:
    safe_question_hooks = _sanitize_question_hooks(domain, question_hooks)
    return KnowledgeUnit(
        knowledge_id,
        title,
        domain,
        summary,
        evidence_template,
        boundary,
        source_refs=("docs/v20.knowledge.mainline_expansion",),
        feature_hooks=feature_hooks,
        question_hooks=safe_question_hooks,
        retrieval_tags=retrieval_tags,
        rule_atoms=(
            KnowledgeRuleAtom(
                atom_id,
                atom_type,
                "requires",
                atom_value,
                "condition",
                0.74,
                boundary=boundary,
            ),
        ),
        portrait_mappings=(
            KnowledgePortraitMapping(
                portrait_key,
                portrait_label,
                domain,
                portrait_description,
                "warm",
                from_rule_atoms=(atom_id,),
                question_seeds=(question_title,),
            ),
        ),
        question_mappings=(
            KnowledgeQuestionMapping(
                question_key,
                question_title,
                domain,
                trigger_rule_atoms=(atom_id,),
            ),
        ),
        answer_guidance=(
            KnowledgeAnswerGuidance(
                f"answer.{atom_id}",
                domain,
                portrait_description,
                allowed_phrases=("证据", "复核", "结构", "路径", "边界"),
                forbidden_phrases=("必然", "一定", "保证", "注定"),
                boundary=boundary,
            ),
        ),
    )


def _sanitize_question_hooks(domain: str, question_hooks: tuple[str, ...]) -> tuple[str, ...]:
    return _derive_question_hooks(
        domain=domain,
        category=domain,
        statement="",
        structured_facts={},
    ) if not question_hooks else tuple(
        dict.fromkeys(
            hook
            for hook in question_hooks
            if hook in _allowed_question_hooks_for_domain(domain)
        )
    ) or _derive_question_hooks(domain=domain, category=domain, statement="", structured_facts={})


def _allowed_question_hooks_for_domain(domain: str) -> tuple[str, ...]:
    return {
        "strength": ("q_strength_assessment",),
        "ten_god": ("q_ten_god_focus", "q_ten_god_metadata", "q_hidden_stem_role"),
        "useful_god": ("q_useful_god_candidates", "q_useful_god_evidence_gaps"),
        "element": ("q_element_balance", "q_element_support_pressure"),
        "branch": ("q_branch_relation_detail", "q_time_vs_natal_relation", "q_structure_overview"),
        "wealth": ("q_income_stability", "q_income_factors"),
        "pattern": ("q_pattern_structure",),
        "time": ("q_time_layer_context", "q_time_relation_triggers"),
        "career": ("q_career_structure",),
        "relationship": ("q_relationship_structure",),
        "health": ("q_health_balance_boundary",),
    }.get(domain, ("q_structure_overview",))
