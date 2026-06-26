from __future__ import annotations

from v30.validation import run_synthetic_tier
from v30.validation.synthetic_typical_bazi_answer_calibration import (
    SYNTHETIC_TYPICAL_BAZI_ANSWER_CALIBRATION_VERSION,
    build_synthetic_typical_bazi_answer_calibration,
    run_synthetic_typical_bazi_answer_calibration,
)


def test_core_cal_s1_typical_answer_calibration_ready() -> None:
    result = run_synthetic_typical_bazi_answer_calibration()

    assert result["version"] == SYNTHETIC_TYPICAL_BAZI_ANSWER_CALIBRATION_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["synthetic_typical_answer_calibration_ready"] is True
    assert result["decision"]["failed_case_ids"] == []
    assert result["decision"]["case_count"] >= 5
    assert result["next_mainline_selection"]["task_id"] == "CORE-CAL-S2"


def test_core_cal_s1_blocks_internal_or_english_leak() -> None:
    result = build_synthetic_typical_bazi_answer_calibration(
        case_rows=[
            {
                "case_id": "bad.leak",
                "label": "leak",
                "day_master": "庚",
                "question_id": "q_v30_user_wealth_tendency",
                "expected_domain_tokens": ["财运"],
                "expected_mechanism_tokens": ["财星"],
                "answer": {
                    "text": "庚日主财运看财星。Use domain language as review path language, not life-result prediction. v30.rule",
                    "evidence_ids": ["e1", "e2", "e3", "e4", "e5"],
                    "boundary": "rule_bound_answer_no_llm_fact_mutation",
                },
            }
        ]
    )

    assert result["status"] == "blocked"
    assert result["decision"]["synthetic_typical_answer_calibration_ready"] is False
    assert "no_internal_or_english_leak" in result["decision"]["failed_check_ids"]


def test_synthetic_typical_bazi_answer_tier_is_registered() -> None:
    result = run_synthetic_tier("synthetic_typical_bazi_answer")

    assert result.suite_id == "v30.synthetic.synthetic_typical_bazi_answer"
    assert result.passed is True
    assert result.case_count >= 3
