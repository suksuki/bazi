from __future__ import annotations

from v20.answer.composer import compose_answer
from v20.answer.evidence import build_evidence_pack
from v20.answer.measurement_policy import prediction_policy
from v20.answer.plan import build_answer_plan
from v20.core.chart import build_chart_facts, chart_input_from_displays
from v20.core.strength import infer_core
from v20.core.time_context import build_time_context
from v20.features.compiler import compile_features
from v20.graph.chart_graph import build_chart_graph
from v20.graph.rule_graph import select_rule_paths
from v20.interaction.portrait_projection import portrait_projection
from v20.interaction.questions import recommend_questions
from v20.knowledge.alignment import knowledge_feature_alignment
from v20.knowledge.retrieval import retrieve_knowledge
from v20.llm.assist import attach_answer_safety_review, build_llm_routing_assist
from v20.llm.contracts import LLM_CONTRACTS
from v20.measurement.report import build_measurement_report


def run_runtime_from_pillars(
    year: str,
    month: str,
    day: str,
    hour: str,
    *,
    input_id: str = "",
    question_key: str = "",
    user_text: str = "",
    flow_year_pillar: str = "",
    luck_pillar: str = "",
    flow_month_pillar: str = "",
    locale: str = "zh",
) -> dict[str, object]:
    chart_input = chart_input_from_displays(year, month, day, hour, input_id=input_id)
    chart_facts = build_chart_facts(chart_input)
    time_context = build_time_context(
        chart_facts,
        flow_year_pillar=flow_year_pillar,
        luck_pillar=luck_pillar,
        flow_month_pillar=flow_month_pillar,
    )
    core = infer_core(chart_facts)
    chart_graph = build_chart_graph(chart_facts)
    rule_paths = select_rule_paths(chart_graph)
    feature_layer = compile_features(chart_facts, core, rule_paths, time_context)
    questions = recommend_questions(feature_layer)
    llm_routing_assist = build_llm_routing_assist(user_text, feature_layer, questions, locale=locale)
    selected_question = _select_question(questions, question_key or str(llm_routing_assist.get("routed_question_key", "")))
    knowledge_report = retrieve_knowledge(feature_layer, requested_domains=(selected_question.domain,))
    evidence_pack = build_evidence_pack(feature_layer)
    answer_plan = build_answer_plan(selected_question, feature_layer, evidence_pack)
    portrait = portrait_projection(feature_layer)
    measurement_report = build_measurement_report(feature_layer, questions, answer_plan, portrait)
    answer_text = compose_answer(answer_plan, locale=locale)
    llm_assist = attach_answer_safety_review(llm_routing_assist, answer_text)
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
        "selected_question": selected_question.to_dict(),
        "portrait_projection": portrait,
        "measurement_report": measurement_report.to_dict(),
        "answer_plan": answer_plan.to_dict(),
        "answer_text": answer_text,
        "prediction_policy": prediction_policy(),
        "llm_capabilities": [contract.to_dict() for contract in LLM_CONTRACTS],
        "llm_assist": llm_assist,
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
