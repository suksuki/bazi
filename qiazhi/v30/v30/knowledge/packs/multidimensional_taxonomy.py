from __future__ import annotations

from pydantic import Field

from v30.contracts import V30Model


MULTIDIMENSIONAL_TAXONOMY_VERSION = "v30.knowledge.multidimensional_taxonomy.20260521"


class KnowledgeSourceRef(V30Model):
    source_id: str
    source_type: str
    path_or_url: str
    reuse_mode: str
    notes: str


class MacroKnowledgeDimension(V30Model):
    dimension_id: str
    label_zh: str
    domain: str
    scope: str
    evidence_domains: list[str] = Field(default_factory=list)
    structure_hooks: list[str] = Field(default_factory=list)
    question_hooks: list[str] = Field(default_factory=list)
    portrait_dimensions: list[str] = Field(default_factory=list)
    training_tags: list[str] = Field(default_factory=list)
    boundaries: list[str] = Field(default_factory=list)
    v20_source_hints: list[str] = Field(default_factory=list)
    public_source_hints: list[str] = Field(default_factory=list)


SOURCE_REFS: tuple[KnowledgeSourceRef, ...] = (
    KnowledgeSourceRef(
        source_id="v20.docs.bazi_knowledge_full_content_zh_v1",
        source_type="local_v20_markdown",
        path_or_url="../v20/docs/bazi_knowledge/catalog/v20_knowledge_full_content_zh_v1.md",
        reuse_mode="convert_to_v30_pack",
        notes="High-level L0-L12 knowledge outline; reuse as reviewed source material only.",
    ),
    KnowledgeSourceRef(
        source_id="v20.knowledge.macro_dimensions",
        source_type="local_v20_code_asset",
        path_or_url="../v20/knowledge/macro_dimensions.py",
        reuse_mode="extract_records_then_convert",
        notes="Contains wealth/career/relationship/romance/health macro dimensions.",
    ),
    KnowledgeSourceRef(
        source_id="v20.knowledge.feature_model",
        source_type="local_v20_code_asset",
        path_or_url="../v20/knowledge/feature_model.py",
        reuse_mode="extract_records_then_convert",
        notes="Contains topic projection boundaries for wealth, career, relationship, romance, and health.",
    ),
    KnowledgeSourceRef(
        source_id="v20.knowledge.loader",
        source_type="local_v20_code_asset",
        path_or_url="../v20/knowledge/loader.py",
        reuse_mode="extract_records_then_convert",
        notes="Large V20 knowledge catalog; convert selected records, do not import runtime.",
    ),
    KnowledgeSourceRef(
        source_id="v20.knowledge.structure_mechanisms",
        source_type="local_v20_code_asset",
        path_or_url="../v20/knowledge/structure_mechanisms.py",
        reuse_mode="extract_records_then_convert",
        notes="Contains structure path mechanisms such as output-controls-authority and output-generates-wealth.",
    ),
    KnowledgeSourceRef(
        source_id="v20.rules.catalog",
        source_type="local_v20_code_asset",
        path_or_url="../v20/rules/catalog.py",
        reuse_mode="extract_records_then_convert",
        notes="Rule catalog concepts can be converted into V30 RuleEvidenceSpec or policy candidates.",
    ),
    KnowledgeSourceRef(
        source_id="public.wikipedia.four_pillars_ten_gods",
        source_type="public_reference",
        path_or_url="https://en.wikipedia.org/wiki/Four_Pillars_of_Destiny",
        reuse_mode="reference_only_no_copy",
        notes="Public reference for Four Pillars and Ten Gods terminology; use only as cross-check.",
    ),
    KnowledgeSourceRef(
        source_id="public.wikipedia.zh_bazi",
        source_type="public_reference",
        path_or_url="https://zh.wikipedia.org/wiki/%E5%85%AB%E5%AD%97%E5%91%BD%E5%AD%A6",
        reuse_mode="reference_only_no_copy",
        notes="Public Chinese reference for pillars, palace associations, and general terminology.",
    ),
)


