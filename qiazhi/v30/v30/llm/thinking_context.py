from __future__ import annotations

from typing import Any

from v30.brain import build_expression_role_state
from v30.contracts import CoreRuntimeResult
from v30.llm.bazi_context import role_llm_profile
from v30.reasoning import build_xuanming_core_model


THINKING_STAGE_CONTEXT_VERSION = "v30.thinking_stage_context_pack.v1"

STAGE_MODULES: dict[str, list[str]] = {
    "chart_build": ["M1_M2", "time_boundary", "xuanming_strength"],
    "knowledge_library": ["M3_knowledge", "knowledge_boundary"],
    "rule_matching": ["M3_rules", "counter_evidence"],
    "feature_extraction": ["M3_features", "M4_model_signals"],
    "portrait_projection": ["M3_portrait", "diagnosis_portraits"],
    "path_reasoning": ["M3_structure_graph", "diagnosis_paths", "xuanming_path"],
    "structure_reasoning": ["M4_model_signals", "M5_ranked_decisions", "xuanming_structure"],
    "useful_god_arbitration": ["xuanming_useful_god", "M5_ranked_decisions", "avoidance_model"],
    "timing_layers": ["M1_M2_time_layers", "luck_flow", "six_pillar_context"],
    "domain_synthesis": ["M6_practical_reading", "real_bazi_diagnosis", "M8_domain_cards"],
    "final_report": ["M8_answer_surface", "accepted_stage_summaries", "role_contract"],
}

REASONING_BY_STAGE: dict[str, list[str]] = {
    "chart_build": ["chart_axis", "strength_model"],
    "knowledge_library": ["mainline"],
    "rule_matching": ["structure_model", "useful_god_model"],
    "feature_extraction": ["ten_god_model", "strength_model"],
    "portrait_projection": ["mainline", "path_model"],
    "path_reasoning": ["path_model", "mainline"],
    "structure_reasoning": ["structure_model", "useful_god_model"],
    "useful_god_arbitration": ["useful_god_model", "strength_model", "path_model"],
    "timing_layers": ["timing_model", "mainline"],
    "domain_synthesis": ["path_model", "mainline"],
    "final_report": ["mainline", "structure_model"],
}

