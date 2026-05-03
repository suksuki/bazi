from __future__ import annotations

from fastapi.testclient import TestClient
from collections import Counter

from v20.api.runtime import run_runtime_from_pillars
from v20.core.chart import build_chart_facts, chart_input_from_displays
from v20.core.strength import infer_core
from v20.decision.questions import resolve_requested_question
from v20.features.compiler import compile_features
from v20.features.schema import FeatureLayer
from v20.interaction.question_ranker import QuestionRankingPolicy, question_ranking_manifest
from v20.interaction.questions import QuestionCandidate
from v20.interaction.questions import recommend_questions
from v20.measurement.domain_alignment import align_question_candidate
from v20.server import app


def test_v20_question_ranking_policy_reorders_only_existing_candidates() -> None:
    facts = build_chart_facts(chart_input_from_displays("甲子", "戊辰", "甲午", "辛酉"))
    layer = compile_features(facts, infer_core(facts))
    baseline = recommend_questions(layer)
    boosted = recommend_questions(
        layer,
        ranking_policy=QuestionRankingPolicy(
            policy_id="test.boost.wealth",
            domain_weights={"wealth": 0.4},
            source="test",
            status="draft",
        ),
    )

    assert {row.question_key for row in baseline} == {row.question_key for row in boosted}
    assert boosted[0].domain == "wealth"
    assert boosted[0].question_key in {row.question_key for row in baseline}


def test_v20_question_ranking_manifest_blocks_new_question_generation() -> None:
    manifest = question_ranking_manifest()

    assert manifest["runtime_mutation"] is False
    assert "new_question_key" in manifest["blocked_learning_outputs"]
    assert "decision_report_validation" in manifest["allowed_learning_inputs"]
    assert "QUESTION_RANKING_IS_REORDER_ONLY" in manifest["guardrails"]


def test_v20_question_ranking_policy_endpoint_and_runtime_remain_feature_backed() -> None:
    client = TestClient(app)
    manifest = client.get("/api/v20/questions/ranking-policy").json()
    result = run_runtime_from_pillars("甲子", "戊辰", "甲午", "辛酉", input_id="ranker")

    assert manifest["runtime_mutation"] is False
    assert result["questions"]
    assert all(row["source_feature_ids"] for row in result["questions"])
    assert all(row["alignment_status"] in {"bazi_core_aligned", "bazi_projection_aligned"} for row in result["questions"])


def test_v20_questions_surface_chart_specific_material_without_new_keys() -> None:
    baseline = run_runtime_from_pillars("甲子", "戊辰", "甲午", "辛酉", input_id="ranker.baseline")
    timed = run_runtime_from_pillars(
        "庚午",
        "辛巳",
        "丁丑",
        "乙巳",
        input_id="ranker.timed",
        flow_year_pillar="丙午",
        luck_pillar="甲申",
    )

    assert {row["question_key"] for row in baseline["questions"]} != set()
    assert {row["question_key"] for row in baseline["questions"]} >= {"q_strength_assessment", "q_branch_relation_detail"}
    assert {row["question_key"] for row in timed["questions"]} >= {"q_time_layer_context", "q_income_stability"}
    assert any("关系" in row["title"] for row in baseline["questions"] if row["question_key"] == "q_branch_relation_detail")
    assert any("财运" in row["title"] or "财星" in row["title"] for row in timed["questions"])
    assert all("五行差距" not in row["title"] and "扶助分" not in row["title"] for row in timed["questions"])
    assert timed["decision_report"]["decision_count"] >= 1


def test_v20_questions_include_strategy_and_be_diversified() -> None:
    runtime = run_runtime_from_pillars("甲子", "戊辰", "甲午", "辛酉", input_id="ranker.strategy")

    questions = runtime["questions"]
    strategies = {row.get("question_strategy", "") for row in questions}

    assert len(questions) >= 4
    assert "" not in strategies
    assert len(strategies) >= 2


def test_v20_question_alignment_blocks_off_core_prompts() -> None:
    facts = build_chart_facts(chart_input_from_displays("庚午", "辛巳", "丁丑", "乙巳"))
    layer = compile_features(facts, infer_core(facts))
    questions = recommend_questions(layer)
    bad = QuestionCandidate(
        question_key="q_lottery_pick",
        title="今天适合买什么彩票号码？",
        domain="lottery",
        score=0.99,
        source_feature_ids=("feature.wealth.material_available",),
        boundary="不属于八字命理结构测算。",
        measurement_topic="lottery",
        measurement_stage="off_topic",
    )
    alignment = align_question_candidate(
        question_key=bad.question_key,
        domain=bad.domain,
        title=bad.title,
        source_feature_ids=bad.source_feature_ids,
        boundary=bad.boundary,
    )

    assert questions
    assert all(row.alignment_status in {"bazi_core_aligned", "bazi_projection_aligned"} for row in questions)
    assert all(row.bazi_focus for row in questions)
    assert alignment.ok is False
    assert "domain_not_bazi_measurement:lottery" in alignment.failures


def test_v20_resolve_question_prefers_rule_aligned_candidate_for_same_key() -> None:
    feature_layer = FeatureLayer(version="v20.question.unit", features=())
    questions = (
        QuestionCandidate(
            question_key="q_useful_god_candidates",
            title="通用用神问题",
            domain="useful_god",
            score=0.9,
            source_feature_ids=("f_1",),
            boundary="结构复核",
            measurement_topic="用神",
            measurement_stage="projection",
            source_rule_key="rule.strength.capacity",
            source_decision_status="confirmed",
        ),
        QuestionCandidate(
            question_key="q_useful_god_candidates",
            title="更具体用神问题",
            domain="useful_god",
            score=0.8,
            source_feature_ids=("f_2",),
            boundary="结构复核",
            measurement_topic="用神",
            measurement_stage="projection",
            source_rule_key="rule.useful_god.candidate_gate",
            source_decision_status="confirmed",
        ),
    )
    selected = resolve_requested_question(
        questions=questions,
        question_key="q_useful_god_candidates",
        question_id="",
        feature_layer=feature_layer,
    )
    assert selected.source_rule_key.startswith("rule.useful_god.")


def test_v20_question_generation_limits_repetition_per_key() -> None:
    runtime = run_runtime_from_pillars("乙酉", "戊申", "丁丑", "壬辰", input_id="ranking.unique")
    counts = Counter(row["question_key"] for row in runtime["questions"])
    assert max(counts.values()) <= 1


def test_v20_question_agent_suppresses_answered_question_and_refreshes_followups() -> None:
    first = run_runtime_from_pillars(
        "甲子",
        "戊辰",
        "甲午",
        "辛酉",
        input_id="ranking.agent.first",
        user_text="我想看财运",
    )
    answered = first["questions"][0]
    refreshed = run_runtime_from_pillars(
        "甲子",
        "戊辰",
        "甲午",
        "辛酉",
        input_id="ranking.agent.second",
        question_id=answered["question_id"],
        user_text=answered["title"],
        answered_question_ids=(answered["question_id"],),
    )

    assert refreshed["selected_question"]["question_id"] == answered["question_id"]
    assert answered["question_id"] not in {row["question_id"] for row in refreshed["questions"]}
    assert refreshed["question_agent_state"]["suppressed_question_count"] >= 1
    assert refreshed["question_agent_state"]["generated_followup_count"] >= 1
    assert any(row["question_strategy"] == "agent_followup" for row in refreshed["questions"])
    assert all("RuleSpec" not in row["title"] and "条件成立" not in row["title"] for row in refreshed["questions"])
