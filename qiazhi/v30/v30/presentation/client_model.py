from __future__ import annotations

from v30.contracts import ClientPresentationModel, CoreRuntimeResult
from v30.expression import render_question_label, summarize_question_labels
from v30.presentation.client_profiles import client_profile
from v30.presentation.i18n import build_locale_terminology_contract, label, term_label
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
    payload["text"] = _customer_answer_text(str(payload.get("text") or ""))
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


def _customer_answer_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    kept: list[str] = []
    blocked_prefixes = ("基础判断：", "路径复核：", "特征画像：", "边界：")
    blocked_contains = (
        "llm_bazi_answer_draft",
        "LLM accepted",
        "LLM fallback",
        "rule_bound_fallback",
        "rule_bound_llm_deferred",
        "policy_effect",
        "证据数=",
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
    return cleaned or text.strip()


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
        "next_question",
    ]
    hidden_fields = _hidden_projection_tokens()
    additive_fields = [
        "reading_surface",
        "core_bazi_reading",
        "domain_cards",
        "questions",
        "answer_panel",
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
            "next_question",
            "options",
            "interaction_goal",
        ],
        "customer_surface_order": customer_surface_order,
        "core_first_projection": {
            "version": "v30.core_first_projection.v1",
            "required_surface_prefix": customer_surface_order[:2],
            "calculation_before_questions": True,
            "question_loop_position": "after_core_calculation_surface",
            "calibration_probe_position": "after_customer_visible_calculation",
            "boundary": "core_bazi_calculation_is_presented_before_questions_or_feedback_loops",
        },
        "customer_surface_contract": surface_contract,
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
    ready = (
        isinstance(core, dict)
        and core.get("surface_type") == "core_bazi_calculation"
        and isinstance(domain_cards, list)
        and bool(domain_cards)
        and isinstance(next_question, dict)
    )
    return {
        "version": "v30.customer_surface_contract.v1",
        "surface_type": str(reading_surface.get("surface_type") or ""),
        "has_core_bazi_reading": isinstance(core, dict) and core.get("surface_type") == "core_bazi_calculation",
        "has_domain_cards": isinstance(domain_cards, list) and bool(domain_cards),
        "has_time_context": isinstance(reading_surface.get("time_context", {}), dict) and bool(reading_surface.get("time_context", {})),
        "has_next_question": isinstance(next_question, dict) and bool(next_question),
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
    agent_flow = runtime.question_plan.policy_effect.get("agent_question_flow", {})
    domain_readings = practical.get("domain_readings", {}) if isinstance(practical, dict) else {}
    focus_domains = _focus_domains(domain_readings)
    domain_cards = _domain_cards(domain_readings, focus_domains, locale=locale)
    next_question = _surface_question_projection(_next_question_from_graph(runtime, questions))
    core_bazi_reading = _core_bazi_reading(runtime, domain_cards)
    basic_assertions = core_bazi_reading.get("basic_assertions", [])
    basic_assertions = basic_assertions if isinstance(basic_assertions, list) else []
    return {
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
        "reading_summary": {
            "title": _customer_summary_title(
                runtime,
                domain_cards,
                locale=locale,
                diagnostic=role_key not in USER_VISIBLE_ROLES,
            ),
            "status": practical.get("status", "ready") if isinstance(practical, dict) else "ready",
            "focus_domains": focus_domains,
            "primary_message": _primary_message(domain_cards, locale=locale),
            "diagnosis_overview": _diagnosis_overview(runtime),
            "timing_status": _nested_dict(practical, "timing_summary", "status", default="natal_only"),
            "boundary": "customer_summary_expresses_bazi_context_without_exposing_internal_diagnostics",
        },
        "diagnosis_overview": _diagnosis_overview(runtime),
        "domain_cards": domain_cards,
        "basic_assertions": basic_assertions,
        "bazi_features": _bazi_feature_rows(runtime, detailed=role_key not in USER_VISIBLE_ROLES),
        "bazi_portraits": _bazi_portrait_rows(runtime, detailed=role_key not in USER_VISIBLE_ROLES),
        "bazi_paths": _bazi_path_rows(runtime, detailed=role_key not in USER_VISIBLE_ROLES),
        "core_bazi_reading": core_bazi_reading,
        "structure_dynamics": _customer_structure_dynamics(runtime, role_key=role_key, locale=locale),
        "time_context": _customer_time_context(runtime),
        "next_question": next_question,
        "next_question_id": str(next_question.get("question_id") or "") if isinstance(next_question, dict) else "",
        "interaction_stage": _interaction_stage(runtime),
        "selected_domain": _interaction_selected_domain(runtime),
        "visible_next_question_id": str(next_question.get("question_id") or "") if isinstance(next_question, dict) else "",
        "options": _surface_options(next_question, domain_cards),
        "question_count": len(questions),
        "next_stage": agent_flow.get("next_stage", "") if isinstance(agent_flow, dict) else "",
        "interaction_goal": "ask_high_value_question_then_refresh_context",
        "internal_context_visible": role_key not in USER_VISIBLE_ROLES,
        "boundary": "customer_surface_is_projection_not_chart_fact_or_debug_trace",
    }


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


def _primary_message(domain_cards: list[dict[str, object]], *, locale: str) -> str:
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
    }
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
        "boundary": "next_question_is_customer_projection_not_internal_strategy_trace",
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


def _next_question_from_graph(runtime: CoreRuntimeResult, questions: list[dict[str, object]]) -> dict[str, object]:
    if not questions:
        return {}
    state = runtime.question_plan.policy_effect.get("interaction_state", {})
    visible_next_id = state.get("visible_next_question_id") if isinstance(state, dict) else ""
    if visible_next_id:
        for question in questions:
            if str(question.get("question_id")) == str(visible_next_id):
                return question
    graph = runtime.question_plan.policy_effect.get("question_dialogue_graph", {})
    next_id = graph.get("next_question_id") if isinstance(graph, dict) else ""
    if next_id:
        for question in questions:
            if str(question.get("question_id")) == str(next_id):
                return question
    return questions[0]


def _nested_dict(payload: object, section: str, key: str, *, default: object = None) -> object:
    if not isinstance(payload, dict):
        return default
    section_payload = payload.get(section, {})
    if not isinstance(section_payload, dict):
        return default
    return section_payload.get(key, default)


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
