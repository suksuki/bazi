from __future__ import annotations

from datetime import datetime, timezone
import os
from typing import Any

from v30.contracts import (
    BaziQuestionAnchor,
    ChartContext,
    CoreRuntimeResult,
    FeatureEvidence,
    QuestionIntentPlan,
)
from v30.answer import build_answer_context, compose_rule_bound_answer
from v30.brain import (
    CENTRAL_BRAIN_VERSION,
    build_adaptive_question_diagnostics,
    build_central_brain_trace,
    build_central_reading_state,
    build_expression_role_state,
    build_recommendation_brain_context,
    route_real_bazi_diagnosis,
    summarize_diagnosis_route,
)
from v30.core.chart_context import build_chart_context_from_displays
from v30.core.ten_god_energy import build_ten_god_energy_model
from v30.evidence import compile_feature_evidence
from v30.hidden_factor import (
    build_individualized_model_projection,
    build_hidden_factor_probes,
    build_latent_bazi_attributes,
    build_latent_bazi_profile,
    build_latent_question_need_strategy,
    calibrate_hidden_factors,
    normalize_hidden_factor_state_payload,
    summarize_individualized_model_projection,
    summarize_latent_bazi_attributes,
    summarize_latent_bazi_profile,
)
from v30.interaction_brain import process_interaction_turn
from v30.interaction_constraints import validate_structured_interaction_payload
from v30.expression import EXPRESSION_FRAMEWORK_VERSION, build_runtime_narrative_plan, render_narrative
from v30.knowledge import (
    KnowledgeRulePortraitSignal,
    build_macro_dimension_signals,
    build_knowledge_rule_portrait_signals,
    load_core_macro_pack,
    match_krp_library_units,
    summarize_core_macro_pack,
    summarize_krp_library_units,
)
from v30.llm import (
    LLM_OUTPUT_CONTRACT_VERSION,
    build_answer_draft_contract,
    build_failure_cluster_summary_contract,
    build_question_explanation_contract,
    build_synthetic_case_draft_contract,
    compose_bazi_llm_answer_draft,
    llm_provider_readiness_report,
    summarize_llm_output_contracts,
)
from v30.mainline import select_mainline_state
from v30.questions import build_question_dialogue_graph, recommend_questions, select_question_anchors
from v30.structure import select_structure_state
from v30.policy import RuntimePointerStore
from v30.policy.runtime_pointer import baseline_artifact
from v30.portrait import (
    build_macro_portrait_projection_views,
    build_macro_portrait_projections,
    summarize_macro_portrait_projection_views,
    summarize_macro_portrait_projections,
)
from v30.practical import build_agent_question_flow, build_practical_reading_context, build_ranked_decisions
from v30.production import build_production_sidecar
from v30.diagnosis import (
    build_diagnosis_graph,
    extract_diagnosis_features,
    extract_diagnosis_portraits,
    generate_diagnosis_claims,
    match_real_bazi_rules,
    summarize_diagnosis_claims,
    summarize_diagnosis_features,
    summarize_diagnosis_graph,
    summarize_diagnosis_paths,
    summarize_diagnosis_portraits,
    summarize_rule_matches,
    translate_dynamic_paths,
)


RUNTIME_POLICY_FAMILIES = ("structure_policy", "mainline_policy", "question_policy", "rule_policy")


def _should_use_runtime_policy_pointers(
    *,
    policy_payload_overrides: dict[str, dict[str, object]],
    active_policy_version_overrides: dict[str, str] | None,
) -> bool:
    return "V30_RUNTIME_DIR" in os.environ


def _baseline_policy_versions() -> dict[str, str]:
    return {
        family: baseline_artifact(family).artifact_id
        for family in RUNTIME_POLICY_FAMILIES
    }


def _policy_payload(
    pointer_store: RuntimePointerStore | None,
    family: str,
) -> dict[str, object]:
    if pointer_store is None:
        return _runtime_baseline_policy_payload(family)
    return pointer_store.load_active_artifact(family).payload


def _runtime_baseline_policy_payload(family: str) -> dict[str, object]:
    payload = baseline_artifact(family).payload
    if family == "structure_policy":
        return {
            **payload,
            "weights": {
                "mechanism.hidden_factor_dialogue_probe": 1.0,
                "mechanism.ten_god_visibility_context": 1.0,
                "mechanism.useful_god_candidate_gate": 1.0,
                "mechanism.branch_relation_dynamic_review": 1.0,
            },
        }
    if family == "question_policy":
        return {
            **payload,
            "weights": {
                "topic_weights": {"*": 1.0},
                "intent_weights": {"*": 1.0},
                "stage_weights": {"*": 1.0},
                "question_weights": {"*": 1.0},
            },
        }
    if family == "rule_policy":
        return {
            **payload,
            "weights": {
                "rule_weights": {"*": 1.0},
                "domain_weights": {"*": 1.0},
            },
        }
    return payload


def create_smoke_runtime(
    reading_id: str,
    day_master: str = "甲",
    day_master_element: str = "wood",
    locale: str = "zh",
    luck_pillar: str = "",
    flow_year_pillar: str = "",
    hidden_factor_user_calibrated: bool = False,
    useful_god_path_resolved: bool = False,
    branch_single_factor_confirmed: bool = False,
    policy_payload_overrides: dict[str, dict[str, object]] | None = None,
    active_policy_version_overrides: dict[str, str] | None = None,
) -> CoreRuntimeResult:
    context = build_chart_context_from_displays(
        reading_id=reading_id,
        year="甲子",
        month="乙丑",
        day=f"{day_master}寅",
        hour="丁卯",
        luck_pillar=luck_pillar,
        flow_year_pillar=flow_year_pillar,
        locale=locale,
    )
    return create_runtime_from_context(
        context,
        hidden_factor_user_calibrated=hidden_factor_user_calibrated,
        useful_god_path_resolved=useful_god_path_resolved,
        branch_single_factor_confirmed=branch_single_factor_confirmed,
        policy_payload_overrides=policy_payload_overrides,
        active_policy_version_overrides=active_policy_version_overrides,
        trace_suffix="smoke",
    )


