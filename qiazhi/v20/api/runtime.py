from __future__ import annotations

from v20.answer.composer import compose_answer
from v20.answer.evidence import build_evidence_pack
from v20.answer.measurement_policy import prediction_policy
from v20.answer.plan import build_answer_plan
from v20.core.chart import build_chart_facts, chart_input_from_displays
from v20.core.strength import infer_core
from v20.core.time_context import build_time_context
from v20.decision.engine import build_decision_report
from v20.decision.knowledge_bridge import attach_knowledge_rule_bridge
from v20.decision.fusion import build_runtime_decision_fusion
from v20.decision.latent_signals import build_latent_signal_report
from v20.decision.questions import recommend_decision_questions, resolve_requested_question
from v20.decision.validation import validate_decision_report
from v20.dynamics.engine import build_structure_dynamics
from v20.features.compiler import compile_features
from v20.features.state_model import build_feature_state_model
from v20.graph.chart_graph import build_chart_graph
from v20.graph.rule_graph import select_rule_paths
from v20.intelligence.knowledge_semantic_model import (
    build_knowledge_semantic_model,
    validate_knowledge_semantic_model,
)
from v20.knowledge.alignment import knowledge_feature_alignment
from v20.knowledge.retrieval import retrieve_knowledge
from v20.interaction.question_intent import build_question_intent_model
from v20.interaction.question_agent import apply_question_agent_state
from v20.interaction.question_i18n import localize_question_candidate, localize_question_candidates
from v20.interaction.portrait_graph import build_portrait_graph_summary
from v20.interaction.portrait_projection import build_portrait_projection
from v20.interaction.session_model import build_interaction_session_model
from v20.llm.assist import attach_answer_safety_review, build_llm_routing_assist
from v20.llm.context import build_llm_context_pack
from v20.llm.contracts import LLM_CONTRACTS
from v20.llm.practitioner import build_practitioner_answer_with_llm
from v20.llm.tasks import rewrite_answer_plan_with_llm
from v20.measurement.report import build_measurement_report
from v20.orchestrator.engine import ReasoningRecorder
from v20.orchestrator.mainline import arbitrate_mainline


