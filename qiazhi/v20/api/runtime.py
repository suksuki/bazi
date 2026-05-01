from __future__ import annotations

from v20.answer.composer import compose_answer
from v20.answer.evidence import build_evidence_pack
from v20.answer.measurement_policy import prediction_policy
from v20.answer.plan import build_answer_plan
from v20.core.chart import build_chart_facts, chart_input_from_displays
from v20.core.strength import infer_core
from v20.core.time_context import build_time_context
from v20.decision.engine import build_decision_report
from v20.decision.questions import recommend_decision_questions, resolve_requested_question
from v20.decision.validation import validate_decision_report
from v20.features.compiler import compile_features
from v20.graph.chart_graph import build_chart_graph
from v20.graph.rule_graph import select_rule_paths
from v20.intelligence.knowledge_semantic_model import (
    build_knowledge_semantic_model,
    validate_knowledge_semantic_model,
)
from v20.knowledge.alignment import knowledge_feature_alignment
from v20.knowledge.retrieval import retrieve_knowledge
from v20.llm.assist import attach_answer_safety_review, build_llm_routing_assist
from v20.llm.context import build_llm_context_pack
from v20.llm.contracts import LLM_CONTRACTS
from v20.llm.practitioner import build_practitioner_answer_with_llm
from v20.llm.tasks import rewrite_answer_plan_with_llm
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
    llm_mode: str = "deterministic",
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
    decision_report = build_decision_report(chart_facts, core, feature_layer, time_context)
    decision_validation = validate_decision_report(decision_report)
    dynamic_portrait = decision_report.get("dynamic_portrait", {})
    questions = recommend_decision_questions(decision_report, feature_layer)
    llm_routing_assist = build_llm_routing_assist(user_text, feature_layer, questions, locale=locale)
    selected_question = resolve_requested_question(
        questions,
        question_key or str(llm_routing_assist.get("routed_question_key", "")),
        feature_layer,
    )
    if all(question.question_key != selected_question.question_key for question in questions):
        questions = (selected_question, *questions)
    knowledge_report = retrieve_knowledge(feature_layer, requested_domains=(selected_question.domain,))
    evidence_pack = build_evidence_pack(feature_layer)
    answer_plan = build_answer_plan(
        selected_question,
        feature_layer,
        evidence_pack,
        knowledge_report,
        decision_report=decision_report,
    )
    knowledge_semantic_model = build_knowledge_semantic_model(
        feature_layer,
        knowledge_report,
        user_text=user_text,
    )
    knowledge_semantic_validation = validate_knowledge_semantic_model(knowledge_semantic_model)
    measurement_report = build_measurement_report(feature_layer, questions, answer_plan, dynamic_portrait if isinstance(dynamic_portrait, dict) else {})
    deterministic_answer_text = compose_answer(answer_plan, locale=locale)
    answer_text = deterministic_answer_text
    answer_rewrite = {
        "version": "v20.llm_answer_rewrite.v1",
        "status": "not_requested",
        "text": deterministic_answer_text,
        "source": "deterministic_answer",
        "runtime_mutation": False,
        "guardrails": ["DETERMINISTIC_ANSWER_DEFAULT", "LLM_REWRITE_REQUIRES_EXPLICIT_MODE"],
    }
    practitioner_answer = {
        "version": "v20.llm_practitioner_answer.v1",
        "status": "not_requested",
        "text": deterministic_answer_text,
        "source": "deterministic_answer",
        "runtime_mutation": False,
        "guardrails": ["DETERMINISTIC_ANSWER_DEFAULT", "PRACTITIONER_ANSWER_REQUIRES_EXPLICIT_MODE"],
    }
    if llm_mode == "rewrite":
        answer_rewrite = rewrite_answer_plan_with_llm(
            answer_plan,
            deterministic_answer_text,
            locale=locale,
        )
        answer_text = str(answer_rewrite.get("text") or deterministic_answer_text)
    if llm_mode == "practitioner":
        practitioner_answer = build_practitioner_answer_with_llm(
            chart_facts=chart_facts.to_dict(),
            time_context=time_context.to_dict(),
            selected_question=selected_question.to_dict(),
            decision_report=decision_report,
            knowledge_semantic_model=knowledge_semantic_model,
            dynamic_portrait=dynamic_portrait if isinstance(dynamic_portrait, dict) else {},
            answer_plan=answer_plan,
            deterministic_answer_text=deterministic_answer_text,
            locale=locale,
        )
        answer_text = str(practitioner_answer.get("text") or deterministic_answer_text)
    llm_assist = attach_answer_safety_review(llm_routing_assist, answer_text)
    llm_assist["answer_rewrite"] = answer_rewrite
    llm_assist["practitioner_answer"] = practitioner_answer
    llm_assist["context_pack"] = build_llm_context_pack(
        user_text,
        feature_layer,
        questions,
        knowledge_report,
        answer_plan,
        answer_text,
        decision_report=decision_report,
        dynamic_portrait=dynamic_portrait if isinstance(dynamic_portrait, dict) else {},
        locale=locale,
    )
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
        "knowledge_semantic_model": knowledge_semantic_model,
        "knowledge_semantic_validation": knowledge_semantic_validation,
        "decision_report": decision_report,
        "decision_validation": decision_validation,
        "dynamic_portrait": dynamic_portrait,
        "questions": [row.to_dict() for row in questions],
        "selected_question": selected_question.to_dict(),
        "measurement_report": measurement_report.to_dict(),
        "answer_plan": answer_plan.to_dict(),
        "answer_text": answer_text,
        "prediction_policy": prediction_policy(),
        "llm_capabilities": [contract.to_dict() for contract in LLM_CONTRACTS],
        "llm_assist": llm_assist,
        "runtime_mutation": False,
        "guardrails": ["V20_INDEPENDENT_RUNTIME", "DYNAMIC_DECISION_SPINE_FIRST", "NO_V19_IMPORTS"],
    }
