from __future__ import annotations

from v30.contracts import ClientPresentationModel, CoreRuntimeResult
from v30.brain.text_options import build_response_option_set_for_question, role_visible_option_sets
from v30.expression import render_question_label, summarize_question_labels
from v30.presentation.client_profiles import client_profile
from v30.presentation.i18n import build_locale_terminology_contract, label, term_label
from v30.presentation.product_projection import (
    build_decision_workbench_product_surface,
    output_runtime_contract,
)
from v30.presentation.surface_orchestrator import (
    build_surface_orchestration,
    output_pipeline_contract,
    surface_orchestration_policy,
)
from v30.portrait import build_macro_portrait_projection_views, summarize_macro_portrait_projection_views


USER_VISIBLE_ROLES = {"guest", "user"}
DIAGNOSTIC_ROLES = {"practitioner", "admin", "analyst", "lab"}


def build_presentation_model(
    runtime: CoreRuntimeResult,
    role_key: str = "user",
    locale: str = "zh",
    client: str = "web",
) -> ClientPresentationModel:
    role_key = _resolve_role(role_key)
    profile = client_profile(client)
    resolved_client = profile.client
    visible_anchors = [
        anchor for anchor in runtime.question_anchors
        if role_key not in USER_VISIBLE_ROLES or anchor.anchor_status == "bound"
    ]
    recommendations = {
        str(row.get("question_id")): row
        for row in runtime.question_plan.recommended_questions
    }
    recommendation_order = {
        str(row.get("question_id")): index
        for index, row in enumerate(runtime.question_plan.recommended_questions)
    }
    visible_anchors = sorted(
        visible_anchors,
        key=lambda anchor: (
            int(recommendation_order.get(anchor.question_id, 9999)),
            anchor.question_id,
        ),
    )
    if role_key in USER_VISIBLE_ROLES:
        interaction_state = runtime.question_plan.policy_effect.get("interaction_state", {})
        invalid_retry_question_id = (
            str(interaction_state.get("invalid_retry_question_id") or "")
            if isinstance(interaction_state, dict)
            else ""
        )
        answered_question_ids = (
            {
                str(question_id)
                for question_id in interaction_state.get("answered_question_ids", [])
                if question_id
            }
            if isinstance(interaction_state, dict)
            else set()
        )
        product_anchors = [
            anchor for anchor in visible_anchors
            if (
                recommendations.get(anchor.question_id, {}).get("interaction_type") == "user_question"
                and anchor.question_id not in answered_question_ids
            )
            or (invalid_retry_question_id and anchor.question_id == invalid_retry_question_id)
        ]
        if product_anchors:
            visible_anchors = sorted(
                product_anchors,
                key=lambda anchor: _customer_anchor_priority(
                    anchor,
                    invalid_retry_question_id=invalid_retry_question_id,
                ),
            )
        else:
            visible_anchors = [
                anchor for anchor in visible_anchors
                if recommendations.get(anchor.question_id, {}).get("interaction_type") != "calibration_probe"
            ]
    visible_anchors = visible_anchors[: profile.max_questions]
    rendered_labels = [
        render_question_label(
            anchor,
            recommendations.get(anchor.question_id, {}),
            role_key=role_key,
            locale=locale,
            client=resolved_client,
        )
        for anchor in visible_anchors
    ]
    labels_by_question = {row.question_id: row for row in rendered_labels}
    rendered_label_summary = summarize_question_labels(rendered_labels)
    show_reasons = profile.show_reasons
    show_diagnostics = role_key in DIAGNOSTIC_ROLES
    portrait_views = _portrait_views(runtime, role_key=role_key, client=resolved_client)
    portrait_view_summary = summarize_macro_portrait_projection_views(portrait_views)
    question_rows = [
        {
            "question_id": anchor.question_id,
            "anchor_status": anchor.anchor_status,
            "label": labels_by_question[anchor.question_id].label,
            "label_source": labels_by_question[anchor.question_id].source,
            "label_boundary": labels_by_question[anchor.question_id].boundary,
            "score": recommendations.get(anchor.question_id, {}).get("score"),
            "stage": recommendations.get(anchor.question_id, {}).get("stage"),
            "stage_label": label(locale, str(recommendations.get(anchor.question_id, {}).get("stage", ""))),
            "topic": recommendations.get(anchor.question_id, {}).get("topic"),
            "topic_label": label(locale, str(recommendations.get(anchor.question_id, {}).get("topic", ""))),
            "question_value": recommendations.get(anchor.question_id, {}).get("question_value", ""),
            "interaction_type": recommendations.get(anchor.question_id, {}).get("interaction_type", ""),
            "answer_mode": recommendations.get(anchor.question_id, {}).get("answer_mode", ""),
            "expected_information_gain": recommendations.get(anchor.question_id, {}).get("expected_information_gain", {}),
            "options": recommendations.get(anchor.question_id, {}).get("options", []),
            "answer_constraints": recommendations.get(anchor.question_id, {}).get("answer_constraints", {}),
            "quality_contract": recommendations.get(anchor.question_id, {}).get("quality_contract", {}),
            "semantic_projection": recommendations.get(anchor.question_id, {}).get("semantic_projection", {}),
            "reasons": recommendations.get(anchor.question_id, {}).get("reasons", []) if show_reasons else [],
        }
        for anchor in visible_anchors
    ]
    if role_key in USER_VISIBLE_ROLES:
        question_rows = [_customer_question_row(row) for row in question_rows]
    reading_surface = _reading_surface(
        runtime,
        questions=question_rows,
        role_key=role_key,
        locale=locale,
        client=resolved_client,
    )
    diagnostics = _diagnostics(
        runtime,
        portrait_views,
        portrait_view_summary,
        rendered_labels,
        rendered_label_summary,
    ) if show_diagnostics else {}
    answer_panel = runtime.answer_result.model_dump(mode="json") if runtime.answer_result else None
    if answer_panel is not None:
        answer_panel = {
            **answer_panel,
            "user_submitted": _answer_panel_user_submitted(runtime, answer_panel),
            "question_stage_id": _answer_panel_question_stage_id(runtime, answer_panel),
            "question_label": _answer_panel_question_label(
                runtime,
                answer_panel,
                role_key=role_key,
                locale=locale,
                client=resolved_client,
            ),
        }
    if role_key in USER_VISIBLE_ROLES and answer_panel is not None:
        answer_panel = _customer_answer_panel(answer_panel, reading_surface)
    elif role_key in DIAGNOSTIC_ROLES and answer_panel is not None:
        answer_panel = _diagnostic_answer_panel(answer_panel, reading_surface, role_key=role_key)
    projection_contract = _projection_contract(
        role_key=role_key,
        client=resolved_client,
        reading_surface=reading_surface,
        questions=question_rows,
        answer_panel=answer_panel,
        diagnostics=diagnostics,
    )
    return ClientPresentationModel(
        reading_id=runtime.reading_id,
        role_key=role_key,
        locale=locale,
        client=resolved_client,
        layout={
            "version": "v30.presentation.v1",
            "client": resolved_client,
            "density": profile.density,
            "locale": locale,
            "client_profile": profile.model_dump(mode="json"),
            "role_profile": _role_profile(role_key),
            "locale_terminology_contract": build_locale_terminology_contract(locale),
            "portrait_projection_view_summary": portrait_view_summary,
            "rendered_question_label_summary": rendered_label_summary,
        },
        header={"title": label(locale, "app_title"), "subtitle": runtime.mainline_state.title},
        reading_surface=reading_surface,
        chart_summary={
            "day_master": runtime.chart_context.day_master,
            "day_master_element": runtime.chart_context.day_master_element,
            "chart_build_source": runtime.chart_context.input_pillars.get("chart_build_source", {}),
            "six_pillar_context": runtime.chart_context.time_layers.get("six_pillar_context", {}) if show_diagnostics else {},
            "boundary": "chart_summary_is_customer_safe_projection_not_full_bazi_context",
        },
        mainline_card={
            "title": runtime.mainline_state.title,
            "state": runtime.mainline_state.state,
            "why_selected": runtime.mainline_state.why_selected if show_diagnostics else "",
            "boundary": "mainline_card_is_summary_projection_full_reason_in_diagnostics",
        },
        structure_card={
            "label": runtime.structure_state.semantic_label if show_diagnostics else "bazi_context_available",
            "state": runtime.structure_state.state if show_diagnostics else "internal_context",
            "confidence": runtime.structure_state.confidence if show_diagnostics else None,
            "dynamic_path_count": runtime.structure_state.path_scores.get("dynamic_path_count", 0.0) if show_diagnostics else None,
            "top_dynamic_path_score": runtime.structure_state.path_scores.get("top_dynamic_path_score", 0.0) if show_diagnostics else None,
            "boundary": "structure_card_is_internal_bazi_context_hidden_for_customer_roles",
        },
        questions=question_rows,
        answer_panel=answer_panel,
        actions=[
            {"type": action, "label": label(locale, action), "method": _action_method(action)}
            for action in _visible_actions(profile.actions, role_key)
        ],
        diagnostics=diagnostics,
        projection_contract=projection_contract,
    )


def _action_method(action: str) -> str:
    if action == "run_training":
        return "POST"
    if action == "open_trace":
        return "GET"
    return "POST"


def _visible_actions(actions: list[str], role_key: str) -> list[str]:
    if role_key in USER_VISIBLE_ROLES:
        return [action for action in actions if action == "submit_answer"]
    return actions


def _customer_question_row(row: dict[str, object]) -> dict[str, object]:
    payload = dict(row)
    gain = payload.get("expected_information_gain", {})
    if isinstance(gain, dict):
        payload["expected_information_gain"] = {
            key: value
            for key, value in gain.items()
            if key in {"score", "primary_gain", "reduces", "practical_focus_domains"}
        }
    contract = payload.get("quality_contract", {})
    if isinstance(contract, dict):
        payload["quality_contract"] = {
            key: value
            for key, value in contract.items()
            if key in {"version", "purpose", "optimizes_for", "reading_focus"}
        }
    semantic = payload.get("semantic_projection", {})
    if isinstance(semantic, dict):
        payload["semantic_projection"] = _customer_question_semantic_projection(semantic)
    payload["reasons"] = []
    return payload


def _customer_anchor_priority(anchor, *, invalid_retry_question_id: str = "") -> tuple[int, str]:
    question_id = getattr(anchor, "question_id", "")
    if invalid_retry_question_id and question_id == invalid_retry_question_id:
        return (-1, question_id)
    priority = {
        "q_v30_user_career_direction": 0,
        "q_v30_user_wealth_tendency": 1,
        "q_v30_user_relationship_pattern": 2,
        "q_v30_user_timing_pressure": 3,
        "q_v30_user_decision_blindspot": 4,
    }
    return (priority.get(question_id, 50), question_id)


def _customer_answer_panel(answer_panel: dict[str, object], reading_surface: dict[str, object]) -> dict[str, object]:
    payload = dict(answer_panel)
    question_id = str(payload.get("question_id") or "")
    payload["answer_id"] = f"{question_id}:answer" if question_id else "answer"
    payload["text"] = _customer_answer_text(
        str(payload.get("text") or ""),
        source=str(payload.get("source") or ""),
        llm_metadata=payload.get("llm_metadata") if isinstance(payload.get("llm_metadata"), dict) else {},
    )
    payload["visual_hint"] = _answer_visual_hint(payload, reading_surface)
    evidence_ids = payload.get("evidence_ids", [])
    if isinstance(evidence_ids, list):
        payload["evidence_count"] = len(evidence_ids)
    payload["evidence_ids"] = []
    llm_metadata = payload.get("llm_metadata", {})
    if isinstance(llm_metadata, dict):
        llm_metadata = _ensure_product_context_summary(llm_metadata, reading_surface)
        payload["llm_metadata"] = {
            key: value
            for key, value in llm_metadata.items()
            if key in {"status", "fallback_reason", "executed", "context_pack_summary", "boundary"}
        }
    return payload


def _answer_panel_user_submitted(runtime: CoreRuntimeResult, answer_panel: dict[str, object]) -> bool:
    question_id = str(answer_panel.get("question_id") or "")
    if not question_id:
        return False
    outcomes = runtime.question_plan.session_state.get("question_outcomes", [])
    if not isinstance(outcomes, list):
        return False
    for row in outcomes:
        if not isinstance(row, dict):
            continue
        if str(row.get("question_id") or "") != question_id:
            continue
        return str(row.get("outcome_status") or "") in {"answered", "skipped", "invalid"}
    return False


def _answer_panel_question_stage_id(runtime: CoreRuntimeResult, answer_panel: dict[str, object]) -> str:
    question_id = str(answer_panel.get("question_id") or "")
    if not question_id:
        return ""
    outcomes = runtime.question_plan.session_state.get("question_outcomes", [])
    if isinstance(outcomes, list):
        for row in outcomes:
            if not isinstance(row, dict) or str(row.get("question_id") or "") != question_id:
                continue
            stage_id = _dialogue_stage_id_from_topic_stage(
                topic=str(row.get("topic") or ""),
                stage=str(row.get("stage") or ""),
            )
            if stage_id:
                return stage_id
    central = runtime.question_plan.policy_effect.get("central_reading_state", {})
    central = central if isinstance(central, dict) else {}
    recommended = runtime.question_plan.recommended_questions
    for row in recommended:
        if not isinstance(row, dict) or str(row.get("question_id") or "") != question_id:
            continue
        stage_id = _dialogue_turn_stage_id(central, _surface_question_projection(row))
        return stage_id
    return ""


def _answer_panel_question_label(
    runtime: CoreRuntimeResult,
    answer_panel: dict[str, object],
    *,
    role_key: str,
    locale: str,
    client: str,
) -> str:
    question_id = str(answer_panel.get("question_id") or "")
    if not question_id:
        return ""
    recommendations = {
        str(row.get("question_id")): row
        for row in runtime.question_plan.recommended_questions
        if isinstance(row, dict)
    }
    anchor = next((row for row in runtime.question_anchors if row.question_id == question_id), None)
    if anchor is not None:
        return render_question_label(
            anchor,
            recommendations.get(question_id, {}),
            role_key=role_key,
            locale=locale,
            client=client,
        ).label
    recommendation = recommendations.get(question_id, {})
    if isinstance(recommendation, dict):
        return str(
            recommendation.get("label")
            or recommendation.get("question")
            or recommendation.get("prompt")
            or recommendation.get("title")
            or ""
        )
    return ""


def _customer_answer_text(
    text: str,
    *,
    source: str = "",
    llm_metadata: dict[str, object] | None = None,
) -> str:
    metadata = llm_metadata if isinstance(llm_metadata, dict) else {}
    status = str(metadata.get("status") or "")
    if status in {"deferred", "loading"} or source in {"rule_bound_llm_deferred", "llm_pending"}:
        return "本次回答正在等待大模型推演，完成后会只展示结论和建议。"
    lines = [line.strip() for line in text.splitlines()]
    kept: list[str] = []
    blocked_prefixes = ("基础判断：", "路径复核：", "特征画像：", "边界：", "诊断口径：")
    blocked_contains = (
        "llm_bazi_answer_draft",
        "LLM accepted",
        "LLM fallback",
        "rule_bound_fallback",
        "rule_bound_llm_deferred",
        "policy_effect",
        "证据数=",
        "当前回答已绑定",
        "结构化明细见诊断字段",
    )
    for line in lines:
        if not line:
            continue
        if line.startswith("诊断复核："):
            line = line.removeprefix("诊断复核：").strip()
        if "该画像维度由规则" in line:
            line = line.split("该画像维度由规则", 1)[0].strip()
        if line.startswith(blocked_prefixes):
            continue
        if any(token in line for token in blocked_contains):
            continue
        kept.append(line)
    cleaned = "\n".join(kept).strip()
    if cleaned:
        return cleaned
    if any(token in text for token in blocked_contains) or any(text.strip().startswith(prefix) for prefix in blocked_prefixes):
        return "本次回答没有形成可展示的用户结论，请重新推演这一问。"
    return text.strip()


def _ensure_product_context_summary(
    llm_metadata: dict[str, object],
    reading_surface: dict[str, object],
) -> dict[str, object]:
    summary = llm_metadata.get("context_pack_summary", {})
    if isinstance(summary, dict) and summary.get("layers"):
        return llm_metadata
    payload = dict(llm_metadata)
    payload["context_pack_summary"] = _presentation_product_context_summary(
        reading_surface,
        task_type=str(payload.get("task_type") or ""),
        role_key=str(payload.get("role_key") or reading_surface.get("role_key") or "user"),
    )
    return payload


def _presentation_product_context_summary(
    reading_surface: dict[str, object],
    *,
    task_type: str,
    role_key: str,
) -> dict[str, object]:
    surface = reading_surface if isinstance(reading_surface, dict) else {}
    layer_specs = (
        ("basic_assertions", surface.get("basic_assertions")),
        ("domain_card", surface.get("domain_cards")),
        ("bazi_features", surface.get("bazi_features")),
        ("bazi_portraits", surface.get("bazi_portraits")),
        ("bazi_paths", surface.get("bazi_paths")),
        ("time_context", surface.get("time_context")),
        ("role_contract", surface.get("role_contract")),
    )
    layers = [name for name, value in layer_specs if _surface_layer_present(value)]
    return {
        "version": "v30.bazi_llm_product_context_pack_summary.v1",
        "task_type": task_type,
        "role_key": role_key,
        "layers": layers,
        "required_layers": [name for name, _value in layer_specs],
        "missing_layers": [name for name, _value in layer_specs if name not in layers],
        "layer_counts": {
            name: len(value) if isinstance(value, list) else 1 if isinstance(value, dict) and value else 0
            for name, value in layer_specs
        },
        "raw_runtime_payload_included": False,
        "chart_fact_mutation_allowed": False,
        "boundary": "presentation_llm_context_summary_tracks_product_surface_layers_without_raw_runtime",
    }


def _surface_layer_present(value: object) -> bool:
    if isinstance(value, list):
        return bool(value)
    if isinstance(value, dict):
        return bool(value)
    return bool(value)


def _diagnostic_answer_panel(
    answer_panel: dict[str, object],
    reading_surface: dict[str, object],
    *,
    role_key: str,
) -> dict[str, object]:
    payload = dict(answer_panel)
    original_text = _customer_answer_text(str(payload.get("text") or ""))
    evidence_ids = payload.get("evidence_ids", [])
    evidence_ids = evidence_ids if isinstance(evidence_ids, list) else []
    role_label = "命理师复核" if role_key == "practitioner" else "诊断复核"
    diagnostic_lines = [
        _diagnostic_basis_line(reading_surface),
        _diagnostic_path_line(reading_surface),
        _diagnostic_feature_line(reading_surface),
        _diagnostic_boundary_line(reading_surface, evidence_count=len(evidence_ids)),
    ]
    payload["original_text"] = original_text
    payload["text"] = _diagnostic_role_answer_text(
        original_text,
        reading_surface,
        role_key=role_key,
    )
    payload["role_adaptation"] = {
        "version": "v30.role_adapted_answer_projection.v1",
        "role_key": role_key,
        "label": role_label,
        "density": "diagnostics_separate_from_answer_text",
        "diagnostic_lines": [line for line in diagnostic_lines if line],
        "uses_basic_assertions": bool(reading_surface.get("basic_assertions")),
        "uses_bazi_paths": bool(reading_surface.get("bazi_paths")),
        "uses_features_and_portraits": bool(reading_surface.get("bazi_features")) or bool(reading_surface.get("bazi_portraits")),
        "chart_fact_mutation_allowed": False,
        "boundary": "role_adaptation_keeps_answer_text_customer_facing_and_moves_diagnostics_to_structured_fields",
    }
    return payload