def run_runtime_from_pillars(
    year: str,
    month: str,
    day: str,
    hour: str,
    *,
    input_id: str = "",
    question_key: str = "",
    question_id: str = "",
    user_text: str = "",
    flow_year_pillar: str = "",
    luck_pillar: str = "",
    flow_month_pillar: str = "",
    locale: str = "zh",
    llm_mode: str = "deterministic",
    practitioner_selections: tuple[dict[str, object], ...] = (),
    latent_event_answers: tuple[dict[str, object], ...] = (),
    answered_question_ids: tuple[str, ...] = (),
    answered_question_keys: tuple[str, ...] = (),
) -> dict[str, object]:
    recorder = ReasoningRecorder()
    chart_input = recorder.run(
        "chart_input",
        "四柱输入标准化",
        "request_payload",
        "chart_input",
        lambda: chart_input_from_displays(year, month, day, hour, input_id=input_id),
    )
    chart_facts = recorder.run(
        "chart_facts",
        "命盘事实抽取",
        "ChartInput",
        "chart_facts",
        lambda: build_chart_facts(chart_input),
    )
    time_context = recorder.run(
        "time_context",
        "岁运时间层解析",
        "ChartFacts+time_payload",
        "time_context",
        lambda: build_time_context(
            chart_facts,
            flow_year_pillar=flow_year_pillar,
            luck_pillar=luck_pillar,
            flow_month_pillar=flow_month_pillar,
        ),
    )
    core = recorder.run("core_inference", "日主承载推断", "ChartFacts", "core_inference", lambda: infer_core(chart_facts))
    chart_graph = recorder.run("chart_graph", "命盘图谱构建", "ChartFacts", "chart_graph", lambda: build_chart_graph(chart_facts))
    rule_paths = recorder.run("rule_paths", "规则路径选择", "ChartGraph", "rule_paths", lambda: select_rule_paths(chart_graph))
    feature_layer = recorder.run(
        "feature_layer",
        "特征层编译",
        "ChartFacts+CoreInference+RulePaths+TimeContext",
        "feature_layer",
        lambda: compile_features(chart_facts, core, rule_paths, time_context),
    )
    decision_report = recorder.run(
        "decision_report",
        "规则裁决报告",
        "ChartFacts+CoreInference+FeatureLayer+TimeContext+KnowledgeBridge",
        "decision_report",
        lambda: attach_knowledge_rule_bridge(build_decision_report(chart_facts, core, feature_layer, time_context)),
    )
    latent_signal_report = recorder.run(
        "latent_signal_report",
        "潜在校准信号",
        "ChartFacts+CoreInference+TimeContext+DecisionReport",
        "latent_signal_report",
        lambda: build_latent_signal_report(chart_facts, core, time_context, decision_report),
    )
    decision_report["latent_signal_report"] = latent_signal_report
    decision_report["runtime_decision_fusion"] = recorder.run(
        "runtime_decision_fusion",
        "命理师校准融合",
        "DecisionReport+PractitionerSelections",
        "decision_report.runtime_decision_fusion",
        lambda: build_runtime_decision_fusion(
            decision_report,
            practitioner_selections=practitioner_selections,
        ),
    )
    decision_report["portrait_projection"] = recorder.run(
        "portrait_projection",
        "画像轴投射",
        "FeatureLayer+DecisionReport+RuntimeDecisionFusion",
        "decision_report.portrait_projection",
        lambda: build_portrait_projection(
            feature_layer,
            decision_report.get("defeasible_decision_model", {}),
            decision_report,
            runtime_decision_fusion=decision_report.get("runtime_decision_fusion", {}),
        ),
    )
    decision_validation = recorder.run(
        "decision_validation",
        "裁决报告校验",
        "DecisionReport",
        "decision_validation",
        lambda: validate_decision_report(decision_report),
    )
    portrait_projection = decision_report.get("portrait_projection", {})
    feature_state_model = recorder.run(
        "feature_state_model",
        "特征状态融合",
        "FeatureLayer+DecisionReport",
        "feature_state_model",
        lambda: build_feature_state_model(feature_layer, decision_report),
    )
    structure_dynamics = recorder.run(
        "structure_dynamics",
        "结构动态生成",
        "ChartFacts+FeatureLayer+FeatureStateModel+DecisionReport+TimeContext",
        "structure_dynamics",
        lambda: build_structure_dynamics(chart_facts, feature_layer, feature_state_model, time_context, decision_report),
    )
    questions = recorder.run(
        "question_candidates",
        "智能问题生成",
        "DecisionReport+FeatureLayer+TimeContext+CalibrationSignals",
        "questions",
        lambda: recommend_decision_questions(
            decision_report,
            feature_layer,
            runtime_decision_fusion=decision_report.get("runtime_decision_fusion", {}),
            time_context=time_context,
            practitioner_selections=practitioner_selections,
            latent_event_answers=latent_event_answers,
        ),
    )
    llm_routing_assist = build_llm_routing_assist(user_text, feature_layer, questions, locale=locale)
    routed_question_key = "" if (practitioner_selections or latent_event_answers) and not question_key else str(llm_routing_assist.get("routed_question_key", ""))
    selected_question = resolve_requested_question(
        questions,
        question_key or routed_question_key,
        question_id,
        feature_layer,
    )
    questions = _selected_first_questions(questions, selected_question, llm_routing_assist)
    questions, question_agent_state = apply_question_agent_state(
        questions,
        selected_question,
        answered_question_ids=answered_question_ids,
        answered_question_keys=answered_question_keys,
    )
    questions = localize_question_candidates(questions, locale=locale)
    selected_question = _localized_selected_question(selected_question, questions, locale)
    portrait_graph_summary = build_portrait_graph_summary(
        portrait_projection if isinstance(portrait_projection, dict) else {},
        decision_report,
        tuple(questions),
    )
    question_intent_model = recorder.run(
        "question_intent_model",
        "问题意图排序",
        "DecisionReport+FeatureStateModel+Questions+SelectedQuestion",
        "question_intent_model",
        lambda: build_question_intent_model(
            decision_report=decision_report,
            feature_state_model=feature_state_model,
            questions=questions,
            selected_question=selected_question,
            runtime_decision_fusion=decision_report.get("runtime_decision_fusion", {}),
        ),
    )
    mainline_arbitration = recorder.run(
        "mainline_arbitration",
        "智能中枢主线仲裁",
        "DecisionReport+FeatureStateModel+StructureDynamics+QuestionIntent+TimeContext",
        "mainline_arbitration",
        lambda: arbitrate_mainline(
            decision_report=decision_report,
            feature_state_model=feature_state_model,
            structure_dynamics=structure_dynamics,
            question_intent_model=question_intent_model,
            time_context=time_context.to_dict(),
            practitioner_selections=practitioner_selections,
        ),
    )
    decision_report["practitioner_controls"] = tuple(
        [
            *tuple(decision_report.get("practitioner_controls", ())),
            *_mainline_arbitration_controls(mainline_arbitration),
        ]
    )
    practitioner_session = _practitioner_session_lens(
        practitioner_selections,
        questions,
        selected_question,
    )
    latent_event_session = _latent_event_session_lens(
        latent_event_answers,
        questions,
        selected_question,
    )
    interaction_session = build_interaction_session_model(
        selected_question=selected_question,
        questions=questions,
        question_intent_model=question_intent_model,
        practitioner_session=practitioner_session,
        latent_event_session=latent_event_session,
        decision_report=decision_report,
    )
    knowledge_report = recorder.run(
        "knowledge_retrieval",
        "知识库检索",
        "FeatureLayer+SelectedQuestion",
        "knowledge_report",
        lambda: retrieve_knowledge(feature_layer, requested_domains=(selected_question.domain,)),
    )
    evidence_pack = recorder.run("evidence_pack", "证据包构建", "FeatureLayer", "answer_plan.evidence_pack", lambda: build_evidence_pack(feature_layer))
    answer_plan = recorder.run(
        "answer_plan",
        "回答计划生成",
        "SelectedQuestion+FeatureLayer+EvidencePack+KnowledgeReport+DecisionReport",
        "answer_plan",
        lambda: build_answer_plan(
            selected_question,
            feature_layer,
            evidence_pack,
            knowledge_report,
            decision_report=decision_report,
            mainline_arbitration=mainline_arbitration,
        ),
    )
    knowledge_semantic_model = build_knowledge_semantic_model(
        feature_layer,
        knowledge_report,
        user_text=user_text,
    )
    knowledge_semantic_validation = validate_knowledge_semantic_model(knowledge_semantic_model)
    measurement_report = recorder.run(
        "measurement_report",
        "测算报告聚合",
        "FeatureLayer+Questions+AnswerPlan+PortraitProjection",
        "measurement_report",
        lambda: build_measurement_report(feature_layer, questions, answer_plan, portrait_projection if isinstance(portrait_projection, dict) else {}),
    )
    deterministic_answer_text = recorder.run(
        "deterministic_answer",
        "确定性回答生成",
        "AnswerPlan",
        "answer_text",
        lambda: compose_answer(answer_plan, locale=locale),
    )
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
            portrait_projection=portrait_projection if isinstance(portrait_projection, dict) else {},
            feature_state_model=feature_state_model,
            question_intent_model=question_intent_model,
            interaction_session=interaction_session,
            mainline_arbitration=mainline_arbitration,
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
        portrait_projection=portrait_projection if isinstance(portrait_projection, dict) else {},
        chart_facts=chart_facts.to_dict(),
        time_context=time_context.to_dict(),
        selected_question=selected_question.to_dict(),
        knowledge_semantic_model=knowledge_semantic_model,
        feature_state_model=feature_state_model,
        question_intent_model=question_intent_model,
        interaction_session=interaction_session,
        mainline_arbitration=mainline_arbitration,
        locale=locale,
    )
    reasoning_orchestrator = recorder.to_orchestrator(
        {
            "primary_mainline": "mainline_arbitration.primary_mainline",
            "structure_dynamics": "structure_dynamics.dominant_chain",
            "selected_question": "selected_question",
            "answer": "answer_text",
        }
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
        "feature_state_model": feature_state_model,
        "structure_dynamics": structure_dynamics,
        "mainline_arbitration": mainline_arbitration,
        "reasoning_orchestrator": reasoning_orchestrator,
        "knowledge_report": knowledge_report.to_dict(),
        "knowledge_refs": [row.to_dict() for row in knowledge_report.refs],
        "knowledge_alignment": knowledge_feature_alignment(feature_layer),
        "knowledge_semantic_model": knowledge_semantic_model,
        "knowledge_semantic_validation": knowledge_semantic_validation,
        "decision_report": decision_report,
        "decision_validation": decision_validation,
        "portrait_graph_summary": portrait_graph_summary,
        "latent_signal_report": latent_signal_report,
        "questions": [row.to_dict() for row in questions],
        "question_intent_model": question_intent_model,
        "question_agent_state": question_agent_state,
        "selected_question": selected_question.to_dict(),
        "practitioner_session": practitioner_session,
        "latent_event_session": latent_event_session,
        "interaction_session": interaction_session,
        "measurement_report": measurement_report.to_dict(),
        "answer_plan": answer_plan.to_dict(),
        "answer_text": answer_text,
        "prediction_policy": prediction_policy(),
        "llm_capabilities": [contract.to_dict() for contract in LLM_CONTRACTS],
        "llm_assist": llm_assist,
        "runtime_mutation": False,
        "guardrails": ["V20_INDEPENDENT_RUNTIME", "DYNAMIC_DECISION_SPINE_FIRST", "NO_V19_IMPORTS"],
    }