def create_runtime_from_context(
    context: ChartContext,
    *,
    hidden_factor_user_calibrated: bool = False,
    useful_god_path_resolved: bool = False,
    branch_single_factor_confirmed: bool = False,
    policy_payload_overrides: dict[str, dict[str, object]] | None = None,
    active_policy_version_overrides: dict[str, str] | None = None,
    trace_suffix: str = "runtime",
) -> CoreRuntimeResult:
    reading_id = context.reading_id
    policy_payload_overrides = policy_payload_overrides or {}
    use_runtime_pointers = _should_use_runtime_policy_pointers(
        policy_payload_overrides=policy_payload_overrides,
        active_policy_version_overrides=active_policy_version_overrides,
    )
    pointer_store = RuntimePointerStore() if use_runtime_pointers else None
    active_policy_versions = (
        pointer_store.active_versions(RUNTIME_POLICY_FAMILIES)
        if pointer_store is not None
        else _baseline_policy_versions()
    )
    if active_policy_version_overrides:
        active_policy_versions.update(active_policy_version_overrides)
    rule_policy = (
        policy_payload_overrides.get("rule_policy")
        or _policy_payload(pointer_store, "rule_policy")
    )
    ten_god_energy_model = build_ten_god_energy_model(context)
    feature_evidence = compile_feature_evidence(
        context,
        rule_policy,
        ten_god_energy_model=ten_god_energy_model,
        supplemental_evidence=_supplemental_feedback_evidence(
            context_id=context.context_id,
            hidden_factor_user_calibrated=hidden_factor_user_calibrated,
            useful_god_path_resolved=useful_god_path_resolved,
            branch_single_factor_confirmed=branch_single_factor_confirmed,
        ),
    )
    hidden_factor_probes = build_hidden_factor_probes(context, feature_evidence)
    hidden_factor_calibration = calibrate_hidden_factors(context.context_id, feature_evidence)
    knowledge_rule_portrait_signals = build_knowledge_rule_portrait_signals(feature_evidence)
    structure_policy = (
        policy_payload_overrides.get("structure_policy")
        or _policy_payload(pointer_store, "structure_policy")
    )
    question_policy = (
        policy_payload_overrides.get("question_policy")
        or _policy_payload(pointer_store, "question_policy")
    )
    krp_library_units = match_krp_library_units(feature_evidence, question_policy)
    krp_library_summary = summarize_krp_library_units(krp_library_units)
    core_macro_pack = load_core_macro_pack()
    core_macro_summary = summarize_core_macro_pack(core_macro_pack, feature_evidence)
    macro_dimension_signals = build_macro_dimension_signals(feature_evidence, core_macro_pack)
    macro_portrait_projections = build_macro_portrait_projections(
        [row.model_dump(mode="json") for row in macro_dimension_signals]
    )
    macro_portrait_summary = summarize_macro_portrait_projections(macro_portrait_projections)
    macro_portrait_projection_views = build_macro_portrait_projection_views(
        macro_portrait_projections,
        role_key="user",
        client="web",
    )
    macro_portrait_view_summary = summarize_macro_portrait_projection_views(macro_portrait_projection_views)
    ten_god_energy_payload = ten_god_energy_model.model_dump(mode="json")
    ten_god_energy_summary = _ten_god_energy_summary(ten_god_energy_payload)
    model_signal_summary = _model_signal_summary(context, ten_god_energy_summary)
    structure = select_structure_state(
        context,
        feature_evidence,
        knowledge_rule_portrait_signals,
        structure_policy,
        model_signal_summary=model_signal_summary,
    )
    mainline = select_mainline_state(structure, feature_evidence, knowledge_rule_portrait_signals)
    ranked_decisions = build_ranked_decisions(
        context,
        feature_evidence,
        structure,
        model_signal_summary=model_signal_summary,
    )
    practical_reading = build_practical_reading_context(
        context,
        structure,
        ranked_decisions,
        ten_god_energy_summary=ten_god_energy_summary,
    )
    real_bazi_diagnosis = _build_real_bazi_diagnosis_payload(
        reading_id=reading_id,
        context=context,
        feature_evidence=feature_evidence,
        structure=structure,
        model_signal_summary=model_signal_summary,
        krp_library_units=krp_library_units,
    )
    practical_reading = practical_reading.model_copy(
        update={
            "domain_readings": _apply_real_bazi_diagnosis_to_domain_readings(
                practical_reading.domain_readings,
                real_bazi_diagnosis,
            ),
            "boundaries": [
                *practical_reading.boundaries,
                "real_bazi_diagnosis_claims_are_consumed_as_m6_reading_support_not_chart_facts",
            ],
        }
    )
    m3_completion_summary = _m3_completion_summary(
        feature_evidence=feature_evidence,
        knowledge_rule_portrait_signals=knowledge_rule_portrait_signals,
        structure_path_scores=structure.path_scores,
        structure_graph_nodes=structure.graph_nodes,
        mainline_supporting=mainline.supporting_mainlines,
        krp_library_summary=krp_library_summary,
        model_signal_summary=model_signal_summary,
        ranked_decisions=ranked_decisions,
        practical_reading_context=practical_reading.model_dump(mode="json"),
    )
    agent_question_flow = build_agent_question_flow(practical_reading, context)
    question_anchors = select_question_anchors(context, structure, mainline, feature_evidence)
    recommendation_brain_context = build_recommendation_brain_context(
        reading_id=reading_id,
        role_key="user",
        active_mainline_id=mainline.mainline_id,
        time_status=str(context.time_layers.get("status", "not_provided")),
        hidden_factor_status=str(hidden_factor_calibration.status),
    )
    latent_attributes = build_latent_bazi_attributes(context=context).model_dump(mode="json")
    individualized_projection = build_individualized_model_projection(
        context=context,
        ten_god_energy_model=ten_god_energy_payload,
        ten_god_energy_summary=ten_god_energy_summary,
        ranked_decisions=ranked_decisions,
        latent_attributes=latent_attributes,
    )
    latent_question_strategy = build_latent_question_need_strategy(
        context=context,
        latent_attributes=latent_attributes,
        individualized_projection=individualized_projection,
        practical_reading_context=practical_reading.model_dump(mode="json"),
        model_signal_summary=model_signal_summary,
        question_outcomes=[],
    )
    recommendations = recommend_questions(
        question_anchors,
        structure=structure,
        mainline=mainline,
        evidence=feature_evidence,
        active_policy_versions=active_policy_versions,
        knowledge_rule_portrait_signals=knowledge_rule_portrait_signals,
        macro_dimension_signals=[row.model_dump(mode="json") for row in macro_dimension_signals],
        question_policy=question_policy,
        central_brain_context=recommendation_brain_context,
        practical_reading_context=practical_reading.model_dump(mode="json"),
        model_signal_summary=model_signal_summary,
        latent_question_strategy=latent_question_strategy,
    )
    question_dialogue_graph = build_question_dialogue_graph(
        reading_id=reading_id,
        recommendations=recommendations,
        hidden_factor_calibration=hidden_factor_calibration.model_dump(mode="json"),
        hidden_factor_state={},
    )
    interaction_state = _interaction_state(question_dialogue_graph.model_dump(mode="json"), [], recommendations)
    central_reading_state = build_central_reading_state(
        reading_id=reading_id,
        role_key="user",
        diagnosis=real_bazi_diagnosis,
        recommendations=recommendations,
        question_dialogue_graph=question_dialogue_graph.model_dump(mode="json"),
        interaction_state=interaction_state,
        practical_reading_context=practical_reading.model_dump(mode="json"),
        ranked_decisions=ranked_decisions,
        model_signal_summary=model_signal_summary,
        question_policy=question_policy,
        question_outcomes=[],
    )
    plan = QuestionIntentPlan(
        plan_id=f"{reading_id}:question-plan:smoke",
        role_key="user",
        candidate_intents=[str(row["intent_id"]) for row in recommendations],
        recommended_questions=recommendations,
        hidden_factor_probes=[probe.model_dump(mode="json") for probe in hidden_factor_probes],
        knowledge_rule_portrait_signals=[
            signal.model_dump(mode="json") for signal in knowledge_rule_portrait_signals
        ],
        policy_effect={
            "active_policy_versions": active_policy_versions,
            "structure_policy_payload": structure_policy,
            "question_policy_payload": question_policy,
            "rule_policy_payload": rule_policy,
            "krp_library_units": krp_library_units,
            "krp_library_summary": krp_library_summary,
            "core_macro_pack_summary": core_macro_summary,
            "macro_dimension_signals": [row.model_dump(mode="json") for row in macro_dimension_signals],
            "macro_portrait_projections": [row.model_dump(mode="json") for row in macro_portrait_projections],
            "macro_portrait_summary": macro_portrait_summary,
            "macro_portrait_projection_views": [
                row.model_dump(mode="json") for row in macro_portrait_projection_views
            ],
            "macro_portrait_view_summary": macro_portrait_view_summary,
            "hidden_factor_calibration": hidden_factor_calibration.model_dump(mode="json"),
            "latent_bazi_attributes": latent_attributes,
            "latent_bazi_attributes_summary": summarize_latent_bazi_attributes(latent_attributes),
            "latent_bazi_individualized_projection": individualized_projection,
            "latent_bazi_individualized_projection_summary": summarize_individualized_model_projection(individualized_projection),
            "latent_question_strategy": latent_question_strategy,
            "ten_god_energy_model": ten_god_energy_payload,
            "ten_god_energy_summary": ten_god_energy_summary,
            "model_signal_summary": model_signal_summary,
            "ranked_decisions": ranked_decisions,
            "practical_reading_context": practical_reading.model_dump(mode="json"),
            "real_bazi_diagnosis": real_bazi_diagnosis,
            "m3_completion_summary": m3_completion_summary,
            "agent_question_flow": agent_question_flow,
            "recommendation_brain_context": recommendation_brain_context,
            "question_dialogue_graph": question_dialogue_graph.model_dump(mode="json"),
            "interaction_state": interaction_state,
            "central_reading_state": central_reading_state,
        },
    )
    selected_anchor = _select_answer_anchor(question_anchors, recommendations)
    without_answer = CoreRuntimeResult(
        reading_id=reading_id,
        chart_context=context,
        feature_evidence=feature_evidence,
        structure_state=structure,
        mainline_state=mainline,
        question_plan=plan,
        question_anchors=question_anchors,
        trace_id=f"{reading_id}:trace:{trace_suffix}",
    )
    answer_context = build_answer_context(without_answer, selected_anchor) if selected_anchor is not None else None
    answer_result = (
        compose_rule_bound_answer(answer_context, runtime=without_answer)
        if answer_context is not None
        else None
    )
    if answer_context is not None and answer_result is not None:
        answer_result = compose_bazi_llm_answer_draft(
            without_answer,
            answer_context,
            answer_result,
            reading_surface=_runtime_reading_surface(without_answer),
        )
    plan = _attach_expression_policy_effect(without_answer, plan, answer_context, answer_result)
    result = CoreRuntimeResult(
        reading_id=reading_id,
        chart_context=context,
        feature_evidence=feature_evidence,
        structure_state=structure,
        mainline_state=mainline,
        question_plan=plan,
        question_anchors=question_anchors,
        answer_context=answer_context,
        answer_result=answer_result,
        trace_id=f"{reading_id}:trace:{trace_suffix}",
    )
    return _attach_production_sidecar(result)