def _diagnostic_role_answer_text(
    customer_text: str,
    reading_surface: dict[str, object],
    *,
    role_key: str,
) -> str:
    assertions = reading_surface.get("basic_assertions", [])
    paths = reading_surface.get("bazi_paths", [])
    features = reading_surface.get("bazi_features", [])
    assertion_count = len(assertions) if isinstance(assertions, list) else 0
    path_count = len(paths) if isinstance(paths, list) else 0
    feature_count = len(features) if isinstance(features, list) else 0
    if role_key == "practitioner":
        prefix = (
            f"命理师复核口径：按{assertion_count}条命局判断、{path_count}条动态路径和"
            f"{feature_count}条特征证据复核，同一结论需回到强弱、结构、时运承接三层互证。"
        )
    else:
        prefix = (
            f"诊断口径：当前回答已绑定{assertion_count}条命局判断、{path_count}条动态路径和"
            f"{feature_count}条特征证据；结构化明细见诊断字段。"
        )
    return "\n".join(part for part in (prefix, customer_text.strip()) if part).strip()


def _diagnostic_basis_line(reading_surface: dict[str, object]) -> str:
    assertions = reading_surface.get("basic_assertions", [])
    if not isinstance(assertions, list) or not assertions:
        return ""
    picked = [
        str(row.get("assertion") or "")
        for row in assertions
        if isinstance(row, dict) and row.get("kind") in {"strength_assertion", "structure_assertion", "useful_god_direction"}
    ][:3]
    return f"基础判断：{'；'.join(item for item in picked if item)}" if picked else ""


def _diagnostic_path_line(reading_surface: dict[str, object]) -> str:
    paths = reading_surface.get("bazi_paths", [])
    if not isinstance(paths, list) or not paths:
        return ""
    picked = [
        f"{row.get('path_label')}({','.join(str(item) for item in row.get('domain_impact', [])[:3])})"
        for row in paths[:3]
        if isinstance(row, dict)
    ]
    return f"路径复核：{'；'.join(item for item in picked if item)}" if picked else ""


def _diagnostic_feature_line(reading_surface: dict[str, object]) -> str:
    features = reading_surface.get("bazi_features", [])
    portraits = reading_surface.get("bazi_portraits", [])
    feature = features[0] if isinstance(features, list) and features and isinstance(features[0], dict) else {}
    portrait = portraits[0] if isinstance(portraits, list) and portraits and isinstance(portraits[0], dict) else {}
    parts = []
    if feature:
        parts.append(f"特征={feature.get('label')}: {feature.get('statement')}")
    if portrait:
        parts.append(f"画像={portrait.get('label')}: {portrait.get('statement')}")
    return f"特征画像：{'；'.join(parts)}" if parts else ""


def _diagnostic_boundary_line(reading_surface: dict[str, object], *, evidence_count: int) -> str:
    paths = reading_surface.get("bazi_paths", [])
    boundary = ""
    if isinstance(paths, list) and paths and isinstance(paths[0], dict):
        boundary = str(paths[0].get("uncertainty_boundary") or "")
    evidence = f"证据数={evidence_count}" if evidence_count else "证据链见诊断面板"
    if boundary:
        return f"边界：{boundary}；{evidence}；不改四柱、大运、流年事实。"
    return f"边界：{evidence}；不改四柱、大运、流年事实。"


def _projection_contract(
    *,
    role_key: str,
    client: str,
    reading_surface: dict[str, object],
    questions: list[dict[str, object]],
    answer_panel: dict[str, object] | None,
    diagnostics: dict[str, object],
) -> dict[str, object]:
    leak_scan = _projection_leak_scan(
        role_key=role_key,
        reading_surface=reading_surface,
        questions=questions,
        answer_panel=answer_panel,
        diagnostics=diagnostics,
    )
    customer_surface_order = [
        "core_bazi_reading",
        "domain_cards",
        "time_context",
        "calibration_surface",
        "conversation_surface",
        "thinking_surface",
    ]
    hidden_fields = _hidden_projection_tokens()
    additive_fields = [
        "reading_surface",
        "core_bazi_reading",
        "domain_cards",
        "questions",
        "answer_panel",
        "surface_orchestrator",
        "calibration_surface",
        "conversation_surface",
        "thinking_surface",
        "legacy_dialogue_surface",
        "next_question_id",
        "visible_next_question_id",
        "internal_next_question_id",
        "actor_context",
        "llm_runtime_status",
        "actions",
        "diagnostics",
        "projection_contract",
    ]
    surface_contract = _customer_surface_contract(reading_surface, customer_surface_order)
    return {
        "version": "v30.api_projection_contract.v1",
        "role_key": role_key,
        "client": client,
        "contract_scope": "client_presentation_model",
        "required_top_level_fields": [
            "reading_surface",
            "questions",
            "answer_panel",
            "actions",
            "diagnostics",
            "projection_contract",
        ],
        "required_reading_surface_fields": [
            "core_bazi_reading",
            "domain_cards",
            "time_context",
            "surface_orchestrator",
            "calibration_surface",
            "conversation_surface",
            "thinking_surface",
            "legacy_dialogue_surface",
        ],
        "customer_surface_order": customer_surface_order,
        "surface_orchestration_policy": surface_orchestration_policy(),
        "surface_output_pipeline_contract": output_pipeline_contract(),
        "output_runtime_product_projection_contract": output_runtime_contract(),
        "core_first_projection": {
            "version": "v30.core_first_projection.v1",
            "required_surface_prefix": customer_surface_order[:2],
            "calculation_before_questions": True,
            "question_loop_position": "after_core_calculation_surface",
            "calibration_probe_position": "after_customer_visible_calculation",
            "boundary": "core_bazi_calculation_is_presented_before_questions_or_feedback_loops",
        },
        "customer_surface_contract": surface_contract,
        "dialogue_entry_policy": {
            "version": "v30.dialogue_entry_policy.v1",
            "customer_primary_entry": "reading_surface.conversation_surface",
            "legacy_customer_primary_entry": "reading_surface.current_dialogue_turn",
            "stage_probe_entry_v2": "reading_surface.calibration_surface",
            "thinking_entry_v2": "reading_surface.thinking_surface",
            "legacy_current_dialogue_turn_status": "diagnostic_compatibility_only",
            "customer_direct_legacy_fields_exposed": False,
            "questions_array_role": "fallback_compatibility_and_non_customer_diagnostics",
            "question_dialogue_graph_role": "memory_relation_graph_only",
            "recommender_role": "candidate_source_only",
            "frontend_selection_allowed": False,
            "answer_submit_source": "reading_surface.calibration_surface.visible_probe_cards[].submit_contract",
            "legacy_answer_submit_source": "reading_surface.current_dialogue_turn.question",
            "legacy_answer_submit_source_status": "deprecated_compatibility_only",
            "calibration_submit_source_v2": "reading_surface.calibration_surface.visible_probe_cards[].submit_contract",
            "conversation_submit_source_v2": "reading_surface.conversation_surface.submit_contract",
            "max_visible_customer_questions": 1,
            "boundary": "dialogue_entry_policy_prevents_legacy_question_pool_from_selecting_customer_turn",
        },
        "customer_visible_roles": sorted(USER_VISIBLE_ROLES),
        "diagnostic_roles": sorted(DIAGNOSTIC_ROLES),
        "diagnostics_visible": bool(diagnostics),
        "additive_api_policy": {
            "must_preserve": additive_fields,
            "field_count": len(additive_fields),
            "boundary": "projection_contract_is_additive_and_does_not_rewrite_chart_facts",
        },
        "internal_visibility_policy": {
            "guest_user_diagnostics": "hidden",
            "practitioner_admin_lab_diagnostics": "role_gated",
            "hidden_fields": hidden_fields,
            "boundary": "projection_visibility_changes_surface_not_bazi_facts",
        },
        "role_visibility_matrix": {
            "version": "v30.role_visibility_matrix.v1",
            "guest": _role_visibility_policy("guest"),
            "user": _role_visibility_policy("user"),
            "practitioner": _role_visibility_policy("practitioner"),
            "admin": _role_visibility_policy("admin"),
            "analyst": _role_visibility_policy("analyst"),
            "lab": _role_visibility_policy("lab"),
            "boundary": "role_visibility_changes_projection_depth_not_runtime_calculation",
        },
        "customer_forbidden_fields": {
            "version": "v30.customer_forbidden_projection_fields.v1",
            "fields": hidden_fields,
            "applies_to": sorted(USER_VISIBLE_ROLES),
            "boundary": "customer_projection_hides_diagnostics_training_policy_and_raw_scores",
        },
        "leak_scan": leak_scan,
        "boundary": "api_projection_contract_keeps_customer_surface_simple_and_internal_context_role_gated",
    }


def _resolve_role(role_key: str) -> str:
    if role_key in {"guest", "user", "practitioner", "analyst", "admin", "lab"}:
        return role_key
    return "user"


def _hidden_projection_tokens() -> list[str]:
    return [
        "policy_effect",
        "question_policy",
        "structure_policy",
        "dynamic_graph",
        "path_scores",
        "feature_evidence",
        "hidden_factor_calibration",
        "hidden_factor_state",
        "training_signal",
        "raw_weight",
        "raw_score",
        "llm_answer_draft_call",
        "adaptive_question_diagnostics",
        "central_brain_trace",
        "internal_next_question_id",
    ]


def _role_visibility_policy(role_key: str) -> dict[str, object]:
    diagnostic = role_key in DIAGNOSTIC_ROLES
    return {
        "diagnostics_visible": diagnostic,
        "raw_scores_visible": False,
        "policy_payloads_visible": diagnostic,
        "training_internals_visible": diagnostic,
        "customer_surface_core_first": True,
    }


def _customer_surface_contract(
    reading_surface: dict[str, object],
    customer_surface_order: list[str],
) -> dict[str, object]:
    core = reading_surface.get("core_bazi_reading", {})
    domain_cards = reading_surface.get("domain_cards", [])
    next_question = reading_surface.get("next_question", {})
    current_turn = reading_surface.get("current_dialogue_turn", {})
    legacy = reading_surface.get("legacy_dialogue_surface", {})
    legacy = legacy if isinstance(legacy, dict) else {}
    calibration = reading_surface.get("calibration_surface", {})
    conversation = reading_surface.get("conversation_surface", {})
    thinking = reading_surface.get("thinking_surface", {})
    ready = (
        isinstance(core, dict)
        and core.get("surface_type") == "core_bazi_calculation"
        and isinstance(domain_cards, list)
        and bool(domain_cards)
        and isinstance(calibration, dict)
        and bool(calibration)
        and isinstance(conversation, dict)
        and bool(conversation)
        and isinstance(thinking, dict)
        and bool(thinking)
    )
    return {
        "version": "v30.customer_surface_contract.v1",
        "surface_type": str(reading_surface.get("surface_type") or ""),
        "has_core_bazi_reading": isinstance(core, dict) and core.get("surface_type") == "core_bazi_calculation",
        "has_domain_cards": isinstance(domain_cards, list) and bool(domain_cards),
        "has_time_context": isinstance(reading_surface.get("time_context", {}), dict) and bool(reading_surface.get("time_context", {})),
        "has_current_dialogue_turn": isinstance(current_turn, dict) and bool(current_turn),
        "has_next_question": isinstance(next_question, dict) and bool(next_question),
        "has_legacy_dialogue_surface": bool(legacy),
        "direct_legacy_fields_exposed": bool(legacy.get("direct_fields_exposed")),
        "legacy_status": str(legacy.get("status") or ""),
        "has_calibration_surface": isinstance(calibration, dict) and bool(calibration),
        "has_conversation_surface": isinstance(conversation, dict) and bool(conversation),
        "has_thinking_surface": isinstance(thinking, dict) and bool(thinking),
        "questions_array_fallback_only": True if not current_turn else (
            _nested_bool(current_turn, "compatibility", "questions_array_is_legacy_only")
            or _nested_bool(current_turn, "compatibility", "questions_array_is_fallback_only")
        ),
        "primary_dialogue_entry": "conversation_surface",
        "legacy_dialogue_entry": "current_dialogue_turn",
        "primary_probe_entry_v2": "calibration_surface",
        "primary_thinking_entry_v2": "thinking_surface",
        "surface_prefix_ready": ready,
        "surface_order": customer_surface_order,
        "boundary": "customer_surface_contract_validates_projection_shape_not_bazi_facts",
    }


def _projection_leak_scan(
    *,
    role_key: str,
    reading_surface: dict[str, object],
    questions: list[dict[str, object]],
    answer_panel: dict[str, object] | None,
    diagnostics: dict[str, object],
) -> dict[str, object]:
    hidden_tokens = _hidden_projection_tokens()
    if role_key not in USER_VISIBLE_ROLES:
        return {
            "version": "v30.projection_leak_scan.v1",
            "applies_to_customer_surface": False,
            "forbidden_token_hits": [],
            "diagnostics_hidden": False,
            "passed": True,
            "boundary": "diagnostic_roles_can_see_internal_context_without_rewriting_facts",
        }
    rendered_surface = str(
        {
            "reading_surface": reading_surface,
            "questions": questions,
            "answer_panel": answer_panel or {},
        }
    )
    hits = sorted({token for token in hidden_tokens if token in rendered_surface})
    return {
        "version": "v30.projection_leak_scan.v1",
        "applies_to_customer_surface": True,
        "forbidden_token_hits": hits,
        "diagnostics_hidden": not bool(diagnostics),
        "passed": not hits and not diagnostics,
        "boundary": "customer_projection_hides_internal_policy_training_and_raw_signal_fields",
    }


def _role_profile(role_key: str) -> dict[str, object]:
    profiles = {
        "guest": {
            "label": "游客",
            "surface": "preview",
            "diagnostics_visible": False,
            "can_submit_answer": True,
        },
        "user": {
            "label": "普通用户",
            "surface": "customer_reading",
            "diagnostics_visible": False,
            "can_submit_answer": True,
        },
        "practitioner": {
            "label": "命理师",
            "surface": "practitioner_review",
            "diagnostics_visible": True,
            "can_submit_answer": True,
        },
        "analyst": {
            "label": "分析师",
            "surface": "analysis",
            "diagnostics_visible": True,
            "can_submit_answer": True,
        },
        "admin": {
            "label": "Admin",
            "surface": "operations",
            "diagnostics_visible": True,
            "can_submit_answer": True,
        },
        "lab": {
            "label": "Lab",
            "surface": "lab",
            "diagnostics_visible": True,
            "can_submit_answer": True,
        },
    }
    payload = dict(profiles.get(role_key, profiles["user"]))
    payload.update({"role_key": role_key, "boundary": "role_profile_changes_projection_not_chart_fact"})
    return payload


def _diagnostics(
    runtime: CoreRuntimeResult,
    portrait_views: list[object],
    portrait_view_summary: dict[str, object],
    rendered_labels: list[object],
    rendered_label_summary: dict[str, object],
) -> dict[str, object]:
    return {
        "trace_id": runtime.trace_id,
        "actor_context": runtime.question_plan.policy_effect.get("actor_context", {}),
        "active_policy_versions": runtime.question_plan.policy_effect.get("active_policy_versions", {}),
        "chart_build_source": runtime.chart_context.input_pillars.get("chart_build_source", {}),
        "calendar_conversion_trace": runtime.chart_context.input_pillars.get("conversion_trace", {}),
        "hidden_factor_probe_count": len(runtime.question_plan.hidden_factor_probes),
        "knowledge_rule_portrait_signal_count": len(runtime.question_plan.knowledge_rule_portrait_signals),
        "recommendation_count": len(runtime.question_plan.recommended_questions),
        "krp_library_unit_count": len(runtime.question_plan.policy_effect.get("krp_library_units", [])),
        "hidden_factor_calibration": runtime.question_plan.policy_effect.get("hidden_factor_calibration", {}),
        "hidden_factor_state": runtime.question_plan.policy_effect.get("hidden_factor_state", {}),
        "latent_bazi_profile": runtime.question_plan.policy_effect.get("latent_bazi_profile", {}),
        "latent_bazi_profile_summary": runtime.question_plan.policy_effect.get("latent_bazi_profile_summary", {}),
        "latent_bazi_attributes": runtime.question_plan.policy_effect.get("latent_bazi_attributes", {}),
        "latent_bazi_attributes_summary": runtime.question_plan.policy_effect.get("latent_bazi_attributes_summary", {}),
        "latent_bazi_individualized_projection": runtime.question_plan.policy_effect.get("latent_bazi_individualized_projection", {}),
        "latent_bazi_individualized_projection_summary": runtime.question_plan.policy_effect.get("latent_bazi_individualized_projection_summary", {}),
        "latent_question_strategy": runtime.question_plan.policy_effect.get("latent_question_strategy", {}),
        "latent_policy_observability": _latent_policy_observability(runtime),
        "ten_god_energy_model": runtime.question_plan.policy_effect.get("ten_god_energy_model", {}),
        "ten_god_energy_summary": runtime.question_plan.policy_effect.get("ten_god_energy_summary", {}),
        "model_signal_summary": runtime.question_plan.policy_effect.get("model_signal_summary", {}),
        "question_outcomes": runtime.question_plan.policy_effect.get("question_outcomes", []),
        "question_dialogue_graph": runtime.question_plan.policy_effect.get("question_dialogue_graph", {}),
        "interaction_state": runtime.question_plan.policy_effect.get("interaction_state", {}),
        "central_reading_state": runtime.question_plan.policy_effect.get("central_reading_state", {}),
        "interaction_brain_summary": _interaction_brain_summary(runtime),
        "adaptive_question_diagnostics": runtime.question_plan.policy_effect.get("adaptive_question_diagnostics", {}),
        "ranked_decisions": runtime.question_plan.policy_effect.get("ranked_decisions", {}),
        "practical_reading_context": runtime.question_plan.policy_effect.get("practical_reading_context", {}),
        "real_bazi_diagnosis": runtime.question_plan.policy_effect.get("real_bazi_diagnosis", {}),
        "agent_question_flow": runtime.question_plan.policy_effect.get("agent_question_flow", {}),
        "macro_portrait_projection_views": [
            row.model_dump(mode="json") if hasattr(row, "model_dump") else row for row in portrait_views
        ],
        "macro_portrait_view_summary": portrait_view_summary,
        "rendered_question_labels": [
            row.model_dump(mode="json") if hasattr(row, "model_dump") else row for row in rendered_labels
        ],
        "rendered_question_label_summary": rendered_label_summary,
        "llm_output_contract_summary": runtime.question_plan.policy_effect.get("llm_output_contract_summary", {}),
        "llm_provider_readiness": runtime.question_plan.policy_effect.get("llm_provider_readiness", {}),
        "llm_answer_draft_call": runtime.question_plan.policy_effect.get("llm_answer_draft_call", {}),
        "llm_runtime_status": _llm_runtime_status(runtime),
        "central_brain": _central_brain_diagnostics(runtime),
        "dynamic_path_count": runtime.structure_state.path_scores.get("dynamic_path_count", 0.0),
        "bazi_context": _bazi_context(runtime),
    }