def _selected_first_questions(questions, selected_question, llm_routing_assist):
    intent = llm_routing_assist.get("intent", {}) if isinstance(llm_routing_assist, dict) else {}
    intent_result = intent.get("result", {}) if isinstance(intent, dict) else {}
    candidate_keys = [str(row) for row in intent_result.get("candidate_question_keys", ()) if str(row)]
    domains = [str(row) for row in intent_result.get("feature_domains", ()) if str(row)]
    suggestions = llm_routing_assist.get("question_suggestions", {}) if isinstance(llm_routing_assist, dict) else {}
    for row in suggestions.get("suggestions", ()) if isinstance(suggestions, dict) else ():
        if isinstance(row, dict) and str(row.get("question_key", "")):
            candidate_keys.append(str(row["question_key"]))
    key_rank = {key: index for index, key in enumerate(dict.fromkeys(candidate_keys), start=1)}
    domain_rank = {domain: index for index, domain in enumerate(dict.fromkeys(domains), start=1)}
    selected_id = selected_question.question_id or selected_question.question_key
    unique = (
        selected_question,
        *(
            question
            for question in questions
            if (question.question_id or question.question_key) != selected_id
        ),
    )

    def rank(item):
        if (item.question_id or item.question_key) == selected_id:
            return (0, 0)
        if item.question_key in key_rank:
            return (1, key_rank[item.question_key])
        if item.domain in domain_rank:
            return (2, domain_rank[item.domain])
        return (3, 0)

    return tuple(sorted(unique, key=rank))