def attach_hidden_factor_state(
    runtime: CoreRuntimeResult,
    hidden_factor_state: dict[str, object] | None,
) -> CoreRuntimeResult:
    if not hidden_factor_state:
        return runtime
    hidden_factor_state = normalize_hidden_factor_state_payload(hidden_factor_state)
    question_policy = runtime.question_plan.policy_effect.get("question_policy_payload", {})
    active_policy_versions = runtime.question_plan.policy_effect.get("active_policy_versions", {})
    question_outcomes = _question_outcomes(runtime)
    latent_profile = build_latent_bazi_profile(
        context=runtime.chart_context,
        structure=runtime.structure_state,
        feature_evidence=runtime.feature_evidence,
        hidden_factor_state=hidden_factor_state,
        real_bazi_diagnosis=_dict_policy_effect(runtime, "real_bazi_diagnosis"),
        question_outcomes=question_outcomes,
    ).model_dump(mode="json")
    latent_attributes = build_latent_bazi_attributes(
        context=runtime.chart_context,
        latent_profile=latent_profile,
    ).model_dump(mode="json")
    individualized_projection = build_individualized_model_projection(
        context=runtime.chart_context,
        ten_god_energy_model=_dict_policy_effect(runtime, "ten_god_energy_model"),
        ten_god_energy_summary=_dict_policy_effect(runtime, "ten_god_energy_summary"),
        ranked_decisions=_dict_policy_effect(runtime, "ranked_decisions"),
        latent_attributes=latent_attributes,
    )
    latent_question_strategy = build_latent_question_need_strategy(
        context=runtime.chart_context,
        latent_attributes=latent_attributes,
        individualized_projection=individualized_projection,
        practical_reading_context=_dict_policy_effect(runtime, "practical_reading_context"),
        model_signal_summary=_dict_policy_effect(runtime, "model_signal_summary"),
        question_outcomes=question_outcomes,
    )
    recommendations = recommend_questions(
        runtime.question_anchors,
        structure=runtime.structure_state,
        mainline=runtime.mainline_state,
        evidence=runtime.feature_evidence,
        active_policy_versions=active_policy_versions if isinstance(active_policy_versions, dict) else {},
        knowledge_rule_portrait_signals=[
            KnowledgeRulePortraitSignal.model_validate(row)
            for row in runtime.question_plan.knowledge_rule_portrait_signals
        ],
        macro_dimension_signals=_list_policy_effect(runtime, "macro_dimension_signals"),
        question_policy=question_policy if isinstance(question_policy, dict) else {},
        hidden_factor_state=hidden_factor_state,
        question_outcomes=question_outcomes,
        central_brain_context=build_recommendation_brain_context(
            reading_id=runtime.reading_id,
            role_key=runtime.question_plan.role_key,
            active_mainline_id=runtime.mainline_state.mainline_id,
            time_status=str(runtime.chart_context.time_layers.get("status", "not_provided")),
            hidden_factor_status=str(hidden_factor_state.get("status") or _dict_policy_effect(runtime, "hidden_factor_calibration").get("status") or "unknown"),
        ),
        practical_reading_context=_dict_policy_effect(runtime, "practical_reading_context"),
        model_signal_summary=_dict_policy_effect(runtime, "model_signal_summary"),
        latent_question_strategy=latent_question_strategy,
    )
    question_dialogue_graph = build_question_dialogue_graph(
        reading_id=runtime.reading_id,
        recommendations=recommendations,
        hidden_factor_calibration=_dict_policy_effect(runtime, "hidden_factor_calibration"),
        hidden_factor_state=hidden_factor_state,
        question_outcomes=question_outcomes,
    )
    recommendation_brain_context = build_recommendation_brain_context(
        reading_id=runtime.reading_id,
        role_key=runtime.question_plan.role_key,
        active_mainline_id=runtime.mainline_state.mainline_id,
        time_status=str(runtime.chart_context.time_layers.get("status", "not_provided")),
        hidden_factor_status=str(hidden_factor_state.get("status") or _dict_policy_effect(runtime, "hidden_factor_calibration").get("status") or "unknown"),
    )
    interaction_state = _interaction_state(
        question_dialogue_graph.model_dump(mode="json"),
        question_outcomes,
        recommendations,
    )
    central_reading_state = build_central_reading_state(
        reading_id=runtime.reading_id,
        role_key=str(runtime.question_plan.role_key),
        diagnosis=_dict_policy_effect(runtime, "real_bazi_diagnosis"),
        recommendations=recommendations,
        question_dialogue_graph=question_dialogue_graph.model_dump(mode="json"),
        interaction_state=interaction_state,
        practical_reading_context=_dict_policy_effect(runtime, "practical_reading_context"),
        ranked_decisions=_dict_policy_effect(runtime, "ranked_decisions"),
        model_signal_summary=_dict_policy_effect(runtime, "model_signal_summary"),
        question_policy=question_policy if isinstance(question_policy, dict) else {},
        question_outcomes=question_outcomes,
    )
    policy_effect = {
        **runtime.question_plan.policy_effect,
        "hidden_factor_state": hidden_factor_state,
        "latent_bazi_profile": latent_profile,
        "latent_bazi_profile_summary": summarize_latent_bazi_profile(latent_profile),
        "latent_bazi_attributes": latent_attributes,
        "latent_bazi_attributes_summary": summarize_latent_bazi_attributes(latent_attributes),
        "latent_bazi_individualized_projection": individualized_projection,
        "latent_bazi_individualized_projection_summary": summarize_individualized_model_projection(individualized_projection),
        "latent_question_strategy": latent_question_strategy,
        "recommendation_brain_context": recommendation_brain_context,
        "question_dialogue_graph": question_dialogue_graph.model_dump(mode="json"),
        "interaction_state": interaction_state,
        "central_reading_state": central_reading_state,
    }
    plan = runtime.question_plan.model_copy(
        update={
            "recommended_questions": recommendations,
            "candidate_intents": [str(row["intent_id"]) for row in recommendations],
            "policy_effect": policy_effect,
        }
    )
    selected_anchor = _select_answer_anchor(runtime.question_anchors, recommendations)
    without_answer = runtime.model_copy(update={"question_plan": plan, "answer_context": None, "answer_result": None})
    answer_context = build_answer_context(without_answer, selected_anchor) if selected_anchor is not None else None
    answer_result = (
        compose_rule_bound_answer(answer_context, runtime=without_answer)
        if answer_context is not None
        else None
    )
    if answer_context is not None and answer_result is not None:
        answer_result = compose_bazi_llm_answer_draft(
            without_answer,
            answer_context,
            answer_result,
            reading_surface=_runtime_reading_surface(without_answer),
        )
    plan = _attach_expression_policy_effect(without_answer, plan, answer_context, answer_result)
    result = without_answer.model_copy(update={"question_plan": plan, "answer_context": answer_context, "answer_result": answer_result})
    return _attach_production_sidecar(result)