def _latent_policy_observability(runtime: CoreRuntimeResult) -> dict[str, object]:
    policy_effect = runtime.question_plan.policy_effect
    question_policy = policy_effect.get("question_policy_payload", {})
    rule_policy = policy_effect.get("rule_policy_payload", {})
    question_policy = question_policy if isinstance(question_policy, dict) else {}
    rule_policy = rule_policy if isinstance(rule_policy, dict) else {}
    question_weights = question_policy.get("weights", {})
    rule_weights = rule_policy.get("weights", {})
    question_weights = question_weights if isinstance(question_weights, dict) else {}
    rule_weights = rule_weights if isinstance(rule_weights, dict) else {}
    question_latent_policy = question_weights.get("latent_bazi_attribute_policy", {})
    rule_latent_policy = rule_weights.get("latent_bazi_attribute_policy", {})
    question_latent_policy = question_latent_policy if isinstance(question_latent_policy, dict) else {}
    rule_latent_policy = rule_latent_policy if isinstance(rule_latent_policy, dict) else {}
    attrs = policy_effect.get("latent_bazi_attributes", {})
    attrs = attrs if isinstance(attrs, dict) else {}
    summary = policy_effect.get("latent_bazi_attributes_summary", {})
    summary = summary if isinstance(summary, dict) else {}
    strategy = policy_effect.get("latent_question_strategy", {})
    strategy = strategy if isinstance(strategy, dict) else {}
    recommendations = [
        row for row in runtime.question_plan.recommended_questions
        if isinstance(row, dict)
    ]
    influenced = [
        {
            "question_id": str(row.get("question_id") or ""),
            "topic": str(row.get("topic") or ""),
            "interaction_type": str(row.get("interaction_type") or ""),
            "policy_reasons": [
                str(reason)
                for reason in row.get("reasons", [])
                if "latent_bazi_attribute_policy" in str(reason) or "latent_question" in str(reason)
            ],
        }
        for row in recommendations
        if any(
            "latent_bazi_attribute_policy" in str(reason) or "latent_question" in str(reason)
            for reason in row.get("reasons", [])
        )
    ]
    blocked_routes = question_latent_policy.get("blocked_training_routes", [])
    blocked_routes = [str(row) for row in blocked_routes] if isinstance(blocked_routes, list) else []
    active_versions = policy_effect.get("active_policy_versions", {})
    active_versions = active_versions if isinstance(active_versions, dict) else {}
    return {
        "version": "v30.latent_policy_observability.v1",
        "status": "policy_active" if question_latent_policy else "default_runtime_no_candidate_policy",
        "active_policy_versions": {
            "question_policy": str(active_versions.get("question_policy") or ""),
            "rule_policy": str(active_versions.get("rule_policy") or ""),
        },
        "attribute_status": str(attrs.get("status") or "default"),
        "active_global_attributes": summary.get("active_global_attributes", [])
        if isinstance(summary.get("active_global_attributes", []), list)
        else [],
        "active_domain_biases": summary.get("active_domain_biases", [])
        if isinstance(summary.get("active_domain_biases", []), list)
        else [],
        "latent_question_strategy": {
            "status": str(strategy.get("status") or ""),
            "need_score": strategy.get("need_score"),
            "ask_now": strategy.get("ask_now"),
            "target_domain": str(strategy.get("target_domain") or ""),
            "reasons": strategy.get("reasons", []) if isinstance(strategy.get("reasons", []), list) else [],
        },
        "question_policy": _latent_policy_public_projection(question_latent_policy),
        "rule_policy": _latent_policy_public_projection(rule_latent_policy),
        "influenced_questions": influenced,
        "influenced_question_count": len(influenced),
        "training_boundary": {
            "can_tune_latent_inference": question_latent_policy.get("can_tune_latent_inference") is True,
            "can_tune_question_strategy": question_latent_policy.get("can_tune_question_strategy") is True,
            "can_tune_individualized_projection": question_latent_policy.get("can_tune_individualized_projection") is True,
            "can_tune_chart_facts": question_latent_policy.get("can_tune_chart_facts") is True,
            "blocked_training_routes": blocked_routes,
            "chart_fact_mutation_allowed": False,
            "boundary": "latent_policy_observability_trains_personalization_question_strategy_and_projection_not_chart_facts",
        },
        "customer_visible": False,
        "boundary": "latent_policy_observability_is_admin_diagnostic_surface_not_customer_reading_text",
    }


def _latent_policy_public_projection(policy: dict[str, object]) -> dict[str, object]:
    if not policy:
        return {}
    return {
        "mode": str(policy.get("mode") or ""),
        "source_signal_id": str(policy.get("source_signal_id") or ""),
        "reverse_inference_weight": policy.get("reverse_inference_weight"),
        "question_need_weight": policy.get("question_need_weight"),
        "individualized_projection_weight": policy.get("individualized_projection_weight"),
        "domain_bias_keys": sorted(str(key) for key in _dict_keys(policy.get("domain_bias_weights"))),
        "ten_god_modifier_keys": sorted(str(key) for key in _dict_keys(policy.get("ten_god_modifier_weights"))),
        "global_attribute_keys": sorted(str(key) for key in _dict_keys(policy.get("global_attribute_weights"))),
        "can_tune_chart_facts": policy.get("can_tune_chart_facts") is True,
        "boundary": str(policy.get("boundary") or ""),
    }


def _dict_keys(value: object) -> list[str]:
    return list(value.keys()) if isinstance(value, dict) else []


def _interaction_brain_summary(runtime: CoreRuntimeResult) -> dict[str, object]:
    result = runtime.question_plan.policy_effect.get("interaction_brain_result", {})
    result = result if isinstance(result, dict) else {}
    outcomes = runtime.question_plan.policy_effect.get("question_outcomes", [])
    outcomes = [row for row in outcomes if isinstance(row, dict)] if isinstance(outcomes, list) else []
    latest = outcomes[-1] if outcomes else {}
    state = runtime.question_plan.policy_effect.get("interaction_state", {})
    state = state if isinstance(state, dict) else {}
    absorbed = result.get("absorbed_signals", [])
    rejected = result.get("rejected_signals", [])
    return {
        "version": "v30.interaction_brain_diagnostics_summary.v1",
        "result_version": str(result.get("version") or ""),
        "latest_question_id": str(latest.get("question_id") or result.get("question_id") or ""),
        "latest_constraint_valid": latest.get("constraint_valid"),
        "allowed_to_update_hidden_factor": result.get("allowed_to_update_hidden_factor"),
        "hidden_factor_feedback_saved": result.get("hidden_factor_feedback_saved"),
        "invalid_retry_question_id": str(state.get("invalid_retry_question_id") or ""),
        "visible_next_question_id": str(state.get("visible_next_question_id") or ""),
        "internal_next_question_id": str(state.get("internal_next_question_id") or ""),
        "absorbed_signal_count": len(absorbed) if isinstance(absorbed, list) else 0,
        "rejected_signal_count": len(rejected) if isinstance(rejected, list) else 0,
        "chart_fact_mutation_allowed": bool(result.get("chart_fact_mutation_allowed")),
        "internal_feedback_payload_visible": "hidden_factor_feedback_payload" in result,
        "boundary": "interaction_brain_diagnostics_are_role_gated_and_do_not_mutate_chart_facts",
    }


def _portrait_views(runtime: CoreRuntimeResult, *, role_key: str, client: str) -> list[object]:
    projections = runtime.question_plan.policy_effect.get("macro_portrait_projections", [])
    if not isinstance(projections, list):
        projections = []
    return build_macro_portrait_projection_views(
        [row for row in projections if isinstance(row, dict)],
        role_key=role_key,
        client=client,
    )


def _reading_surface(
    runtime: CoreRuntimeResult,
    *,
    questions: list[dict[str, object]],
    role_key: str,
    locale: str,
    client: str,
) -> dict[str, object]:
    practical = runtime.question_plan.policy_effect.get("practical_reading_context", {})
    central = runtime.question_plan.policy_effect.get("central_reading_state", {})
    final_synthesis = central.get("final_synthesis", {}) if isinstance(central, dict) else {}
    final_synthesis = final_synthesis if isinstance(final_synthesis, dict) else {}
    agent_flow = runtime.question_plan.policy_effect.get("agent_question_flow", {})
    domain_readings = practical.get("domain_readings", {}) if isinstance(practical, dict) else {}
    focus_domains = _focus_domains(domain_readings)
    domain_cards = _domain_cards(domain_readings, focus_domains, locale=locale)
    next_question = _surface_question_projection(_next_question_from_dialogue_plan(runtime, questions))
    current_dialogue_turn = _current_dialogue_turn(
        runtime,
        next_question=next_question,
        questions=questions,
        role_key=role_key,
    )
    if isinstance(current_dialogue_turn.get("question"), dict) and current_dialogue_turn["question"].get("response_option_set"):
        next_question = {
            **next_question,
            "response_option_set": current_dialogue_turn["question"]["response_option_set"],
        }
    dialogue = _dialogue_projection(runtime, next_question=next_question, questions=questions)
    core_bazi_reading = _core_bazi_reading(runtime, domain_cards)
    basic_assertions = core_bazi_reading.get("basic_assertions", [])
    basic_assertions = basic_assertions if isinstance(basic_assertions, list) else []
    reading_summary = {
        "title": _customer_summary_title(
            runtime,
            domain_cards,
            locale=locale,
            diagnostic=role_key not in USER_VISIBLE_ROLES,
        ),
        "status": practical.get("status", "ready") if isinstance(practical, dict) else "ready",
        "focus_domains": focus_domains,
        "primary_message": _primary_message(domain_cards, locale=locale, final_synthesis=final_synthesis),
        "final_conclusion": str(final_synthesis.get("conclusion") or ""),
        "final_advice": str(final_synthesis.get("advice") or ""),
        "final_synthesis_status": str(final_synthesis.get("status") or ""),
        "diagnosis_overview": _diagnosis_overview(runtime),
        "timing_status": _nested_dict(practical, "timing_summary", "status", default="natal_only"),
        "boundary": "customer_summary_uses_final_synthesis_without_exposing_internal_diagnostics",
    }
    customer_final_synthesis = _customer_final_synthesis(final_synthesis)
    surface_orchestrator = build_surface_orchestration(
        runtime,
        reading_summary=reading_summary,
        final_synthesis=customer_final_synthesis,
        domain_cards=domain_cards,
        current_dialogue_turn=current_dialogue_turn,
        next_question=next_question,
        dialogue=dialogue,
        questions=questions,
        role_key=role_key,
        locale=locale,
        client=client,
    )
    legacy_dialogue_surface = _legacy_dialogue_surface(
        current_dialogue_turn=current_dialogue_turn,
        next_question=next_question,
        dialogue=dialogue,
        domain_cards=domain_cards,
        role_key=role_key,
    )
    surface = {
        "version": "v30.customer_reading_surface.v1",
        "role_key": role_key,
        "role_contract": _reading_surface_role_contract(role_key),
        "locale": locale,
        "client": client,
        "surface_type": "customer_reading_loop",
        "chart_status": runtime.chart_context.input_pillars.get("chart_build_source", {}).get(
            "status",
            runtime.chart_context.time_layers.get("status", "ready"),
        ),
        "reading_summary": reading_summary,
        "final_synthesis": customer_final_synthesis,
        "decision_workbench": _decision_workbench_projection(central, role_key=role_key),
        "decision_feedback": _decision_feedback_projection(central, role_key=role_key),
        "diagnosis_overview": _diagnosis_overview(runtime),
        "domain_cards": domain_cards,
        "basic_assertions": basic_assertions,
        "bazi_features": _bazi_feature_rows(runtime, detailed=role_key not in USER_VISIBLE_ROLES),
        "bazi_portraits": _bazi_portrait_rows(runtime, detailed=role_key not in USER_VISIBLE_ROLES),
        "bazi_paths": _bazi_path_rows(runtime, detailed=role_key not in USER_VISIBLE_ROLES),
        "core_bazi_reading": core_bazi_reading,
        "structure_dynamics": _customer_structure_dynamics(runtime, role_key=role_key, locale=locale),
        "time_context": _customer_time_context(runtime),
        "surface_orchestrator": surface_orchestrator,
        "surface_policy": surface_orchestrator["reading_surface_policy"],
        "calibration_surface": surface_orchestrator["calibration_surface"],
        "conversation_surface": surface_orchestrator["conversation_surface"],
        "thinking_surface": surface_orchestrator["thinking_surface"],
        "legacy_dialogue_surface": legacy_dialogue_surface,
        "interaction_stage": _interaction_stage(runtime),
        "selected_domain": _interaction_selected_domain(runtime),
        "question_count": len(questions),
        "next_stage": agent_flow.get("next_stage", "") if isinstance(agent_flow, dict) else "",
        "interaction_goal": "surface_orchestrated_reading_probe_conversation_thinking",
        "internal_context_visible": role_key not in USER_VISIBLE_ROLES,
        "boundary": "customer_surface_uses_four_surface_contracts_legacy_dialogue_role_gated",
    }
    if role_key not in USER_VISIBLE_ROLES:
        surface.update(_diagnostic_legacy_dialogue_fields(legacy_dialogue_surface))
    return surface


def _current_dialogue_turn(
    runtime: CoreRuntimeResult,
    *,
    next_question: dict[str, object],
    questions: list[dict[str, object]],
    role_key: str,
) -> dict[str, object]:
    central = runtime.question_plan.policy_effect.get("central_reading_state", {})
    central = central if isinstance(central, dict) else {}
    action = central.get("next_action", {})
    action = action if isinstance(action, dict) else {}
    decision_trace = central.get("brain_decision_trace", {})
    decision_trace = decision_trace if isinstance(decision_trace, dict) else {}
    voi_policy = central.get("value_of_information_policy", {})
    voi_policy = voi_policy if isinstance(voi_policy, dict) else {}
    stage_id = _dialogue_turn_stage_id(central, next_question)
    target_claim_ids = _dialogue_turn_target_claim_ids(central, next_question)
    question = next_question if isinstance(next_question, dict) else {}
    raw_action = str(decision_trace.get("selected_action") or action.get("action") or "")
    has_question = bool(question.get("question_id"))
    relevance = _dialogue_turn_relevance_gate(
        raw_action=raw_action,
        question=question,
        stage_id=stage_id,
        target_claim_ids=target_claim_ids,
        voi_policy=voi_policy,
    )
    turn_action = "ask" if has_question and relevance["passed"] else (
        "continue" if raw_action == "continue_next_stage" else "conclude" if raw_action == "conclude_stage" else "stop"
    )
    if role_key in USER_VISIBLE_ROLES and has_question and turn_action != "ask":
        question = {}
    response_option_set = build_response_option_set_for_question(
        question,
        stage_id=stage_id,
        role_key=role_key,
    ) if turn_action == "ask" else {}
    if question and response_option_set:
        question = {
            **question,
            "response_option_set": response_option_set,
        }
    visible_option_sets = role_visible_option_sets([response_option_set], role_key=role_key) if response_option_set else []
    return {
        "version": "v30.current_dialogue_turn.v1",
        "action": turn_action,
        "stage_id": stage_id,
        "stage_display": _dialogue_turn_stage_display(stage_id),
        "question": question if turn_action == "ask" else {},
        "why_now": _dialogue_turn_reason(action, question, stage_id),
        "target_claim_ids": target_claim_ids,
        "target_claim_count": len(target_claim_ids),
        "semantic_focus": _customer_semantic_focus(question),
        "response_option_set": response_option_set if response_option_set else {},
        "visible_option_sets": visible_option_sets,
        "visual_hint": _dialogue_turn_visual_hint(question, stage_id, action=turn_action, voi_policy=voi_policy),
        "decision_source": "central_reading_state.brain_decision_trace",
        "decision_basis": {
            "selected_action": str(decision_trace.get("selected_action") or raw_action),
            "question_value": _bounded_float(voi_policy.get("question_value"), 0.0),
            "information_gain": _bounded_float(voi_policy.get("information_gain"), 0.0),
            "user_cost": _bounded_float(voi_policy.get("user_cost"), 0.0),
            "top_claim_score": _bounded_float(voi_policy.get("top_claim_score"), 0.0),
            "relevance_passed": relevance["passed"],
            "relevance_reason": relevance["reason"],
            "boundary": "decision_basis_is_customer_safe_summary_not_internal_trace",
        },
        "ui_policy": {
            "max_visible_questions": 1,
            "allow_free_text": False,
            "show_engine_diagnostics": False,
            "question_source": "current_dialogue_turn",
            "boundary": "frontend_must_not_select_question_from_questions_array",
        },
        "compatibility": {
            "questions_array_is_legacy_only": True,
            "compatible_question_count": len(questions),
            "next_question_id": str(question.get("question_id") or ""),
        },
        "boundary": "current_dialogue_turn_is_customer_safe_single_dialogue_exit_not_chart_fact",
    }


def _legacy_dialogue_surface(
    *,
    current_dialogue_turn: dict[str, object],
    next_question: dict[str, object],
    dialogue: dict[str, object],
    domain_cards: list[dict[str, object]],
    role_key: str,
) -> dict[str, object]:
    direct_fields_exposed = role_key not in USER_VISIBLE_ROLES
    next_question_id = str(next_question.get("question_id") or "") if isinstance(next_question, dict) else ""
    payload: dict[str, object] = {
        "version": "v30.legacy_dialogue_surface.v1",
        "status": "diagnostic_payload_available" if direct_fields_exposed else "hidden_for_customer",
        "direct_fields_exposed": direct_fields_exposed,
        "customer_product_entry": False,
        "replacement_entries": [
            "calibration_surface",
            "conversation_surface",
            "thinking_surface",
        ],
        "legacy_next_question_id": next_question_id if direct_fields_exposed else "",
        "legacy_field_names": [
            "current_dialogue_turn",
            "next_question",
            "dialogue",
            "next_question_id",
            "visible_next_question_id",
            "options",
        ],
        "boundary": "legacy_dialogue_payload_is_role_gated_and_not_customer_product_entry",
    }
    if direct_fields_exposed:
        payload["payload"] = {
            "current_dialogue_turn": current_dialogue_turn,
            "next_question": next_question,
            "dialogue": dialogue,
            "next_question_id": next_question_id,
            "visible_next_question_id": next_question_id,
            "options": _surface_options(next_question, domain_cards),
        }
    return payload


def _diagnostic_legacy_dialogue_fields(legacy_dialogue_surface: dict[str, object]) -> dict[str, object]:
    payload = legacy_dialogue_surface.get("payload", {})
    return payload if isinstance(payload, dict) else {}


def _dialogue_turn_relevance_gate(
    *,
    raw_action: str,
    question: dict[str, object],
    stage_id: str,
    target_claim_ids: list[str],
    voi_policy: dict[str, object],
) -> dict[str, object]:
    if raw_action not in {"ask_stage_question", "ask_hidden_attribute_probe"}:
        return {"passed": False, "reason": "central_brain_did_not_select_dialogue"}
    if not question.get("question_id"):
        return {"passed": False, "reason": "missing_question"}
    if not stage_id:
        return {"passed": False, "reason": "missing_relevant_stage"}
    question_value = _bounded_float(voi_policy.get("question_value"), 0.0)
    information_gain = _bounded_float(voi_policy.get("information_gain"), 0.0)
    user_cost = _bounded_float(voi_policy.get("user_cost"), 0.0)
    if user_cost >= 0.85:
        return {"passed": False, "reason": "user_cost_too_high"}
    if target_claim_ids:
        return {"passed": True, "reason": "target_claim_bound"}
    if question_value >= 0.25 and information_gain >= 0.35:
        return {"passed": True, "reason": "voi_threshold_passed"}
    return {"passed": False, "reason": "low_relevance"}


