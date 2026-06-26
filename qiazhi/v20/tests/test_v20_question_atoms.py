from __future__ import annotations

from v20.interaction.question_atoms import (
    QuestionSessionState,
    build_next_question_plan,
    question_atom_registry_manifest,
    question_atoms_for_role,
)
from v20.api.runtime import run_runtime_from_pillars
from v20.api.runtime import _merge_next_question_plan_into_questions
from v20.interaction.questions import QuestionCandidate


def test_v20_question_atom_registry_covers_roles_topics_and_stages() -> None:
    manifest = question_atom_registry_manifest()

    assert manifest["version"] == "v20.question_atom_registry.v1"
    assert manifest["atom_count"] >= 26
    assert manifest["roles"]["guest"] >= 6
    assert manifest["roles"]["user"] >= manifest["roles"]["guest"]
    assert manifest["roles"]["analyst"] >= 8
    assert manifest["roles"]["admin"] >= 2
    assert {"career_structure", "wealth_channel", "timing_trigger", "structure_dynamics", "health_balance", "useful_god", "admin_observe"}.issubset(
        set(manifest["topics"])
    )
    assert {"entry", "focus", "structure", "timing", "observe"}.issubset(set(manifest["stages"]))
    assert "NO_WEB_TEXT_IS_COPIED_VERBATIM" in manifest["guardrails"]


def test_v20_question_atoms_are_role_specific() -> None:
    guest_titles = {atom.template_zh for atom in question_atoms_for_role("guest")}
    analyst_titles = {atom.template_zh for atom in question_atoms_for_role("analyst")}
    admin_titles = {atom.template_zh for atom in question_atoms_for_role("admin")}

    assert any("最值得先看" in title for title in guest_titles)
    assert any("健康和状态" in title for title in guest_titles)
    assert any("结构主链" in title for title in analyst_titles)
    assert any("藏干" in title for title in analyst_titles)
    assert any("suppression" in title for title in admin_titles)
    assert not guest_titles.intersection(admin_titles)


def test_v20_next_question_plan_suppresses_answered_questions_and_prefers_followup() -> None:
    plan = build_next_question_plan(
        role_key="user",
        session_state=QuestionSessionState(
            answered_question_keys=("q_career_structure",),
            answered_topics=("career_structure",),
            last_question_key="q_career_structure",
            last_domain="career",
            last_stage="focus",
            topic_depth={"career_structure": 2},
        ),
        primary_domain="career",
        primary_stage="structure",
        has_time_context=True,
    )

    recommended = plan["recommended_atoms"]
    suppressed = plan["suppressed_atoms"]

    assert plan["version"] == "v20.next_question_plan.v1"
    assert plan["session_memory"]["topic_depth"]["career_structure"] == 2
    assert plan["policy_trace"]["status"] in {"active", "baseline"}
    assert plan["role_journey"]["target_stages"] == ("focus", "structure")
    assert all(row["question_key"] != "q_career_structure" for row in recommended)
    assert any(row["question_key"] == "q_career_structure" for row in suppressed)
    assert recommended[0]["stage"] in {"timing", "advice", "entry", "focus", "structure"}
    assert any("已问过" in row["reason"] or "深度上限" in row["reason"] for row in suppressed)


def test_v20_next_question_plan_uses_time_context_for_timing_questions() -> None:
    without_time = build_next_question_plan(
        role_key="user",
        session_state=QuestionSessionState(last_question_key="q_career_structure", last_domain="career", last_stage="structure"),
        primary_domain="career",
        primary_stage="structure",
        has_time_context=False,
        runtime_policy={},
    )
    with_time = build_next_question_plan(
        role_key="user",
        session_state=QuestionSessionState(last_question_key="q_career_structure", last_domain="career", last_stage="structure"),
        primary_domain="career",
        primary_stage="structure",
        has_time_context=True,
        runtime_policy={},
    )

    without_time_keys = {row["atom_id"] for row in without_time["recommended_atoms"]}
    with_time_keys = {row["atom_id"] for row in with_time["recommended_atoms"]}

    assert "atom.user.timing.trigger" not in without_time_keys
    assert "atom.user.timing.trigger" in with_time_keys
    timing = next(row for row in with_time["recommended_atoms"] if row["atom_id"] == "atom.user.timing.trigger")
    assert "当前有大运流年上下文" in timing["score_reasons"]
    assert "承接上一问合法链路" in timing["score_reasons"]
    assert "符合当前角色追问节奏" in timing["score_reasons"]
    assert "atom.user.timing.trigger" in with_time["active_followup_targets"]
    assert any(row["from_atom_id"] == "atom.user.timing.trigger" for row in with_time["followup_edges"])


