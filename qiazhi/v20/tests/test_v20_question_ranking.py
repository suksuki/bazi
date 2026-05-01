from __future__ import annotations

from fastapi.testclient import TestClient

from v20.api.runtime import run_runtime_from_pillars
from v20.core.chart import build_chart_facts, chart_input_from_displays
from v20.core.strength import infer_core
from v20.features.compiler import compile_features
from v20.interaction.question_ranker import QuestionRankingPolicy, question_ranking_manifest
from v20.interaction.questions import recommend_questions
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
    assert "QUESTION_RANKING_IS_REORDER_ONLY" in manifest["guardrails"]


def test_v20_question_ranking_policy_endpoint_and_runtime_remain_feature_backed() -> None:
    client = TestClient(app)
    manifest = client.get("/api/v20/questions/ranking-policy").json()
    result = run_runtime_from_pillars("甲子", "戊辰", "甲午", "辛酉", input_id="ranker")

    assert manifest["runtime_mutation"] is False
    assert result["questions"]
    assert all(row["source_feature_ids"] for row in result["questions"])