def _customer_semantic_focus(question: dict[str, object]) -> dict[str, object]:
    semantic = question.get("semantic_projection", {}) if isinstance(question, dict) else {}
    semantic = semantic if isinstance(semantic, dict) else {}
    if not semantic:
        return {}
    return {
        "version": "v30.customer_semantic_focus.v1",
        "macro_domain": str(semantic.get("macro_domain") or ""),
        "macro_label": str(semantic.get("macro_label") or ""),
        "selected_slot": str(semantic.get("selected_slot") or ""),
        "keywords": [str(row) for row in _as_list(semantic.get("keywords"))[:6]],
        "ten_god_drivers": _customer_ten_god_drivers(_as_list(semantic.get("ten_god_drivers"))),
        "boundary": "customer_semantic_focus_explains_question_theme_without_internal_weights",
    }


def _customer_ten_god_drivers(rows: list[object]) -> list[dict[str, object]]:
    projected: list[dict[str, object]] = []
    for row in rows[:3]:
        if not isinstance(row, dict):
            continue
        projected.append({
            "ten_god": str(row.get("ten_god") or ""),
            "label": str(row.get("label") or ""),
        })
    return projected


def _dialogue_turn_stage_id(central: dict[str, object], question: dict[str, object]) -> str:
    seed = central.get("current_turn_seed", {})
    if isinstance(seed, dict) and str(seed.get("question_id") or "") == str(question.get("question_id") or ""):
        stage_id = str(seed.get("stage_id") or "")
        if stage_id:
            return stage_id
    question_id = str(question.get("question_id") or "")
    opportunities = central.get("stage_question_opportunities", [])
    if isinstance(opportunities, list):
        for row in opportunities:
            if isinstance(row, dict) and str(row.get("question_id") or "") == question_id:
                return str(row.get("step_id") or "")
    topic = str(question.get("topic") or "")
    stage = str(question.get("stage") or "")
    stage_id = _dialogue_stage_id_from_topic_stage(topic=topic, stage=stage)
    if stage_id:
        return stage_id
    return ""


def _dialogue_stage_id_from_topic_stage(*, topic: str, stage: str) -> str:
    if topic in {"time_context", "timing"} or stage == "context_completion":
        return "timing_layers"
    if topic in {"useful_god", "structure_dynamic", "decision"} or stage == "candidate_review":
        return "path_reasoning"
    if topic == "hidden_factor" or stage == "dialogue_discovery":
        return "portrait_projection"
    if topic in {"career", "wealth", "relationship", "health", "practical_reading"}:
        return "domain_synthesis"
    if stage == "mainline_review":
        return "structure_reasoning"
    return ""


def _dialogue_turn_target_claim_ids(central: dict[str, object], question: dict[str, object]) -> list[str]:
    seed = central.get("current_turn_seed", {})
    if isinstance(seed, dict) and str(seed.get("question_id") or "") == str(question.get("question_id") or ""):
        claims = seed.get("target_claim_ids", [])
        if isinstance(claims, list) and claims:
            return [str(claim_id) for claim_id in claims if claim_id][:4]
    question_id = str(question.get("question_id") or "")
    opportunities = central.get("stage_question_opportunities", [])
    if isinstance(opportunities, list):
        for row in opportunities:
            if isinstance(row, dict) and str(row.get("question_id") or "") == question_id:
                claims = row.get("target_claim_ids", [])
                return [str(claim_id) for claim_id in claims if claim_id][:4] if isinstance(claims, list) else []
    needs = central.get("needs_question_claim_ids", [])
    if isinstance(needs, list) and needs:
        return [str(claim_id) for claim_id in needs if claim_id][:4]
    top = central.get("top_claim_ids", [])
    return [str(claim_id) for claim_id in top if claim_id][:1] if isinstance(top, list) else []


def _dialogue_turn_reason(action: dict[str, object], question: dict[str, object], stage_id: str) -> str:
    if not question:
        reason = str(action.get("reason") or "")
        if reason == "top_claim_has_enough_multi_module_support":
            return "这一页证据已经足够，优先给结论和建议，不再额外追问。"
        return "当前阶段先收束结论，不额外增加用户输入。"
    topic = _topic_label(str(question.get("topic") or ""))
    gain = question.get("expected_information_gain", {})
    gain = gain if isinstance(gain, dict) else {}
    readable_gain = _readable_gain(str(gain.get("primary_gain") or ""))
    stage = _dialogue_turn_stage_display(stage_id)
    return f"这个问题只补“{stage}”里的一个关键背景，用来把{topic}判断落到更具体的结论和建议：{readable_gain}。"


def _dialogue_turn_stage_display(stage_id: str) -> str:
    labels = {
        "chart_build": "排盘校准",
        "rule_matching": "规则匹配",
        "feature_extraction": "特征抽取",
        "portrait_projection": "画像校准",
        "path_reasoning": "路径判断",
        "structure_reasoning": "结构判断",
        "timing_layers": "时运判断",
        "domain_synthesis": "领域建议",
    }
    return labels.get(stage_id, "当前步骤")


def _dialogue_turn_visual_hint(
    question: dict[str, object],
    stage_id: str,
    *,
    action: str,
    voi_policy: dict[str, object] | None = None,
) -> dict[str, object]:
    voi_policy = voi_policy if isinstance(voi_policy, dict) else {}
    topic = str(question.get("topic") or "")
    gain = question.get("expected_information_gain", {}) if isinstance(question, dict) else {}
    gain = gain if isinstance(gain, dict) else {}
    score = _bounded_float(voi_policy.get("information_gain"), _bounded_float(gain.get("score"), 0.0))
    user_cost = _bounded_float(voi_policy.get("user_cost"), 0.22 if topic != "hidden_factor" else 0.34)
    if action != "ask" or not question:
        return {
            "version": "v30.dialogue_visual_hint.v1",
            "kind": "stage_conclusion_marker",
            "title": "本页直接收束",
            "chips": ["结论优先", "不额外追问"],
            "markers": [],
            "guidance": "证据足够时，系统不强行提问。",
            "boundary": "visual_hint_explains_dialogue_action_not_bazi_fact",
        }
    chips = [_topic_label(topic), _dialogue_turn_stage_display(stage_id), "只问一个关键点"]
    if topic == "hidden_factor":
        chips.append("校准线索")
    return {
        "version": "v30.dialogue_visual_hint.v1",
        "kind": "advice_compass" if topic != "hidden_factor" else "hidden_signal_probe",
        "title": f"{_topic_label(topic)}判断焦点",
        "chips": [chip for chip in chips if chip][:4],
        "markers": [
            {"label": "信息增益", "value": score or 0.56},
            {"label": "输入成本", "value": user_cost},
        ],
        "guidance": _dialogue_visual_guidance(topic, str(gain.get("primary_gain") or "")),
        "boundary": "visual_hint_turns_dialogue_context_into_lightweight_customer_visual_not_diagnostic_trace",
    }


def _dialogue_visual_guidance(topic: str, gain: str) -> str:
    if topic == "career":
        return "回答后会把事业建议收束到稳定承接、职责上升或转型突破。"
    if topic == "wealth":
        return "回答后会把财务建议收束到赚钱方式、风险边界和节奏。"
    if topic == "relationship":
        return "回答后会把关系建议收束到相处模式、反复矛盾和边界。"
    if topic == "timing":
        return "回答后会把建议放到当前大运和流年的触发点上。"
    if topic == "hidden_factor":
        return "回答只作为隐藏线索校准，不会改写四柱和命盘事实。"
    if "decision" in gain or topic == "decision":
        return "回答后会突出当前最需要避开的决策盲点。"
    return "回答后会把结论和建议变得更具体。"


def _answer_visual_hint(answer_panel: dict[str, object], reading_surface: dict[str, object]) -> dict[str, object]:
    calibration = reading_surface.get("calibration_surface", {}) if isinstance(reading_surface, dict) else {}
    cards = calibration.get("visible_probe_cards", []) if isinstance(calibration, dict) else []
    card = cards[0] if isinstance(cards, list) and cards and isinstance(cards[0], dict) else {}
    visual = card.get("visual_hint", {}) if isinstance(card, dict) else {}
    topic = str(card.get("topic") or "") if isinstance(card, dict) else ""
    status = str((answer_panel.get("llm_metadata", {}) if isinstance(answer_panel.get("llm_metadata"), dict) else {}).get("status") or "")
    chips = [_topic_label(topic) if topic else "", "结论优先", "建议落地"]
    if status:
        chips.append("LLM增强" if status == "accepted" else "等待推演" if status in {"deferred", "loading"} else "未完成")
    return {
        "version": "v30.answer_visual_hint.v1",
        "kind": "advice_compass",
        "title": "本轮建议方向",
        "chips": [chip for chip in chips if chip][:4],
        "guidance": str(visual.get("guidance") or "优先阅读结论和建议，再看依据。") if isinstance(visual, dict) else "优先阅读结论和建议，再看依据。",
        "boundary": "answer_visual_hint_summarizes_customer_advice_direction_not_internal_reasoning",
    }