def attach_question_outcome(
    runtime: CoreRuntimeResult,
    question_id: str,
    answer_payload: dict[str, Any],
) -> CoreRuntimeResult:
    anchor = next((row for row in runtime.question_anchors if row.question_id == question_id), None)
    if anchor is None:
        raise ValueError(f"question not found: {question_id}")
    current = runtime.question_plan.session_state.get("question_outcomes", [])
    outcomes = [row for row in current if isinstance(row, dict)] if isinstance(current, list) else []
    existing_by_question = {
        str(row.get("question_id")): row
        for row in outcomes
        if isinstance(row, dict)
    }
    prior = existing_by_question.get(question_id)
    now = datetime.now(timezone.utc)
    recommendation = next(
        (row for row in runtime.question_plan.recommended_questions if row.get("question_id") == question_id),
        {},
    )
    topic = str(recommendation.get("topic") or _topic_from_anchor(anchor))
    stage = str(recommendation.get("stage") or _stage_from_anchor(anchor))
    constraints = recommendation.get("answer_constraints", {})
    constraints = constraints if isinstance(constraints, dict) else {}
    structured_payload = answer_payload.get("structured_payload")
    structured_payload = structured_payload if isinstance(structured_payload, dict) else {}
    interaction_turn_signal = validate_structured_interaction_payload(
        question_id=question_id,
        question_type=str(constraints.get("constraint_type") or ""),
        constraints=constraints,
        structured_payload=structured_payload,
        free_note=str(answer_payload.get("answer") or ""),
        selected_option=str(answer_payload.get("selected_option") or ""),
    )
    event = {
        "event_id": str(answer_payload.get("event_id") or (prior or {}).get("event_id") or f"{runtime.reading_id}:question-outcome:{question_id}"),
        "reading_id": runtime.reading_id,
        "question_id": question_id,
        "intent_id": anchor.intent_id,
        "topic": topic,
        "stage": stage,
        "submit_source": {
            "version": "v30.question_outcome_submit_source.v1",
            "submit_surface": str(answer_payload.get("submit_surface") or "legacy_answer_endpoint"),
            "submit_source_id": str(answer_payload.get("submit_source_id") or ""),
            "submit_contract_version": str(answer_payload.get("submit_contract_version") or ""),
            "legacy": not bool(answer_payload.get("submit_surface")),
            "boundary": "submit_source_records_ui_surface_without_changing_chart_facts",
        },
        "answer": str(answer_payload.get("answer") or ""),
        "outcome_status": _question_outcome_status(answer_payload.get("outcome_status")),
        "selected_option": str(answer_payload.get("selected_option") or ""),
        "structured_payload": structured_payload,
        "interaction_turn_signal": interaction_turn_signal,
        "constraint_valid": bool(interaction_turn_signal.get("valid")),
        "constraint_errors": interaction_turn_signal.get("validation_errors", []),
        "confidence": _bounded_float(answer_payload.get("confidence"), default=0.6),
        "feedback_tags": _str_list(answer_payload.get("feedback_tags")),
        "created_at": str((prior or {}).get("created_at") or now.isoformat()),
        "updated_at": now.isoformat(),
        "boundary": "question_outcome_feedback_not_chart_fact",
    }
    merged = [row for row in outcomes if str(row.get("question_id")) != question_id]
    merged.append(event)
    session_state = {
        **runtime.question_plan.session_state,
        "question_outcomes": merged,
        "known_user_signals": _known_user_signals(merged),
        "latest_interaction_turn_signal": interaction_turn_signal,
    }
    question_policy = runtime.question_plan.policy_effect.get("question_policy_payload", {})
    active_policy_versions = runtime.question_plan.policy_effect.get("active_policy_versions", {})
    hidden_factor_state = _dict_policy_effect(runtime, "hidden_factor_state")
    latent_question_strategy = build_latent_question_need_strategy(
        context=runtime.chart_context,
        latent_attributes=_dict_policy_effect(runtime, "latent_bazi_attributes"),
        individualized_projection=_dict_policy_effect(runtime, "latent_bazi_individualized_projection"),
        practical_reading_context=_dict_policy_effect(runtime, "practical_reading_context"),
        model_signal_summary=_dict_policy_effect(runtime, "model_signal_summary"),
        question_outcomes=merged,
    )
    recommendations = recommend_questions(
        runtime.question_anchors,
        structure=runtime.structure_state,
        mainline=runtime.mainline_state,
        evidence=runtime.feature_evidence,
        active_policy_versions=active_policy_versions if isinstance(active_policy_versions, dict) else {},
        knowledge_rule_portrait_signals=[
            KnowledgeRulePortraitSignal.model_validate(row)
            for row in runtime.question_plan.knowledge_rule_portrait_signals
        ],
        macro_dimension_signals=_list_policy_effect(runtime, "macro_dimension_signals"),
        question_policy=question_policy if isinstance(question_policy, dict) else {},
        hidden_factor_state=hidden_factor_state,
        question_outcomes=merged,
        central_brain_context=build_recommendation_brain_context(
            reading_id=runtime.reading_id,
            role_key=runtime.question_plan.role_key,
            active_mainline_id=runtime.mainline_state.mainline_id,
            time_status=str(runtime.chart_context.time_layers.get("status", "not_provided")),
            hidden_factor_status=str(hidden_factor_state.get("status") or _dict_policy_effect(runtime, "hidden_factor_calibration").get("status") or "unknown"),
        ),
        practical_reading_context=_dict_policy_effect(runtime, "practical_reading_context"),
        model_signal_summary=_dict_policy_effect(runtime, "model_signal_summary"),
        latent_question_strategy=latent_question_strategy,
    )
    question_dialogue_graph = build_question_dialogue_graph(
        reading_id=runtime.reading_id,
        recommendations=recommendations,
        hidden_factor_calibration=_dict_policy_effect(runtime, "hidden_factor_calibration"),
        hidden_factor_state=hidden_factor_state,
        question_outcomes=merged,
    )
    interaction_state = _interaction_state(question_dialogue_graph.model_dump(mode="json"), merged, recommendations)
    central_reading_state = build_central_reading_state(
        reading_id=runtime.reading_id,
        role_key=str(runtime.question_plan.role_key),
        diagnosis=_dict_policy_effect(runtime, "real_bazi_diagnosis"),
        recommendations=recommendations,
        question_dialogue_graph=question_dialogue_graph.model_dump(mode="json"),
        interaction_state=interaction_state,
        practical_reading_context=_dict_policy_effect(runtime, "practical_reading_context"),
        ranked_decisions=_dict_policy_effect(runtime, "ranked_decisions"),
        model_signal_summary=_dict_policy_effect(runtime, "model_signal_summary"),
        question_policy=question_policy if isinstance(question_policy, dict) else {},
        question_outcomes=merged,
    )
    policy_effect = {
        **runtime.question_plan.policy_effect,
        "question_outcomes": merged,
        "known_user_signals": _known_user_signals(merged),
        "question_dialogue_graph": question_dialogue_graph.model_dump(mode="json"),
        "interaction_state": interaction_state,
        "central_reading_state": central_reading_state,
        "latent_question_strategy": latent_question_strategy,
        "latest_interaction_turn_signal": interaction_turn_signal,
        "interaction_brain_result": process_interaction_turn(
            reading_id=runtime.reading_id,
            question_id=question_id,
            turn_signal=interaction_turn_signal,
        ),
    }
    plan = runtime.question_plan.model_copy(
        update={
            "session_state": session_state,
            "recommended_questions": recommendations,
            "candidate_intents": [str(row["intent_id"]) for row in recommendations],
            "policy_effect": policy_effect,
        }
    )
    selected_anchor = anchor
    without_answer = runtime.model_copy(update={"question_plan": plan, "answer_context": None, "answer_result": None})
    answer_context = build_answer_context(without_answer, selected_anchor) if selected_anchor is not None else None
    answer_result = (
        compose_rule_bound_answer(answer_context, runtime=without_answer)
        if answer_context is not None
        else None
    )
    if answer_context is not None and answer_result is not None:
        answer_result = compose_bazi_llm_answer_draft(
            without_answer,
            answer_context,
            answer_result,
            reading_surface=_runtime_reading_surface(without_answer),
        )
    plan = _attach_expression_policy_effect(without_answer, plan, answer_context, answer_result)
    result = without_answer.model_copy(update={"question_plan": plan, "answer_context": answer_context, "answer_result": answer_result})
    return _attach_production_sidecar(result)


def _attach_expression_policy_effect(
    runtime: CoreRuntimeResult,
    plan: QuestionIntentPlan,
    answer_context,
    answer_result=None,
) -> QuestionIntentPlan:
    if answer_context is None:
        return plan
    role_state = build_expression_role_state(
        reading_id=runtime.reading_id,
        role_key=runtime.question_plan.role_key,
        locale=runtime.chart_context.locale,
        client="web",
    )
    narrative_plan = build_runtime_narrative_plan(runtime, answer_context=answer_context, role_state=role_state)
    rendered = render_narrative(narrative_plan)
    brain_trace = build_central_brain_trace(
        runtime,
        answer_context=answer_context,
        expression_plan=narrative_plan.model_dump(mode="json"),
        rendered_narrative=rendered.model_dump(mode="json"),
    )
    adaptive_question_diagnostics = build_adaptive_question_diagnostics(
        runtime,
        central_brain_trace=brain_trace.model_dump(mode="json"),
    )
    policy_effect = {
        **plan.policy_effect,
        "expression_framework_version": EXPRESSION_FRAMEWORK_VERSION,
        "expression_plan": narrative_plan.model_dump(mode="json"),
        "rendered_narrative": rendered.model_dump(mode="json"),
        "central_brain_version": CENTRAL_BRAIN_VERSION,
        "central_brain_trace": brain_trace.model_dump(mode="json"),
        "adaptive_question_diagnostics": adaptive_question_diagnostics.model_dump(mode="json"),
        "llm_provider_readiness": llm_provider_readiness_report(),
    }
    if answer_result is not None:
        contracts = [
            build_answer_draft_contract(answer_context, answer_result, role_key=plan.role_key),
            build_question_explanation_contract(answer_context, role_key=plan.role_key),
            build_synthetic_case_draft_contract(answer_context, role_key="lab"),
            build_failure_cluster_summary_contract(answer_context, role_key="lab"),
        ]
        policy_effect.update(
            {
                "llm_output_contract_version": LLM_OUTPUT_CONTRACT_VERSION,
                "llm_output_contracts": [contract.model_dump(mode="json") for contract in contracts],
                "llm_output_contract_summary": summarize_llm_output_contracts(contracts),
                "llm_answer_draft_call": answer_result.llm_metadata,
            }
        )
    return plan.model_copy(update={"policy_effect": policy_effect})


