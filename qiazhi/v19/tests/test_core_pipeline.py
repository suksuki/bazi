from __future__ import annotations

from v19.core import compare_v18_vs_v19, evaluate, evaluate_core, validate_inference_bundle


def _chart() -> dict:
    return {
        "chart_id": "v19_core_pipeline_case",
        "four_pillars": {
            "year": "甲子",
            "month": "丙辰",
            "day": "戊午",
            "hour": "壬戌",
        },
        "luck_pillar": "癸亥",
        "flow_pillar": "甲辰",
    }


def test_v19_evaluate_defaults_to_core_bazi_without_domain_conclusion() -> None:
    result = evaluate(_chart())

    assert result["intent"] == "core_bazi"
    assert set(result) >= {"features", "strength", "structure", "bazi_inference_bundle"}
    assert "wealth_profile" not in result
    assert "evidence" not in result
    assert "prediction_id" not in result
    assert "ledger" not in result
    assert "conclusions" not in result
    assert all(row["layer"] == "feature" for row in result["features"]["features"])
    assert validate_inference_bundle(result["bazi_inference_bundle"])["valid"] is True


def test_evaluate_core_returns_core_and_valid_inference_language() -> None:
    result = evaluate_core(_chart())

    assert set(result) >= {"features", "strength", "structure", "inference"}
    assert "wealth_profile" not in result
    assert "evidence" not in result
    assert validate_inference_bundle(result["inference"])["valid"] is True
    assert set(result["inference"]) == {
        "version",
        "schema_version",
        "chart_id",
        "day_master_state",
        "ten_god_structure",
        "energy_flow",
        "structural_stability",
        "internal_conflicts",
        "uncertainty_sources",
        "guardrails",
    }


def test_v19_pipeline_order_core_strength_structure_inference() -> None:
    result = evaluate_core(_chart())
    feature_ids = {row["feature_id"] for row in result["features"]["features"]}
    structure_source_ids = {
        row["source_feature_id"]
        for row in result["structure"]["relation_effects"] + result["structure"]["vault_effects"] + result["structure"]["flow_effects"]
    }

    assert structure_source_ids <= feature_ids
    assert "NO_DOMAIN_CONCLUSION" in result["inference"]["guardrails"]
    assert "CORE_BAZI_INFERENCE_LANGUAGE" in result["inference"]["guardrails"]


def test_compare_v18_vs_v19_returns_core_comparison_summary() -> None:
    comparison = compare_v18_vs_v19(_chart())

    assert comparison["chart_id"]
    assert set(comparison["comparison"]) >= {
        "strength_tendency_match",
        "support_score_delta",
        "pressure_score_delta",
        "relation_counts_match",
        "conflict_overlap",
        "difference_notes",
    }
