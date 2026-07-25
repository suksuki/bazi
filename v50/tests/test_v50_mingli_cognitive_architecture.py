from __future__ import annotations

from core.contracts import BirthInputCanonical
from core.mingli_agent import CognitiveOrchestrator, MingliAgent, MingliContextCompiler, ModelPolicyRouter, compile_chart_world
from core.mingli_agent.reasoner import _ollama_metrics


def _world():
    birth = BirthInputCanonical.model_validate({
        "birth_input_id": "cognitive-architecture-fixture",
        "name": "结构测试",
        "gender": "male",
        "calendar_type": "solar",
        "birth_date": "1987-05-12",
        "birth_time": "18:00",
        "birth_location": "上海",
        "timezone": "Asia/Shanghai",
        "year_pillar": "丁巳",
        "month_pillar": "乙巳",
        "day_pillar": "乙丑",
        "hour_pillar": "乙酉",
        "input_quality": "explicit_pillars",
    })
    return compile_chart_world(reading_id="cognitive-architecture-fixture", birth_input=birth)


def test_context_compiler_produces_stage_specific_minimum_context():
    world = _world()
    compiler = MingliContextCompiler()
    pattern = compiler.compile(world=world, stage="pattern")
    prediction = compiler.compile(
        world=world,
        stage="prediction",
        cognitive_state={"selected_hypothesis_id": "h1"},
    )
    work = compiler.compile(
        world=world,
        stage="work_path",
        cognitive_state={"selected_hypothesis_id": "h1"},
    )
    assert pattern.content_hash != prediction.content_hash
    assert len(pattern.knowledge_refs) > len(prediction.knowledge_refs)
    assert prediction.payload["frozen_cognitive_state"]["selected_hypothesis_id"] == "h1"
    assert prediction.payload["timing_context"] == {}
    assert pattern.payload["immutable_chart_ledger"]
    assert pattern.payload["element_role_ledger"] == {
        "wood": "比劫/同类",
        "fire": "食伤/输出",
        "earth": "财星/资源结果",
        "metal": "官杀/规则压力",
        "water": "印星/支持输入",
    }
    assert pattern.attention_receipt.critical_omission_refs == []
    assert pattern.attention_receipt.selected_fact_refs == pattern.fact_refs
    assert pattern.payload["attention"]
    assert pattern.reasoning_phase == "independent_observation"
    assert pattern.experimental_tool_refs == []
    assert work.reasoning_phase == "tool_challenge"
    assert work.experimental_tool_refs
    assert all(
        item["authority"] != "experimental_tool_observation"
        for item in pattern.payload["facts"]
    )
    assert not [item for item in pattern.payload["facts"] if item["category"] == "graph_relation"]
    graph_relations = [fact for fact in world.facts if fact.category == "graph_relation"]
    assert graph_relations
    assert all(fact.authority == "experimental_tool_observation" for fact in graph_relations)
    assert all("strength" not in fact.payload for fact in world.facts if fact.category == "graph_relation")


def test_attention_selection_is_order_invariant_and_auditable():
    world = _world()
    compiler = MingliContextCompiler()
    original = compiler.compile(world=world, stage="pattern")
    reversed_world = world.model_copy(update={"facts": list(reversed(world.facts))})
    reordered = compiler.compile(world=reversed_world, stage="pattern")

    assert original.fact_refs == reordered.fact_refs
    assert original.content_hash == reordered.content_hash
    assert original.attention_receipt == reordered.attention_receipt
    assert not any(
        item.selected and item.category in {"candidate_path", "estimated_sensitivity", "tool_salience"}
        for item in original.attention_receipt.items
    )
    challenge = compiler.compile(world=world, stage="work_path")
    assert any(
        item.selected and item.category in {"candidate_path", "estimated_sensitivity", "tool_salience"}
        for item in challenge.attention_receipt.items
    )


def test_model_policy_routes_cognition_tasks_without_mingli_answers(monkeypatch):
    monkeypatch.setenv("V50_MINGLI_AGENT_MODEL", "whole-model")
    monkeypatch.setenv("V50_MINGLI_PATTERN_MODEL", "pattern-model")
    monkeypatch.setenv("V50_MINGLI_DOMAIN_MODEL", "domain-model")
    router = ModelPolicyRouter.from_env()
    assert router.route("pattern_preview").model == "pattern-model"
    assert router.route("pattern_preview").max_tokens == 420
    assert router.route("pattern_hypothesis").model == "pattern-model"
    assert router.route("career_reasoning").model == "domain-model"
    assert router.route("pattern_hypothesis").thinking is False
    assert router.route("prediction_probe").thinking is False
    assert {item["task"] for item in router.manifest()} >= {"pattern_preview", "pattern_hypothesis", "career_reasoning", "case_turn"}
    monkeypatch.setenv("V50_MINGLI_PATTERN_THINKING", "true")
    assert ModelPolicyRouter.from_env().route("pattern_hypothesis").thinking is True


def test_default_agent_model_instances_follow_the_same_policy_environment(monkeypatch):
    monkeypatch.setenv("V50_MINGLI_AGENT_MODEL", "whole-model")
    monkeypatch.setenv("V50_MINGLI_PATTERN_MODEL", "pattern-model")
    monkeypatch.setenv("V50_MINGLI_WORK_MODEL", "work-model")
    monkeypatch.setenv("V50_MINGLI_DOMAIN_MODEL", "domain-model")
    agent = MingliAgent()

    assert agent.model.model == "whole-model"
    assert agent.pattern_model.model == "pattern-model"
    assert agent.work_model.model == "work-model"
    assert agent.domain_model.model == "domain-model"


def test_orchestrator_records_context_and_execution_but_not_a_verdict():
    world = _world()
    context = MingliContextCompiler().compile(world=world, stage="pattern")
    route = ModelPolicyRouter.from_env().route("pattern_hypothesis")
    orchestrator = CognitiveOrchestrator()
    result = orchestrator.execute(
        stage="pattern_hypothesis",
        route=route,
        context=context,
        artifact_type="PatternHypothesisDraft",
        operation=lambda: {"artifact": "owned_by_reasoner"},
    )
    receipt = orchestrator.receipt().stage_receipts[0]
    assert result == {"artifact": "owned_by_reasoner"}
    assert receipt.context_hash == context.content_hash
    assert receipt.status == "completed"
    assert receipt.artifact_type == "PatternHypothesisDraft"


def test_ollama_transport_metrics_are_normalized_and_attach_to_stage_receipt():
    metrics = _ollama_metrics(
        body={
            "total_duration": 2_500_000_000,
            "load_duration": 100_000_000,
            "prompt_eval_count": 1234,
            "prompt_eval_duration": 400_000_000,
            "eval_count": 321,
            "eval_duration": 1_800_000_000,
        },
        schema_attempts=1,
        response_bytes=4096,
    )
    world = _world()
    context = MingliContextCompiler().compile(world=world, stage="pattern")
    route = ModelPolicyRouter.from_env().route("pattern_hypothesis")
    orchestrator = CognitiveOrchestrator()
    orchestrator.execute(
        stage="pattern_hypothesis",
        route=route,
        context=context,
        artifact_type="PatternHypothesisDraft",
        operation=lambda: True,
    )
    orchestrator.annotate_last(stage="pattern_hypothesis", metrics=metrics)
    receipt = orchestrator.receipt().stage_receipts[0]

    assert receipt.transport_total_ms == 2500
    assert receipt.load_duration_ms == 100
    assert receipt.prompt_eval_count == 1234
    assert receipt.eval_count == 321
    assert receipt.schema_attempts == 1
    assert receipt.response_bytes == 4096