def _attach_production_sidecar(runtime: CoreRuntimeResult) -> CoreRuntimeResult:
    policy_effect = runtime.question_plan.policy_effect
    central_state = _dict_policy_effect(runtime, "central_reading_state")
    sidecar = build_production_sidecar(
        reading_id=runtime.reading_id,
        feature_evidence=runtime.feature_evidence,
        macro_signals=_list_policy_effect(runtime, "macro_dimension_signals"),
        ranked_decisions=_dict_policy_effect(runtime, "ranked_decisions"),
        practical_context=_dict_policy_effect(runtime, "practical_reading_context"),
        diagnosis=_dict_policy_effect(runtime, "real_bazi_diagnosis"),
        central_state=central_state,
        decision_result=central_state.get("decision_result") if isinstance(central_state, dict) else {},
        final_synthesis=central_state.get("final_synthesis") if isinstance(central_state, dict) else {},
        reading_surface=_runtime_reading_surface(runtime),
    )
    sidecar_payload = sidecar.model_dump(mode="json")
    plan = runtime.question_plan.model_copy(
        update={
            "policy_effect": {
                **policy_effect,
                "production_sidecar": sidecar_payload,
                "production_signal_registry": sidecar_payload["registry"],
                "production_usage_audit": sidecar_payload["usage_audit"],
                "production_module_audit": sidecar_payload["module_audit"],
                "production_audit_summary": sidecar_payload["summary"],
            }
        }
    )
    return runtime.model_copy(update={"question_plan": plan})


def _dict_policy_effect(runtime: CoreRuntimeResult, key: str) -> dict[str, object]:
    value = runtime.question_plan.policy_effect.get(key, {})
    return value if isinstance(value, dict) else {}


def _build_real_bazi_diagnosis_payload(
    *,
    reading_id: str,
    context: ChartContext,
    feature_evidence: list[FeatureEvidence],
    structure: Any,
    model_signal_summary: dict[str, Any],
    krp_library_units: list[dict[str, Any]],
) -> dict[str, Any]:
    paths = translate_dynamic_paths(structure, timing_context=context.time_layers)
    matches = match_real_bazi_rules(
        feature_evidence=feature_evidence,
        structure_state=structure,
        model_signal_summary=model_signal_summary,
        krp_units=krp_library_units,
    )
    features = extract_diagnosis_features(
        feature_evidence=feature_evidence,
        matched_rules=matches,
        diagnosis_paths=paths,
    )
    portraits = extract_diagnosis_portraits(
        matched_rules=matches,
        diagnosis_paths=paths,
        krp_units=krp_library_units,
    )
    claims = generate_diagnosis_claims(
        matched_rules=matches,
        features=features,
        paths=paths,
        portraits=portraits,
    )
    graph = build_diagnosis_graph(
        reading_id=reading_id,
        matched_rules=matches,
        features=features,
        paths=paths,
        portraits=portraits,
        claims=claims,
    )
    routes = {
        mode: route_real_bazi_diagnosis(
            reading_id=reading_id,
            role_key="user",
            graph=graph,
            claims=claims,
            paths=paths,
            portraits=portraits,
            requested_mode=mode,  # type: ignore[arg-type]
        )
        for mode in ("overview", "career", "wealth", "relationship", "health", "timing", "hidden_factor_calibration")
    }
    claim_payloads = [claim.model_dump(mode="json") for claim in claims]
    path_payloads = [path.model_dump(mode="json") for path in paths]
    portrait_payloads = [portrait.model_dump(mode="json") for portrait in portraits]
    return {
        "version": "v30.real_bazi_diagnosis.runtime_integration.v1",
        "reading_id": reading_id,
        "status": "ready" if claims else "empty",
        "summaries": {
            "rules": summarize_rule_matches(matches),
            "features": summarize_diagnosis_features(features),
            "paths": summarize_diagnosis_paths(paths),
            "portraits": summarize_diagnosis_portraits(portraits),
            "claims": summarize_diagnosis_claims(claims),
            "graph": summarize_diagnosis_graph(graph),
        },
        "routes": {key: summarize_diagnosis_route(route) for key, route in routes.items()},
        "selected_routes": {key: route.model_dump(mode="json") for key, route in routes.items()},
        "matched_rules": [match.model_dump(mode="json") for match in matches],
        "features": [feature.model_dump(mode="json") for feature in features],
        "claims": claim_payloads,
        "paths": path_payloads,
        "portraits": portrait_payloads,
        "graph": graph.model_dump(mode="json"),
        "public_projection": _real_bazi_public_projection(claim_payloads, path_payloads, portrait_payloads, routes),
        "storage_policy": {
            "postgres_target": "v30_diagnosis_runs",
            "redis_cache_key": f"v30:diagnosis:latest:{reading_id}",
            "authoritative_facts_stored_here": False,
            "boundary": "runtime_diagnosis_payload_is_projection_and_replay_data_not_chart_fact_source",
        },
        "boundary": "real_bazi_diagnosis_consumes_m1_to_m6_evidence_without_mutating_chart_facts",
    }


def _real_bazi_public_projection(
    claims: list[dict[str, Any]],
    paths: list[dict[str, Any]],
    portraits: list[dict[str, Any]],
    routes: dict[str, Any],
) -> dict[str, Any]:
    return {
        "version": "v30.real_bazi_diagnosis.public_projection.v1",
        "diagnosis_overview": _public_claim_text(claims, "structure"),
        "domain_summaries": {
            domain: _public_claim_text(claims, domain)
            for domain in ("career", "wealth", "relationship", "health", "timing", "useful_god", "hidden_factor")
        },
        "domain_claims": {
            domain: _public_claims(claims, domain, limit=5)
            for domain in ("career", "wealth", "relationship", "health", "timing", "useful_god", "hidden_factor")
        },
        "domain_paths": {
            domain: _public_paths(paths, domain, limit=4)
            for domain in ("career", "wealth", "relationship", "health", "timing", "useful_god", "structure")
        },
        "domain_portraits": {
            domain: _public_portraits(portraits, domain, limit=4)
            for domain in ("career", "wealth", "relationship", "health", "useful_god", "hidden_factor", "structure")
        },
        "route_summaries": {
            key: {
                "selected_domain": route.selected_domain,
                "selected_claim_count": len(route.selected_claim_ids),
                "followup_required": route.followup_required,
                "expression_density": route.expression_density,
            }
            for key, route in routes.items()
        },
        "boundary": "public_diagnosis_projection_contains_bounded_claim_text_not_internal_graph_or_raw_scores",
    }


def _apply_real_bazi_diagnosis_to_domain_readings(
    domain_readings: dict[str, Any],
    diagnosis: dict[str, Any],
) -> dict[str, Any]:
    projection = diagnosis.get("public_projection", {})
    projection = projection if isinstance(projection, dict) else {}
    summaries = projection.get("domain_summaries", {})
    claims = projection.get("domain_claims", {})
    paths = projection.get("domain_paths", {})
    portraits = projection.get("domain_portraits", {})
    if not isinstance(summaries, dict):
        summaries = {}
    if not isinstance(claims, dict):
        claims = {}
    if not isinstance(paths, dict):
        paths = {}
    if not isinstance(portraits, dict):
        portraits = {}
    out: dict[str, Any] = {}
    for domain, payload in domain_readings.items():
        row = dict(payload) if isinstance(payload, dict) else {}
        domain_summary = str(summaries.get(domain) or "")
        domain_claims = claims.get(domain, [])
        domain_paths = paths.get(domain, [])
        domain_portraits = portraits.get(domain, [])
        if domain_summary:
            row["summary"] = domain_summary
            row["customer_takeaway"] = domain_summary
            row["diagnosis_summary"] = domain_summary
            row["core_claim_quality"] = _core_claim_quality(
                domain=domain,
                diagnosis_summary=domain_summary,
                diagnosis_claims=domain_claims,
                diagnosis_paths=domain_paths,
                diagnosis_portraits=domain_portraits,
            )
        if isinstance(domain_claims, list):
            row["diagnosis_claims"] = domain_claims
        if isinstance(domain_paths, list):
            row["diagnosis_paths"] = domain_paths
        if isinstance(domain_portraits, list):
            row["portrait_dimensions"] = domain_portraits
        row["depends_on_modules"] = _append_unique(
            [str(item) for item in row.get("depends_on_modules", [])] if isinstance(row.get("depends_on_modules"), list) else [],
            ["RBD_real_bazi_diagnosis"],
        )
        module_trace = row.get("module_trace", {})
        if isinstance(module_trace, dict):
            row["module_trace"] = {
                **module_trace,
                "uses_real_bazi_diagnosis": True,
                "rbd_claim_count": len(domain_claims) if isinstance(domain_claims, list) else 0,
                "chart_fact_mutation_allowed": False,
            }
        row["rbd_reading_boundary"] = "practical_domain_reading_consumes_rbd_claims_without_fixed_event_or_chart_fact_mutation"
        out[str(domain)] = row
    return out


