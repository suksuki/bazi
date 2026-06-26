from __future__ import annotations

from collections import Counter

from v20.api.runtime import run_runtime_from_pillars
from v20.core.chart import build_chart_facts, chart_input_from_displays
from v20.core.strength import infer_core
from v20.decision.questions import resolve_requested_question
from v20.decision.question_source_runtime import build_question_source_ranking_report
from v20.decision.question_sources import question_source_manifest
from v20.graph.question_source_graph import arbitrate_question_source_paths, build_question_source_paths
from v20.features.compiler import compile_features
from v20.features.schema import FeatureLayer
from v20.features.schema import BaziFeature
from v20.interaction.question_ranker import QuestionRankingPolicy, question_ranking_manifest
from v20.interaction.question_seed_registry import (
    SEED_QUESTION_STRATEGY,
    build_seed_question_candidates,
    question_seed_registry_manifest,
)
from v20.interaction.questions import QuestionCandidate
from v20.interaction.questions import recommend_questions
from v20.measurement.domain_alignment import align_question_candidate
from v20.server import app


def _endpoint(path: str, method: str = "GET"):
    method = method.upper()
    for route in app.routes:
        if getattr(route, "path", "") == path and method in getattr(route, "methods", set()):
            return route.endpoint
    raise AssertionError(f"route not found: {method} {path}")


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


def test_v20_decision_question_source_manifest_keeps_generation_order_explicit() -> None:
    manifest = question_source_manifest()
    source_keys = tuple(row["source_key"] for row in manifest)
    orders = tuple(int(row["order"]) for row in manifest)

    assert source_keys[:5] == (
        "runtime_fusion",
        "mainline",
        "portrait_axis",
        "decision_hit",
        "feature_hook",
    )
    assert "practitioner_refresh" in source_keys
    assert "latent_event" in source_keys
    assert source_keys[-1] == "fallback"
    assert orders == tuple(sorted(orders))


def test_v20_question_source_graph_consumes_manifest_without_generating_questions() -> None:
    paths = build_question_source_paths()
    report = arbitrate_question_source_paths()
    source_keys = {row.source_key for row in paths}
    selected_keys = {str(row["source_key"]) for row in report["selected_paths"]}

    assert source_keys >= {"runtime_fusion", "mainline", "seed_registry", "practitioner_refresh", "latent_event", "fallback"}
    assert report["runtime_mutation"] is False
    assert "NO_NEW_QUESTION_GENERATION" in report["guardrails"]
    assert "fallback" not in selected_keys
    assert any(row.conflict_tags for row in paths if row.source_key == "seed_registry")
    assert any("practitioner_feedback" in row.learning_tags for row in paths if row.source_key == "practitioner_refresh")


def test_v20_question_source_graph_applies_path_propagation_conflict_and_learning_scores() -> None:
    paths = {row.source_key: row for row in build_question_source_paths()}
    report = arbitrate_question_source_paths()

    assert paths["runtime_fusion"].propagated_weight > 0
    assert paths["seed_registry"].conflict_penalty > 0
    assert paths["practitioner_refresh"].learning_boost > paths["seed_registry"].learning_boost
    assert paths["fallback"].conflict_penalty > paths["fallback"].learning_boost
    assert any("conflict_penalty" in note for note in paths["seed_registry"].arbitration_notes)
    assert any(row["source_key"] == "seed_registry" for row in report["conflict_summary"])
    assert any(row["source_key"] == "practitioner_refresh" for row in report["learning_summary"])


def test_v20_question_source_graph_consumes_quality_signal_as_rerank_only_boost() -> None:
    baseline = {row.source_key: row for row in build_question_source_paths()}
    boosted = {
        row.source_key: row
        for row in build_question_source_paths(
            quality_signal={
                "source_quality_scores": {
                    "mainline": 0.82,
                    "seed_registry": 0.4,
                },
                "candidates": (
                    {
                        "candidate_type": "brain_memory_policy",
                        "quality_score": 0.9,
                    },
                ),
            }
        )
    }
    report = arbitrate_question_source_paths(
        quality_signal={
            "source_quality_scores": {"mainline": 0.82},
            "candidates": ({"candidate_type": "brain_memory_policy", "quality_score": 0.9},),
        }
    )

    assert set(boosted) == set(baseline)
    assert boosted["mainline"].quality_boost > 0
    assert boosted["mainline"].score > baseline["mainline"].score
    assert boosted["latent_event"].quality_boost > 0
    assert "QUALITY_SIGNALS_RERANK_ONLY" in report["guardrails"]
    assert any(row["source_key"] == "mainline" for row in report["quality_summary"])


def test_v20_question_source_ranking_report_explains_existing_questions_without_reordering() -> None:
    runtime = run_runtime_from_pillars("甲子", "戊辰", "甲午", "辛酉", input_id="source.report")
    questions = tuple(QuestionCandidate(**row) for row in runtime["questions"])
    report = build_question_source_ranking_report(questions)

    assert report["version"] == "v20.question_source_ranking_report.v1"
    assert report["question_count"] == len(questions)
    assert [row["question_id"] for row in report["rows"]] == [row.question_id or row.question_key for row in questions]
    assert all(row["source_key"] for row in report["rows"])
    assert "NO_QUESTION_ORDER_MUTATION" in report["guardrails"]