def _bounded_float(value: object, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return round(max(0.0, min(1.0, number)), 3)


def _int_count(value: object, default: int = 0) -> int:
    try:
        return max(0, int(float(value)))
    except (TypeError, ValueError):
        return default


def _as_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _dialogue_projection(
    runtime: CoreRuntimeResult,
    *,
    next_question: dict[str, object],
    questions: list[dict[str, object]],
) -> dict[str, object]:
    state = runtime.question_plan.policy_effect.get("interaction_state", {})
    state = state if isinstance(state, dict) else {}
    known = state.get("known_user_signals", {})
    known = known if isinstance(known, dict) else {}
    outcomes = runtime.question_plan.session_state.get("question_outcomes", [])
    outcomes = outcomes if isinstance(outcomes, list) else []
    answered_ids = [
        str(row)
        for row in state.get("answered_question_ids", [])
        if row
    ] if isinstance(state.get("answered_question_ids"), list) else []
    selected_options = [
        str(row)
        for row in state.get("selected_option_ids", [])
        if row
    ] if isinstance(state.get("selected_option_ids"), list) else []
    next_topic = str(next_question.get("topic") or "")
    next_gain = next_question.get("expected_information_gain", {})
    next_gain = next_gain if isinstance(next_gain, dict) else {}
    return {
        "version": "v30.customer_dialogue_projection.v1",
        "status": "ready" if next_question else "complete",
        "title": "智能问答会话",
        "summary": _dialogue_summary(answered_count=len(answered_ids), next_topic=next_topic),
        "next_question_id": str(next_question.get("question_id") or ""),
        "next_question_label": str(next_question.get("label") or ""),
        "why_this_question": _why_this_question(next_topic, str(next_gain.get("primary_gain") or "")),
        "reply_guidance": _reply_guidance(next_question),
        "progress": {
            "answered_count": len(answered_ids),
            "selected_option_count": len(selected_options),
            "absorbed_signal_count": int(known.get("answered_question_count") or 0),
        },
        "memory_chips": _dialogue_memory_chips(state, known),
        "latest_turn": _latest_turn_summary(outcomes),
        "boundary": "customer_dialogue_projection_shows_conversation_state_without_internal_strategy_trace",
    }


def _dialogue_summary(*, answered_count: int, next_topic: str) -> str:
    if answered_count:
        return f"已吸收 {answered_count} 轮回答，下一步继续校准{_topic_label(next_topic)}。"
    return f"先从{_topic_label(next_topic)}切入，让后续解读更贴近你的真实处境。"


def _why_this_question(topic: str, primary_gain: str) -> str:
    topic_label = _topic_label(topic)
    if primary_gain:
        return f"这个问题能补足{topic_label}判断所需的关键背景：{_readable_gain(primary_gain)}。"
    return f"这个问题用于确认{topic_label}里的真实关注点，再把报告收束到更具体的方向。"


def _readable_gain(value: str) -> str:
    labels = {
        "answer_career_direction": "确认事业方向和现实选择",
        "answer_wealth_tendency": "确认财务关注点和风险偏好",
        "answer_relationship_pattern": "确认关系模式和互动压力",
        "answer_timing_pressure": "确认近期年份与阶段压力",
        "answer_decision_blindspot": "确认决策盲点和需要避开的误区",
        "hidden_factor": "确认隐藏线索是否反复出现",
        "structure": "确认结构判断的现实落点",
        "timing": "确认时运触发点",
    }
    key = str(value or "").strip().lower()
    if key in labels:
        return labels[key]
    for token, label in labels.items():
        if token in key:
            return label
    return key.replace("_", " ") or "补充关键背景"


def _reply_guidance(question: dict[str, object]) -> str:
    constraints = question.get("answer_constraints", {})
    constraint_type = str(constraints.get("constraint_type") or "") if isinstance(constraints, dict) else ""
    if constraint_type == "structured_hidden_factor":
        return "优先选择反复出现的状态、年份和强度；系统只把它当作校准线索，不会改写命盘事实。"
    if constraint_type == "timing_context_check":
        return "可以补充相关年份或阶段，系统会用它定位时运语境。"
    if constraint_type == "domain_followup":
        return "选择最想看的领域，也可以补一句最近正在面对的具体选择。"
    return "可以直接选择一个方向，也可以补一句最近最困扰你的背景。"


def _dialogue_memory_chips(state: dict[str, object], known: dict[str, object]) -> list[str]:
    chips: list[str] = []
    selected_domain = str(state.get("selected_domain") or "")
    if selected_domain:
        chips.append(f"关注：{_topic_label(selected_domain)}")
    answered = state.get("answered_question_ids", [])
    if isinstance(answered, list) and answered:
        chips.append(f"已答：{len(answered)}")
    selected = state.get("selected_option_ids", [])
    if isinstance(selected, list) and selected:
        chips.append(f"选项：{len(selected)}")
    absorbed = int(known.get("answered_question_count") or 0)
    if absorbed:
        chips.append(f"线索：{absorbed}")
    return chips[:6]


def _latest_turn_summary(outcomes: list[object]) -> dict[str, object]:
    for row in reversed(outcomes):
        if not isinstance(row, dict):
            continue
        return {
            "question_id": str(row.get("question_id") or ""),
            "status": str(row.get("outcome_status") or row.get("status") or ""),
            "selected_option": str(row.get("selected_option") or ""),
            "boundary": "latest_turn_summary_is_user_visible_memory_not_chart_fact",
        }
    return {}


def _topic_label(topic: str) -> str:
    labels = {
        "career": "事业",
        "wealth": "财运",
        "relationship": "关系",
        "romance": "关系",
        "health": "健康",
        "timing": "时运",
        "structure": "结构",
        "useful_god": "用神",
        "hidden_factor": "隐藏线索",
        "decision": "决策",
        "risk": "风险",
        "overview": "整体",
    }
    return labels.get(str(topic or "").lower(), str(topic or "当前命盘"))


def _focus_domains(domain_readings: object) -> list[str]:
    if not isinstance(domain_readings, dict):
        return []
    priority = ["career", "wealth", "relationship", "health", "timing"]
    scored = [
        (
            domain,
            float(domain_readings[domain].get("priority_score", 0.0)),
            str(domain_readings[domain].get("state", "")) == "active",
        )
        for domain in priority
        if isinstance(domain_readings.get(domain), dict)
    ]
    scored = sorted(scored, key=lambda row: (-int(row[2]), -row[1], priority.index(row[0])))
    return [domain for domain, _score, _active in scored[:3]]


def _reading_surface_role_contract(role_key: str) -> dict[str, object]:
    diagnostic = role_key in DIAGNOSTIC_ROLES
    return {
        "version": "v30.reading_surface_role_contract.v1",
        "role_key": role_key,
        "density": "evidence_chain" if diagnostic else "practical",
        "diagnostics_visible": diagnostic,
        "customer_safe": role_key in USER_VISIBLE_ROLES,
        "answer_style": "practitioner_review" if role_key == "practitioner" else "diagnostic_review" if diagnostic else "customer_reading",
        "boundary": "role_contract_changes_projection_density_not_chart_fact",
    }


def _domain_cards(domain_readings: object, focus_domains: list[str], *, locale: str) -> list[dict[str, object]]:
    if not isinstance(domain_readings, dict):
        return []
    cards: list[dict[str, object]] = []
    priority = ["career", "wealth", "relationship", "health", "timing"]
    ordered_domains = [
        *[domain for domain in focus_domains if domain in priority],
        *[domain for domain in priority if domain not in focus_domains],
    ]
    for domain in ordered_domains:
        payload = domain_readings.get(domain, {})
        if not isinstance(payload, dict):
            continue
        cards.append(
            {
                "domain": domain,
                "label": term_label(locale, domain),
                "state": str(payload.get("state") or "review"),
                "summary": str(payload.get("summary") or ""),
                "customer_takeaway": str(payload.get("customer_takeaway") or ""),
                "diagnosis_summary": str(payload.get("diagnosis_summary") or payload.get("summary") or ""),
                "diagnosis_claims": _customer_diagnosis_claims(payload.get("diagnosis_claims", [])),
                "diagnosis_paths": _customer_diagnosis_paths(payload.get("diagnosis_paths", [])),
                "core_claim_quality": _customer_core_claim_quality(payload.get("core_claim_quality", {})),
                "path_summary": _domain_card_path_summary(payload.get("diagnosis_paths", [])),
                "path_assertions": _domain_card_path_assertions(payload.get("diagnosis_paths", [])),
                "portrait_dimensions": _customer_portrait_dimensions(payload.get("portrait_dimensions", [])),
                "action_prompt": str(payload.get("action_prompt") or ""),
                "priority_score": float(payload.get("priority_score", 0.0)),
                "timing_status": _nested(payload, "timing_trigger", "status", default=""),
                "boundary": "domain_card_is_customer_projection_not_internal_bazi_context",
            }
        )
    return cards


def _customer_summary_title(
    runtime: CoreRuntimeResult,
    domain_cards: list[dict[str, object]],
    *,
    locale: str,
    diagnostic: bool,
) -> str:
    if diagnostic:
        return runtime.mainline_state.title
    if locale == "en":
        return "Chart calculated, ready for structured reading"
    if locale == "ko":
        return "명식 계산 완료, 구조와 상담 주제를 확인할 수 있습니다"
    domains = "、".join(str(row.get("label") or row.get("domain") or "") for row in domain_cards[:3] if row)
    return f"命盘已排好，可以先看{domains or '结构与重点问题'}"


def _primary_message(domain_cards: list[dict[str, object]], *, locale: str, final_synthesis: dict[str, object] | None = None) -> str:
    final_synthesis = final_synthesis if isinstance(final_synthesis, dict) else {}
    customer_summary = str(final_synthesis.get("customer_summary") or "")
    if customer_summary:
        return customer_summary
    if not domain_cards:
        if locale == "en":
            return "The reading will first confirm the most useful question, then expand into concrete areas."
        if locale == "ko":
            return "먼저 가장 중요한 질문을 확인한 뒤 구체 영역으로 이어갑니다."
        return "当前会先确认最值得看的问题，再展开具体领域。"
    first = domain_cards[0]
    label_text = str(first.get("label") or first.get("domain") or "重点领域")
    if locale == "en":
        return f"{label_text} is currently a priority area. The system will explain it through evidence-backed candidate paths, not fixed verdicts."
    if locale == "ko":
        return f"현재 {label_text} 영역을 우선 볼 수 있습니다. 단정이 아니라 근거가 있는 후보 경로로 설명합니다."
    summary = str(first.get("diagnosis_summary") or first.get("summary") or "")
    if summary:
        return summary
    return f"当前优先看{label_text}。系统会结合命盘结构、十神、五行和时间层来分析，但只作为有依据的候选判断，不直接下绝对断语。"


def _customer_final_synthesis(final_synthesis: dict[str, object]) -> dict[str, object]:
    if not isinstance(final_synthesis, dict) or not final_synthesis:
        return {}
    return {
        "version": str(final_synthesis.get("version") or ""),
        "status": str(final_synthesis.get("status") or ""),
        "primary_domain": str(final_synthesis.get("primary_domain") or ""),
        "focus_domains": [str(row) for row in final_synthesis.get("focus_domains", []) if row] if isinstance(final_synthesis.get("focus_domains"), list) else [],
        "conclusion": str(final_synthesis.get("conclusion") or ""),
        "advice": str(final_synthesis.get("advice") or ""),
        "customer_summary": str(final_synthesis.get("customer_summary") or ""),
        "decision_engine": _customer_decision_engine_summary(final_synthesis.get("decision_engine", {})),
        "decision_verdicts": _customer_decision_verdicts(final_synthesis.get("decision_verdicts", [])),
        "decision_focus": str(_nested(final_synthesis, "synthesis_blueprint", "decision_focus", default="")),
        "assertion_level": str(_nested(final_synthesis, "synthesis_blueprint", "assertion_level", default="")),
        "allowed_assertions": [
            str(row)
            for row in _nested(final_synthesis, "synthesis_blueprint", "allowed_assertions", default=[])
            if row
        ][:3] if isinstance(_nested(final_synthesis, "synthesis_blueprint", "allowed_assertions", default=[]), list) else [],
        "action_steps": [
            str(row)
            for row in _nested(final_synthesis, "synthesis_blueprint", "action_steps", default=[])
            if row
        ][:3] if isinstance(_nested(final_synthesis, "synthesis_blueprint", "action_steps", default=[]), list) else [],
        "risk_boundary": str(_nested(final_synthesis, "synthesis_blueprint", "risk_boundary", default="")),
        "evidence_chain": [
            {
                "domain": str(row.get("domain") or ""),
                "score": row.get("score"),
                "evidence": [str(item) for item in row.get("evidence", []) if item] if isinstance(row.get("evidence"), list) else [],
                "boundary": "customer_final_synthesis_evidence_is_summary_not_raw_trace",
            }
            for row in final_synthesis.get("evidence_chain", [])
            if isinstance(row, dict)
        ][:4] if isinstance(final_synthesis.get("evidence_chain"), list) else [],
        "visual_hint": _customer_final_synthesis_visual_hint(final_synthesis.get("visual_hint", {})),
        "quality_judge": _customer_final_synthesis_quality_judge(final_synthesis.get("brain_judge", {})),
        "quality_contract": {
            "conclusion_first": bool(_nested(final_synthesis, "quality_contract", "conclusion_first", default=True)),
            "advice_actionable": bool(_nested(final_synthesis, "quality_contract", "advice_actionable", default=True)),
            "uses_decision_verdicts": bool(_nested(final_synthesis, "quality_contract", "uses_decision_verdicts", default=False)),
            "brain_judge_accepted": bool(_nested(final_synthesis, "quality_contract", "brain_judge_accepted", default=False)),
            "chart_fact_mutation_allowed": False,
        },
        "boundary": "customer_final_synthesis_is_central_brain_output_not_llm_or_chart_fact_mutation",
    }


def _decision_feedback_projection(central: object, *, role_key: str) -> dict[str, object]:
    central_dict = central if isinstance(central, dict) else {}
    summary = central_dict.get("decision_feedback_recalculation_summary", {})
    summary = summary if isinstance(summary, dict) else {}
    if not summary:
        return {}
    diagnostic = role_key in DIAGNOSTIC_ROLES
    affected_domains = [
        str(row)
        for row in summary.get("affected_domains", [])
        if row
    ][:6] if isinstance(summary.get("affected_domains"), list) else []
    base = {
        "version": str(summary.get("version") or ""),
        "feedback_applied": bool(summary.get("feedback_applied")),
        "visible_detail_level": "diagnostic" if diagnostic else "customer_summary",
        "affected_verdict_count": len(summary.get("affected_verdict_ids", [])) if isinstance(summary.get("affected_verdict_ids"), list) else 0,
        "affected_domains": affected_domains if diagnostic else [],
        "status_text": "本轮反馈已进入裁决校准。" if summary.get("feedback_applied") else "当前暂无反馈校准。",
        "chart_fact_mutation_allowed": False,
        "boundary": "decision_feedback_projection_shows_feedback_recalculation_without_mutating_chart_facts",
    }
    if not diagnostic:
        return base
    admin_projection = summary.get("admin_training_projection", {})
    admin_projection = admin_projection if isinstance(admin_projection, dict) else {}
    return {
        **base,
        "effect_count": int(_bounded_float(summary.get("effect_count"), 0.0)),
        "question_outcome_count": int(_bounded_float(summary.get("question_outcome_count"), 0.0)),
        "practitioner_selection_count": int(_bounded_float(summary.get("practitioner_selection_count"), 0.0)),
        "affected_candidate_ids": [
            str(row)
            for row in summary.get("affected_candidate_ids", [])
            if row
        ][:8] if isinstance(summary.get("affected_candidate_ids"), list) else [],
        "affected_claim_ids": [
            str(row)
            for row in summary.get("affected_claim_ids", [])
            if row
        ][:8] if isinstance(summary.get("affected_claim_ids"), list) else [],
        "affected_verdict_ids": [
            str(row)
            for row in summary.get("affected_verdict_ids", [])
            if row
        ][:8] if isinstance(summary.get("affected_verdict_ids"), list) else [],
        "score_adjustments": [
            {
                "candidate_id": str(row.get("candidate_id") or ""),
                "claim_id": str(row.get("claim_id") or ""),
                "domain": str(row.get("domain") or ""),
                "score_delta": _bounded_float(row.get("score_delta"), 0.0),
                "confidence_after_feedback": _bounded_float(row.get("confidence_after_feedback"), 0.0),
                "boundary": "score_adjustment_is_feedback_weight_trace_not_chart_fact",
            }
            for row in summary.get("score_adjustments", [])
            if isinstance(row, dict)
        ][:8] if isinstance(summary.get("score_adjustments"), list) else [],
        "admin_training_projection": {
            "version": str(admin_projection.get("version") or ""),
            "trainable": bool(admin_projection.get("trainable")),
            "targets": [
                str(row)
                for row in admin_projection.get("targets", [])
                if row
            ][:8] if isinstance(admin_projection.get("targets"), list) else [],
            "blocked_targets": [
                str(row)
                for row in admin_projection.get("blocked_targets", [])
                if row
            ][:8] if isinstance(admin_projection.get("blocked_targets"), list) else [],
            "boundary": "admin_training_projection_is_diagnostic_feedback_trace_not_policy_promotion",
        },
    }


def _decision_workbench_projection(central: object, *, role_key: str) -> dict[str, object]:
    return build_decision_workbench_product_surface(central, role_key=role_key)


def _decision_workbench_verdict_cards(
    verdicts: list[dict[str, object]],
    *,
    diagnostic: bool,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    limit = 8 if diagnostic else 5
    for verdict in verdicts[:limit]:
        allowed = [str(row) for row in _as_list(verdict.get("allowed_assertions")) if str(row)][:2]
        advice = [str(row) for row in _as_list(verdict.get("advice_points")) if str(row)][:2]
        rows.append(
            {
                "verdict_id": str(verdict.get("verdict_id") or ""),
                "domain": str(verdict.get("domain") or ""),
                "domain_label": _domain_label(str(verdict.get("domain") or "")),
                "headline": str(verdict.get("headline") or ""),
                "assertion_level": str(verdict.get("assertion_level") or ""),
                "confidence": _bounded_float(verdict.get("confidence"), 0.0),
                "primary_text": allowed[0] if allowed else str(verdict.get("headline") or ""),
                "advice_points": advice,
                "has_alternative_branch": bool(_as_list(verdict.get("alternative_branch_ids"))),
                "next_question_count": len(_as_list(verdict.get("next_question_slots"))),
                "evidence_count": len(_as_list(verdict.get("evidence_refs"))),
                "counter_evidence_count": len(_as_list(verdict.get("counter_evidence_refs"))),
                "diagnostic_trace": _decision_workbench_trace(verdict) if diagnostic else {},
                "boundary": "decision_workbench_verdict_card_is_verdict_projection_not_llm_or_raw_signal",
            }
        )
    return rows


def _decision_workbench_trace(verdict: dict[str, object]) -> dict[str, object]:
    trace = verdict.get("trace", {})
    trace = trace if isinstance(trace, dict) else {}
    conflict = trace.get("conflict_resolver", {})
    conflict = conflict if isinstance(conflict, dict) else {}
    return {
        "source_candidate_id": str(trace.get("source_candidate_id") or ""),
        "source_claim_id": str(trace.get("source_claim_id") or ""),
        "candidate_signal_count": len(_as_list(trace.get("source_signal_ids"))),
        "conflict_count": _int_count(conflict.get("conflict_count")),
        "top_source_signal_count": _int_count(conflict.get("top_source_signal_count")),
        "score_mutation_allowed": False,
        "chart_fact_mutation_allowed": False,
        "boundary": "diagnostic_trace_is_role_gated_and_read_only",
    }


def _decision_workbench_conflict_cards(
    audits: list[dict[str, object]],
    *,
    diagnostic: bool,
) -> list[dict[str, object]]:
    cards: list[dict[str, object]] = []
    for audit in audits:
        conflict_count = _int_count(audit.get("conflict_count"))
        if conflict_count <= 0:
            continue
        conflict_types = [str(row) for row in _as_list(audit.get("conflict_types")) if str(row)]
        card = {
            "domain": str(audit.get("domain") or ""),
            "domain_label": _domain_label(str(audit.get("domain") or "")),
            "conflict_count": conflict_count,
            "conflict_types": [_conflict_type_label(row) for row in conflict_types[:3]],
            "top_candidate_id": str(audit.get("top_candidate_id") or "") if diagnostic else "",
            "top_confidence": _bounded_float(audit.get("top_confidence"), 0.0),
            "runner_up_confidence": _bounded_float(audit.get("runner_up_confidence"), 0.0),
            "confidence_gap": _bounded_float(audit.get("confidence_gap"), 0.0),
            "needed_question": str(audit.get("needed_question") or ""),
            "resolution_policy": _resolution_policy_label(str(audit.get("resolution_policy") or "")),
            "signal_bound_candidate_count": _int_count(audit.get("signal_bound_candidate_count")) if diagnostic else 0,
            "candidate_signal_count": _int_count(audit.get("candidate_signal_count")) if diagnostic else 0,
            "boundary": "decision_workbench_conflict_card_preserves_branch_uncertainty_without_forcing_verdict",
        }
        cards.append(card)
    return cards[:8 if diagnostic else 4]


def _conflict_type_label(value: str) -> str:
    labels = {
        "close_branch_probability": "分支权重接近",
        "requires_calibration": "需要校准",
        "counter_evidence_present": "存在反证",
    }
    return labels.get(value, value or "冲突")


def _resolution_policy_label(value: str) -> str:
    if not value:
        return "保留分支，等待更多证据。"
    if "keep_both_branches" in value:
        return "主分支和备选先同时保留，等待命理师或用户反馈拉开权重。"
    if "ask_only_if_value" in value:
        return "只有问题信息增益足够时才追问，避免打扰用户。"
    if "downgrade_assertion" in value:
        return "反证未解决前降低断语强度。"
    policies = [part.strip() for part in value.split(";") if part.strip()]
    if len(policies) > 1:
        return "；".join(_resolution_policy_label(part) for part in policies)
    return value


def _customer_decision_engine_summary(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or not value:
        return {}
    return {
        "version": str(value.get("version") or ""),
        "status": str(value.get("status") or ""),
        "engine_version": str(value.get("engine_version") or ""),
        "uses_decision_verdicts": bool(value.get("uses_decision_verdicts")),
        "verdict_count": int(_bounded_float(value.get("verdict_count"), 0.0)),
        "llm_expression_only": bool(value.get("llm_expression_only")),
        "chart_fact_mutation_allowed": False,
        "boundary": "customer_decision_engine_summary_hides_internal_weights_and_preserves_verdict_boundary",
    }


def _customer_decision_verdicts(value: object) -> list[dict[str, object]]:
    verdicts = value if isinstance(value, list) else []
    rows: list[dict[str, object]] = []
    for row in verdicts[:4]:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "verdict_id": str(row.get("verdict_id") or ""),
                "domain": str(row.get("domain") or ""),
                "headline": str(row.get("headline") or ""),
                "assertion_level": str(row.get("assertion_level") or ""),
                "confidence": _bounded_float(row.get("confidence"), 0.0),
                "allowed_assertions": [str(item) for item in row.get("allowed_assertions", []) if item][:2] if isinstance(row.get("allowed_assertions"), list) else [],
                "advice_points": [str(item) for item in row.get("advice_points", []) if item][:2] if isinstance(row.get("advice_points"), list) else [],
                "has_next_question_slot": bool(row.get("next_question_slots")),
                "boundary": "customer_decision_verdict_is_public_projection_of_decision_engine_not_llm_text",
            }
        )
    return rows


def _customer_final_synthesis_quality_judge(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or not value:
        return {}
    scores = value.get("scores", {})
    scores = scores if isinstance(scores, dict) else {}
    return {
        "version": str(value.get("version") or ""),
        "accepted": bool(value.get("accepted")),
        "quality_score": _bounded_float(value.get("quality_score"), 0.0),
        "scores": {
            "evidence_binding": _bounded_float(scores.get("evidence_binding"), 0.0),
            "conclusion_strength": _bounded_float(scores.get("conclusion_strength"), 0.0),
            "advice_actionability": _bounded_float(scores.get("advice_actionability"), 0.0),
            "template_risk": _bounded_float(scores.get("template_risk"), 0.0),
            "overclaim_risk": _bounded_float(scores.get("overclaim_risk"), 0.0),
        },
        "failure_count": len(value.get("failures", [])) if isinstance(value.get("failures"), list) else 0,
        "reason_codes": [str(row) for row in value.get("reason_codes", []) if row][:5] if isinstance(value.get("reason_codes"), list) else [],
        "boundary": "customer_quality_judge_is_safe_summary_not_internal_judge_trace",
    }


def _customer_final_synthesis_visual_hint(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or not value:
        return {}
    markers = value.get("markers", [])
    return {
        "version": str(value.get("version") or ""),
        "kind": str(value.get("kind") or "advice_compass"),
        "title": str(value.get("title") or ""),
        "chips": [str(row) for row in value.get("chips", []) if row][:4] if isinstance(value.get("chips"), list) else [],
        "markers": [
            {
                "label": str(row.get("label") or ""),
                "value": _bounded_float(row.get("value"), 0.0),
            }
            for row in markers
            if isinstance(row, dict)
        ][:3] if isinstance(markers, list) else [],
        "guidance": str(value.get("guidance") or ""),
        "boundary": "customer_final_synthesis_visual_hint_is_structured_result_preview_not_raw_trace",
    }


def _customer_structure_dynamics(runtime: CoreRuntimeResult, *, role_key: str, locale: str) -> dict[str, object]:
    structure = runtime.structure_state
    path_scores = structure.path_scores if isinstance(structure.path_scores, dict) else {}
    paths = _dynamic_path_rows(structure.graph_nodes, detailed=role_key not in USER_VISIBLE_ROLES)
    dynamic_count = int(path_scores.get("dynamic_path_count", 0.0) or 0)
    conflict_count = int(path_scores.get("dynamic_conflict_family_count", 0.0) or 0)
    resolution_count = int(path_scores.get("dynamic_path_resolution_family_count", 0.0) or 0)
    tongguan_count = int(path_scores.get("dynamic_tongguan_path_count", 0.0) or 0)
    zhihua_count = int(path_scores.get("dynamic_zhihua_path_count", 0.0) or 0)
    summary_parts = []
    if dynamic_count:
        summary_parts.append(f"已形成 {dynamic_count} 条结构动态路径")
    if resolution_count:
        summary_parts.append(f"{resolution_count} 类通关/承接线索")
    if conflict_count:
        summary_parts.append(f"{conflict_count} 类冲突压力线索")
    summary = "，".join(summary_parts) or "当前结构动态仍以原局证据和后续问答继续校准。"
    emphasis = _structure_emphasis(tongguan_count=tongguan_count, zhihua_count=zhihua_count, conflict_count=conflict_count)
    return {
        "version": "v30.structure_dynamics_surface.v1",
        "label": term_label(locale, "structure_dynamic"),
        "state": structure.state,
        "semantic_label": _customer_structure_label(structure.semantic_label),
        "summary": summary,
        "emphasis": emphasis,
        "dynamic_path_count": dynamic_count,
        "conflict_family_count": conflict_count,
        "resolution_family_count": resolution_count,
        "domain_path_counts": {
            "wealth": int(path_scores.get("dynamic_wealth_path_count", 0.0) or 0),
            "career": int(path_scores.get("dynamic_career_path_count", 0.0) or 0),
            "relationship": int(path_scores.get("dynamic_relationship_path_count", 0.0) or 0),
            "health": int(path_scores.get("dynamic_health_review_path_count", 0.0) or 0),
            "useful_god": int(path_scores.get("dynamic_useful_god_candidate_path_count", 0.0) or 0),
        },
        "mechanism_counts": {
            "tongguan": tongguan_count,
            "zhihua": zhihua_count,
            "resource_mediation": int(path_scores.get("dynamic_tongguan_resource_mediator_path_count", 0.0) or 0),
            "output_wealth_bridge": int(path_scores.get("dynamic_tongguan_output_wealth_bridge_path_count", 0.0) or 0),
            "wealth_authority_resource": int(path_scores.get("dynamic_zhihua_wealth_authority_resource_path_count", 0.0) or 0),
        },
        "top_paths": paths,
        "visible_detail_level": "diagnostic" if role_key not in USER_VISIBLE_ROLES else "customer_summary",
        "boundary": "structure_dynamics_projects_m3_dynamic_paths_as_reading_context_not_fixed_geju_or_event_verdict",
    }


def _diagnosis_overview(runtime: CoreRuntimeResult) -> str:
    diagnosis = runtime.question_plan.policy_effect.get("real_bazi_diagnosis", {})
    projection = diagnosis.get("public_projection", {}) if isinstance(diagnosis, dict) else {}
    return str(projection.get("diagnosis_overview") or "") if isinstance(projection, dict) else ""


def _customer_diagnosis_claims(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    rows: list[dict[str, object]] = []
    for row in value[:5]:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "claim_id": str(row.get("claim_id") or ""),
                "claim_level": str(row.get("claim_level") or ""),
                "claim_text": str(row.get("claim_text") or ""),
                "confidence_band": str(row.get("confidence_band") or ""),
                "needs_user_calibration": bool(row.get("needs_user_calibration", False)),
                "boundary": "diagnosis_claim_customer_projection_is_bounded_not_raw_trace",
            }
        )
    return rows


def _customer_core_claim_quality(value: object) -> dict[str, object]:
    payload = value if isinstance(value, dict) else {}
    return {
        "version": str(payload.get("version") or ""),
        "source": str(payload.get("source") or ""),
        "summary_ready": bool(payload.get("summary_ready")),
        "quality_ready": bool(payload.get("quality_ready")),
        "uses_traceable_claims": bool(payload.get("uses_traceable_claims")),
        "diagnosis_claim_count": int(payload.get("diagnosis_claim_count", 0) or 0),
        "diagnosis_path_count": int(payload.get("diagnosis_path_count", 0) or 0),
        "portrait_dimension_count": int(payload.get("portrait_dimension_count", 0) or 0),
        "generic_language_hits": [
            str(row)
            for row in payload.get("generic_language_hits", [])
            if str(row)
        ] if isinstance(payload.get("generic_language_hits"), list) else [],
        "fixed_event_prediction_allowed": bool(payload.get("fixed_event_prediction_allowed", False)),
        "chart_fact_mutation_allowed": bool(payload.get("chart_fact_mutation_allowed", False)),
        "boundary": "core_claim_quality_customer_projection_exposes_quality_flags_not_internal_trace",
    }


def _customer_diagnosis_paths(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    rows: list[dict[str, object]] = []
    for row in value[:4]:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "path_id": str(row.get("path_id") or ""),
                "mechanism": str(row.get("mechanism") or ""),
                "diagnosis_statement": str(row.get("diagnosis_statement") or ""),
                "risk_statement": str(row.get("risk_statement") or ""),
                "boundary": "diagnosis_path_customer_projection_not_fixed_event",
            }
        )
    return rows


def _domain_card_path_summary(value: object) -> str:
    paths = _customer_diagnosis_paths(value)
    if not paths:
        return ""
    first = paths[0]
    mechanism = str(first.get("mechanism") or "路径")
    statement = str(first.get("diagnosis_statement") or "")
    meaning = _path_practical_meaning(statement, mechanism)
    return f"{mechanism}：{meaning}" if meaning else mechanism


def _domain_card_path_assertions(value: object) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in _customer_diagnosis_paths(value)[:3]:
        mechanism = str(path.get("mechanism") or "")
        rows.append(
            {
                "path_id": str(path.get("path_id") or ""),
                "path_label": mechanism or "八字路径",
                "assertion": _path_practical_meaning(str(path.get("diagnosis_statement") or ""), mechanism),
                "uncertainty_boundary": str(path.get("risk_statement") or ""),
                "boundary": "domain_card_path_assertion_is_bounded_reading_not_event_verdict",
            }
        )
    return rows


def _customer_portrait_dimensions(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    rows: list[dict[str, object]] = []
    for row in value[:4]:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "portrait_id": str(row.get("portrait_id") or ""),
                "dimension": str(row.get("dimension") or ""),
                "statement": str(row.get("statement") or ""),
                "confidence_band": str(row.get("confidence_band") or ""),
                "boundary": "diagnosis_portrait_customer_projection_not_personality_fact",
            }
        )
    return rows