def _core_claim_quality(
    *,
    domain: str,
    diagnosis_summary: str,
    diagnosis_claims: Any,
    diagnosis_paths: Any,
    diagnosis_portraits: Any,
) -> dict[str, Any]:
    text = diagnosis_summary.strip()
    claims = diagnosis_claims if isinstance(diagnosis_claims, list) else []
    paths = diagnosis_paths if isinstance(diagnosis_paths, list) else []
    portraits = diagnosis_portraits if isinstance(diagnosis_portraits, list) else []
    generic_tokens = (
        "Current chart",
        "supports strength",
        "候选路径表达",
        "不做确定断语",
        "可以进入具体问题",
        "需结合后续问答",
        "fallback",
    )
    bazi_terms = ("财", "官", "印", "食伤", "十神", "五行", "结构", "大运", "流年", "用神", "日主")
    return {
        "version": "v30.core_bazi_claim_quality.v1",
        "domain": str(domain),
        "source": "RBD_real_bazi_diagnosis",
        "summary_ready": bool(text),
        "customer_takeaway_source": "diagnosis_summary",
        "bazi_specific_term_count": sum(1 for term in bazi_terms if term in text),
        "generic_language_hits": [token for token in generic_tokens if token in text],
        "diagnosis_claim_count": len(claims),
        "diagnosis_path_count": len(paths),
        "portrait_dimension_count": len(portraits),
        "uses_traceable_claims": bool(claims),
        "fixed_event_prediction_allowed": False,
        "chart_fact_mutation_allowed": False,
        "quality_ready": bool(text) and bool(claims) and not any(token in text for token in generic_tokens),
        "boundary": "core_bazi_claim_quality_validates_customer_reading_claims_not_life_truth_or_chart_facts",
    }


def _public_claim_text(claims: list[dict[str, Any]], domain: str) -> str:
    for level in ("domain", "path", "timing", "portrait", "feature", "question"):
        for claim in claims:
            if str(claim.get("domain") or "") == domain and str(claim.get("claim_level") or "") == level:
                return str(claim.get("claim_text") or "")
    return ""


def _public_claims(claims: list[dict[str, Any]], domain: str, *, limit: int) -> list[dict[str, Any]]:
    rows = [
        {
            "claim_id": str(claim.get("claim_id") or ""),
            "claim_level": str(claim.get("claim_level") or ""),
            "claim_text": str(claim.get("claim_text") or ""),
            "confidence_band": str(claim.get("confidence_band") or ""),
            "needs_user_calibration": bool(claim.get("needs_user_calibration", False)),
            "boundary": "diagnosis_claim_customer_projection_is_bounded_and_traceable",
        }
        for claim in claims
        if str(claim.get("domain") or "") == domain
    ]
    return rows[:limit]


def _public_paths(paths: list[dict[str, Any]], domain: str, *, limit: int) -> list[dict[str, Any]]:
    rows = [
        {
            "path_id": str(path.get("path_id") or ""),
            "mechanism": str(path.get("mechanism") or ""),
            "diagnosis_statement": str(path.get("diagnosis_statement") or ""),
            "risk_statement": str(path.get("risk_statement") or ""),
            "boundary": "diagnosis_path_customer_projection_not_event_prediction",
        }
        for path in paths
        if domain in [str(row) for row in path.get("domain_targets", []) if row]
    ]
    return rows[:limit]


def _public_portraits(portraits: list[dict[str, Any]], domain: str, *, limit: int) -> list[dict[str, Any]]:
    rows = [
        {
            "portrait_id": str(portrait.get("portrait_id") or ""),
            "dimension": str(portrait.get("dimension") or ""),
            "statement": str(portrait.get("statement") or ""),
            "confidence_band": str(portrait.get("confidence_band") or ""),
            "boundary": "diagnosis_portrait_customer_projection_not_personality_fact",
        }
        for portrait in portraits
        if str(portrait.get("domain") or "") == domain
    ]
    return rows[:limit]


def _append_unique(values: list[str], additions: list[str]) -> list[str]:
    out = list(values)
    for item in additions:
        if item not in out:
            out.append(item)
    return out


def _runtime_reading_surface(runtime: CoreRuntimeResult) -> dict[str, object]:
    practical = runtime.question_plan.policy_effect.get("practical_reading_context", {})
    diagnosis = runtime.question_plan.policy_effect.get("real_bazi_diagnosis", {})
    diagnosis_projection = diagnosis.get("public_projection", {}) if isinstance(diagnosis, dict) else {}
    agent_flow = runtime.question_plan.policy_effect.get("agent_question_flow", {})
    next_question = _runtime_next_question(runtime)
    domain_readings = practical.get("domain_readings", {}) if isinstance(practical, dict) else {}
    return {
        "version": "v30.customer_reading_surface.runtime_compact.v1",
        "reading_summary": {
            "title": runtime.mainline_state.title,
            "status": practical.get("status", "ready") if isinstance(practical, dict) else "ready",
            "timing_status": _nested_policy_dict(practical, "timing_summary", "status", default="natal_only"),
            "diagnosis_overview": str(diagnosis_projection.get("diagnosis_overview") or "") if isinstance(diagnosis_projection, dict) else "",
        },
        "focus_domains": _runtime_focus_domains(domain_readings),
        "next_question": next_question if isinstance(next_question, dict) else {},
        "next_stage": agent_flow.get("next_stage", "") if isinstance(agent_flow, dict) else "",
        "boundary": "runtime_compact_surface_for_llm_expression_not_chart_fact",
    }


def _runtime_next_question(runtime: CoreRuntimeResult) -> dict[str, object]:
    recommendations = runtime.question_plan.recommended_questions
    if not recommendations:
        return {}
    graph = runtime.question_plan.policy_effect.get("question_dialogue_graph", {})
    next_id = graph.get("next_question_id") if isinstance(graph, dict) else ""
    if next_id:
        for row in recommendations:
            if str(row.get("question_id")) == str(next_id):
                return row
    return recommendations[0]


def _interaction_state(
    question_dialogue_graph: dict[str, object],
    question_outcomes: list[dict[str, object]],
    recommendations: list[dict[str, object]],
) -> dict[str, object]:
    answered_question_ids = [
        str(row.get("question_id"))
        for row in question_outcomes
        if isinstance(row, dict) and row.get("question_id")
    ]
    selected_domain = _selected_domain(question_outcomes)
    internal_next_question_id = str(
        question_dialogue_graph.get("internal_next_question_id")
        or question_dialogue_graph.get("next_question_id")
        or ""
    )
    invalid_retry_question_id = _invalid_retry_question_id(question_outcomes)
    visible_next_question_id = _visible_next_question_id(
        recommendations,
        answered_question_ids=set(answered_question_ids),
        preferred_question_id=internal_next_question_id,
        invalid_retry_question_id=invalid_retry_question_id,
    )
    return {
        "version": "v30.interaction_state.v1",
        "interaction_stage": _interaction_stage(question_outcomes, visible_next_question_id),
        "selected_domain": selected_domain,
        "answered_question_ids": answered_question_ids,
        "selected_option_ids": [
            str(row.get("selected_option"))
            for row in question_outcomes
            if isinstance(row, dict) and row.get("selected_option")
        ],
        "known_user_signals": _known_user_signals(question_outcomes),
        "visible_next_question_id": visible_next_question_id,
        "internal_next_question_id": internal_next_question_id,
        "invalid_retry_question_id": invalid_retry_question_id,
        "followup_reason": str(question_dialogue_graph.get("followup_reason") or ""),
        "boundary": "interaction_state_guides_followup_not_chart_fact",
    }


def _interaction_stage(question_outcomes: list[dict[str, object]], visible_next_question_id: str) -> str:
    if not question_outcomes:
        return "initial_question_selection"
    if visible_next_question_id:
        return "followup_question_selection"
    return "answer_context_ready"


def _selected_domain(question_outcomes: list[dict[str, object]]) -> str:
    for row in reversed(question_outcomes):
        if not isinstance(row, dict):
            continue
        option = str(row.get("selected_option") or "")
        if option.startswith("domain:"):
            return option.split(":", 1)[1]
        if option in {"career", "wealth", "relationship", "health", "timing", "decision"}:
            return option
        topic = str(row.get("topic") or "")
        if topic in {"career", "wealth", "relationship", "health", "timing", "decision"}:
            return topic
    return ""


def _visible_next_question_id(
    recommendations: list[dict[str, object]],
    *,
    answered_question_ids: set[str],
    preferred_question_id: str,
    invalid_retry_question_id: str = "",
) -> str:
    by_id = {
        str(row.get("question_id")): row
        for row in recommendations
        if isinstance(row, dict) and row.get("question_id")
    }
    if invalid_retry_question_id and invalid_retry_question_id in by_id:
        return invalid_retry_question_id
    preferred = by_id.get(preferred_question_id)
    if (
        isinstance(preferred, dict)
        and preferred_question_id not in answered_question_ids
        and str(preferred.get("interaction_type")) == "user_question"
    ):
        return preferred_question_id
    for row in recommendations:
        question_id = str(row.get("question_id") or "")
        if (
            question_id
            and question_id not in answered_question_ids
            and str(row.get("interaction_type")) == "user_question"
        ):
            return question_id
    for row in recommendations:
        question_id = str(row.get("question_id") or "")
        if question_id and question_id not in answered_question_ids:
            return question_id
    return preferred_question_id


def _invalid_retry_question_id(question_outcomes: list[dict[str, object]]) -> str:
    for row in reversed(question_outcomes):
        if isinstance(row, dict) and row.get("constraint_valid") is False:
            return str(row.get("question_id") or "")
    return ""