def test_v20_question_ranking_policy_endpoint_and_runtime_remain_feature_backed() -> None:
    manifest = _endpoint("/api/v20/questions/ranking-policy")()
    seed_manifest = _endpoint("/api/v20/questions/seed-registry")()
    result = run_runtime_from_pillars("甲子", "戊辰", "甲午", "辛酉", input_id="ranker")

    assert manifest["runtime_mutation"] is False
    assert seed_manifest["runtime_mutation"] is False
    assert "SEED_QUESTIONS_ARE_CANDIDATES_ONLY" in seed_manifest["guardrails"]
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


def test_v20_seed_questions_are_chart_matched_candidates_not_fixed_output() -> None:
    layer = FeatureLayer(
        version="test.seed.layer",
        features=(
            BaziFeature(
                feature_id="feature.wealth.seed",
                title="财星透出但承接需看日主",
                domain="wealth",
                source_layers=("test",),
                evidence_refs=(),
                confidence=0.8,
                readiness="available",
                boundary="财星结构候选",
            ),
            BaziFeature(
                feature_id="feature.strength.seed",
                title="日主承载需要扶助复核",
                domain="strength",
                source_layers=("test",),
                evidence_refs=(),
                confidence=0.72,
                readiness="available",
                boundary="日主强弱候选",
            ),
        ),
    )
    report = {
        "decisions": (
            {"domain": "wealth", "label": "财星可见但日主承接待扶助", "score": 0.76},
        )
    }

    seeds = build_seed_question_candidates(report, layer)
    manifest = question_seed_registry_manifest()

    assert manifest["version"] == "v20.question_seed_registry.v1"
    assert manifest["seed_count"] >= 20
    assert {row.domain for row in seeds} == {"wealth", "strength"}
    assert all(row.question_strategy == SEED_QUESTION_STRATEGY for row in seeds)
    assert all(row.source_feature_ids for row in seeds)
    assert all(row.alignment_status == "bazi_core_aligned" for row in seeds)
    assert any("财星可见但日主承接待扶助" in row.title for row in seeds)
    assert not any(row.domain == "time" for row in seeds)


def test_v20_seed_source_key_survives_role_projection_without_guest_decision_key() -> None:
    from v20.access.projection import project_runtime_for_role

    result = {
        "questions": [
            {
                "question_key": "q_income_factors",
                "question_id": "qid.seed.wealth",
                "title": "财星可见但日主承接待扶助明显时，财运机会、压力和承接力先看哪一段？",
                "domain": "wealth",
                "question_strategy": "seed_registry",
                "source_decision_key": "seed.wealth.opportunity_pressure",
                "measurement_topic": "财富",
                "measurement_stage": "projection",
            }
        ],
        "selected_question": {},
        "answer_text": "测试",
        "role": {"role_key": "guest"},
    }

    projected = project_runtime_for_role(result, "guest")
    question = projected["questions"][0]

    assert question["seed_source_key"] == "seed.wealth.opportunity_pressure"
    assert "source_decision_key" not in question
    assert question["title"] == "财务先看稳定度还是机会点？"


def test_v20_role_question_view_runtime_pointer_boosts_matching_seed() -> None:
    from v20.role_view.projection import apply_role_question_view

    result = apply_role_question_view(
        {
            "questions": [
                {
                    "question_key": "q_career_structure",
                    "title": "事业普通问题",
                    "domain": "career",
                    "question_strategy": "seed_registry",
                    "source_decision_key": "seed.career.role_pressure",
                },
                {
                    "question_key": "q_income_factors",
                    "title": "财星可见但日主承接待扶助明显时，财运机会、压力和承接力先看哪一段？",
                    "domain": "wealth",
                    "question_strategy": "seed_registry",
                    "source_decision_key": "seed.wealth.opportunity_pressure",
                },
            ]
        },
        "user",
        runtime_pointer={
            "runtime_applied": True,
            "policy_payload": {
                "seed_fit_policy": [
                    {
                        "source_role": "user",
                        "seed_key": "seed.wealth.opportunity_pressure",
                    }
                ]
            },
        },
    )

    assert result["questions"][0]["seed_source_key"] == "seed.wealth.opportunity_pressure"
    assert result["questions"][0]["role_view_policy_boost"] > 0


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


def test_v20_question_agent_suppresses_answered_question_without_legacy_followups() -> None:
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
    assert refreshed["question_agent_state"]["generated_followup_count"] == 0
    assert not any(row["question_strategy"] == "agent_followup" for row in refreshed["questions"])
    assert refreshed["next_question_plan"]["recommended_questions"]
    assert all("RuleSpec" not in row["title"] and "条件成立" not in row["title"] for row in refreshed["questions"])