def _localized_selected_question(selected_question, questions, locale: str):
    selected_id = selected_question.question_id or selected_question.question_key
    for row in questions:
        if (row.question_id or row.question_key) == selected_id:
            return row
    return localize_question_candidate(selected_question, locale=locale)


def _practitioner_session_lens(practitioner_selections, questions, selected_question) -> dict[str, object]:
    effects = []
    questions_by_key = {question.question_id or question.question_key: question for question in questions}
    selected_id = selected_question.question_id or selected_question.question_key
    for selection in practitioner_selections:
        if not isinstance(selection, dict):
            continue
        control_key = str(selection.get("control_key", ""))
        option = str(selection.get("option", ""))
        matched_questions = [
            question
            for question in questions
            if (question.question_id or question.question_key) == selected_id
            or question.domain == _control_domain(control_key)
        ][:3]
        effects.append(
            {
                "control_key": control_key,
                "option": option,
                "effect": "question_ranking_refresh",
                "matched_question_keys": [question.question_key for question in matched_questions],
                "matched_question_titles": [question.title for question in matched_questions],
                "selected_question_key": selected_question.question_key,
                "runtime_rule_mutation": False,
            }
        )
    selected = questions_by_key.get(selected_id, selected_question)
    return {
        "version": "v20.practitioner_session_lens.v1",
        "selection_count": len(practitioner_selections),
        "selections": list(practitioner_selections),
        "questions_refreshed": bool(practitioner_selections),
        "selected_question_key": selected.question_key,
        "selected_question_id": selected.question_id or selected.question_key,
        "selected_question_title": selected.title,
        "selection_effects": effects,
        "runtime_mutation": False,
        "guardrails": [
            "PRACTITIONER_SELECTIONS_ARE_SESSION_LENS_ONLY",
            "NO_CORE_RULE_TRUTH_MUTATION",
            "QUESTION_RANKING_REFRESHES_CURRENT_SESSION",
        ],
    }


