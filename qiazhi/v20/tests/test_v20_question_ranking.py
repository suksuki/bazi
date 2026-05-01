from __future__ import annotations

from fastapi.testclient import TestClient

from v20.api.runtime import run_runtime_from_pillars
from v20.core.chart import build_chart_facts, chart_input_from_displays
from v20.core.strength import infer_core
from v20.answer.rule_candidate_support import build_rule_candidate_question_ranking
from v20.features.compiler import compile_features
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
    assert "shadow_rule_candidate_validation" in manifest["allowed_learning_inputs"]
    assert "QUESTION_RANKING_IS_REORDER_ONLY" in manifest["guardrails"]


def test_v20_rule_candidate_question_ranking_is_bounded_reorder_only() -> None:
    facts = build_chart_facts(chart_input_from_displays("壬寅", "甲辰", "丙子", "甲午"))
    layer = compile_features(facts, infer_core(facts))
    policy, report = build_rule_candidate_question_ranking(layer)
    baseline = recommend_questions(layer)
    boosted = recommend_questions(layer, ranking_policy=policy)

    assert report["status"] == "active_shadow"
    assert report["runtime_mutation"] is False
    assert policy.max_adjustment <= 0.06
    assert {row.question_key for row in baseline} == {row.question_key for row in boosted}
    assert all(row["ranking_weight"] <= 0.06 for row in report["domain_signals"])


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
    assert any("年柱子与日柱午冲" in row["title"] for row in baseline["questions"])
    assert any("正财" in row["title"] and "财星结构边界" in row["title"] for row in timed["questions"])
    assert all("五行差距" not in row["title"] and "扶助分" not in row["title"] for row in timed["questions"])
    assert any("chart_specific_salience" in row["sources"] for row in timed["feature_discovery"]["ranked_features"])


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