def _runtime_focus_domains(domain_readings: object) -> list[dict[str, object]]:
    if not isinstance(domain_readings, dict):
        return []
    rows = [
        (
            domain,
            payload,
            float(payload.get("priority_score", 0.0)),
        )
        for domain, payload in domain_readings.items()
        if isinstance(payload, dict)
    ]
    rows = sorted(rows, key=lambda row: (-row[2], row[0]))
    return [
        {
            "domain": str(domain),
            "summary": str(payload.get("summary", "")),
            "customer_takeaway": str(payload.get("customer_takeaway", "")),
            "action_prompt": str(payload.get("action_prompt", "")),
            "priority_score": score,
        }
        for domain, payload, score in rows[:3]
    ]


def _ten_god_energy_summary(model: dict[str, object]) -> dict[str, object]:
    scores = model.get("scores", {})
    if not isinstance(scores, dict):
        scores = {}
    rows = [
        {
            "label": str(label),
            "family": str(payload.get("family", "")) if isinstance(payload, dict) else "",
            "energy": float(payload.get("energy", 0.0)) if isinstance(payload, dict) else 0.0,
            "stability": float(payload.get("stability", 0.0)) if isinstance(payload, dict) else 0.0,
            "volatility": float(payload.get("volatility", 0.0)) if isinstance(payload, dict) else 0.0,
        }
        for label, payload in scores.items()
    ]
    return {
        "version": "v30.ten_god_energy_summary.v1",
        "status": str(model.get("status") or "pending"),
        "dominant_ten_gods": model.get("dominant_ten_gods", []),
        "high_volatility_ten_gods": model.get("high_volatility_ten_gods", []),
        "low_stability_ten_gods": model.get("low_stability_ten_gods", []),
        "top_energy": sorted(rows, key=lambda row: (-row["energy"], row["label"]))[:3],
        "boundary": "ten_god_energy_summary_is_model_signal_not_chart_fact",
    }


def _model_signal_summary(context: ChartContext, ten_god_energy_summary: dict[str, object]) -> dict[str, object]:
    top_energy = ten_god_energy_summary.get("top_energy", [])
    if not isinstance(top_energy, list):
        top_energy = []
    high_volatility = [
        str(row)
        for row in ten_god_energy_summary.get("high_volatility_ten_gods", [])
        if row
    ]
    low_stability = [
        str(row)
        for row in ten_god_energy_summary.get("low_stability_ten_gods", [])
        if row
    ]
    energy_bands = [_energy_band(row) for row in top_energy if isinstance(row, dict)]
    calibration_profile = _model_signal_calibration_profile(energy_bands)
    ranked_inputs = {
        domain: {
            "energy_bands": energy_bands,
            "stability_notes": low_stability,
            "volatility_notes": high_volatility,
            "requires_review": bool(high_volatility or low_stability),
            "boundary": "model_signal_guides_candidate_ranking_not_chart_fact",
        }
        for domain in ("strength", "structure_pattern", "useful_god")
    }
    return {
        "version": "v30.model_signal_summary.v1",
        "summary_id": f"{context.context_id}:model-signal-summary",
        "status": str(ten_god_energy_summary.get("status") or "pending"),
        "source": "ten_god_energy_model",
        "dominant_ten_gods": ten_god_energy_summary.get("dominant_ten_gods", []),
        "energy_bands": energy_bands,
        "calibration_profile": calibration_profile,
        "interface_contract": {
            "version": "v30.model_signal_interface_contract.v1",
            "consumers": [
                "structure_selector",
                "ranked_decisions",
                "answer_context",
                "training_signals",
                "admin_diagnostics",
            ],
            "allowed_fields": [
                "summary_id",
                "status",
                "dominant_ten_gods",
                "energy_bands",
                "stability_alerts",
                "volatility_alerts",
                "ranked_decision_inputs",
                "answer_guidance",
                "calibration_profile",
            ],
            "forbidden_fields": ["raw_weight", "raw_score", "energy", "stability", "volatility"],
            "boundary": "model_signal_interface_exposes_bands_and_alerts_not_raw_scores_or_chart_facts",
        },
        "stability_alerts": low_stability,
        "volatility_alerts": high_volatility,
        "ranked_decision_inputs": ranked_inputs,
        "answer_guidance": [
            "Use ten-god energy as a bounded model signal.",
            "Describe volatility and low stability as review conditions, not fixed outcomes.",
        ],
        "raw_score_visible": False,
        "boundary": "model_signal_summary_is_bounded_signal_not_chart_fact_or_customer_raw_score",
    }


def _m3_completion_summary(
    *,
    feature_evidence: list[FeatureEvidence],
    knowledge_rule_portrait_signals: list[KnowledgeRulePortraitSignal],
    structure_path_scores: dict[str, float],
    structure_graph_nodes: list[dict[str, object]],
    mainline_supporting: list[str],
    krp_library_summary: dict[str, object],
    model_signal_summary: dict[str, object],
    ranked_decisions: dict[str, dict[str, Any]],
    practical_reading_context: dict[str, Any],
) -> dict[str, object]:
    source_family_ids = [
        str(row) for row in krp_library_summary.get("source_family_ids", [])
        if str(row)
    ] if isinstance(krp_library_summary.get("source_family_ids", []), list) else []
    reference_asset_ids = [
        str(row) for row in krp_library_summary.get("reference_asset_ids", [])
        if str(row)
    ] if isinstance(krp_library_summary.get("reference_asset_ids", []), list) else []
    krp_domains = sorted(
        str(domain)
        for domain in (
            krp_library_summary.get("by_domain", {}).keys()
            if isinstance(krp_library_summary.get("by_domain", {}), dict) else []
        )
        if str(domain)
    )
    rule_evidence = [row for row in feature_evidence if row.domain == "rule"]
    rule_states = sorted({
        support.removeprefix("rule_decision_state:")
        for row in rule_evidence
        for support in row.supports
        if support.startswith("rule_decision_state:")
    })
    signal_types = sorted({str(row.signal_type) for row in knowledge_rule_portrait_signals})
    mechanism_nodes = [
        node for node in structure_graph_nodes
        if isinstance(node, dict) and node.get("kind") == "mechanism_path"
    ]
    dynamic_nodes = [
        node for node in structure_graph_nodes
        if isinstance(node, dict) and node.get("kind") == "dynamic_path"
    ]
    m4_supported = (
        model_signal_summary.get("version") == "v30.model_signal_summary.v1"
        and float(structure_path_scores.get("model_signal_summary_ready", 0.0) or 0.0) >= 1.0
        and float(structure_path_scores.get("model_signal_structure_path_adjustment", 0.0) or 0.0) >= 0.0
    )
    m5_basis_rows = [
        payload.get("scoring_basis", {})
        for payload in ranked_decisions.values()
        if isinstance(payload, dict)
    ]
    m5_supported_count = sum(
        1 for basis in m5_basis_rows
        if isinstance(basis, dict)
        and float(basis.get("dynamic_path_count", 0.0) or 0.0) > 0.0
        and str(basis.get("boundary") or "") == "ranked_decision_scoring_basis_uses_chart_facts_and_model_signals_not_fixed_verdict"
    )
    domain_readings = (
        practical_reading_context.get("domain_readings", {})
        if isinstance(practical_reading_context, dict) else {}
    )
    domain_readings = domain_readings if isinstance(domain_readings, dict) else {}
    m6_supported_count = sum(
        1 for payload in domain_readings.values()
        if isinstance(payload, dict)
        and isinstance(payload.get("module_trace", {}), dict)
        and payload["module_trace"].get("uses_m3_structure_evidence") is True
        and payload["module_trace"].get("chart_fact_mutation_allowed") is False
    )
    required_support = {
        "source_registry": len(set(source_family_ids)) >= 6,
        "v20_reference_registry": len(set(reference_asset_ids)) >= 2,
        "krp_domain_coverage": len(set(krp_domains)) >= 10,
        "knowledge_rule_portrait_signals": {"knowledge", "rule", "portrait"} <= set(signal_types),
        "rule_evidence_counterevidence": bool(rule_evidence) and bool(rule_states),
        "mechanism_paths": len(mechanism_nodes) >= 4,
        "dynamic_graph_paths": len(dynamic_nodes) > 0 and float(structure_path_scores.get("dynamic_path_count", 0.0) or 0.0) > 0.0,
        "mainline_arbitration": any(str(row).startswith("rule_signal:") for row in mainline_supporting)
        and "strength_pattern_candidate_review" in mainline_supporting,
        "m4_model_signal_support": m4_supported,
        "m5_ranked_decision_support": m5_supported_count >= 2,
        "m6_practical_reading_support": m6_supported_count >= 5,
    }
    ready = all(required_support.values())
    return {
        "version": "v30.m3_completion_summary.v1",
        "status": "ready" if ready else "needs_review",
        "source_family_count": len(set(source_family_ids)),
        "reference_asset_count": len(set(reference_asset_ids)),
        "krp_domain_count": len(set(krp_domains)),
        "signal_types": signal_types,
        "rule_evidence_count": len(rule_evidence),
        "rule_states": rule_states,
        "mechanism_path_count": len(mechanism_nodes),
        "dynamic_path_count": int(float(structure_path_scores.get("dynamic_path_count", 0.0) or 0.0)),
        "mainline_support_count": len(mainline_supporting),
        "m4_model_signal_support": m4_supported,
        "m5_ranked_decision_support_count": m5_supported_count,
        "m6_practical_reading_support_count": m6_supported_count,
        "required_support": required_support,
        "completion_coverage": round(sum(1 for value in required_support.values() if value) / len(required_support), 3),
        "acts_as_conclusion_engine": False,
        "chart_fact_mutation_allowed": False,
        "boundary": "m3_completion_summary_validates_evidence_spine_supports_m4_m5_m6_not_final_verdicts",
    }


