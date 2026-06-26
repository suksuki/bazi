from __future__ import annotations

from v30.validation import SYNTHETIC_UI_CORE_READING_PRODUCT_CASES, run_synthetic_tier


def test_ui_core_reading_product_synthetic_tier_passes() -> None:
    result = run_synthetic_tier("ui_core_reading_product")

    assert result.suite_id == "v30.synthetic.ui_core_reading_product"
    assert result.case_count == len(SYNTHETIC_UI_CORE_READING_PRODUCT_CASES)
    assert result.case_count >= 4
    assert result.passed
    assert result.failed_count == 0

    for row in result.results:
        quality = row.observed["ui_core_reading_product_quality"]
        assert quality["version"] == "v30.ui_core_reading_product.synthetic_quality.v1"
        assert quality["product_ready"] is True
        assert quality["basic_assertion_count"] >= 5
        assert quality["feature_count"] >= 4
        assert quality["portrait_count"] >= 4
        assert quality["path_count"] >= 3
        assert quality["domain_card_path_summary_count"] >= 3
        assert quality["domain_card_path_assertion_count"] >= 3
        assert quality["role_answer_differentiated"] is True
        assert quality["llm_context_required_layers_present"] is True
        assert quality["missing_llm_context_layers"] == []
        assert quality["generic_language_hit_count"] == 0
        assert quality["internal_leak_count"] == 0