STAGE_PROMPT_PROFILES: dict[str, dict[str, object]] = {
    "rule_matching": {
        "profile_id": "v30.stage_prompt.rule_matching.v1",
        "scene": "matched_rule_interpretation",
        "task": "解释本页命中的规则族、规则在此命盘中的作用，以及哪些规则需要进入下一页验证。",
        "must_name": ["matched_rule_family", "rule_effect_in_chart", "next_verification_target"],
        "avoid": ["不要写最终人生判断", "不要泛泛解释规则库", "不要把未命中的规则写成结论"],
        "answer_shape": "规则命中 -> 命盘作用 -> 验证方向 -> 行动提醒",
    },
    "portrait_projection": {
        "profile_id": "v30.stage_prompt.portrait_projection.v1",
        "scene": "portrait_tendency_synthesis",
        "task": "把本页画像倾向讲清楚：画像是什么、由哪些规则或特征支撑、对用户意味着什么。",
        "must_name": ["portrait_tendency", "supporting_feature_or_rule", "user_facing_implication"],
        "avoid": ["不要把画像说成必然事件", "不要脱离本页画像扩展到完整报告", "不要重复工程流程"],
        "answer_shape": "画像倾向 -> 支撑证据 -> 现实表现 -> 提醒",
    },
    "path_reasoning": {
        "profile_id": "v30.stage_prompt.path_reasoning.v1",
        "scene": "force_flow_path_derivation",
        "task": "解释本页做功路径：力量从哪里来、通过什么机制流动、落到哪些领域。",
        "must_name": ["primary_path_mechanism", "force_flow_direction", "domain_landing"],
        "avoid": ["不要重写规则页", "不要写完整领域报告", "不要只说强弱而不说力量流向"],
        "answer_shape": "路径机制 -> 力量流向 -> 领域落点 -> 建议",
    },
    "structure_reasoning": {
        "profile_id": "v30.stage_prompt.structure_reasoning.v1",
        "scene": "structure_decision_review",
        "task": "审定本页结构主线：旺衰、格局、用神取向和反证边界如何共同决定主线。",
        "must_name": ["structure_mainline", "useful_god_boundary", "counterevidence_or_confidence"],
        "avoid": ["不要只给性格描述", "不要跳到具体年份事件", "不要新增命盘事实"],
        "answer_shape": "结构主线 -> 取舍依据 -> 边界反证 -> 用神/行动方向",
    },
    "useful_god_arbitration": {
        "profile_id": "v30.stage_prompt.useful_god_arbitration.v1",
        "scene": "useful_god_avoidance_arbitration",
        "task": "解释本页用神忌神取舍：当前取用策略是什么，忌避风险是什么，哪些反证会让它降权。",
        "must_name": ["useful_god_strategy", "avoidance_risk", "counterevidence_boundary"],
        "avoid": ["不要说唯一用神已定", "不要说某五行永久为忌", "不要把候选策略直接翻译成财富职位婚姻结果"],
        "answer_shape": "用神取向 -> 忌避风险 -> 取舍依据 -> 后续验证",
    },
    "timing_layers": {
        "profile_id": "v30.stage_prompt.timing_layers.v1",
        "scene": "luck_flow_activation",
        "task": "解释本页时运：大运和流年如何激活原局路径，哪些结论必须等待时间资料。",
        "must_name": ["luck_pillar_or_gap", "flow_year_or_gap", "activated_original_path"],
        "avoid": ["不要凭空创造年份事件", "不要离开原局路径单断流年", "不要把时运缺口写成确定结论"],
        "answer_shape": "时运入口 -> 激活路径 -> 阶段主题 -> 边界",
    },
    "domain_synthesis": {
        "profile_id": "v30.stage_prompt.domain_synthesis.v1",
        "scene": "practical_domain_advice",
        "task": "把本页领域合成转成用户能执行的结论：哪个领域最重要、证据来自哪里、怎么做。",
        "must_name": ["priority_domain", "supporting_path_or_structure", "concrete_action_advice"],
        "avoid": ["不要平均铺开所有领域", "不要写空泛安慰", "不要脱离规则路径证据"],
        "answer_shape": "优先领域 -> 证据链 -> 结论 -> 行动建议",
    },
    "final_report": {
        "profile_id": "v30.stage_prompt.final_report.v1",
        "scene": "final_stage_synthesis",
        "task": "收束已完成阶段，给出最终结论、核心建议和证据边界；不得新增事实。",
        "must_name": ["final_conclusion", "core_advice", "evidence_boundary"],
        "avoid": ["不要新增命盘事实", "不要重复所有页面", "不要把未验证信息说成定论"],
        "answer_shape": "最终结论 -> 核心建议 -> 关键依据 -> 边界",
    },
}


