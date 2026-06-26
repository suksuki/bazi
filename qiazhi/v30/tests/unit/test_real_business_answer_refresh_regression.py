from __future__ import annotations

from copy import deepcopy

from v30.validation.real_business_answer_refresh_regression import (
    ANSWER_REFRESH_CASES,
    REAL_BUSINESS_ANSWER_REFRESH_REGRESSION_VERSION,
    build_real_business_answer_refresh_regression,
)


def _b2_ready() -> dict[str, object]:
    return {
        "version": "v30.real_business_bazi_reading_regression_pack.v1",
        "decision": {
            "business_reading_regression_ready": True,
        },
    }


def test_b3_answer_refresh_regression_preserves_core_reading_surface() -> None:
    result = build_real_business_answer_refresh_regression(
        b2_regression_pack=_b2_ready(),
        answer_cases=ANSWER_REFRESH_CASES,
    )

    assert result["version"] == REAL_BUSINESS_ANSWER_REFRESH_REGRESSION_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "b3_answer_refresh_regression_ready"
    assert result["refresh_summary"]["answer_case_count"] == len(ANSWER_REFRESH_CASES)
    assert result["refresh_summary"]["passed_answer_case_count"] == len(ANSWER_REFRESH_CASES)
    assert result["refresh_summary"]["stable_core_fingerprint_count"] == len(ANSWER_REFRESH_CASES)
    assert result["next_mainline_selection"]["task_id"] == "B4"
    assert result["policy_boundary"]["chart_fact_mutation_allowed"] is False


def test_b3_blocks_when_b2_regression_pack_is_not_ready() -> None:
    b2 = deepcopy(_b2_ready())
    b2["decision"]["business_reading_regression_ready"] = False  # type: ignore[index]

    result = build_real_business_answer_refresh_regression(
        b2_regression_pack=b2,
        answer_cases=ANSWER_REFRESH_CASES,
    )

    assert result["status"] == "blocked"
    assert result["decision"]["decision_status"] == "b3_answer_refresh_regression_blocked"
    assert "b2_regression_pack_not_ready" in result["decision"]["blockers"]
    assert result["decision"]["chart_fact_mutation_allowed"] is False