def _model_signal_calibration_profile(energy_bands: list[dict[str, object]]) -> dict[str, object]:
    energy_counts = _band_counts(energy_bands, "energy_band")
    stability_counts = _band_counts(energy_bands, "stability_band")
    volatility_counts = _band_counts(energy_bands, "volatility_band")
    flags = _model_signal_calibration_flags(
        energy_counts=energy_counts,
        stability_counts=stability_counts,
        volatility_counts=volatility_counts,
    )
    return {
        "version": "v30.model_signal_calibration_profile.v1",
        "family_coverage": sorted({str(row.get("family") or "") for row in energy_bands if row.get("family")}),
        "family_coverage_count": len({str(row.get("family") or "") for row in energy_bands if row.get("family")}),
        "energy_band_counts": energy_counts,
        "stability_band_counts": stability_counts,
        "volatility_band_counts": volatility_counts,
        "calibration_flags": flags,
        "ranked_decision_adjustments": _model_signal_ranked_decision_adjustments(flags),
        "boundary": "model_signal_calibration_profile_trains_policy_not_chart_facts",
    }


def _model_signal_calibration_flags(
    *,
    energy_counts: dict[str, int],
    stability_counts: dict[str, int],
    volatility_counts: dict[str, int],
) -> list[str]:
    flags: list[str] = []
    if energy_counts.get("high", 0) >= 2:
        flags.append("multi_high_energy_review")
    if volatility_counts.get("high", 0) >= 1:
        flags.append("volatility_review_required")
    if stability_counts.get("low", 0) >= 1:
        flags.append("low_stability_review_required")
    if energy_counts.get("high", 0) >= 1 and volatility_counts.get("high", 0) >= 1:
        flags.append("dominant_signal_needs_timing_boundary")
    if not flags:
        flags.append("model_signal_balanced_review")
    return flags


def _model_signal_ranked_decision_adjustments(flags: list[str]) -> dict[str, object]:
    return {
        "version": "v30.model_signal_ranked_decision_adjustments.v1",
        "applies_to": ["strength", "structure_pattern", "useful_god"],
        "review_flags": flags,
        "score_bias": {
            "strength_review_penalty": 0.03 if "volatility_review_required" in flags else 0.0,
            "dynamic_structure_bonus": 0.05 if "dominant_signal_needs_timing_boundary" in flags else 0.0,
            "useful_god_non_unique_bonus": 0.04 if "multi_high_energy_review" in flags else 0.0,
        },
        "boundary": "model_signal_adjustments_tune_ranked_candidates_not_chart_facts",
    }


def _band_counts(rows: list[dict[str, object]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "")
        if not value:
            continue
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _energy_band(row: dict[str, object]) -> dict[str, object]:
    label = str(row.get("label") or "")
    return {
        "label": label,
        "family": str(row.get("family") or ""),
        "energy_band": _band(float(row.get("energy", 0.0))),
        "stability_band": _band(float(row.get("stability", 0.0))),
        "volatility_band": _band(float(row.get("volatility", 0.0))),
    }


def _band(value: float) -> str:
    if value >= 0.72:
        return "high"
    if value >= 0.42:
        return "medium"
    if value > 0:
        return "low"
    return "none"


def _nested_policy_dict(payload: object, section: str, key: str, *, default: object = None) -> object:
    if not isinstance(payload, dict):
        return default
    section_payload = payload.get(section, {})
    if not isinstance(section_payload, dict):
        return default
    return section_payload.get(key, default)


def _list_policy_effect(runtime: CoreRuntimeResult, key: str) -> list[dict[str, object]]:
    value = runtime.question_plan.policy_effect.get(key, [])
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, dict)]


def _question_outcomes(runtime: CoreRuntimeResult) -> list[dict[str, object]]:
    value = runtime.question_plan.session_state.get("question_outcomes", [])
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []


def _known_user_signals(outcomes: list[dict[str, object]]) -> dict[str, object]:
    selected_options = [str(row.get("selected_option")) for row in outcomes if row.get("selected_option")]
    topics = [str(row.get("topic")) for row in outcomes if row.get("topic")]
    return {
        "version": "v30.known_user_signals.v1",
        "answered_question_count": len(outcomes),
        "selected_options": selected_options,
        "topics": sorted(set(topics)),
        "boundary": "known_user_signals_condition_dialogue_not_chart_fact",
    }


def _question_outcome_status(value: object) -> str:
    status = str(value or "answered").strip().lower()
    return status if status in {"answered", "skipped", "unclear", "confirmed", "denied"} else "answered"


def _bounded_float(value: object, *, default: float) -> float:
    try:
        return round(max(0.0, min(1.0, float(value))), 3)
    except (TypeError, ValueError):
        return default


def _str_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(row) for row in value if row is not None and str(row)]
    if value is None:
        return []
    return [str(value)]


def _topic_from_anchor(anchor: BaziQuestionAnchor) -> str:
    if anchor.intent_id == "discover_hidden_factor_amplifier":
        return "hidden_factor"
    if anchor.intent_id == "review_useful_god_candidate_paths":
        return "useful_god"
    if anchor.missing_requirements:
        return "time_context"
    return "mainline"


def _stage_from_anchor(anchor: BaziQuestionAnchor) -> str:
    if anchor.intent_id == "discover_hidden_factor_amplifier":
        return "dialogue_discovery"
    if anchor.missing_requirements:
        return "context_completion"
    if anchor.intent_id == "review_useful_god_candidate_paths":
        return "candidate_review"
    return "mainline_review"


def _supplemental_feedback_evidence(
    *,
    context_id: str,
    hidden_factor_user_calibrated: bool,
    useful_god_path_resolved: bool,
    branch_single_factor_confirmed: bool,
) -> list[FeatureEvidence]:
    rows: list[FeatureEvidence] = []
    if hidden_factor_user_calibrated:
        rows.append(
            FeatureEvidence(
                evidence_id=f"{context_id}:feedback:hidden_factor_user_calibrated",
                domain="feedback",
                kind="hidden_factor_calibration",
                label="hidden_factor_user_calibrated:true",
                source=context_id,
                confidence=0.92,
                supports=["hidden_factor_user_calibrated", "special_event_confirmed"],
                boundary="feedback_evidence_counters_dialogue_boundary_not_chart_fact",
            )
        )
    if useful_god_path_resolved:
        rows.append(
            FeatureEvidence(
                evidence_id=f"{context_id}:feedback:useful_god_path_resolved",
                domain="feedback",
                kind="useful_god_resolution",
                label="useful_god_path_resolved:true",
                source=context_id,
                confidence=0.9,
                supports=["fixed_useful_god_verdict", "useful_god_path_resolved"],
                boundary="feedback_evidence_counters_candidate_gate_not_chart_fact",
            )
        )
    if branch_single_factor_confirmed:
        rows.append(
            FeatureEvidence(
                evidence_id=f"{context_id}:feedback:branch_single_factor_confirmed",
                domain="feedback",
                kind="branch_relation_single_factor",
                label="branch_single_factor_confirmed:true",
                source=context_id,
                confidence=0.86,
                supports=["single_factor_reading"],
                boundary="feedback_evidence_counters_dynamic_review_gate_not_chart_fact",
            )
        )
    return rows


def _select_answer_anchor(
    question_anchors: list[BaziQuestionAnchor],
    recommendations: list[dict[str, object]],
) -> BaziQuestionAnchor | None:
    if not question_anchors:
        return None
    anchor_by_question = {
        getattr(anchor, "question_id"): anchor
        for anchor in question_anchors
    }
    for recommendation in recommendations:
        if str(recommendation.get("interaction_type") or "") != "user_question":
            continue
        question_id = str(recommendation.get("question_id") or "")
        if question_id in anchor_by_question:
            return anchor_by_question[question_id]
    for recommendation in recommendations:
        question_id = str(recommendation.get("question_id") or "")
        if question_id in anchor_by_question:
            return anchor_by_question[question_id]
    return question_anchors[0]
