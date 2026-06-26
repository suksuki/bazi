from __future__ import annotations

from pydantic import Field

from v30.contracts import V30Model


SOURCE_REGISTRY_VERSION = "v30.knowledge_source_registry.v1"


class KnowledgeSourceFamily(V30Model):
    source_family_id: str
    title: str
    source_tier: str
    domains: list[str] = Field(default_factory=list)
    rule_families: list[str] = Field(default_factory=list)
    extraction_targets: list[str] = Field(default_factory=list)
    validation_requirements: list[str] = Field(default_factory=list)
    urls: list[str] = Field(default_factory=list)
    runtime_boundary: str


SOURCE_FAMILIES: tuple[KnowledgeSourceFamily, ...] = (
    KnowledgeSourceFamily(
        source_family_id="v30.source.zi_ping_pattern_month_command",
        title="Zi Ping pattern and month-command useful-god tradition",
        source_tier="classic_primary_or_classic_digest",
        domains=["structure_pattern", "useful_god", "strength", "time_context"],
        rule_families=["month_command", "pattern_success_failure_rescue", "candidate_useful_god"],
        extraction_targets=["structure_pattern_candidate_rules", "useful_god_candidate_boundaries", "pattern_failure_rescue_counterevidence"],
        validation_requirements=["must_remain_candidate_review", "must_expose_month_command_evidence", "must_block_fixed_geju_or_useful_god_verdict"],
        urls=["https://www.luckclub.cn/bazi/002/014/", "https://zh.wikipedia.org/wiki/%E5%AD%90%E5%B9%B3%E7%9C%9F%E8%A9%AE"],
        runtime_boundary="source_family_supports_pattern_candidates_not_fixed_destiny_verdict",
    ),
    KnowledgeSourceFamily(
        source_family_id="v30.source.san_ming_tong_hui_system_catalog",
        title="San Ming Tong Hui five-element, ten-god, relation, luck and pattern catalog",
        source_tier="classic_primary_digest",
        domains=["element", "ten_god", "branch_relation", "time_context", "structure_pattern"],
        rule_families=["five_element_generation_control", "wang_xiang_xiu_qiu_si", "branch_relations", "luck_flow_review"],
        extraction_targets=["feature_atoms", "branch_relation_rules", "time_layer_review_rules", "classic_pattern_catalog"],
        validation_requirements=["must_separate_fact_relation_from_prediction", "must_expose_relation_evidence_ids", "must_block_single_factor_event_claim"],
        urls=["https://www.luckclub.cn/bazi/005/"],
        runtime_boundary="source_family_supports_feature_and_relation_atoms_not_event_prediction",
    ),
    KnowledgeSourceFamily(
        source_family_id="v30.source.yuan_hai_zi_ping_pattern_catalog",
        title="Yuan Hai Zi Ping ten-god and pattern catalog",
        source_tier="classic_primary_digest",
        domains=["ten_god", "structure_pattern", "useful_god", "branch_relation"],
        rule_families=["ten_god_categories", "inner_outer_patterns", "branch_combination_conflict", "useful_god_review"],
        extraction_targets=["ten_god_family_units", "structure_pattern_catalog", "branch_relation_feature_atoms"],
        validation_requirements=["must_use_as_catalog_not_direct_outcome", "must_require_structure_path_review"],
        urls=["https://www.gushicimingju.com/dianji/yuanhaiziping/", "https://www.luckclub.cn/bazi/001/"],
        runtime_boundary="source_family_supports_cataloged_candidates_not_direct_life_outcomes",
    ),
    KnowledgeSourceFamily(
        source_family_id="v30.source.di_tian_sui_flow_mechanism",
        title="Di Tian Sui flow, generation-control and dynamic mechanism tradition",
        source_tier="classic_primary_or_classic_digest",
        domains=["structure_dynamic", "element", "useful_god", "domain_rule"],
        rule_families=["flow_continuity", "tongguan", "zhihua", "blockage_resolution"],
        extraction_targets=["dynamic_graph_mechanism_paths", "path_resolution_families", "counterevidence_resolution_rules"],
        validation_requirements=["must_emit_mechanism_paths", "must_expose_competing_and_suppressed_paths", "must_not_be_public_verdict_layer"],
        urls=["https://k.sina.com.cn/article_6463721012_181448e34001008o0f.html"],
        runtime_boundary="source_family_supports_dynamic_mechanism_candidates_not_public_verdicts",
    ),
    KnowledgeSourceFamily(
        source_family_id="v30.source.qiong_tong_bao_jian_climate_review",
        title="Qiong Tong Bao Jian seasonal climate and regulation review",
        source_tier="classic_primary_or_classic_digest",
        domains=["time_context", "element", "useful_god", "structure_pattern"],
        rule_families=["tiaohou", "ten_stems_by_month", "climate_regulation"],
        extraction_targets=["climate_review_features", "regulation_useful_god_candidates", "seasonal_boundary_rules"],
        validation_requirements=["must_remain_climate_review", "must_not_directly_set_final_useful_god", "must_expose_season_and_day_stem_evidence"],
        urls=["https://www.haiyunzhai.com/yjzln/283292.html", "https://www.dajiazhao.com/sm/qtbj/", "https://zh.wikipedia.org/wiki/%E7%A9%B7%E9%80%9A%E5%AE%9D%E9%89%B4"],
        runtime_boundary="source_family_supports_climate_review_not_final_useful_god_verdict",
    ),
    KnowledgeSourceFamily(
        source_family_id="v30.source.shen_feng_tong_kao_disease_medicine",
        title="Shen Feng Tong Kao disease-medicine useful-god review",
        source_tier="classic_primary_digest",
        domains=["useful_god", "structure_dynamic", "element", "rule"],
        rule_families=["bing_yao", "diao_ku_wang_ruo", "sun_yi_sheng_zhang", "blockage_counterevidence"],
        extraction_targets=["disease_medicine_review_rules", "blockage_counterevidence", "useful_god_support_weakening_evidence"],
        validation_requirements=["must_emit_support_and_weakening_evidence", "must_preserve_counterevidence_trace", "must_not_override_chart_facts"],
        urls=["https://www.gushicimingju.com/dianji/shenfengtongkao/17337.html"],
        runtime_boundary="source_family_supports_disease_medicine_review_not_fixed_useful_god",
    ),
)


def list_source_families() -> list[KnowledgeSourceFamily]:
    return list(SOURCE_FAMILIES)


def summarize_source_registry() -> dict[str, object]:
    domains = sorted({domain for source in SOURCE_FAMILIES for domain in source.domains})
    rule_families = sorted({family for source in SOURCE_FAMILIES for family in source.rule_families})
    return {
        "version": SOURCE_REGISTRY_VERSION,
        "source_family_count": len(SOURCE_FAMILIES),
        "source_family_ids": [source.source_family_id for source in SOURCE_FAMILIES],
        "domains": domains,
        "rule_families": rule_families,
        "classic_source_count": sum(1 for source in SOURCE_FAMILIES if "classic" in source.source_tier),
        "boundary": "knowledge_source_registry_guides_rule_extraction_not_runtime_verdicts",
    }
