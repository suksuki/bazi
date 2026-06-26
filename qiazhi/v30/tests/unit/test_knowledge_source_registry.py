from __future__ import annotations

from v30.knowledge.source_registry import list_source_families, summarize_source_registry


def test_source_registry_covers_m3_classic_source_families() -> None:
    sources = list_source_families()
    source_ids = {source.source_family_id for source in sources}
    assert "v30.source.zi_ping_pattern_month_command" in source_ids
    assert "v30.source.san_ming_tong_hui_system_catalog" in source_ids
    assert "v30.source.yuan_hai_zi_ping_pattern_catalog" in source_ids
    assert "v30.source.di_tian_sui_flow_mechanism" in source_ids
    assert "v30.source.qiong_tong_bao_jian_climate_review" in source_ids
    assert "v30.source.shen_feng_tong_kao_disease_medicine" in source_ids
    assert all(source.urls for source in sources)
    assert all(source.runtime_boundary for source in sources)
    assert all(source.validation_requirements for source in sources)


def test_source_registry_covers_core_m3_domains_and_boundaries() -> None:
    summary = summarize_source_registry()
    assert summary["version"] == "v30.knowledge_source_registry.v1"
    assert summary["source_family_count"] >= 6
    assert set(summary["domains"]) >= {
        "element",
        "ten_god",
        "branch_relation",
        "time_context",
        "structure_pattern",
        "structure_dynamic",
        "useful_god",
        "domain_rule",
        "rule",
    }
    assert set(summary["rule_families"]) >= {
        "month_command",
        "wang_xiang_xiu_qiu_si",
        "branch_relations",
        "tongguan",
        "zhihua",
        "tiaohou",
        "bing_yao",
    }
    assert summary["boundary"] == "knowledge_source_registry_guides_rule_extraction_not_runtime_verdicts"