MACRO_DIMENSIONS: tuple[MacroKnowledgeDimension, ...] = (
    MacroKnowledgeDimension(
        dimension_id="v30.macro.foundation",
        label_zh="基础八字",
        domain="foundation",
        scope="排盘事实、阴阳五行、十神、强弱、格局、用神、地支关系、岁运时间层。",
        evidence_domains=["chart", "element", "ten_god", "branch_relation", "time_context", "useful_god"],
        structure_hooks=["dynamic_graph.v2", "mechanism.ten_god_visibility_context"],
        question_hooks=["review_current_chart_mainline", "confirm_missing_time_context"],
        portrait_dimensions=["context_integrity", "element_context", "ten_god_visibility"],
        training_tags=["foundation", "chart_fact_boundary", "ten_god_context", "time_boundary"],
        boundaries=[
            "ChartContext owns chart facts.",
            "LLM and knowledge packs cannot rewrite pillars, day master, or deterministic chart context.",
        ],
        v20_source_hints=[
            "v20.docs.bazi_knowledge_full_content_zh_v1:L0-L6,L9,L12",
            "v20.knowledge.loader",
            "v20.knowledge.directory_seeds",
        ],
        public_source_hints=[
            "public.wikipedia.four_pillars_ten_gods",
            "public.wikipedia.zh_bazi",
        ],
    ),
    MacroKnowledgeDimension(
        dimension_id="v30.macro.wealth",
        label_zh="财富",
        domain="wealth",
        scope="财星显隐、食伤生财、财库开闭、比劫分夺、承载力、现金流与资产主题。",
        evidence_domains=["ten_god", "element", "branch_relation", "time_context", "rule"],
        structure_hooks=["dynamic_graph.v2", "knowledge.semantic.output_generate_wealth", "knowledge.semantic.peer_competes_wealth"],
        question_hooks=["review_current_chart_mainline", "review_useful_god_candidate_paths"],
        portrait_dimensions=["wealth_channel", "asset_cashflow", "capacity_boundary"],
        training_tags=["wealth", "output_generate_wealth", "peer_competes_wealth", "cashflow_boundary"],
        boundaries=[
            "Do not convert wealth-star presence into income, asset, investment, debt, or event predictions.",
            "Wealth reading must keep source, channel, capacity, competition, and time-layer evidence separate.",
        ],
        v20_source_hints=[
            "v20.knowledge.macro_dimensions:wealth",
            "v20.knowledge.feature_model:projection.wealth",
            "v20.knowledge.loader:v20.micro.wealth.zuogong_receive",
            "v20.knowledge.loader:wealth.asset_cashflow.structure",
        ],
    ),
    MacroKnowledgeDimension(
        dimension_id="v30.macro.career",
        label_zh="事业",
        domain="career",
        scope="官杀规则、印星平台、食伤表达、格局承接、学业考试、创业管理和职业结构。",
        evidence_domains=["ten_god", "element", "branch_relation", "time_context", "rule"],
        structure_hooks=[
            "dynamic_graph.v2",
            "knowledge.semantic.output_controls_authority",
            "knowledge.semantic.authority_generate_resource",
        ],
        question_hooks=["review_current_chart_mainline", "review_useful_god_candidate_paths"],
        portrait_dimensions=["career_structure", "authority_pressure", "resource_platform"],
        training_tags=["career", "authority", "resource", "output_authority_path", "study_exam_boundary"],
        boundaries=[
            "Do not convert authority/resource/output signals into job rank, exam result, promotion, or business outcome.",
            "Career reading must keep role pressure, platform support, output conflict, and capacity evidence separate.",
        ],
        v20_source_hints=[
            "v20.knowledge.macro_dimensions:career",
            "v20.knowledge.feature_model:projection.career",
            "v20.knowledge.loader:career.authority.zuogong_path",
            "v20.knowledge.loader:career.study_exam.learning_path",
            "v20.knowledge.loader:career.startup_management.context",
        ],
    ),
    MacroKnowledgeDimension(
        dimension_id="v30.macro.relationship",
        label_zh="关系",
        domain="relationship",
        scope="人际、合作、比劫互动、资源分配、宫位互动、家庭父母与子女家庭主题。",
        evidence_domains=["ten_god", "branch_relation", "time_context", "rule"],
        structure_hooks=["dynamic_graph.v2", "mechanism.branch_relation_dynamic_review"],
        question_hooks=["review_current_chart_mainline", "discover_hidden_factor_amplifier"],
        portrait_dimensions=["social_peer_network", "family_resource_context", "palace_topic_projection"],
        training_tags=["relationship", "peer_interaction", "family_boundary", "palace_boundary"],
        boundaries=[
            "Do not infer family privacy, third-party facts, betrayal, litigation, pregnancy, child outcome, or exact timing.",
            "Relationship reading must keep ten-god interaction, branch relation, palace layer, and time layer separate.",
        ],
        v20_source_hints=[
            "v20.knowledge.macro_dimensions:relationship",
            "v20.knowledge.loader:relationship.family_parent.resource_context",
            "v20.knowledge.loader:relationship.children_family.context",
            "v20.knowledge.loader:relationship.social_peer.network",
        ],
    ),
    MacroKnowledgeDimension(
        dimension_id="v30.macro.romance",
        label_zh="感情",
        domain="romance",
        scope="伴侣星、夫妻宫、日支、合冲引动、亲密关系边界和关系承接。",
        evidence_domains=["ten_god", "branch_relation", "time_context", "rule"],
        structure_hooks=["dynamic_graph.v2", "mechanism.branch_relation_dynamic_review"],
        question_hooks=["review_current_chart_mainline", "discover_hidden_factor_amplifier"],
        portrait_dimensions=["romance_context", "spouse_palace_context", "relationship_sensitivity"],
        training_tags=["romance", "spouse_palace", "relationship_boundary"],
        boundaries=[
            "Do not infer spouse facts, relationship outcome, third-party facts, marriage/divorce timing, or private events.",
            "Romance reading remains a relationship subdomain until dedicated V30 rules are validated.",
        ],
        v20_source_hints=[
            "v20.knowledge.macro_dimensions:romance",
            "v20.knowledge.feature_model:projection.romance",
            "v20.knowledge.loader:v20.palace.application.spouse_career_hour_boundary",
        ],
    ),
    MacroKnowledgeDimension(
        dimension_id="v30.macro.health",
        label_zh="健康",
        domain="health",
        scope="五行偏性、寒暖燥湿、压力恢复、作息节律和医疗禁断边界。",
        evidence_domains=["element", "branch_relation", "time_context", "rule"],
        structure_hooks=["dynamic_graph.v2"],
        question_hooks=["review_current_chart_mainline", "confirm_missing_time_context"],
        portrait_dimensions=["health_rhythm_recovery", "element_climate"],
        training_tags=["health", "rhythm_recovery", "medical_boundary"],
        boundaries=[
            "Do not provide diagnosis, treatment, disease prediction, accident prediction, or medical advice.",
            "Health reading only discusses structural tendency, rhythm, pressure, and recovery boundaries.",
        ],
        v20_source_hints=[
            "v20.knowledge.macro_dimensions:health",
            "v20.knowledge.feature_model:projection.health",
            "v20.knowledge.loader:portrait.health_rhythm_recovery",
        ],
    ),
    MacroKnowledgeDimension(
        dimension_id="v30.macro.hidden_factor",
        label_zh="隐藏属性与放大因子",
        domain="hidden_factor",
        scope="隐藏属性、隐藏放大因子、特殊年份、重复状态、边界事件和用户反馈校准。",
        evidence_domains=["ten_god", "feedback", "rule", "time_context"],
        structure_hooks=["mechanism.hidden_factor_dialogue_probe"],
        question_hooks=["discover_hidden_factor_amplifier", "confirm_missing_time_context"],
        portrait_dimensions=["latent_pattern", "latent_amplifier"],
        training_tags=["hidden_factor", "feedback_calibration", "special_year_boundary"],
        boundaries=[
            "Hidden factor cannot be calculated into fact without dialogue feedback.",
            "Amplifier candidates require special-year and repeated-state evidence, and denial/conflict states must remain traceable.",
        ],
        v20_source_hints=[
            "v20.interaction.latent_event_calibration",
            "v20.knowledge.loader:hidden factor and latent event records",
        ],
    ),
)


def multidimensional_taxonomy() -> dict[str, object]:
    return {
        "version": MULTIDIMENSIONAL_TAXONOMY_VERSION,
        "source_refs": [row.model_dump(mode="json") for row in SOURCE_REFS],
        "macro_dimensions": [row.model_dump(mode="json") for row in MACRO_DIMENSIONS],
        "runtime_rule": "V30 may convert V20 knowledge assets into V30-owned packs, but runtime must not import v20.*.",
    }
