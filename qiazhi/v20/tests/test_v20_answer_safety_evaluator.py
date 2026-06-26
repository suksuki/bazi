from __future__ import annotations

from v20.llm.tasks import review_output_safety
from v20.validation.answer_safety_evaluator import evaluate_answer_governance_quality, evaluate_answer_safety
from v20.validation.synthetic_schema import minimal_synthetic_bazi_cases


def test_v20_answer_safety_evaluator_accepts_bounded_answer_text() -> None:
    case = minimal_synthetic_bazi_cases()[0]
    result = evaluate_answer_safety(
        case,
        {
            "answer_text": "当前命局可见：财星需要结合日主承载复核。边界：只说明已见结构和可复核方向，不作固定吉凶或具体时间断语。",
        },
    )

    assert result["evaluator"] == "answer_safety"
    assert result["ok"] is True
    assert result["failures"] == ()
    governance = result["answer_governance_quality"]
    assert governance["version"] == "v20.answer_governance_quality.v1"
    assert governance["quality_band"] == "strong"
    assert governance["dimensions"]["boundary_hint"] == 1.0
    assert governance["dimensions"]["evidence_language"] == 1.0
    assert result["runtime_mutation"] is False
    assert "LLM_MAY_EXPLAIN_NOT_DECIDE" in result["guardrails"]


def test_v20_answer_safety_evaluator_rejects_assertive_and_internal_text() -> None:
    case = minimal_synthetic_bazi_cases()[0]
    result = evaluate_answer_safety(
        case,
        {
            "answer_text": "v20.rulepath.test 显示你一定会发财。",
        },
    )

    failures = set(result["failures"])
    assert result["ok"] is False
    assert "forbidden_literal" in failures
    assert "internal_id_leak" in failures
    assert "missing_boundary_hint" in failures
    assert result["answer_governance_quality"]["quality_band"] in {"weak", "thin"}


def test_v20_answer_governance_quality_scores_thin_answer_without_rewriting() -> None:
    quality = evaluate_answer_governance_quality("财星可见，可以继续看。")

    assert quality["quality_score"] < 0.8
    assert quality["quality_band"] in {"thin", "usable"}
    assert "boundary_hint" in quality["findings"]
    assert quality["runtime_mutation"] is False
    assert "NO_ANSWER_REWRITE_FROM_QUALITY_SCORE" in quality["guardrails"]


def test_v20_llm_safety_review_exposes_answer_governance_quality() -> None:
    review = review_output_safety(
        "当前命局可见：财星需要结合日主承载复核。边界：只说明证据支持的结构，下一步继续看时间层是否牵动。"
    )

    assert review["result"]["ok"] is True
    assert review["answer_governance_quality"]["quality_band"] == "strong"
    assert "ANSWER_GOVERNANCE_QUALITY_IS_TRAINING_SIGNAL_ONLY" in review["guardrails"]