def _bazi_path_rows(runtime: CoreRuntimeResult, *, detailed: bool) -> list[dict[str, object]]:
    return _dynamic_path_rows(runtime.structure_state.graph_nodes, detailed=detailed)


def _path_chain_label(family_chain: list[str]) -> str:
    return " → ".join(_family_label(item) for item in family_chain[:4]) or "八字路径"


def _path_why_active(family_chain: list[str], domains: list[str]) -> str:
    chain = _path_chain_label(family_chain)
    impacts = "、".join(_domain_label(domain) for domain in domains[:3] if domain)
    if impacts:
        return f"{chain}同时牵动{impacts}，因此进入当前测算主路径。"
    return f"{chain}已由结构动态证据触发，作为当前测算路径复核。"


def _path_practical_meaning(statement: str, mechanism: str) -> str:
    text = _clean_product_statement(statement)
    if mechanism == "官印相生":
        return "压力、规则或职责需要转成资质、凭证、学习能力或平台承接。"
    if mechanism == "财官印制化":
        return "财星不是单独看收入，而是先牵动责任与压力，再看资源、资质或平台如何承接。"
    if mechanism == "食伤生财":
        return "财富更依赖输出、技术、表达、方案或流量能否稳定转化。"
    if mechanism == "食伤制官杀":
        return "表达和行动力会触碰规则与权责边界，需要看压力处理和制度适配。"
    if "形成" in text:
        return text.split("形成", 1)[-1].strip("，。")
    return text


def _bazi_feature_rows(runtime: CoreRuntimeResult, *, detailed: bool) -> list[dict[str, object]]:
    diagnosis = runtime.question_plan.policy_effect.get("real_bazi_diagnosis", {})
    features = diagnosis.get("features", []) if isinstance(diagnosis, dict) else []
    if not isinstance(features, list):
        return []
    rows: list[dict[str, object]] = []
    for row in _rank_public_diagnosis_rows(features, id_key="feature_id"):
        if not isinstance(row, dict) or _skip_customer_diagnosis_row(row):
            continue
        payload: dict[str, object] = {
            "domain": str(row.get("domain") or "overview"),
            "label": _feature_label(row),
            "statement": _clean_product_statement(str(row.get("statement") or "")),
            "confidence_band": str(row.get("confidence_band") or ""),
            "evidence_labels": _feature_evidence_labels(row),
            "boundary": "bazi_feature_customer_projection_is_traceable_not_new_chart_fact",
        }
        if detailed:
            payload.update(
                {
                    "feature_id": str(row.get("feature_id") or ""),
                    "family": str(row.get("family") or ""),
                    "evidence_ids": _string_list(row.get("evidence_ids"))[:6],
                    "counter_notes": _string_list(row.get("counter_notes"))[:6],
                }
            )
        rows.append(payload)
    return rows[:8 if detailed else 5]


def _bazi_portrait_rows(runtime: CoreRuntimeResult, *, detailed: bool) -> list[dict[str, object]]:
    diagnosis = runtime.question_plan.policy_effect.get("real_bazi_diagnosis", {})
    portraits = diagnosis.get("portraits", []) if isinstance(diagnosis, dict) else []
    if not isinstance(portraits, list):
        return []
    rows: list[dict[str, object]] = []
    for row in _rank_public_diagnosis_rows(portraits, id_key="portrait_id"):
        if not isinstance(row, dict) or _skip_customer_diagnosis_row(row):
            continue
        payload: dict[str, object] = {
            "domain": str(row.get("domain") or "overview"),
            "dimension": str(row.get("dimension") or ""),
            "label": _portrait_label(row),
            "statement": _clean_product_statement(str(row.get("statement") or "")),
            "confidence_band": str(row.get("confidence_band") or ""),
            "evidence_labels": _portrait_evidence_labels(row),
            "boundary": "bazi_portrait_customer_projection_is_derived_reading_not_personality_fact",
        }
        if detailed:
            payload.update(
                {
                    "portrait_id": str(row.get("portrait_id") or ""),
                    "evidence_ids": _string_list(row.get("evidence_ids"))[:6],
                    "path_ids": _string_list(row.get("path_ids"))[:6],
                    "counter_notes": _string_list(row.get("counter_notes"))[:6],
                }
            )
        rows.append(payload)
    return rows[:8 if detailed else 5]


def _rank_public_diagnosis_rows(rows: list[object], *, id_key: str) -> list[object]:
    domain_rank = {
        "structure": 0,
        "useful_god": 1,
        "career": 2,
        "wealth": 3,
        "relationship": 4,
        "health": 5,
        "timing": 6,
        "hidden_factor": 7,
        "overview": 8,
    }
    confidence_rank = {"high": 0, "medium": 1, "low": 2}
    return sorted(
        rows,
        key=lambda row: (
            domain_rank.get(str(row.get("domain") or "overview"), 99) if isinstance(row, dict) else 99,
            confidence_rank.get(str(row.get("confidence_band") or "medium"), 1) if isinstance(row, dict) else 1,
            str(row.get(id_key) or "") if isinstance(row, dict) else "",
        ),
    )


def _skip_customer_diagnosis_row(row: dict[str, object]) -> bool:
    statement = str(row.get("statement") or "")
    family = str(row.get("family") or "")
    dimension = str(row.get("dimension") or "")
    skip_tokens = (
        "Use training",
        "policy weights",
        "Never hide",
        "不可改写的排盘事实",
        "不能重新生成四柱",
        "进入边界控制",
        "v30.krp.",
    )
    if any(token in statement for token in skip_tokens):
        return True
    return any(token in family or token in dimension for token in ("training", "policy_override", "silent_override"))


def _feature_label(row: dict[str, object]) -> str:
    domain = str(row.get("domain") or "")
    family = str(row.get("family") or "")
    if "strength_pattern" in family:
        return "旺衰格局特征"
    if "hidden_stem" in family:
        return "藏干十神特征"
    if "branch_relation" in family:
        return "地支关系特征"
    if "element" in family:
        return "五行分布特征"
    if "useful_god" in family or domain == "useful_god":
        return "用神候选特征"
    if domain in {"career", "wealth", "relationship", "health", "timing", "hidden_factor", "structure"}:
        return f"{_domain_label(domain)}特征"
    return "八字特征"


def _portrait_label(row: dict[str, object]) -> str:
    dimension = str(row.get("dimension") or "")
    if "wealth" in dimension:
        return "财务画像"
    if "authority" in dimension or "career" in dimension:
        return "事业画像"
    if "relationship" in dimension or "romance" in dimension:
        return "关系画像"
    if "health" in dimension:
        return "健康画像"
    if "useful_god" in dimension:
        return "用神画像"
    if "structure" in dimension or "pattern" in dimension:
        return "结构画像"
    return "命局画像"


def _feature_evidence_labels(row: dict[str, object]) -> list[str]:
    labels = [str(row.get("domain") or ""), str(row.get("confidence_band") or "")]
    family = str(row.get("family") or "")
    if family:
        labels.append(family.split(":")[0])
    return [label for label in labels if label][:4]


def _portrait_evidence_labels(row: dict[str, object]) -> list[str]:
    labels = [str(row.get("domain") or ""), str(row.get("confidence_band") or "")]
    dimension = str(row.get("dimension") or "")
    if dimension:
        labels.append(dimension)
    return [label for label in labels if label][:4]


def _clean_product_statement(value: str) -> str:
    text = value.strip()
    if text.endswith("进入structure诊断特征层，用于生成可追踪断语，不新增排盘事实。"):
        element = text.removesuffix("进入structure诊断特征层，用于生成可追踪断语，不新增排盘事实。")
        return f"五行{_element_label(element)}进入结构判断重点，可作为后续断语的证据之一。"
    if text.startswith("M3 来源复核显示"):
        return "M3 来源复核已把季节、五行强弱、知识库规则和调候线索合并到同一证据层。"
    if text.startswith("月令复核显示"):
        return "月令已经作为结构入口，但仍需结合反证、五行分布和动态路径一起判断。"
    if text.startswith("旺衰格局复核显示"):
        return "旺衰格局复核已纳入日主五行、季节、强弱元素和动态路径，当前只支持候选判断。"
    if text.startswith("藏干十神为"):
        return text.replace("，可作为隐藏因子与反复状态的放大线索，但需要问答校准。", "，可作为背景校准和反复状态的观察线索，仍需问答校准。")
    replacements = {
        "Name 格局 only as candidate until month-command support, counter-force, and path evidence are reviewed.": "格局只能按候选路径表达，需要月令、反证和动态路径共同支持。",
        "Use 格局 language only as candidate review language until supporting paths are validated.": "格局语言只能作为候选复核，需等待路径证据验证。",
        "Frame resource mediation as a path-resolution candidate and keep final resolution evidence-bound.": "印星通关只作为路径承接候选，最终仍要看证据链。",
        "Separate relation type, involved branches, transformation support, interference, and source layer.": "地支关系要分清类型、涉及地支、化合条件、干扰和来源层。",
        "Name branch conflict families only as reviewed dynamics, never as isolated event predictions.": "地支冲刑只作为结构动态复核，不单独推出事件。",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    if " 该画像维度由规则" in text:
        text = text.split(" 该画像维度由规则", 1)[0]
    return text


def _domain_label(domain: str) -> str:
    labels = {
        "overview": "总览",
        "structure": "结构",
        "useful_god": "用神",
        "career": "事业",
        "wealth": "财务",
        "relationship": "关系",
        "health": "健康",
        "timing": "时间",
        "hidden_factor": "校准线索",
    }
    return labels.get(domain, domain)


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(row) for row in value if row]


def _diagnosis_path_rows(runtime: CoreRuntimeResult, *, detailed: bool) -> list[dict[str, object]]:
    diagnosis = runtime.question_plan.policy_effect.get("real_bazi_diagnosis", {})
    projection = diagnosis.get("public_projection", {}) if isinstance(diagnosis, dict) else {}
    domain_paths = projection.get("domain_paths", {}) if isinstance(projection, dict) else {}
    if not isinstance(domain_paths, dict):
        return []
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for domain in ("structure", "wealth", "career", "relationship", "health", "useful_god"):
        values = domain_paths.get(domain, [])
        if not isinstance(values, list):
            continue
        for row in values:
            if not isinstance(row, dict):
                continue
            path_id = str(row.get("path_id") or "")
            if not path_id or path_id in seen:
                continue
            seen.add(path_id)
            payload = {
                "path_id": path_id,
                "mechanism": str(row.get("mechanism") or ""),
                "diagnosis_statement": str(row.get("diagnosis_statement") or ""),
                "risk_statement": str(row.get("risk_statement") or ""),
                "summary": str(row.get("diagnosis_statement") or ""),
                "boundary": "diagnosis_path_projects_rbd_structure_path_not_fixed_event",
            }
            if detailed:
                payload["domain"] = domain
            rows.append(payload)
    return rows[:6 if detailed else 3]


def _dynamic_path_rows(nodes: list[dict[str, object]], *, detailed: bool) -> list[dict[str, object]]:
    paths = [
        row for row in nodes
        if isinstance(row, dict) and row.get("kind") == "dynamic_path"
    ]
    paths.sort(key=lambda row: float(row.get("score", 0.0) or 0.0), reverse=True)
    limit = 6 if detailed else 3
    rows: list[dict[str, object]] = []
    for row in paths[:limit]:
        family_chain = row.get("family_chain", [])
        family_chain = family_chain if isinstance(family_chain, list) else []
        resolution = row.get("resolution_families", [])
        resolution = resolution if isinstance(resolution, list) else []
        conflicts = row.get("conflict_families", [])
        conflicts = conflicts if isinstance(conflicts, list) else []
        payload = {
            "path_id": str(row.get("node_id") or ""),
            "path_label": _path_chain_label([str(item) for item in family_chain]),
            "chain": [_family_label(str(item)) for item in family_chain],
            "path_chain": [_family_label(str(item)) for item in family_chain],
            "state": str(row.get("path_state") or ""),
            "strength_band": _path_strength_band(float(row.get("score", 0.0) or 0.0)),
            "confidence_band": _path_strength_band(float(row.get("score", 0.0) or 0.0)),
            "resolution_labels": [_resolution_label(str(item)) for item in resolution[:4]],
            "conflict_labels": [_resolution_label(str(item)) for item in conflicts[:3]],
            "summary": _dynamic_path_summary(family_chain, resolution, conflicts),
            "meaning": _dynamic_path_meaning(family_chain, resolution, conflicts),
            "diagnosis_statement": _dynamic_path_meaning(family_chain, resolution, conflicts),
            "why_active": _dynamic_path_why_active(family_chain, resolution, conflicts),
            "domain_impact": _dynamic_path_domain_impact(family_chain, resolution),
            "uncertainty_boundary": _dynamic_path_uncertainty(row),
            "boundary": "dynamic_path_is_context_for_structure_review_not_final_verdict",
        }
        if detailed:
            payload["competition_rank"] = row.get("competition_rank", None)
            payload["suppression_band"] = _suppression_band(float(row.get("suppression", 0.0) or 0.0))
            payload["score"] = round(float(row.get("score", 0.0) or 0.0), 3)
            payload["blocked_overclaim"] = ["动态路径只作为结构判断路径，不直接生成固定事件。"]
        rows.append(payload)
    return rows


def _customer_structure_label(label: str) -> str:
    if not label:
        return "结构动态已进入复核路径。"
    lowered = label.lower()
    if "evidence-bound" in lowered or "counter-evidence" in lowered or "mechanism paths scored" in lowered:
        return "结构主线已按证据链、反证和做功路径进入复核。"
    if "branch relations require dynamic review" in label:
        return "地支关系已触发结构动态复核。"
    if "dynamic" in label:
        return "结构动态路径已进入当前测算主线。"
    return "结构判断以证据链和候选路径为准。"


def _structure_emphasis(*, tongguan_count: int, zhihua_count: int, conflict_count: int) -> str:
    if tongguan_count and zhihua_count:
        return "通关与制化路径都需要一起看。"
    if tongguan_count:
        return "重点看通关承接路径。"
    if zhihua_count:
        return "重点看制化转换路径。"
    if conflict_count:
        return "重点看冲突压力与反证。"
    return "重点看证据链是否足够支撑格局候选。"


def _dynamic_path_summary(family_chain: list[object], resolution: list[object], conflicts: list[object]) -> str:
    chain = " → ".join(_family_label(str(item)) for item in family_chain[:4]) or "结构路径"
    if resolution:
        return f"{chain}，{_resolution_label(str(resolution[0]))}。"
    if conflicts:
        return f"{chain}，存在{_resolution_label(str(conflicts[0]))}。"
    return f"{chain}，作为结构复核线索。"


def _dynamic_path_meaning(family_chain: list[object], resolution: list[object], conflicts: list[object]) -> str:
    chain = [str(item) for item in family_chain]
    chain_label = " → ".join(_family_label(item) for item in chain[:4])
    resolution_key = str(resolution[0]) if resolution else ""
    conflict_key = str(conflicts[0]) if conflicts else ""
    if resolution_key == "zhihua_wealth_authority_resource":
        return "财星牵动官杀压力，再由印星或资源承接，适合看资源、资质、平台和责任的转化。"
    if resolution_key == "tongguan_resource_mediator":
        return "印星在冲突之间起承接作用，压力更容易转成学习、凭证、规则或平台支持。"
    if resolution_key == "tongguan_output_wealth_bridge":
        return "食伤把能力、表达或方案转成财星机会，重点看输出能否稳定变现。"
    if resolution_key == "zhihua_output_authority_resource":
        return "食伤触碰规则压力后转向印星承接，适合看专业表达、制度适配和资质沉淀。"
    if {"wealth", "authority", "resource"} <= set(chain):
        return "财、官、印连续牵动，收益、责任和资源需要一起看。"
    if {"output", "wealth"} <= set(chain):
        return "食伤与财星相连，表达、技术、方案或流量是财运入口。"
    if conflict_key:
        return f"路径中有{_resolution_label(conflict_key)}，判断时要看压力如何被承接。"
    if chain_label:
        return f"{chain_label}形成当前结构路径，需看财星、官杀、印星或食伤之间的流动、受阻与承接。"
    return "财星、官杀、印星或食伤之间的流动进入结构动态复核。"


def _dynamic_path_why_active(family_chain: list[object], resolution: list[object], conflicts: list[object]) -> str:
    chain = " → ".join(_family_label(str(item)) for item in family_chain[:4]) or "结构路径"
    if resolution:
        return f"{chain}出现{_resolution_label(str(resolution[0]))}，因此进入当前结构动态。"
    if conflicts:
        return f"{chain}出现{_resolution_label(str(conflicts[0]))}，需要观察承接方式。"
    return f"{chain}由原局十神与地支关系共同触发。"


def _dynamic_path_domain_impact(family_chain: list[object], resolution: list[object]) -> list[str]:
    keys = {str(item) for item in family_chain}
    resolution_keys = {str(item) for item in resolution}
    domains: list[str] = []
    if "wealth" in keys:
        domains.append("财运")
    if "authority" in keys or "resource" in keys:
        domains.append("事业")
    if {"wealth", "authority"} & keys:
        domains.append("关系")
    if resolution_keys or {"authority", "output"} & keys:
        domains.append("用神")
    if not domains:
        domains.append("结构")
    return domains[:4]