def build_thinking_stage_context_pack(
    runtime: CoreRuntimeResult,
    step: dict[str, object],
    *,
    role_key: str,
    locale: str,
    client: str,
) -> dict[str, object]:
    step_id = str(step.get("step_id") or "")
    role_profile = _role_profile(role_key)
    reasoning_model = build_xuanming_core_model(runtime)
    module_context = _module_context(runtime, step_id=step_id, reasoning_model=reasoning_model)
    context_pack = {
        "version": THINKING_STAGE_CONTEXT_VERSION,
        "context_pack_id": f"{runtime.reading_id}:thinking-context:{step_id}:{role_key}:{locale}:{client}",
        "task_type": "thinking_step_summary",
        "context_pack": "ThinkingStageContext",
        "reading_id": runtime.reading_id,
        "role_key": role_key,
        "locale": locale,
        "client": client,
        "stage": _stage_context(step),
        "central_brain": _central_brain_context(runtime, role_key=role_key, locale=locale, client=client),
        "xuanming_reasoning": _reasoning_context(reasoning_model, step_id=step_id),
        "module_context": module_context,
        "prompt_profile": _stage_prompt_profile(step_id),
        "role_contract": _thinking_role_contract(role_profile),
        "output_policy": _output_policy(role_profile),
        "context_budget": {
            "analysis_result": "full",
            "summary_panel": "title_body_points",
            "evidence_digest_max_items": 5,
            "xuanming_submodel_count": len(_dict(reasoning_model).keys()),
            "selected_xuanming_submodels": REASONING_BY_STAGE.get(step_id, ["mainline"]),
            "module_context_rows": len(module_context),
            "raw_runtime_payload_included": False,
            "max_output_chars": 560,
        },
        "raw_runtime_payload_included": False,
        "fact_boundary": {
            "chart_fact_mutation_allowed": False,
            "hidden_factor_confirmation_allowed": False,
            "runtime_mutation_allowed": False,
            "policy_pointer_write_allowed": False,
            "raw_runtime_payload_allowed": False,
        },
        "boundary": "thinking_stage_context_pack_is_module_gated_expression_context_not_runtime_payload",
    }
    return context_pack


def _stage_prompt_profile(step_id: str) -> dict[str, object]:
    profile = STAGE_PROMPT_PROFILES.get(step_id)
    if profile:
        return {
            **profile,
            "stage_id": step_id,
            "trainable": True,
            "boundary": "stage_prompt_profile_controls_scene_specific_llm_task",
        }
    return {
        "profile_id": "v30.stage_prompt.supporting_stage.v1",
        "stage_id": step_id,
        "scene": "supporting_stage_summary",
        "task": "只解释本页已确定事实、证据或边界。",
        "must_name": ["stage_fact", "evidence_or_boundary"],
        "avoid": ["不要跨页推演", "不要生成最终结论"],
        "answer_shape": "本页事实 -> 作用 -> 边界",
        "trainable": True,
        "boundary": "stage_prompt_profile_controls_scene_specific_llm_task",
    }


def _stage_context(step: dict[str, object]) -> dict[str, object]:
    analysis = _dict(step.get("analysis_result"))
    return {
        "step_id": step.get("step_id"),
        "title": step.get("title"),
        "phase": step.get("phase"),
        "confidence": step.get("confidence"),
        "analysis_result": analysis,
        "summary_decision": _dict(analysis.get("summary_decision")),
        "summary_policy": _select(_dict(step.get("summary_policy")), ["llm_enhancement", "reason", "signals", "mode"]),
        "summary_panel": _summary_panel_for_prompt(_dict(step.get("summary_panel"))),
        "stage_points": _stage_points_for_prompt(_list(step.get("stage_points"))),
        "stage_point_set": _stage_point_set_for_prompt(_dict(step.get("stage_point_set"))),
        "evidence_digest": _evidence_digest_for_prompt(_dict(step.get("evidence_digest"))),
        "boundary": "stage_context_is_public_reasoning_not_hidden_chain_of_thought",
    }


