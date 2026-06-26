from __future__ import annotations

from dataclasses import replace

from v20.validation.synthetic_bazi_evaluator import evaluate_synthetic_bazi_actual, evaluate_synthetic_bazi_replay
from v20.validation.synthetic_schema import NegativeExpectation, minimal_synthetic_bazi_cases


def test_v20_synthetic_bazi_evaluator_accepts_expected_actual() -> None:
    case = minimal_synthetic_bazi_cases()[0]
    actual = _actual_for_case(case)

    result = evaluate_synthetic_bazi_actual(case, actual)

    assert result["ok"] is True
    assert result["failures"] == ()
    assert {row["evaluator"] for row in result["evaluator_results"]} == {
        "rule_domains",
        "portrait_labels",
        "questions",
        "role_views",
        "role_answer_governance",
        "answer_safety",
    }
    assert result["runtime_mutation"] is False


def test_v20_synthetic_bazi_evaluator_reports_rule_portrait_question_and_role_failures() -> None:
    base = minimal_synthetic_bazi_cases()[0]
    case = replace(
        base,
        negative=NegativeExpectation(
            forbidden_portrait_labels=("财星压力",),
            forbidden_question_stages=("observe",),
        ),
    )
    actual = {
        "decision_domains": ("career",),
        "portrait_labels": ("财星压力",),
        "question_keys": ("q_other",),
        "question_stages": ("observe",),
        "role_views": {
            "guest": {
                "question_count": 9,
                "question_stages": ("review",),
                "visibility_level": "technical_review",
            }
        },
    }

    result = evaluate_synthetic_bazi_actual(case, actual)
    failures = set(result["failures"])

    assert result["ok"] is False
    assert "missing_rule_domain:wealth" in failures
    assert "missing_rule_domain:strength" in failures
    assert "forbidden_portrait_label:财星压力" in failures
    assert "missing_question_key:q_income_stability" in failures
    assert "forbidden_question_stage:observe" in failures
    assert "role_question_count_exceeded:guest" in failures
    assert "role_visibility_mismatch:guest:technical_review" in failures
    assert "role_forbidden_stage:guest:review" in failures
    assert "missing_role_answer_boundary_density:guest" in failures
    assert "missing_role_answer_style_policy:guest" in failures
    assert "missing_role_view:user" in failures


def test_v20_synthetic_bazi_evaluator_accepts_replay_payload() -> None:
    case = minimal_synthetic_bazi_cases()[0]
    replay = {"actual": _actual_for_case(case)}

    result = evaluate_synthetic_bazi_replay(case, replay)

    assert result["ok"] is True
    assert result["case_id"] == case.case_id
    assert "NO_POLICY_POINTER_MUTATION" in result["guardrails"]


def _actual_for_case(case) -> dict[str, object]:
    return {
        "decision_domains": case.expected.rule_domains,
        "portrait_labels": case.expected.portrait_labels,
        "question_keys": case.expected.question_keys,
        "question_stages": ("focus", "structure"),
        "answer_text": "当前命局可见：财星需要结合日主承载复核。边界：只说明已见结构和可复核方向，不作固定吉凶或具体时间断语。",
        "role_views": {
            "guest": {
                "question_count": 2,
                "question_stages": ("entry",),
                "visibility_level": "public_entry",
                "answer_governance_quality_band": "strong",
                "answer_governance_quality_score": 1.0,
                "answer_boundary_density": "plain_boundary",
                "answer_style_policy": "compress_to_plain_boundary",
            },
            "user": {
                "question_count": 4,
                "question_stages": ("guided",),
                "visibility_level": "public_guided",
                "answer_governance_quality_band": "strong",
                "answer_governance_quality_score": 1.0,
                "answer_boundary_density": "guided_boundary",
                "answer_style_policy": "preserve_guided_boundary",
            },
            "analyst": {
                "question_count": 6,
                "question_stages": ("technical_review",),
                "visibility_level": "technical_review",
                "answer_governance_quality_band": "strong",
                "answer_governance_quality_score": 1.0,
                "answer_boundary_density": "technical_boundary_review",
                "answer_style_policy": "preserve_review_boundary",
            },
            "admin": {
                "question_count": 8,
                "question_stages": ("full_observation",),
                "visibility_level": "system_observation",
                "answer_governance_quality_band": "strong",
                "answer_governance_quality_score": 1.0,
                "answer_boundary_density": "full_boundary_observation",
                "answer_style_policy": "preserve_full_governance_signal",
            },
        },
    }
