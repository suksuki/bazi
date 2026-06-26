from __future__ import annotations

from v30.validation.runtime_answer_integration_delta_review import (
    RUNTIME_ANSWER_INTEGRATION_DELTA_REVIEW_VERSION,
    build_runtime_answer_integration_delta_review,
    run_runtime_answer_integration_delta_review,
)


def test_runtime_answer_integration_delta_review_accepts_runtime_and_api_paths() -> None:
    result = run_runtime_answer_integration_delta_review(reading_id="pytest-core-evidence-5")

    assert result["version"] == RUNTIME_ANSWER_INTEGRATION_DELTA_REVIEW_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["runtime_answer_integration_ready"] is True
    assert result["decision"]["failed_check_ids"] == []
    assert result["quality_summary"]["row_count"] >= 3
    assert result["next_mainline_selection"]["task_id"] == "CORE-EVIDENCE-6"


def test_runtime_answer_integration_delta_review_blocks_generic_answer_panel() -> None:
    result = build_runtime_answer_integration_delta_review(
        reading_id="pytest-core-evidence-5-generic",
        integration_rows=[
            {
                "row_id": "generic_answer_panel",
                "integration_ready": False,
                "checks": {
                    "answer_panel_present": True,
                    "answer_text_is_bazi_specific": False,
                    "answer_text_no_customer_leak": True,
                    "llm_status_is_expected": True,
                    "llm_metadata_is_customer_safe": True,
                    "context_summary_has_product_layers": True,
                    "chart_facts_stable": True,
                    "answer_boundary_non_mutating": True,
                },
                "failed_check_ids": ["answer_text_is_bazi_specific"],
            }
        ],
    )

    assert result["status"] == "blocked"
    assert result["decision"]["runtime_answer_integration_ready"] is False
    assert "answer_text_is_bazi_specific" in result["decision"]["failed_check_ids"]