def _latent_event_session_lens(latent_event_answers, questions, selected_question) -> dict[str, object]:
    effects = []
    selected_id = selected_question.question_id or selected_question.question_key
    for answer in latent_event_answers:
        if not isinstance(answer, dict):
            continue
        scenario_id = str(answer.get("scenario_id", ""))
        domain = _latent_scenario_domain(scenario_id)
        matched_questions = [
            question
            for question in questions
            if (question.question_id or question.question_key) == selected_id
            or question.domain == domain
        ][:3]
        effects.append(
            {
                "scenario_id": scenario_id,
                "year_option": str(answer.get("year_option", "")),
                "result_option": str(answer.get("result_option", "")),
                "effect": "personal_factor_question_ranking_refresh",
                "matched_question_keys": [question.question_key for question in matched_questions],
                "matched_question_titles": [question.title for question in matched_questions],
                "runtime_rule_mutation": False,
            }
        )
    return {
        "version": "v20.latent_event_session_lens.v1",
        "answer_count": len(latent_event_answers),
        "answers": list(latent_event_answers),
        "questions_refreshed": bool(latent_event_answers),
        "selected_question_key": selected_question.question_key,
        "selected_question_id": selected_question.question_id or selected_question.question_key,
        "selected_question_title": selected_question.title,
        "selection_effects": effects,
        "runtime_mutation": False,
        "guardrails": [
            "LATENT_EVENTS_ARE_PERSONAL_CALIBRATION_LENS_ONLY",
            "NO_CORE_RULE_TRUTH_MUTATION",
            "QUESTION_RANKING_REFRESHES_CURRENT_SESSION",
        ],
    }


def _control_domain(control_key: str) -> str:
    return {
        "control.day_master_strength": "strength",
        "control.shang_guan_jian_guan": "career",
        "control.wealth_capacity": "wealth",
        "control.pattern_status": "pattern",
        "control.mainline_arbitration": "mainline",
    }.get(control_key, "")


def _mainline_arbitration_controls(mainline_arbitration: dict[str, object]) -> tuple[dict[str, object], ...]:
    quality_gate = mainline_arbitration.get("quality_gate", {})
    primary = mainline_arbitration.get("primary_mainline", {})
    if not isinstance(quality_gate, dict) or not isinstance(primary, dict):
        return ()
    if not quality_gate.get("requires_review"):
        return ()
    candidate_key = str(primary.get("candidate_key", ""))
    title = str(primary.get("title", "")) or "智能中枢主线"
    return (
        {
            "control_key": "control.mainline_arbitration",
            "label": f"中枢主线复核：{title}",
            "options": ("采用第一主线", "切换到次级主线", "暂缓主线", "证据不足"),
            "default": "采用第一主线",
            "source_decision_keys": (candidate_key,) if candidate_key.startswith("decision.") else (),
            "ui_surface": "analyst_admin_only",
            "guardrails": (
                "MAINLINE_REVIEW_IS_SESSION_SIGNAL",
                "NO_RULE_TRUTH_MUTATION",
                "PROMOTION_REQUIRES_BATCH_VALIDATION",
            ),
        },
    )


def _latent_scenario_domain(scenario_id: str) -> str:
    return {
        "latent.wealth_change": "wealth",
        "latent.career_transition": "career",
        "latent.relationship_shift": "relationship",
        "latent.relocation_environment": "time",
        "latent.stress_recovery": "health",
        "latent.action_result": "strength",
    }.get(scenario_id, "")