def _dynamic_path_uncertainty(row: dict[str, object]) -> str:
    state = str(row.get("path_state") or "")
    if state == "blocked":
        return "路径有受阻点，需看大运流年是否打开承接。"
    if state == "conflict":
        return "路径有冲突压力，需看通关或制化是否成立。"
    if state == "countered":
        return "路径存在反向证据，断语应以主次强弱区分。"
    return "路径用于结构判断，不单独推出具体事件。"


def _family_label(value: str) -> str:
    labels = {
        "self": "比劫",
        "output": "食伤",
        "wealth": "财星",
        "authority": "官杀",
        "resource": "印星",
        "day_master": "日主",
    }
    return labels.get(value, value)


def _resolution_label(value: str) -> str:
    labels = {
        "reaches_day_master": "回到日主",
        "resource_support_path": "印星承接",
        "tongguan_resource_mediator": "印星通关",
        "tongguan_output_wealth_bridge": "食伤生财桥",
        "zhihua_wealth_authority_resource": "财官印制化",
        "zhihua_control_to_generation": "克转生的制化",
        "zhihua_output_authority_resource": "食伤制官转印",
        "generate_control_sequence": "生克连续",
        "control_pressure": "克制压力",
    }
    return labels.get(value, value)


def _path_strength_band(score: float) -> str:
    if score >= 0.78:
        return "high"
    if score >= 0.62:
        return "medium"
    return "low"


def _suppression_band(value: float) -> str:
    if value >= 0.12:
        return "high"
    if value > 0:
        return "medium"
    return "none"


def _core_bazi_reading(runtime: CoreRuntimeResult, domain_cards: list[dict[str, object]]) -> dict[str, object]:
    natal = runtime.chart_context.natal_pillars if isinstance(runtime.chart_context.natal_pillars, dict) else {}
    ranked = runtime.question_plan.policy_effect.get("ranked_decisions", {})
    if not isinstance(ranked, dict):
        ranked = {}
    model_summary = runtime.question_plan.policy_effect.get("model_signal_summary", {})
    if not isinstance(model_summary, dict):
        model_summary = {}
    return {
        "version": "v30.core_bazi_reading.v1",
        "surface_type": "core_bazi_calculation",
        "chart_build": runtime.chart_context.input_pillars.get("chart_build_source", {}),
        "fact_integrity": _core_fact_integrity(runtime),
        "day_master": runtime.chart_context.day_master,
        "day_master_element": runtime.chart_context.day_master_element,
        "base_fact_summary": natal.get("base_fact_summary", {}) if isinstance(natal.get("base_fact_summary"), dict) else {},
        "base_fact_explanations": _base_fact_explanations(runtime, natal),
        "m1_m2_completion_summary": _m1_m2_completion_summary(runtime, natal),
        "basic_assertions": _basic_assertions(runtime, natal, ranked),
        "four_pillars": _pillar_rows(natal.get("pillars", {})),
        "visible_ten_gods": _visible_ten_god_rows(natal.get("visible_ten_gods", [])),
        "hidden_ten_gods": _hidden_ten_god_rows(natal.get("hidden_ten_gods", [])),
        "five_elements": natal.get("element_distribution", {}) if isinstance(natal.get("element_distribution"), dict) else {},
        "relations": _relation_rows(natal.get("relation_hits", [])),
        "time_context": _customer_time_context(runtime),
        "latent_bazi_attributes": _customer_latent_bazi_attributes(runtime),
        "ranked_decisions": _customer_ranked_decisions(ranked),
        "model_signal_summary": _customer_model_signal_summary(model_summary),
        "practical_domains": [
            {
                "domain": str(card.get("domain") or ""),
                "label": str(card.get("label") or ""),
                "summary": str(card.get("summary") or ""),
                "customer_takeaway": str(card.get("customer_takeaway") or ""),
            }
            for card in domain_cards
        ],
        "boundary": "core_bazi_reading_projects_calculation_result_before_questions_without_exposing_internal_diagnostics",
    }


def _customer_latent_bazi_attributes(runtime: CoreRuntimeResult) -> dict[str, object]:
    attrs = runtime.question_plan.policy_effect.get("latent_bazi_attributes", {})
    attrs = attrs if isinstance(attrs, dict) else {}
    summary = runtime.question_plan.policy_effect.get("latent_bazi_attributes_summary", {})
    summary = summary if isinstance(summary, dict) else {}
    global_attrs = attrs.get("global_attributes", {})
    global_attrs = global_attrs if isinstance(global_attrs, dict) else {}
    domain_biases = attrs.get("domain_biases", {})
    domain_biases = domain_biases if isinstance(domain_biases, dict) else {}
    ten_god_modifiers = attrs.get("ten_god_modifiers", {})
    ten_god_modifiers = ten_god_modifiers if isinstance(ten_god_modifiers, dict) else {}
    stability_thresholds = attrs.get("stability_thresholds", {})
    stability_thresholds = stability_thresholds if isinstance(stability_thresholds, dict) else {}
    return {
        "version": "v30.latent_bazi_attributes.customer_projection.v1",
        "display_mode": "debug_raw_values",
        "debug_temporary_remove_later": True,
        "status": str(attrs.get("status") or "default"),
        "items": [
            _latent_attribute_item("机会捕捉", global_attrs.get("luck_index")),
            _latent_attribute_item("稳定承压", global_attrs.get("stability_index")),
            _latent_attribute_item("资源助力", global_attrs.get("resource_index")),
            _latent_attribute_item("风险波动", global_attrs.get("risk_index"), high_label="偏高", low_label="偏低"),
            _latent_attribute_item("事业偏置", domain_biases.get("career_bias")),
            _latent_attribute_item("财务偏置", domain_biases.get("wealth_bias")),
        ],
        "active_count": len(summary.get("active_global_attributes", [])) + len(summary.get("active_domain_biases", []))
        if isinstance(summary.get("active_global_attributes", []), list) and isinstance(summary.get("active_domain_biases", []), list)
        else 0,
        "debug_sections": [
            _latent_debug_section("全局属性", "global_attributes", global_attrs, score_key="value"),
            _latent_debug_section("十神修正", "ten_god_modifiers", ten_god_modifiers, score_key="multiplier"),
            _latent_debug_section("领域偏置", "domain_biases", domain_biases, score_key="value"),
            _latent_debug_section("稳定阈值", "stability_thresholds", stability_thresholds, score_key="value"),
        ],
        "boundary": "customer_latent_attributes_debug_raw_values_are_temporary_projection_not_chart_fact",
    }


def _latent_attribute_item(
    label: str,
    raw: object,
    *,
    high_label: str = "偏强",
    low_label: str = "偏弱",
) -> dict[str, object]:
    row = raw if isinstance(raw, dict) else {}
    try:
        value = float(row.get("value", 0.5))
    except (TypeError, ValueError):
        value = 0.5
    if value >= 0.58:
        band = high_label
    elif value <= 0.42:
        band = low_label
    else:
        band = "中性"
    return {
        "label": label,
        "band": band,
        "confidence_band": _latent_confidence_band(row.get("confidence", 0.1)),
    }


def _latent_confidence_band(value: object) -> str:
    try:
        score = float(value)
    except (TypeError, ValueError):
        score = 0.1
    if score >= 0.55:
        return "较高"
    if score >= 0.25:
        return "中等"
    return "低"


def _latent_debug_section(label: str, section_id: str, rows: dict[str, object], *, score_key: str) -> dict[str, object]:
    return {
        "section_id": section_id,
        "label": label,
        "score_key": score_key,
        "rows": [
            _latent_debug_row(key, value, score_key=score_key)
            for key, value in sorted(rows.items(), key=lambda item: str(item[0]))
        ],
    }


def _latent_debug_row(key: str, raw: object, *, score_key: str) -> dict[str, object]:
    row = raw if isinstance(raw, dict) else {}
    return {
        "key": str(key),
        "score_key": score_key,
        "score": _safe_float(row.get(score_key), default=1.0 if score_key == "multiplier" else 0.5),
        "confidence": _safe_float(row.get("confidence"), default=0.1),
        "evidence_count": int(row.get("evidence_count", 0) or 0),
    }


def _safe_float(value: object, *, default: float) -> float:
    try:
        return round(float(value), 3)
    except (TypeError, ValueError):
        return default


def _basic_assertions(
    runtime: CoreRuntimeResult,
    natal: dict[str, object],
    ranked: dict[str, object],
) -> list[dict[str, object]]:
    summary = natal.get("base_fact_summary", {})
    summary = summary if isinstance(summary, dict) else {}
    rows = [
        _day_master_assertion(runtime, summary),
        _strength_assertion(runtime, ranked),
        _structure_assertion(runtime, ranked),
        _useful_god_assertion(runtime, ranked),
        _current_luck_flow_assertion(runtime),
        _risk_boundary_assertion(runtime, summary),
    ]
    return [row for row in rows if row.get("assertion")]


def _day_master_assertion(runtime: CoreRuntimeResult, summary: dict[str, object]) -> dict[str, object]:
    visible_counts = summary.get("visible_ten_god_counts", {})
    hidden_counts = summary.get("hidden_ten_god_counts", {})
    visible_counts = visible_counts if isinstance(visible_counts, dict) else {}
    hidden_counts = hidden_counts if isinstance(hidden_counts, dict) else {}
    visible_labels = _top_count_labels(visible_counts, limit=2)
    hidden_labels = _top_count_labels(hidden_counts, limit=2)
    support = "、".join([*visible_labels, *hidden_labels][:3])
    detail = f"，十神线索以{support}为先" if support else ""
    return {
        "assertion_id": "basic.day_master",
        "kind": "day_master_assertion",
        "title": "日主参照",
        "assertion": f"此盘以{runtime.chart_context.day_master}{_element_label(runtime.chart_context.day_master_element)}日主为中心{detail}。",
        "evidence": "day_master_and_ten_god_counts",
        "evidence_labels": ["日主", "显性十神", "藏干十神"],
        "source_modules": ["M1/M2"],
        "boundary": "basic_assertion_projects_deterministic_chart_facts_not_final_verdict",
    }


def _strength_assertion(runtime: CoreRuntimeResult, ranked: dict[str, object]) -> dict[str, object]:
    decision = ranked.get("strength", {})
    decision = decision if isinstance(decision, dict) else {}
    candidate = str(decision.get("primary_candidate") or "")
    basis = decision.get("scoring_basis", {})
    basis = basis if isinstance(basis, dict) else {}
    strongest = basis.get("strongest_elements", [])
    weakest = basis.get("weakest_elements", [])
    strongest = strongest if isinstance(strongest, list) else []
    weakest = weakest if isinstance(weakest, list) else []
    element_part = ""
    if strongest or weakest:
        element_part = f"，五行上{_element_list_label(strongest) or '主线'}较突出，{_element_list_label(weakest) or '薄弱处'}较弱"
    return {
        "assertion_id": "basic.strength",
        "kind": "strength_assertion",
        "title": "强弱候选",
        "assertion": f"强弱取{_candidate_label(candidate)}为主{element_part}。",
        "evidence": "ranked_decisions.strength",
        "evidence_labels": ["M5 旺衰候选", "五行分布", "根气摘要"],
        "source_modules": ["M1/M2", "M4", "M5"],
        "boundary": "strength_basic_assertion_is_ranked_candidate_not_fixed_strength_verdict",
    }


def _structure_assertion(runtime: CoreRuntimeResult, ranked: dict[str, object]) -> dict[str, object]:
    decision = ranked.get("structure_pattern", {})
    decision = decision if isinstance(decision, dict) else {}
    candidate = str(decision.get("primary_candidate") or runtime.structure_state.semantic_label or "")
    path_scores = runtime.structure_state.path_scores if isinstance(runtime.structure_state.path_scores, dict) else {}
    path_count = int(path_scores.get("dynamic_path_count", 0.0) or 0)
    path_part = f"，同时纳入{path_count}条结构动态路径" if path_count else "，以原局结构证据为主"
    return {
        "assertion_id": "basic.structure",
        "kind": "structure_assertion",
        "title": "结构路径",
        "assertion": f"结构取{_candidate_label(candidate)}为主{path_part}。",
        "evidence": "ranked_decisions.structure_pattern",
        "evidence_labels": ["M3 结构动态", "M5 结构候选"],
        "source_modules": ["M3", "M5"],
        "boundary": "structure_basic_assertion_is_dynamic_path_context_not_fixed_geju_verdict",
    }


def _useful_god_assertion(runtime: CoreRuntimeResult, ranked: dict[str, object]) -> dict[str, object]:
    decision = ranked.get("useful_god", {})
    decision = decision if isinstance(decision, dict) else {}
    candidate = str(decision.get("primary_candidate") or "")
    alternatives = decision.get("alternatives", [])
    alternatives = alternatives if isinstance(alternatives, list) else []
    alt_labels = [_candidate_label(str(row)) for row in alternatives[:2] if row]
    alt_part = f"，兼看{'、'.join(alt_labels)}" if alt_labels else ""
    return {
        "assertion_id": "basic.useful_god",
        "kind": "useful_god_direction",
        "title": "用神方向",
        "assertion": f"用神取向优先看{_candidate_label(candidate)}{alt_part}。",
        "evidence": "ranked_decisions.useful_god",
        "evidence_labels": ["M5 用神候选", "M3 规则边界", "M4 十神信号"],
        "source_modules": ["M3", "M4", "M5"],
        "boundary": "useful_god_basic_assertion_is_candidate_direction_not_fixed_favorable_verdict",
    }


def _current_luck_flow_assertion(runtime: CoreRuntimeResult) -> dict[str, object]:
    time_context = _customer_time_context(runtime)
    luck = time_context.get("current_luck", {})
    luck = luck if isinstance(luck, dict) else {}
    luck_pillar = str(luck.get("pillar") or luck.get("display") or time_context.get("current_luck_pillar") or "")
    flow_year = str(time_context.get("flow_year_pillar") or "")
    status = str(time_context.get("status") or "")
    if luck_pillar or flow_year:
        assertion = f"当前进入{f'大运{luck_pillar}' if luck_pillar else '大运'}{f'、流年{flow_year}' if flow_year else ''}，用于观察结构触发顺序。"
    else:
        assertion = "当前缺少明确大运或流年上下文，时间判断暂不展开。"
    return {
        "assertion_id": "basic.current_luck_flow",
        "kind": "current_luck_flow_assertion",
        "title": "大运流年",
        "assertion": assertion,
        "evidence": "time_context",
        "evidence_labels": ["大运", "流年", "时间层状态"],
        "source_modules": ["M1/M2"],
        "status": status,
        "boundary": "time_basic_assertion_projects_luck_flow_context_not_event_prediction",
    }


def _risk_boundary_assertion(runtime: CoreRuntimeResult, summary: dict[str, object]) -> dict[str, object]:
    relation_families = summary.get("relation_families", [])
    relation_families = relation_families if isinstance(relation_families, list) else []
    relation_part = f"，地支关系已见{_relation_family_label(relation_families[:3])}" if relation_families else ""
    return {
        "assertion_id": "basic.risk_boundary",
        "kind": "risk_boundary",
        "title": "地支互动",
        "assertion": f"地支互动会影响结构落点{relation_part}，重点看冲合刑害如何牵动财官印食伤。",
        "evidence": "base_fact_summary.relation_families",
        "evidence_labels": ["地支关系", "结构落点", "十神牵动"],
        "source_modules": ["M1/M2", "M3", "M5"],
        "boundary": "risk_boundary_blocks_single_factor_or_feedback_from_becoming_final_verdict",
    }


def _core_fact_integrity(runtime: CoreRuntimeResult) -> dict[str, object]:
    source = runtime.chart_context.input_pillars.get("chart_build_source", {})
    source = source if isinstance(source, dict) else {}
    return {
        "version": "v30.core_fact_integrity.v1",
        "chart_status": str(source.get("status") or ""),
        "source_type": str(source.get("source_type") or ""),
        "deterministic": True,
        "llm_generated": False,
        "training_generated": False,
        "feedback_generated": False,
        "boundary": "core_fact_integrity_blocks_non_deterministic_chart_fact_sources",
    }


def _base_fact_explanations(runtime: CoreRuntimeResult, natal: dict[str, object]) -> dict[str, object]:
    locale = runtime.chart_context.locale
    summary = natal.get("base_fact_summary", {})
    summary = summary if isinstance(summary, dict) else {}
    relation_count = int(summary.get("relation_count", 0) or 0)
    visible_count = int(summary.get("visible_ten_god_count", 0) or 0)
    hidden_count = int(summary.get("hidden_ten_god_count", 0) or 0)
    strongest = summary.get("strongest_elements", [])
    weakest = summary.get("weakest_elements", [])
    strongest = strongest if isinstance(strongest, list) else []
    weakest = weakest if isinstance(weakest, list) else []
    visible_counts = summary.get("visible_ten_god_counts", {})
    visible_counts = visible_counts if isinstance(visible_counts, dict) else {}
    hidden_counts = summary.get("hidden_ten_god_counts", {})
    hidden_counts = hidden_counts if isinstance(hidden_counts, dict) else {}
    relation_families = summary.get("relation_families", [])
    relation_families = relation_families if isinstance(relation_families, list) else []
    root_summary = summary.get("root_fact_summary", {})
    root_summary = root_summary if isinstance(root_summary, dict) else {}
    return {
        "version": "v30.base_bazi_fact_explanations.v1",
        "day_master": {
            "label": term_label(locale, "day_master"),
            "value": runtime.chart_context.day_master,
            "element": runtime.chart_context.day_master_element,
            "explanation": "日主来自日柱天干，是后续十神、五行和结构判断的确定性参照点。",
        },
        "ten_gods": {
            "label": term_label(locale, "ten_god"),
            "visible_count": visible_count,
            "hidden_count": hidden_count,
            "visible_counts": visible_counts,
            "hidden_counts": hidden_counts,
            "explanation": "显性十神来自年、月、时天干与日主的关系；藏干十神来自各地支藏干与日主的关系。",
        },
        "five_elements": {
            "label": term_label(locale, "five_elements"),
            "strongest_elements": strongest,
            "weakest_elements": weakest,
            "explanation": "五行分布是原局天干地支和藏干权重的基础统计，只作为后续强弱和结构判断的输入。",
        },
        "relations": {
            "label": term_label(locale, "branch_relation"),
            "relation_count": relation_count,
            "relation_families": relation_families,
            "explanation": "地支关系只记录合冲刑害破等事实线索，不能单独推出吉凶或事件。",
        },
        "roots_and_vaults": {
            "label": f"{term_label(locale, 'root')} / {term_label(locale, 'vault')}",
            "day_master_root_count": int(root_summary.get("day_master_root_count", 0) or 0),
            "same_element_root_count": int(root_summary.get("same_element_root_count", 0) or 0),
            "vault_branches": root_summary.get("vault_branches", []) if isinstance(root_summary.get("vault_branches"), list) else [],
            "explanation": "根气与库墓只记录藏干出现和库墓地支位置，不直接推出旺衰、格局或用神结论。",
        },
        "time_context": {
            "label": term_label(locale, "timing"),
            "status": str(runtime.chart_context.time_layers.get("status") if isinstance(runtime.chart_context.time_layers, dict) else ""),
            "explanation": "大运、流年、流月只作为时间层上下文，不是确定事件预测。",
        },
        "boundary": "base_fact_explanations_are_deterministic_context_not_ranked_decisions",
    }