def test_v20_next_question_plan_uses_role_journey_and_topic_memory() -> None:
    plan = build_next_question_plan(
        role_key="user",
        session_state=QuestionSessionState(
            answered_topics=("wealth_channel",),
            last_domain="wealth",
            last_stage="timing",
            topic_depth={"wealth_channel": 1},
        ),
        primary_domain="wealth",
        primary_stage="timing",
        has_time_context=True,
        runtime_policy={},
    )

    assert plan["role_journey"]["target_stages"] == ("timing", "advice")
    assert plan["session_memory"]["answered_topics"] == ("wealth_channel",)
    assert plan["session_memory"]["topic_depth"]["wealth_channel"] == 1
    wealth_atoms = [row for row in plan["recommended_atoms"] if row["topic"] == "wealth_channel"]
    assert wealth_atoms
    assert any("同专题已推进，降低重复" in row["score_reasons"] for row in wealth_atoms)
    assert any("避免回退到已过阶段" in row["score_reasons"] for row in wealth_atoms)


def test_v20_next_question_plan_normalizes_measurement_stage_into_atom_journey() -> None:
    plan = build_next_question_plan(
        role_key="user",
        session_state=QuestionSessionState(
            last_question_key="q_career_structure",
            last_domain="career",
            last_stage="domain_reading",
        ),
        primary_domain="career",
        primary_stage="domain_reading",
        has_time_context=True,
        runtime_policy={},
    )

    assert plan["session_memory"]["normalized_last_stage"] == "focus"
    assert plan["role_journey"]["target_stages"] == ("focus", "structure")
    timing = next(row for row in plan["recommended_atoms"] if row["atom_id"] == "atom.user.timing.trigger")
    assert "承接上一问进入时间层" in timing["score_reasons"]


def test_v20_runtime_exposes_next_question_plan_with_answered_suppression() -> None:
    result = run_runtime_from_pillars(
        "丁巳",
        "乙巳",
        "乙丑",
        "乙酉",
        luck_pillar="庚子",
        flow_year_pillar="丙午",
        answered_question_keys=("q_career_structure",),
        input_id="question.atom.runtime",
    )

    plan = result["next_question_plan"]
    recommended_keys = {row["question_key"] for row in plan["recommended_atoms"]}
    suppressed_keys = {row["question_key"] for row in plan["suppressed_atoms"]}

    assert plan["version"] == "v20.next_question_plan.v1"
    assert plan["primary_domain"] == result["mainline_arbitration"]["primary_mainline"]["domain"]
    assert plan["session_memory"]["topic_depth"]["career_structure"] == 1
    assert plan["role_journey"]["role_key"] == "user"
    assert plan["policy_trace"]["status"] in {"active", "baseline"}
    assert {"atom_boost_count", "atom_penalty_count", "topic_boost_count", "stage_boost_count"}.issubset(
        set(plan["policy_trace"])
    )
    assert "q_career_structure" not in recommended_keys
    assert "q_career_structure" in suppressed_keys
    assert any(row["stage"] == "timing" for row in plan["recommended_atoms"])
    assert plan["anchored_recommended_question_count"] == len(plan["recommended_questions"])
    assert plan["recommended_questions"]
    assert all(row["display_title"] for row in plan["recommended_questions"])
    assert any("乙日主" in row["display_title"] for row in plan["recommended_questions"])
    assert "RECOMMENDED_QUESTIONS_USE_BAZI_ANCHORED_DISPLAY_TITLE" in plan["guardrails"]
    assert any(row.get("next_question_atom_id") for row in result["questions"])
    assert any(row.get("next_question_score_reasons") for row in result["questions"])
    assert result["reasoning_orchestrator"]["primary_outputs"]["selected_question"] == "selected_question"


def test_v20_next_question_rank_merge_keeps_highest_ranked_atom_for_same_question_key() -> None:
    questions = (
        QuestionCandidate(
            question_key="q_career_structure",
            question_id="q1",
            title="事业问题",
            domain="career",
            score=0.5,
            source_feature_ids=(),
            boundary="",
            measurement_topic="career",
            measurement_stage="focus",
        ),
    )
    plan = {
        "recommended_atoms": [
            {
                "atom_id": "atom.high",
                "question_key": "q_career_structure",
                "topic": "career_structure",
                "stage": "focus",
                "score": 0.9,
                "score_reasons": ["高优先级"],
            },
            {
                "atom_id": "atom.low",
                "question_key": "q_career_structure",
                "topic": "career_structure",
                "stage": "entry",
                "score": 0.2,
                "score_reasons": ["低优先级"],
            },
        ]
    }

    merged = _merge_next_question_plan_into_questions(questions, plan)

    assert merged[0].next_question_atom_id == "atom.high"
    assert merged[0].next_question_stage == "focus"
    assert merged[0].next_question_score_reasons == ("高优先级",)
