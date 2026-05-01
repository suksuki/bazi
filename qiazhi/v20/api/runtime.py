from __future__ import annotations

from v20.answer.composer import compose_answer
from v20.answer.evidence import build_evidence_pack
from v20.answer.measurement_policy import prediction_policy
from v20.answer.plan import build_answer_plan
from v20.core.chart import build_chart_facts, chart_input_from_displays
from v20.core.strength import infer_core
from v20.core.time_context import empty_time_context
from v20.features.compiler import compile_features
from v20.graph.chart_graph import build_chart_graph
from v20.graph.rule_graph import select_rule_paths
from v20.interaction.portrait_projection import portrait_projection
from v20.interaction.questions import recommend_questions
from v20.knowledge.alignment import knowledge_feature_alignment
from v20.knowledge.retrieval import retrieve_knowledge
from v20.llm.contracts import LLM_CONTRACTS


def run_runtime_from_pillars(
    year: str,
    month: str,
    day: str,
    hour: str,
    *,
    input_id: str = "",
    question_key: str = "",
    locale: str = "zh",
) -> dict[str, object]:
    chart_input = chart_input_from_displays(year, month, day, hour, input_id=input_id)
    chart_facts = build_chart_facts(chart_input)
    time_context = empty_time_context()
    core = infer_core(chart_facts)
    chart_graph = build_chart_graph(chart_facts)
    rule_paths = select_rule_paths(chart_graph)
    feature_layer = compile_features(chart_facts, core, rule_paths)
    knowledge_report = retrieve_knowledge(feature_layer)
    questions = recommend_questions(feature_layer)
    selected_question = _select_question(questions, question_key)
    evidence_pack = build_evidence_pack(feature_layer)
    answer_plan = build_answer_plan(selected_question, feature_layer, evidence_pack)
    answer_text = compose_answer(answer_plan, locale=locale)
    return {
        "version": "v20.runtime_result.v1",
        "input_id": input_id,
        "locale": locale,
        "chart_facts": chart_facts.to_dict(),
        "time_context": time_context.to_dict(),
        "core_inference": core.to_dict(),
        "chart_graph": chart_graph.to_dict(),
        "rule_paths": [row.to_dict() for row in rule_paths],
        "feature_layer": feature_layer.to_dict(),
        "knowledge_report": knowledge_report.to_dict(),
        "knowledge_refs": [row.to_dict() for row in knowledge_report.refs],
        "knowledge_alignment": knowledge_feature_alignment(feature_layer),
        "questions": [row.to_dict() for row in questions],
        "portrait_projection": portrait_projection(feature_layer),
        "answer_plan": answer_plan.to_dict(),
        "answer_text": answer_text,
        "prediction_policy": prediction_policy(),
        "llm_capabilities": [contract.to_dict() for contract in LLM_CONTRACTS],
        "runtime_mutation": False,
        "guardrails": ["V20_INDEPENDENT_RUNTIME", "FEATURE_SPINE_FIRST", "NO_V19_IMPORTS"],
    }


def _select_question(questions: tuple[object, ...], question_key: str):
    if question_key:
        for question in questions:
            if getattr(question, "question_key", "") == question_key:
                return question
    if not questions:
        raise ValueError("No question candidates available.")
    return questions[0]
