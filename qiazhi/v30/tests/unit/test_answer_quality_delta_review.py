from __future__ import annotations

from v30.validation.answer_quality_delta_review import (
    ANSWER_QUALITY_DELTA_REVIEW_VERSION,
    build_answer_quality_delta_review,
    run_answer_quality_delta_review,
)


def test_answer_quality_delta_review_accepts_current_core_answers() -> None:
    result = run_answer_quality_delta_review(reading_id="test-core-evidence-2")

    assert result["version"] == ANSWER_QUALITY_DELTA_REVIEW_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["answer_quality_delta_ready"] is True
    assert result["decision"]["failed_check_ids"] == []
    assert result["quality_summary"]["covered_domains"] == [
        "career",
        "hidden_factor",
        "relationship",
        "timing",
        "wealth",
    ]
    assert result["next_mainline_selection"]["task_id"] == "CORE-EVIDENCE-3"


def test_answer_quality_delta_review_blocks_generic_answer_rows() -> None:
    result = build_answer_quality_delta_review(
        reading_id="test-core-evidence-2-generic",
        answer_rows=[
            {
                "domain": "career",
                "question_id": "q_v30_user_career_direction",
                "quality_ready": False,
                "answer_text": "旺衰、格局、用神综合参考。需结合后续问答复核。",
                "answer_length": 24,
                "evidence_count": 0,
                "checks": {
                    "question_anchor_present": True,
                    "answer_has_customer_visible_text": False,
                    "domain_specific_language_present": False,
                    "bazi_mechanism_present": False,
                    "evidence_layer_present": False,
                    "boundary_language_present": False,
                    "source_evidence_traceable": False,
                    "generic_or_internal_filler_absent": False,
                },
                "failed_check_ids": [
                    "answer_has_customer_visible_text",
                    "domain_specific_language_present",
                    "bazi_mechanism_present",
                    "evidence_layer_present",
                    "boundary_language_present",
                    "source_evidence_traceable",
                    "generic_or_internal_filler_absent",
                ],
            }
        ],
    )

    assert result["status"] == "blocked"
    assert result["decision"]["answer_quality_delta_ready"] is False
    assert "answer_quality_rows_failed" in result["decision"]["blockers"]
    assert "source_evidence_traceable" in result["decision"]["failed_check_ids"]
