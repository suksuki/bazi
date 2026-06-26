from __future__ import annotations

from v20.api.runtime import run_runtime_from_pillars
from v20.interaction.questions import QuestionCandidate
from v20.orchestrator.question_focus import align_questions_to_mainline


def _question(key: str, domain: str, score: float) -> QuestionCandidate:
    return QuestionCandidate(
        question_key=key,
        title=key,
        domain=domain,
        score=score,
        source_feature_ids=(f"feature.{domain}",),
        boundary="只做结构测算，不输出断言。",
        measurement_topic=domain,
        measurement_stage="structure_review",
        question_id=f"id.{key}",
    )


def test_v20_question_focus_selects_primary_mainline_domain_when_default_question_is_unbound() -> None:
    questions = (
        _question("q_wealth", "wealth", 0.88),
        _question("q_strength", "strength", 0.81),
        _question("q_branch", "branch", 0.79),
    )
    focused, selected, report = align_questions_to_mainline(
        questions,
        questions[0],
        {"primary_mainline": {"candidate_key": "mainline.strength", "domain": "strength"}},
    )

    assert selected.question_key == "q_strength"
    assert focused[0].question_key == "q_strength"
    assert report["status"] == "selected_mainline_domain_question"
    assert report["primary_domain"] == "strength"
    assert "QUESTION_FOCUS_FOLLOWS_MAINLINE_ARBITRATION" in report["guardrails"]


def test_v20_question_focus_preserves_explicit_user_question() -> None:
    questions = (
        _question("q_wealth", "wealth", 0.88),
        _question("q_strength", "strength", 0.81),
    )
    focused, selected, report = align_questions_to_mainline(
        questions,
        questions[0],
        {"primary_mainline": {"candidate_key": "mainline.strength", "domain": "strength"}},
        explicit_question_requested=True,
    )

    assert selected.question_key == "q_wealth"
    assert focused[0].question_key == "q_wealth"
    assert report["status"] == "explicit_question_preserved"
    assert report["explicit_question_requested"] is True


def test_v20_question_focus_consumes_fast_track_runtime_policy() -> None:
    questions = (
        _question("q_career_low", "career", 0.5),
        _question("q_career_high", "career", 0.54),
        _question("q_wealth", "wealth", 0.9),
    )
    focused, selected, report = align_questions_to_mainline(
        questions,
        questions[0],
        {"primary_mainline": {"candidate_key": "mainline.career", "domain": "career"}},
        runtime_policy_pointer={
            "runtime_applied": True,
            "active_policy_version": "v20.orchestrator_policy.candidate.test",
            "policy_payload": {
                "question_focus_policy": (
                    {
                        "runtime_allowed": True,
                        "domain": "career",
                        "average_strength": 1.0,
                    },
                )
            },
        },
    )

    assert selected.domain == "career"
    assert focused[0].domain == "career"
    assert focused[0].score >= 0.6
    assert report["runtime_policy_effect"]["status"] == "applied"
    assert report["runtime_policy_effect"]["domain_boost"] == 0.04
    assert "FAST_TRACK_POLICY_CAN_RERANK_QUESTIONS" in report["guardrails"]


def test_v20_runtime_exposes_question_mainline_focus_and_keeps_selected_first() -> None:
    result = run_runtime_from_pillars("甲子", "戊辰", "甲午", "辛酉", input_id="v20.question-focus")
    focus = result["question_mainline_focus"]

    assert focus["version"] == "v20.question_mainline_focus.v1"
    assert focus["runtime_mutation"] is False
    assert result["questions"][0]["question_key"] == result["selected_question"]["question_key"]
    assert result["question_intent_model"]["selected_question_intent"]["question_key"] == result["selected_question"]["question_key"]
    if focus["status"] in {"selected_mainline_domain_question", "already_aligned"}:
        assert result["selected_question"]["domain"] == result["mainline_arbitration"]["primary_mainline"]["domain"]
