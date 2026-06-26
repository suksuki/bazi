from __future__ import annotations

from dataclasses import replace

from v20.answer.composer import compose_answer
from v20.answer.evidence import build_evidence_pack
from v20.answer.measurement_policy import prediction_policy
from v20.answer.plan import build_answer_plan
from v20.core.chart import build_chart_facts, chart_input_from_displays
from v20.core.context_frame import (
    attach_context_binding,
    build_bazi_context_frame,
    build_context_alignment_report,
    build_context_binding,
)
from v20.core.strength import infer_core
from v20.core.time_context import build_time_context
from v20.decision.engine import build_decision_report
from v20.decision.knowledge_bridge import attach_knowledge_rule_bridge
from v20.decision.fusion import build_runtime_decision_fusion
from v20.decision.latent_signals import build_latent_signal_report
from v20.decision.questions import recommend_decision_questions, resolve_requested_question
from v20.decision.question_source_runtime import build_question_source_ranking_report
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
from v20.interaction.question_anchor import bind_questions_to_bazi_context
from v20.interaction.question_atoms import QuestionSessionState, build_next_question_plan
from v20.interaction.question_i18n import localize_question_candidate, localize_question_candidates
from v20.interaction.portrait_graph import build_portrait_graph_summary
from v20.interaction.portrait_projection import build_portrait_projection
from v20.interaction.question_source_record import record_question_source_ranking_report
from v20.interaction.session_model import build_interaction_session_model
from v20.llm.assist import attach_answer_safety_review, build_llm_routing_assist
from v20.llm.context import build_llm_context_pack
from v20.llm.contracts import LLM_CONTRACTS
from v20.llm.practitioner import build_practitioner_answer_with_llm, validate_practitioner_answer_day_master
from v20.llm.tasks import rewrite_answer_plan_with_llm
from v20.measurement.report import build_measurement_report
from v20.orchestrator.engine import ReasoningRecorder
from v20.orchestrator.brain_state import build_orchestrator_brain_state
from v20.orchestrator.evidence import compile_orchestrator_evidence
from v20.orchestrator.mainline import arbitrate_mainline
from v20.orchestrator.memory import build_brain_memory_signal
from v20.orchestrator.policy_observability import build_policy_observability_summary
from v20.orchestrator.question_focus import align_questions_to_mainline
from v20.orchestrator.runtime_policy import build_runtime_policy_pointer


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
    source_role: str = "user",
    record_question_source_report: bool = False,
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
    bazi_context_frame = recorder.run(
        "bazi_context_frame",
        "八字上下文绑定",
        "ChartFacts+TimeContext",
        "bazi_context_frame",
        lambda: build_bazi_context_frame(
            chart_facts=chart_facts,
            time_context=time_context,
            input_id=input_id,
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
    attach_context_binding(
        structure_dynamics,
        bazi_context_frame,
        module_key="structure_dynamics",
        evidence_domains=tuple(str(row.get("domain", "")) for row in structure_dynamics.get("activated_structures", ()) if isinstance(row, dict)),
        time_sensitive=time_context.status == "ready",
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
    attach_context_binding(
        question_intent_model,
        bazi_context_frame,
        module_key="question_intent_model",
        evidence_domains=tuple(str(row.domain) for row in questions),
        feature_ids=tuple(feature_id for row in questions for feature_id in row.source_feature_ids),
        time_sensitive=any(row.domain == "time" for row in questions),
    )
    orchestrator_evidence = recorder.run(
        "orchestrator_evidence",
        "中枢统一证据编译",
        "DecisionReport+FeatureStateModel+StructureDynamics+QuestionIntent+TimeContext",
        "orchestrator_evidence",
        lambda: compile_orchestrator_evidence(
            decision_report=decision_report,
            feature_state_model=feature_state_model,
            structure_dynamics=structure_dynamics,
            question_intent_model=question_intent_model,
            time_context=time_context.to_dict(),
        ),
    )
    orchestrator_policy_preflight = recorder.run(
        "orchestrator_policy_preflight",
        "中枢策略版本预检",
        "PolicyVersionRegistry",
        "orchestrator_policy_pointer.preflight",
        lambda: build_runtime_policy_pointer(brain_memory_signal={}),
    )
    mainline_arbitration = recorder.run(
        "mainline_arbitration",
        "智能中枢主线仲裁",
        "UnifiedEvidence+CandidateMainlines+QuestionIntent+TimeContext+RuntimePolicyPointer",
        "mainline_arbitration",
        lambda: arbitrate_mainline(
            decision_report=decision_report,
            feature_state_model=feature_state_model,
            structure_dynamics=structure_dynamics,
            question_intent_model=question_intent_model,
            time_context=time_context.to_dict(),
            practitioner_selections=practitioner_selections,
            evidence_items=tuple(orchestrator_evidence.get("items", ())),
            runtime_policy_pointer=orchestrator_policy_preflight,
        ),
    )
    explicit_question_focus = bool(question_key or question_id or routed_question_key or practitioner_selections or latent_event_answers)
    questions, selected_question, question_mainline_focus = recorder.run(
        "question_mainline_focus",
        "智能问题贴合主线",
        "Questions+MainlineArbitration",
        "question_mainline_focus",
        lambda: align_questions_to_mainline(
            tuple(questions),
            selected_question,
            mainline_arbitration,
            explicit_question_requested=explicit_question_focus,
            runtime_policy_pointer=orchestrator_policy_preflight,
        ),
    )
    questions = _suppress_answered_questions(
        questions,
        answered_question_ids=answered_question_ids,
        answered_question_keys=answered_question_keys,
    )
    next_question_plan = recorder.run(
        "next_question_plan",
        "下一问策略计划",
        "MainlineArbitration+QuestionSessionState+TimeContext",
        "next_question_plan",
        lambda: build_next_question_plan(
            role_key=source_role,
            session_state=QuestionSessionState(
                answered_question_ids=answered_question_ids,
                answered_question_keys=answered_question_keys,
                answered_topics=tuple(_question_topic_depth(answered_question_keys).keys()),
                last_question_id=selected_question.question_id or selected_question.question_key,
                last_question_key=selected_question.question_key,
                last_domain=selected_question.domain,
                last_stage=selected_question.measurement_stage,
                topic_depth=_question_topic_depth(answered_question_keys),
            ),
            primary_domain=str(mainline_arbitration.get("primary_mainline", {}).get("domain", "")),
            primary_stage=selected_question.measurement_stage,
            has_time_context=_has_runtime_time_context(time_context),
        ),
    )
    questions = recorder.run(
        "next_question_rank_merge",
        "下一问策略合流",
        "Questions+NextQuestionPlan",
        "questions",
        lambda: _merge_next_question_plan_into_questions(questions, next_question_plan),
    )
    questions = recorder.run(
        "question_bazi_anchor",
        "智能问题八字锚定",
        "Questions+BaziContextFrame+StructureDynamics+MainlineArbitration",
        "questions",
        lambda: bind_questions_to_bazi_context(
            tuple(questions),
            bazi_context_frame=bazi_context_frame,
            structure_dynamics=structure_dynamics,
            mainline_arbitration=mainline_arbitration,
            role_key=source_role,
        ),
    )
    questions = tuple(_promote_display_title(question) for question in questions)
    next_question_plan = _attach_bound_questions_to_next_question_plan(next_question_plan, questions)
    selected_question = _sync_selected_question(selected_question, questions)
    if not getattr(selected_question, "question_anchor", {}):
        selected_bound = bind_questions_to_bazi_context(
            (selected_question,),
            bazi_context_frame=bazi_context_frame,
            structure_dynamics=structure_dynamics,
            mainline_arbitration=mainline_arbitration,
            role_key=source_role,
        )
        if selected_bound:
            selected_question = _promote_display_title(selected_bound[0])
    question_source_ranking_report = recorder.run(
        "question_source_ranking_report",
        "问题来源图解释",
        "Questions+QuestionSourceGraph",
        "question_source_ranking_report",
        lambda: build_question_source_ranking_report(tuple(questions)),
    )
    if record_question_source_report:
        try:
            _ = record_question_source_ranking_report(
                input_id=input_id,
                source_role=source_role,
                question_source_ranking_report=question_source_ranking_report,
            )
        except Exception:
            # Question-source telemetry must never make the measurement runtime fail.
            pass
    question_intent_model = recorder.run(
        "question_intent_model_focus",
        "问题意图贴合最终主线",
        "FocusedQuestions+SelectedQuestion+MainlineArbitration",
        "question_intent_model",
        lambda: build_question_intent_model(
            decision_report=decision_report,
            feature_state_model=feature_state_model,
            questions=questions,
            selected_question=selected_question,
            runtime_decision_fusion=decision_report.get("runtime_decision_fusion", {}),
        ),
    )
    attach_context_binding(
        question_intent_model,
        bazi_context_frame,
        module_key="question_intent_model",
        evidence_domains=tuple(str(row.domain) for row in questions),
        feature_ids=tuple(feature_id for row in questions for feature_id in row.source_feature_ids),
        time_sensitive=any(row.domain == "time" for row in questions),
    )
    portrait_graph_summary = build_portrait_graph_summary(
        portrait_projection if isinstance(portrait_projection, dict) else {},
        decision_report,
        tuple(questions),
    )
    brain_state = recorder.run(
        "brain_state",
        "智能中枢状态摘要",
        "MainlineArbitration+UnifiedEvidence+QuestionFocus+StructureDynamics",
        "brain_state",
        lambda: build_orchestrator_brain_state(
            mainline_arbitration=mainline_arbitration,
            orchestrator_evidence=orchestrator_evidence,
            question_mainline_focus=question_mainline_focus,
            structure_dynamics=structure_dynamics,
            selected_question=selected_question,
            time_context=time_context.to_dict(),
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
    brain_memory_signal = recorder.run(
        "brain_memory_signal",
        "智能中枢记忆信号",
        "BrainState+MainlineArbitration+QuestionFocus+SessionCalibration",
        "brain_memory_signal",
        lambda: build_brain_memory_signal(
            input_id=input_id,
            brain_state=brain_state,
            mainline_arbitration=mainline_arbitration,
            question_mainline_focus=question_mainline_focus,
            selected_question=selected_question,
            practitioner_session=practitioner_session,
            latent_event_session=latent_event_session,
        ),
    )
    orchestrator_policy_pointer = recorder.run(
        "orchestrator_policy_pointer",
        "中枢策略版本指针",
        "BrainMemorySignal+PolicyVersionRegistry",
        "orchestrator_policy_pointer",
        lambda: build_runtime_policy_pointer(brain_memory_signal=brain_memory_signal),
    )
    orchestrator_policy_observability = recorder.run(
        "orchestrator_policy_observability",
        "中枢策略在线观测",
        "PolicyPointer+RuntimePolicyEffects",
        "orchestrator_policy_observability",
        lambda: build_policy_observability_summary(
            policy_pointer=orchestrator_policy_pointer,
            mainline_arbitration=mainline_arbitration,
            question_mainline_focus=question_mainline_focus,
        ),
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
        lambda: compose_answer(answer_plan, locale=locale, brain_state=brain_state),
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
            brain_state=brain_state,
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
            brain_state=brain_state,
            answer_plan=answer_plan,
            deterministic_answer_text=deterministic_answer_text,
            locale=locale,
        )
        answer_text = str(practitioner_answer.get("text") or deterministic_answer_text)
    day_master_answer_validation = validate_practitioner_answer_day_master(answer_text, chart_facts.day_master)
    if not day_master_answer_validation.get("ok"):
        answer_text = deterministic_answer_text
        practitioner_answer = practitioner_answer | {
            "status": "fallback",
            "text": deterministic_answer_text,
            "source": "deterministic_fallback",
            "day_master_validation": day_master_answer_validation,
            "guardrails": list(practitioner_answer.get("guardrails", ())) + ["DAY_MASTER_MISMATCH_FORCED_DETERMINISTIC_FALLBACK"],
        }
    llm_assist = attach_answer_safety_review(llm_routing_assist, answer_text)
    llm_assist["answer_rewrite"] = answer_rewrite
    llm_assist["practitioner_answer"] = practitioner_answer
    llm_assist["day_master_answer_validation"] = day_master_answer_validation
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
        brain_state=brain_state,
        locale=locale,
    )
    attach_context_binding(
        decision_report.get("portrait_projection", {}),
        bazi_context_frame,
        module_key="portrait_projection",
        evidence_domains=tuple(str(row.get("domain", "")) for row in portrait_projection.get("axes", ()) if isinstance(row, dict)),
        feature_ids=tuple(feature_id for row in portrait_projection.get("axes", ()) if isinstance(row, dict) for feature_id in row.get("feature_ids", ())),
        time_sensitive=any(str(row.get("domain", "")) == "time" for row in portrait_projection.get("axes", ()) if isinstance(row, dict)),
    )
    attach_context_binding(
        llm_assist["context_pack"],
        bazi_context_frame,
        module_key="llm_context_pack",
        evidence_domains=tuple(str(row.domain) for row in questions),
        time_sensitive=time_context.status == "ready",
    )
    question_context_binding = build_context_binding(
        bazi_context_frame,
        module_key="question_candidates",
        evidence_domains=tuple(str(row.domain) for row in questions),
        feature_ids=tuple(feature_id for row in questions for feature_id in row.source_feature_ids),
        time_sensitive=any(row.domain == "time" for row in questions),
    )
    context_alignment_report = build_context_alignment_report(
        bazi_context_frame,
        bindings={
            "structure_dynamics": structure_dynamics.get("context_binding", {}),
            "portrait_projection": decision_report.get("portrait_projection", {}).get("context_binding", {}),
            "question_intent_model": question_intent_model.get("context_binding", {}),
            "mainline_arbitration": build_context_binding(
                bazi_context_frame,
                module_key="mainline_arbitration",
                evidence_domains=tuple(
                    str(row.get("domain", ""))
                    for row in (mainline_arbitration.get("primary_mainline", {}).get("nodes", ()) or ())
                    if isinstance(row, dict)
                ),
                time_sensitive=time_context.status == "ready",
            ),
            "llm_context_pack": llm_assist["context_pack"].get("context_binding", {}),
        },
    )
    reasoning_orchestrator = recorder.to_orchestrator(
        {
            "primary_mainline": "mainline_arbitration.primary_mainline",
            "brain_state": "brain_state.public_summary",
            "brain_memory_signal": "brain_memory_signal.memory_key",
            "orchestrator_policy_pointer": "orchestrator_policy_pointer.active_policy_version",
            "orchestrator_policy_observability": "orchestrator_policy_observability.status",
            "structure_dynamics": "structure_dynamics.primary_dynamic_chain",
            "selected_question": "selected_question",
            "answer": "answer_text",
        }
    )
    return {
        "version": "v20.runtime_result.v1",
        "input_id": input_id,
        "locale": locale,
        "bazi_context_frame": bazi_context_frame,
        "context_alignment_report": context_alignment_report,
        "chart_facts": chart_facts.to_dict(),
        "time_context": time_context.to_dict(),
        "core_inference": core.to_dict(),
        "chart_graph": chart_graph.to_dict(),
        "rule_paths": [row.to_dict() for row in rule_paths],
        "feature_layer": feature_layer.to_dict(),
        "feature_state_model": feature_state_model,
        "structure_dynamics": structure_dynamics,
        "mainline_arbitration": mainline_arbitration,
        "orchestrator_evidence": orchestrator_evidence,
        "question_mainline_focus": question_mainline_focus,
        "next_question_plan": next_question_plan,
        "question_source_ranking_report": question_source_ranking_report,
        "brain_state": brain_state,
        "brain_memory_signal": brain_memory_signal,
        "orchestrator_policy_pointer": orchestrator_policy_pointer,
        "orchestrator_policy_observability": orchestrator_policy_observability,
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
        "question_context_binding": question_context_binding,
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


def _sync_selected_question(selected_question, questions):  # noqa: ANN001
    selected_id = selected_question.question_id or selected_question.question_key
    for question in questions:
        if selected_id and (question.question_id or question.question_key) == selected_id:
            return question
    return selected_question


def _promote_display_title(question):  # noqa: ANN001
    display_title = str(getattr(question, "display_title", "") or "")
    if display_title and getattr(question, "title", "") != display_title:
        return replace(question, title=display_title)
    return question


def _attach_bound_questions_to_next_question_plan(next_question_plan: dict[str, object], questions) -> dict[str, object]:  # noqa: ANN001
    if not isinstance(next_question_plan, dict):
        return {}
    recommended = []
    atoms = next_question_plan.get("recommended_atoms", ())
    if not isinstance(atoms, list):
        atoms = []
    seen: set[str] = set()
    for atom in atoms:
        if not isinstance(atom, dict):
            continue
        key = str(atom.get("question_key", ""))
        matched = next((question for question in questions if str(question.question_key) == key), None)
        if matched is None:
            continue
        identity = str(matched.question_id or matched.question_key)
        if identity in seen:
            continue
        seen.add(identity)
        anchor = getattr(matched, "question_anchor", {}) or {}
        recommended.append(
            {
                "question_id": matched.question_id or matched.question_key,
                "question_key": matched.question_key,
                "display_title": _question_display_title(matched),
                "domain": matched.domain,
                "topic": matched.next_question_topic or matched.measurement_topic,
                "stage": matched.next_question_stage or matched.measurement_stage,
                "atom_id": matched.next_question_atom_id or str(atom.get("atom_id", "")),
                "anchor_status": anchor.get("anchor_status", "") if isinstance(anchor, dict) else "",
                "day_master": anchor.get("day_master", "") if isinstance(anchor, dict) else "",
                "primary_dynamic_chain_label": anchor.get("primary_dynamic_chain_label", "") if isinstance(anchor, dict) else "",
                "why_this_question": anchor.get("why_this_question", "") if isinstance(anchor, dict) else "",
                "score_reasons": list(matched.next_question_score_reasons),
            }
        )
    guardrails = list(next_question_plan.get("guardrails", ()) or ())
    if "RECOMMENDED_QUESTIONS_USE_BAZI_ANCHORED_DISPLAY_TITLE" not in guardrails:
        guardrails.append("RECOMMENDED_QUESTIONS_USE_BAZI_ANCHORED_DISPLAY_TITLE")
    return {
        **next_question_plan,
        "recommended_questions": recommended,
        "anchored_recommended_question_count": len(recommended),
        "guardrails": guardrails,
    }


def _suppress_answered_questions(
    questions,
    *,
    answered_question_ids: tuple[str, ...],
    answered_question_keys: tuple[str, ...],
):
    answered_ids = {str(row).strip() for row in answered_question_ids if str(row).strip()}
    answered_keys = {str(row).strip() for row in answered_question_keys if str(row).strip()}
    if not answered_ids and not answered_keys:
        return questions
    return tuple(
        question
        for question in questions
        if (question.question_id or question.question_key) not in answered_ids
        and question.question_key not in answered_keys
    )


def _question_topic_depth(answered_question_keys: tuple[str, ...]) -> dict[str, int]:
    depths: dict[str, int] = {}
    for key in answered_question_keys:
        topic = _question_key_topic(str(key))
        if not topic:
            continue
        depths[topic] = depths.get(topic, 0) + 1
    return depths


def _question_key_topic(question_key: str) -> str:
    if "career" in question_key:
        return "career_structure"
    if "income" in question_key or "wealth" in question_key:
        return "wealth_channel"
    if "relationship" in question_key:
        return "relationship_pattern"
    if "time" in question_key:
        return "timing_trigger"
    if "structure" in question_key or "pattern" in question_key:
        return "structure_dynamics"
    if "useful_god" in question_key:
        return "useful_god"
    if "health" in question_key:
        return "health_balance"
    return ""


def _has_runtime_time_context(time_context) -> bool:  # noqa: ANN001
    return bool(
        getattr(time_context, "status", "") == "ready"
        or getattr(time_context, "layers", ())
        or getattr(time_context, "relation_hits", ())
    )


def _question_display_title(question) -> str:  # noqa: ANN001
    return str(getattr(question, "display_title", "") or getattr(question, "title", "") or getattr(question, "question_key", ""))


def _merge_next_question_plan_into_questions(questions, next_question_plan: dict[str, object]):  # noqa: ANN001
    atoms = next_question_plan.get("recommended_atoms", ()) if isinstance(next_question_plan, dict) else ()
    if not isinstance(atoms, list) or not atoms:
        return questions
    atom_by_key = {}
    for atom in atoms:
        if not isinstance(atom, dict):
            continue
        key = str(atom.get("question_key", ""))
        if key and key not in atom_by_key:
            atom_by_key[key] = atom
    scored = []
    for index, question in enumerate(questions):
        atom = atom_by_key.get(str(question.question_key))
        if not atom:
            scored.append((float(question.score or 0.0), -index, question))
            continue
        atom_score = float(atom.get("score", 0.0) or 0.0)
        merged_score = round(float(question.score or 0.0) + min(0.22, atom_score * 0.18), 3)
        enriched = _with_next_question_atom_metadata(question, atom, merged_score)
        scored.append((merged_score, 100 - index, enriched))
    return tuple(row for _score, _order, row in sorted(scored, key=lambda item: (item[0], item[1]), reverse=True))


def _with_next_question_atom_metadata(question, atom: dict[str, object], score: float):  # noqa: ANN001
    payload = question.to_dict()
    payload.update(
        {
            "score": score,
            "next_question_atom_id": str(atom.get("atom_id", "")),
            "next_question_topic": str(atom.get("topic", "")),
            "next_question_stage": str(atom.get("stage", "")),
            "next_question_score": float(atom.get("score", 0.0) or 0.0),
            "next_question_score_reasons": tuple(str(row) for row in atom.get("score_reasons", ()) if str(row))
            if isinstance(atom.get("score_reasons", ()), list | tuple)
            else (),
            "question_strategy": _append_strategy(str(payload.get("question_strategy", "")), "next_question_plan"),
        }
    )
    return replace(question, **{key: value for key, value in payload.items() if hasattr(question, key)})


def _append_strategy(strategy: str, suffix: str) -> str:
    if not strategy:
        return suffix
    if suffix in strategy:
        return strategy
    return f"{strategy}+{suffix}"


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
                "matched_question_titles": [_question_display_title(question) for question in matched_questions],
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
        "selected_question_title": _question_display_title(selected),
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
                "matched_question_titles": [_question_display_title(question) for question in matched_questions],
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
        "selected_question_title": _question_display_title(selected_question),
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