def _stage_points_for_prompt(points: list[Any]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for point in points[:4]:
        if not isinstance(point, dict):
            continue
        rows.append(_select(point, [
            "kind",
            "text",
            "short_label",
            "bazi_terms",
            "macro_domains",
            "evidence_refs",
            "counter_refs",
            "branch_role",
            "branch_probability",
            "resolution_conditions",
            "display_priority",
            "option_set_ids",
        ]))
    return rows


def _stage_point_set_for_prompt(point_set: dict[str, Any]) -> dict[str, object]:
    if not point_set:
        return {}
    quality = _dict(point_set.get("quality_summary"))
    option_projection = _dict(point_set.get("text_option_projection"))
    return {
        "version": point_set.get("version"),
        "stage_id": point_set.get("stage_id"),
        "source": point_set.get("source"),
        "selected_count": point_set.get("selected_count"),
        "quality_summary": _select(quality, ["average_selected_priority", "average_evidence_binding", "average_template_risk", "average_overclaim_risk"]),
        "text_option_projection": _text_option_projection_for_prompt(option_projection),
    }


def _text_option_projection_for_prompt(projection: dict[str, Any]) -> dict[str, object]:
    if not projection:
        return {}
    option_sets = []
    for row in _list(projection.get("option_sets"))[:4]:
        if not isinstance(row, dict):
            continue
        option_sets.append({
            "topic": row.get("topic"),
            "selection_mode": row.get("selection_mode"),
            "option_labels": [
                str(option.get("label") or "")
                for option in _list(row.get("options"))[:4]
                if isinstance(option, dict) and option.get("label")
            ],
        })
    return {
        "version": projection.get("version"),
        "option_set_count": projection.get("option_set_count"),
        "semantic_unit_count": projection.get("semantic_unit_count"),
        "option_sets": option_sets,
        "boundary": "prompt_sees_option_summary_without_practitioner_selection_state",
    }


def _central_brain_context(
    runtime: CoreRuntimeResult,
    *,
    role_key: str,
    locale: str,
    client: str,
) -> dict[str, object]:
    policy = runtime.question_plan.policy_effect
    trace = _dict(policy.get("central_brain_trace"))
    expression_role = build_expression_role_state(
        reading_id=runtime.reading_id,
        role_key=role_key,
        locale=locale,
        client=client,
    )
    return {
        "version": trace.get("version") or "v30.central_brain.v1",
        "brain_state": _select(_dict(trace.get("brain_state")), ["session_phase", "active_mainline_id", "known_context", "unknown_context", "hidden_factor_focus"]),
        "role_state": expression_role,
        "question_strategy": _select(_dict(trace.get("question_strategy")), ["strategy", "hidden_factor_mode"]),
        "feedback_slots": _list(_dict(trace.get("session_memory")).get("feedback_slots"))[:4],
        "boundaries": [
            "central_brain_coordinates_only",
            "central_brain_does_not_mutate_chart_facts",
        ],
    }


def _reasoning_context(reasoning_model: dict[str, object], *, step_id: str) -> dict[str, object]:
    selected = REASONING_BY_STAGE.get(step_id, ["mainline"])
    return {
        "version": reasoning_model.get("version"),
        "selected_submodels": selected,
        "content": {
            key: _compact_reasoning_value(reasoning_model.get(key))
            for key in selected
            if key in reasoning_model
        },
        "contracts": _dict(reasoning_model.get("contracts")),
        "boundary": "xuanming_reasoning_context_is_selected_public_model_signal",
    }


def _module_context(
    runtime: CoreRuntimeResult,
    *,
    step_id: str,
    reasoning_model: dict[str, object],
) -> list[dict[str, object]]:
    policy = runtime.question_plan.policy_effect
    diagnosis = _dict(policy.get("real_bazi_diagnosis"))
    practical = _dict(policy.get("practical_reading_context"))
    natal = _dict(runtime.chart_context.natal_pillars)
    time_layers = _dict(runtime.chart_context.time_layers)
    if step_id == "chart_build":
        return [
            _module("M1_M2", "chart_facts", {
                "day_master": runtime.chart_context.day_master,
                "day_master_element": runtime.chart_context.day_master_element,
                "natal_pillars": natal,
                "time_layers": _select(time_layers, ["status", "luck_pillar", "flow_year_pillar", "target_year", "target_date"]),
            }),
            _module("xuanming_strength", "initial_strength_frame", _dict(reasoning_model.get("strength_model"))),
        ]
    if step_id == "knowledge_library":
        return [
            _module("M3_knowledge", "knowledge_summary", {
                "krp_library_summary": _dict(policy.get("krp_library_summary")),
                "core_macro_pack_summary": _dict(policy.get("core_macro_pack_summary")),
                "unit_count": len(_list(policy.get("krp_library_units"))),
            })
        ]
    if step_id == "rule_matching":
        return [
            _module("M3_rules", "rule_signals", {
                "signal_count": len(runtime.question_plan.knowledge_rule_portrait_signals),
                "matched_rules": _list(diagnosis.get("matched_rules"))[:6],
                "rule_signals": [row.model_dump(mode="json") if hasattr(row, "model_dump") else row for row in runtime.question_plan.knowledge_rule_portrait_signals[:6]],
            })
        ]
    if step_id == "feature_extraction":
        return [
            _module("M3_features", "feature_evidence", {
                "feature_count": len(runtime.feature_evidence),
                "features": [row.model_dump(mode="json") for row in runtime.feature_evidence[:6]],
            }),
            _module("M4_model_signals", "ten_god_energy_summary", _dict(policy.get("ten_god_energy_summary"))),
        ]
    if step_id == "portrait_projection":
        return [_module("M3_portrait", "portrait_projection", {"portraits": _list(diagnosis.get("portraits"))[:6]})]
    if step_id == "path_reasoning":
        return [
            _module("M3_structure_graph", "structure_graph", {
                "graph_nodes": runtime.structure_state.graph_nodes[:8],
                "graph_edges": runtime.structure_state.graph_edges[:8],
                "path_scores": runtime.structure_state.path_scores,
            }),
            _module("diagnosis_paths", "diagnosis_paths", {"paths": _list(diagnosis.get("paths"))[:6]}),
        ]
    if step_id == "structure_reasoning":
        return [
            _module("M5_ranked_decisions", "ranked_decisions", _public_ranked_decisions(_dict(policy.get("ranked_decisions")))),
            _module("xuanming_structure", "structure_model", _dict(reasoning_model.get("structure_model"))),
            _module("xuanming_useful_god", "useful_god_model", _dict(reasoning_model.get("useful_god_model"))),
        ]
    if step_id == "useful_god_arbitration":
        useful = _dict(reasoning_model.get("useful_god_model"))
        return [
            _module("xuanming_useful_god", "useful_god_model", useful),
            _module("avoidance_model", "useful_god_avoidance", _dict(useful.get("avoidance_model"))),
            _module("M5_ranked_decisions", "ranked_decisions", _public_ranked_decisions(_dict(policy.get("ranked_decisions")))),
        ]
    if step_id == "timing_layers":
        return [_module("M1_M2_time_layers", "luck_flow_context", time_layers)]
    if step_id == "domain_synthesis":
        return [
            _module("M6_practical_reading", "domain_readings", _dict(practical.get("domain_readings"))),
            _module("real_bazi_diagnosis", "diagnosis_claims", {
                "claims": _list(diagnosis.get("claims"))[:6],
                "paths": _list(diagnosis.get("paths"))[:6],
                "portraits": _list(diagnosis.get("portraits"))[:6],
            }),
        ]
    if step_id == "final_report":
        answer = runtime.answer_result
        return [
            _module("M8_answer_surface", "answer_result", {
                "text": answer.text if answer else "",
                "source": answer.source if answer else "",
                "boundary": answer.boundary if answer else "",
            })
        ]
    return [_module("thinking_stage", "stage_context", {"step_id": step_id})]


def _module(module_id: str, section_id: str, content: object) -> dict[str, object]:
    return {
        "module_id": module_id,
        "section_id": section_id,
        "content": _compact_reasoning_value(content),
        "boundary": "module_context_is_read_only_prompt_material",
    }


def _thinking_role_contract(role_profile: dict[str, object]) -> dict[str, object]:
    return {
        "role_contract_id": str(role_profile.get("role_contract_id") or "v30.bazi_llm_role.user.v1"),
        "audience": role_profile.get("audience", "customer_reading"),
        "expression_density": role_profile.get("expression_density", "standard"),
        "terminology_depth": role_profile.get("terminology_depth", "medium"),
        "diagnostics_visible": role_profile.get("diagnostics_visible") is True,
        "allowed_task": "thinking_step_summary",
        "boundary": "thinking_role_contract_controls_stage_summary_visibility",
    }


def _output_policy(role_profile: dict[str, object]) -> dict[str, object]:
    diagnostics_visible = role_profile.get("diagnostics_visible") is True
    return {
        "required_fields": ["text", "public_derivation", "candidate_points", "derived_conclusion", "derived_advice"],
        "max_chars": 560,
        "sentence_count": "2_to_4",
        "forbidden_tokens": [
            "context_id",
            "evidence_id",
            "source_id",
            "trace_id",
            "v30.",
            "krp.",
            "JSON",
            "diagnostics",
        ],
        "diagnostics_visible": diagnostics_visible,
        "uncertainty_policy": {
            "allow_evidence_bound_branches": True,
            "required_branch_fields": ["text", "confidence_or_probability", "evidence_refs", "resolution_conditions"],
            "reject_empty_hedges": ["不好说", "仅供参考", "后续再看"],
            "branch_to_option_set": "central_brain_extracts_practitioner_selectable_options",
        },
        "style": "customer_stage_summary" if not diagnostics_visible else "practitioner_stage_summary",
    }


def _summary_panel_for_prompt(summary_panel: dict[str, Any]) -> dict[str, object]:
    return _select(summary_panel, ["title", "body", "points", "source", "boundary"])


def _evidence_digest_for_prompt(evidence_digest: dict[str, Any]) -> dict[str, object]:
    return {
        **_select(evidence_digest, ["title", "body", "raw_count", "boundary"]),
        "items": _list(evidence_digest.get("items"))[:5],
    }


def _public_ranked_decisions(ranked: dict[str, Any]) -> dict[str, object]:
    out: dict[str, object] = {}
    for key, value in ranked.items():
        row = _dict(value)
        if not row:
            continue
        scores = _dict(row.get("candidate_scores"))
        out[str(key)] = {
            **row,
            "primary_candidate": _public_candidate_label(row.get("primary_candidate", "")),
            "alternatives": [_public_candidate_label(item) for item in _list(row.get("alternatives"))[:4]],
            "candidate_scores": {
                _public_candidate_label(candidate): score
                for candidate, score in list(scores.items())[:4]
            },
        }
    return out


def _public_candidate_label(value: object) -> str:
    raw = str(value or "").strip()
    labels = {
        "strong": "日主偏旺候选",
        "slightly_strong": "日主略偏旺候选",
        "balanced": "平衡取向",
        "slightly_weak": "日主略偏弱候选",
        "weak": "日主偏弱候选",
        "dynamic_structure_review": "动态结构复核",
        "ordinary_structure_review": "常规格局复核",
        "special_structure_boundary_review": "特殊格局边界复核",
        "mediation_path_review": "通关承接路径",
        "resource_or_self_support_review": "印比扶助方向",
        "output_or_wealth_release_review": "食伤生财或财星释放方向",
        "authority_regulation_review": "官杀约束承接方向",
        "climate_regulation_review": "调候平衡方向",
        "balance_review": "平衡调候方向",
        "needs_time_layer_review": "需要时运复核",
    }
    if raw in labels:
        return labels[raw]
    if "evidence-bound" in raw.lower():
        return "证据约束型结构"
    return raw.replace("_", " ") or "候选待复核"


def _compact_reasoning_value(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): _compact_reasoning_value(child) for key, child in list(value.items())[:12]}
    if isinstance(value, list):
        return [_compact_reasoning_value(row) for row in value[:8]]
    return value


def _role_profile(role_key: str) -> dict[str, object]:
    try:
        return role_llm_profile(role_key)
    except ValueError:
        return role_llm_profile("user")


def _select(payload: dict[str, Any], keys: list[str]) -> dict[str, object]:
    return {key: payload.get(key) for key in keys if key in payload}


def _dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []
