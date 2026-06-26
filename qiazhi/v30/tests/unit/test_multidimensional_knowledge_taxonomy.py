from __future__ import annotations

from v30.knowledge import (
    CORE_MACRO_PACK_ID,
    build_macro_dimension_signals,
    load_core_macro_pack,
    summarize_core_macro_pack,
)
from v30.knowledge.packs import MACRO_DIMENSIONS, SOURCE_REFS, multidimensional_taxonomy
from v30.runtime import create_smoke_runtime


def test_multidimensional_taxonomy_covers_core_macro_domains() -> None:
    taxonomy = multidimensional_taxonomy()
    domains = {row["domain"] for row in taxonomy["macro_dimensions"]}
    assert domains >= {
        "foundation",
        "wealth",
        "career",
        "relationship",
        "romance",
        "health",
        "hidden_factor",
    }
    assert len(MACRO_DIMENSIONS) >= 7
    assert all(row.boundaries for row in MACRO_DIMENSIONS)
    assert all(row.training_tags for row in MACRO_DIMENSIONS)


def test_multidimensional_taxonomy_documents_v20_conversion_without_runtime_import() -> None:
    taxonomy = multidimensional_taxonomy()
    local_sources = [row for row in SOURCE_REFS if row.source_type.startswith("local_v20")]
    assert local_sources
    assert all(row.reuse_mode in {"convert_to_v30_pack", "extract_records_then_convert"} for row in local_sources)
    assert "must not import v20.*" in taxonomy["runtime_rule"]


def test_macro_dimensions_keep_high_risk_domains_bounded() -> None:
    by_domain = {row.domain: row for row in MACRO_DIMENSIONS}
    assert any("income" in boundary or "asset" in boundary for boundary in by_domain["wealth"].boundaries)
    assert any("job rank" in boundary or "exam result" in boundary for boundary in by_domain["career"].boundaries)
    assert any("spouse facts" in boundary for boundary in by_domain["romance"].boundaries)
    assert any("diagnosis" in boundary for boundary in by_domain["health"].boundaries)


def test_core_macro_pack_loads_from_taxonomy_as_v30_owned_pack() -> None:
    pack = load_core_macro_pack()
    assert pack.pack_id == CORE_MACRO_PACK_ID
    assert pack.source_policy == "converted_source_material_v30_owned_runtime_pack"
    assert len(pack.items) == len(MACRO_DIMENSIONS)
    domains = {item.domain for item in pack.items}
    assert domains >= {"foundation", "wealth", "career", "relationship", "romance", "health", "hidden_factor"}
    assert all(item.pack_id == CORE_MACRO_PACK_ID for item in pack.items)
    assert all(item.source_hints for item in pack.items)
    assert "V20 assets are source hints, not imports" in pack.runtime_rule


def test_core_macro_pack_summary_is_available_in_runtime_policy_effect() -> None:
    runtime = create_smoke_runtime("v30-core-macro-runtime")
    summary = runtime.question_plan.policy_effect["core_macro_pack_summary"]
    assert summary == summarize_core_macro_pack(load_core_macro_pack(), runtime.feature_evidence)
    assert summary["pack_id"] == CORE_MACRO_PACK_ID
    assert summary["item_count"] >= 7
    assert "foundation" in summary["domains"]
    assert "hidden_factor" in summary["active_domains"]
    assert "review_current_chart_mainline" in summary["question_hooks"]
    assert "dynamic_graph.v2" in summary["structure_hooks"]


def test_core_macro_dimension_signals_are_runtime_consumable() -> None:
    runtime = create_smoke_runtime("v30-core-macro-signals")
    signals = runtime.question_plan.policy_effect["macro_dimension_signals"]
    assert signals == [
        row.model_dump(mode="json")
        for row in build_macro_dimension_signals(runtime.feature_evidence, load_core_macro_pack())
    ]
    domains = {row["domain"] for row in signals}
    assert domains >= {"foundation", "wealth", "career", "relationship", "romance", "health", "hidden_factor"}
    wealth = next(row for row in signals if row["domain"] == "wealth")
    assert wealth["evidence_ids"]
    assert "wealth" in wealth["training_tags"]
    assert wealth["boundary"] == "macro_dimension_signal_is_context_projection_not_verdict"