def _m1_m2_completion_summary(runtime: CoreRuntimeResult, natal: dict[str, object]) -> dict[str, object]:
    summary = natal.get("base_fact_summary", {})
    summary = summary if isinstance(summary, dict) else {}
    explanations = _base_fact_explanations(runtime, natal)
    required_summary_keys = {
        "visible_ten_god_counts",
        "hidden_ten_god_counts",
        "hidden_stem_summary",
        "relation_type_counts",
        "relation_families",
        "element_distribution",
        "root_fact_summary",
    }
    present_summary_keys = set(summary)
    explanation_sections = {
        key for key in ("day_master", "ten_gods", "five_elements", "relations", "roots_and_vaults", "time_context")
        if isinstance(explanations.get(key), dict)
    }
    ranked_decisions = runtime.question_plan.policy_effect.get("ranked_decisions", {})
    ranked_decisions = ranked_decisions if isinstance(ranked_decisions, dict) else {}
    m5_basis_rows = [
        payload.get("scoring_basis", {})
        for payload in ranked_decisions.values()
        if isinstance(payload, dict)
    ]
    m5_uses_root_fact_count = sum(
        1 for basis in m5_basis_rows
        if isinstance(basis, dict)
        and basis.get("root_fact_summary_version") == "v30.root_vault_fact_summary.v1"
        and basis.get("root_vault_boundary") == "root_vault_summary_records_presence_without_strength_or_useful_god_verdict"
    )
    practical = runtime.question_plan.policy_effect.get("practical_reading_context", {})
    domain_readings = practical.get("domain_readings", {}) if isinstance(practical, dict) else {}
    domain_readings = domain_readings if isinstance(domain_readings, dict) else {}
    m6_trace_rows = [
        payload.get("module_trace", {})
        for payload in domain_readings.values()
        if isinstance(payload, dict)
    ]
    m6_uses_m1_m2_count = sum(
        1 for trace in m6_trace_rows
        if isinstance(trace, dict)
        and trace.get("version") == "v30.m6_practical_module_trace.v1"
        and trace.get("uses_m1_m2_facts") is True
        and trace.get("chart_fact_mutation_allowed") is False
    )
    deterministic = _core_fact_integrity(runtime)
    non_deterministic_source_count = sum(
        1 for key in ("llm_generated", "training_generated", "feedback_generated")
        if deterministic.get(key)
    )
    required_key_coverage = len(required_summary_keys & present_summary_keys) / len(required_summary_keys)
    explanation_coverage = len(explanation_sections) / 6
    downstream_ready = (
        len(m5_basis_rows) >= 3
        and m5_uses_root_fact_count >= 3
        and len(m6_trace_rows) >= 5
        and m6_uses_m1_m2_count >= 5
    )
    ready = (
        summary.get("status") == "ready"
        and int(summary.get("pillar_count", 0) or 0) == 4
        and required_key_coverage == 1.0
        and explanation_coverage == 1.0
        and deterministic.get("deterministic") is True
        and non_deterministic_source_count == 0
        and downstream_ready
    )
    return {
        "version": "v30.m1_m2_completion_summary.v1",
        "status": "ready" if ready else "needs_review",
        "required_summary_keys": sorted(required_summary_keys),
        "required_key_coverage": round(required_key_coverage, 3),
        "explanation_sections": sorted(explanation_sections),
        "explanation_coverage": round(explanation_coverage, 3),
        "non_deterministic_source_count": non_deterministic_source_count,
        "m5_scoring_basis_count": len(m5_basis_rows),
        "m5_uses_root_fact_summary_count": m5_uses_root_fact_count,
        "m6_module_trace_count": len(m6_trace_rows),
        "m6_uses_m1_m2_fact_count": m6_uses_m1_m2_count,
        "downstream_consumption_ready": downstream_ready,
        "chart_fact_mutation_allowed": False,
        "boundary": "m1_m2_completion_summary_validates_fact_layer_and_downstream_consumption_not_judgment",
    }


def _pillar_rows(pillars: object) -> list[dict[str, object]]:
    if not isinstance(pillars, dict):
        return []
    labels = {"year": "年柱", "month": "月柱", "day": "日柱", "hour": "时柱"}
    rows: list[dict[str, object]] = []
    for key in ["year", "month", "day", "hour"]:
        payload = pillars.get(key, {})
        if not isinstance(payload, dict):
            continue
        stem = str(payload.get("stem") or "")
        branch = str(payload.get("branch") or "")
        rows.append(
            {
                "layer": key,
                "label": labels[key],
                "pillar": str(payload.get("display") or f"{stem}{branch}"),
                "stem": stem,
                "branch": branch,
            }
        )
    return rows


def _visible_ten_god_rows(rows: object) -> list[dict[str, object]]:
    if not isinstance(rows, list):
        return []
    return [
        {
            "position": str(row.get("position") or row.get("pillar") or ""),
            "stem": str(row.get("stem") or ""),
            "ten_god": str(row.get("ten_god") or row.get("label") or ""),
        }
        for row in rows
        if isinstance(row, dict)
    ]


def _hidden_ten_god_rows(rows: object) -> list[dict[str, object]]:
    if not isinstance(rows, list):
        return []
    return [
        {
            "branch": str(row.get("branch") or row.get("pillar") or ""),
            "stem": str(row.get("stem") or ""),
            "ten_god": str(row.get("ten_god") or row.get("label") or ""),
            "weight": row.get("weight", None),
        }
        for row in rows
        if isinstance(row, dict)
    ]


def _relation_rows(rows: object) -> list[dict[str, object]]:
    if not isinstance(rows, list):
        return []
    return [
        {
            "relation": str(row.get("relation") or row.get("relation_type") or row.get("kind") or ""),
            "branches": row.get("branches", []),
            "description": str(row.get("description") or ""),
        }
        for row in rows
        if isinstance(row, dict)
    ][:8]


def _customer_ranked_decisions(ranked: dict[str, object]) -> dict[str, object]:
    labels = {
        "strength": "旺衰强弱",
        "structure_pattern": "结构格局",
        "useful_god": "用神候选",
    }
    projected: dict[str, object] = {}
    for key in ["strength", "structure_pattern", "useful_god"]:
        payload = ranked.get(key, {})
        if not isinstance(payload, dict):
            continue
        projected[key] = {
            "label": labels[key],
            "status": str(payload.get("status") or ""),
            "primary_candidate": str(payload.get("primary_candidate") or ""),
            "alternatives": payload.get("alternatives", []) if isinstance(payload.get("alternatives", []), list) else [],
            "confidence": payload.get("confidence", None),
            "boundary": str(payload.get("boundary") or "ranked_decision_is_candidate_not_fixed_verdict"),
        }
    return projected


def _candidate_label(candidate: str) -> str:
    labels = {
        "strong": "偏旺",
        "slightly_strong": "略偏旺",
        "balanced": "相对平衡",
        "slightly_weak": "略偏弱",
        "weak": "偏弱",
        "needs_time_layer_review": "看大运流年",
        "dynamic_structure_review": "动态结构",
        "ordinary_structure_review": "普通结构",
        "special_structure_boundary_review": "特殊格局边界",
        "mediation_path_review": "通关承接路径",
        "resource_or_self_support_review": "印比扶助方向",
        "output_or_wealth_release_review": "食伤生财或财星释放方向",
        "authority_regulation_review": "官杀约束与规则承接方向",
        "climate_regulation_review": "调候平衡方向",
        "balance_review": "平衡调候方向",
        "output": "输出表达方向",
        "evidence-bound chart structure": "证据约束型结构",
    }
    if "evidence-bound" in candidate:
        return "证据约束型结构"
    return labels.get(candidate, candidate or "待判断")


def _element_label(element: str) -> str:
    labels = {
        "wood": "木",
        "fire": "火",
        "earth": "土",
        "metal": "金",
        "water": "水",
    }
    return labels.get(element, element)


def _element_list_label(values: list[object]) -> str:
    labels = [_element_label(str(row)) for row in values if row]
    return "、".join(labels)


def _top_count_labels(counts: dict[object, object], *, limit: int) -> list[str]:
    rows = sorted(
        ((str(key), int(value or 0)) for key, value in counts.items()),
        key=lambda row: (-row[1], row[0]),
    )
    return [key for key, value in rows[:limit] if value > 0]


def _relation_family_label(values: list[object]) -> str:
    labels = {
        "harmony": "合",
        "clash": "冲",
        "punishment": "刑",
        "harm": "害",
        "break": "破",
        "three_harmony": "三合",
    }
    return "、".join(labels.get(str(row), str(row)) for row in values if row)


def _customer_model_signal_summary(model_summary: dict[str, object]) -> dict[str, object]:
    return {
        "version": str(model_summary.get("version") or "v30.model_signal_summary.customer_projection.v1"),
        "status": str(model_summary.get("status") or ""),
        "top_energy": model_summary.get("top_energy", []) if isinstance(model_summary.get("top_energy", []), list) else [],
        "high_volatility_ten_gods": (
            model_summary.get("high_volatility_ten_gods", [])
            if isinstance(model_summary.get("high_volatility_ten_gods", []), list)
            else []
        ),
        "boundary": "model_signal_summary_is_calibration_signal_not_chart_fact",
    }


def _customer_time_context(runtime: CoreRuntimeResult) -> dict[str, object]:
    layers = runtime.chart_context.time_layers if isinstance(runtime.chart_context.time_layers, dict) else {}
    six = layers.get("six_pillar_context", {})
    luck = layers.get("luck_cycle_context", {})
    flow = layers.get("flow_context", {})
    if not isinstance(six, dict):
        six = {}
    if not isinstance(luck, dict):
        luck = {}
    if not isinstance(flow, dict):
        flow = {}
    cycles = luck.get("luck_cycles", [])
    if not isinstance(cycles, list):
        cycles = []
    current_luck = luck.get("current_luck", {})
    if not isinstance(current_luck, dict):
        current_luck = {}
    return {
        "version": "v30.customer_time_context.v1",
        "status": six.get("status") or layers.get("status") or "pending",
        "target_date": flow.get("target_date", ""),
        "target_year": _target_year_from_flow(flow),
        "six_pillars": six.get("pillars", []) if isinstance(six.get("pillars", []), list) else [],
        "current_luck": current_luck,
        "luck_cycles": cycles,
        "flow_year_pillar": flow.get("flow_year_pillar", ""),
        "flow_month_pillar": flow.get("flow_month_pillar", ""),
        "missing_requirements": six.get("missing_requirements", []),
        "boundary": "customer_time_context_projects_deterministic_luck_flow_without_timing_verdict",
    }


def _target_year_from_flow(flow: dict[str, object]) -> int | None:
    target_date = str(flow.get("target_date") or "")
    if len(target_date) < 4:
        return None
    try:
        return int(target_date[:4])
    except ValueError:
        return None


def _interaction_options(domain_cards: list[dict[str, object]]) -> list[dict[str, object]]:
    options = [
        {
            "option_id": f"domain:{card.get('domain')}",
            "label": str(card.get("label") or card.get("domain") or ""),
            "value": str(card.get("domain") or ""),
            "option_type": "domain_focus",
            "boundary": "structured_option_guides_question_strategy_not_chart_fact",
        }
        for card in domain_cards
        if card.get("domain")
    ]
    if not options:
        options = [
            {
                "option_id": "domain:career",
                "label": "事业",
                "value": "career",
                "option_type": "domain_focus",
                "boundary": "structured_option_guides_question_strategy_not_chart_fact",
            },
            {
                "option_id": "domain:wealth",
                "label": "财务",
                "value": "wealth",
                "option_type": "domain_focus",
                "boundary": "structured_option_guides_question_strategy_not_chart_fact",
            },
        ]
    return options[:4]


def _surface_options(next_question: dict[str, object], domain_cards: list[dict[str, object]]) -> list[dict[str, object]]:
    question_options = next_question.get("options", []) if isinstance(next_question, dict) else []
    if isinstance(question_options, list) and question_options:
        return [row for row in question_options if isinstance(row, dict)][:4]
    return _interaction_options(domain_cards)


def _surface_question_projection(question: dict[str, object]) -> dict[str, object]:
    if not isinstance(question, dict) or not question:
        return {}
    gain = question.get("expected_information_gain", {})
    gain = gain if isinstance(gain, dict) else {}
    return {
        "question_id": str(question.get("question_id") or ""),
        "label": str(question.get("label") or ""),
        "label_source": str(question.get("label_source") or ""),
        "label_boundary": str(question.get("label_boundary") or ""),
        "topic": str(question.get("topic") or ""),
        "topic_label": str(question.get("topic_label") or ""),
        "interaction_type": str(question.get("interaction_type") or ""),
        "answer_mode": str(question.get("answer_mode") or ""),
        "expected_information_gain": {
            "primary_gain": str(gain.get("primary_gain") or ""),
            "score": gain.get("score", None),
            "boundary": "expected_information_gain_is_customer_question_value_not_internal_policy_trace",
        },
        "options": _customer_question_options(question.get("options", [])),
        "answer_constraints": _customer_answer_constraints(question.get("answer_constraints", {})),
        "quality_contract": _customer_question_quality_contract(question.get("quality_contract", {})),
        "semantic_projection": _customer_question_semantic_projection(question.get("semantic_projection", {})),
        "boundary": "next_question_is_customer_projection_not_internal_strategy_trace",
    }


def _customer_question_semantic_projection(value: object) -> dict[str, object]:
    semantic = value if isinstance(value, dict) else {}
    if not semantic:
        return {}
    return {
        "version": str(semantic.get("version") or ""),
        "macro_domain": str(semantic.get("macro_domain") or ""),
        "macro_label": str(semantic.get("macro_label") or ""),
        "selected_slot": str(semantic.get("selected_slot") or ""),
        "keywords": [str(row) for row in _as_list(semantic.get("keywords"))[:6]],
        "ten_god_drivers": _customer_ten_god_drivers(_as_list(semantic.get("ten_god_drivers"))),
        "boundary": "customer_question_semantic_projection_hides_internal_weights",
    }


def _customer_question_options(options: object) -> list[dict[str, object]]:
    if not isinstance(options, list):
        return []
    return [
        {
            "option_id": str(row.get("option_id") or ""),
            "label": str(row.get("label") or ""),
            "value": str(row.get("value") or ""),
            "option_type": str(row.get("option_type") or ""),
            "boundary": "structured_option_guides_customer_answer_not_internal_policy_trace",
        }
        for row in options
        if isinstance(row, dict)
    ][:4]


def _customer_answer_constraints(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        return {}
    allowed = {
        "version",
        "constraint_type",
        "required_fields",
        "optional_fields",
        "year_range",
        "allowed_state_tags",
        "allowed_intensity",
        "allowed_recurrence",
        "allowed_confidence",
        "allowed_domains",
        "free_note_policy",
        "invalid_input_action",
        "chart_fact_mutation_allowed",
        "boundary",
    }
    return {key: value[key] for key in allowed if key in value}


def _customer_question_quality_contract(contract: object) -> dict[str, object]:
    if not isinstance(contract, dict):
        return {}
    return {
        "version": str(contract.get("version") or ""),
        "boundary": "question_quality_contract_is_customer_safe_projection",
    }


def _next_question_from_dialogue_plan(runtime: CoreRuntimeResult, questions: list[dict[str, object]]) -> dict[str, object]:
    if not questions:
        return {}
    central = runtime.question_plan.policy_effect.get("central_reading_state", {})
    dialogue_plan = central.get("dialogue_plan", {}) if isinstance(central, dict) else {}
    planner_question_id = str(dialogue_plan.get("current_question_id") or "") if isinstance(dialogue_plan, dict) else ""
    if not planner_question_id:
        return {}
    for question in questions:
        if str(question.get("question_id")) == planner_question_id:
            return question
    return {}


def _nested_dict(payload: object, section: str, key: str, *, default: object = None) -> object:
    if not isinstance(payload, dict):
        return default
    section_payload = payload.get(section, {})
    if not isinstance(section_payload, dict):
        return default
    return section_payload.get(key, default)


def _nested_bool(payload: object, section: str, key: str) -> bool:
    return bool(_nested_dict(payload, section, key, default=False))


def _bazi_context(runtime: CoreRuntimeResult) -> dict[str, object]:
    return {
        "version": "v30.internal_bazi_context.v1",
        "chart_context_id": runtime.chart_context.context_id,
        "feature_evidence_count": len(runtime.feature_evidence),
        "structure_state": runtime.structure_state.model_dump(mode="json"),
        "mainline_state": runtime.mainline_state.model_dump(mode="json"),
        "ranked_decisions": runtime.question_plan.policy_effect.get("ranked_decisions", {}),
        "practical_reading_context": runtime.question_plan.policy_effect.get("practical_reading_context", {}),
        "agent_question_flow": runtime.question_plan.policy_effect.get("agent_question_flow", {}),
        "model_signal_summary": runtime.question_plan.policy_effect.get("model_signal_summary", {}),
        "boundary": "internal_bazi_context_for_practitioner_admin_lab_not_default_customer_surface",
    }


def _central_brain_diagnostics(runtime: CoreRuntimeResult) -> dict[str, object]:
    trace = runtime.question_plan.policy_effect.get("central_brain_trace", {})
    if not isinstance(trace, dict):
        return {}
    return {
        "version": trace.get("version"),
        "session_phase": _nested(trace, "brain_state", "session_phase"),
        "focus": _nested(trace, "runtime_plan", "focus"),
        "question_strategy": _nested(trace, "question_strategy", "strategy"),
        "expression_surface": _nested(trace, "expression_orchestration", "surface_status"),
        "feedback_targets": _nested(trace, "feedback_strategy", "capture_targets", default=[]),
        "training_routes": [
            str(row.get("target_signal_domain"))
            for row in trace.get("training_signal_routes", [])
            if isinstance(row, dict)
        ],
    }


def _llm_runtime_status(runtime: CoreRuntimeResult) -> dict[str, object]:
    call = runtime.question_plan.policy_effect.get("llm_answer_draft_call", {})
    readiness = runtime.question_plan.policy_effect.get("llm_provider_readiness", {})
    if not isinstance(call, dict):
        call = {}
    if not isinstance(readiness, dict):
        readiness = {}
    return {
        "version": "v30.llm_runtime_status.v1",
        "answer_source": runtime.answer_result.source if runtime.answer_result else "",
        "call_status": call.get("status", "not_called"),
        "fallback_reason": call.get("fallback_reason", ""),
        "executed": bool(call.get("executed", False)),
        "ready_for_connection": bool(readiness.get("ready_for_connection", False)),
        "provider": readiness.get("provider", ""),
        "model": readiness.get("model", ""),
        "boundary": "llm_runtime_status_observes_expression_layer_not_chart_fact",
    }


def _interaction_stage(runtime: CoreRuntimeResult) -> str:
    state = runtime.question_plan.policy_effect.get("interaction_state", {})
    if isinstance(state, dict):
        return str(state.get("interaction_stage") or "")
    return ""


def _interaction_selected_domain(runtime: CoreRuntimeResult) -> str:
    state = runtime.question_plan.policy_effect.get("interaction_state", {})
    if isinstance(state, dict):
        return str(state.get("selected_domain") or "")
    return ""


def _nested(payload: dict[str, object], section: str, key: str, *, default: object = None) -> object:
    section_payload = payload.get(section, {})
    if not isinstance(section_payload, dict):
        return default
    return section_payload.get(key, default)
