from __future__ import annotations

from typing import Any

from v30.brain.stage_points import build_stage_point_set, selected_stage_points
from v30.brain.text_options import build_text_option_projection_from_stage_points, enrich_stage_point_set_with_text_options
from v30.contracts import CoreRuntimeResult
from v30.reasoning import build_xuanming_core_model


THINKING_PROJECTION_VERSION = "v30.thinking_projection.v1"


def build_thinking_projection(runtime: CoreRuntimeResult) -> dict[str, object]:
    reasoning_model = build_xuanming_core_model(runtime)
    policy = runtime.question_plan.policy_effect
    ranked = _dict(policy.get("ranked_decisions"))
    ten_god_summary = _dict(policy.get("ten_god_energy_summary"))
    practical = _dict(policy.get("practical_reading_context"))
    diagnosis = _dict(policy.get("real_bazi_diagnosis"))
    central_reading_state = _dict(policy.get("central_reading_state"))
    steps = [
        _chart_step(runtime),
        _knowledge_step(runtime),
        _rule_step(runtime, diagnosis=diagnosis),
        _feature_step(runtime),
        _portrait_step(diagnosis=diagnosis),
        _path_step(runtime, diagnosis=diagnosis),
        _structure_step(runtime, ranked=ranked, ten_god_summary=ten_god_summary),
        _useful_god_step(reasoning_model=reasoning_model),
        _timing_step(runtime),
        _domain_step(runtime, practical=practical, diagnosis=diagnosis),
        _report_step(runtime),
    ]
    steps = [
        _attach_stage_question_opportunity(_enrich_step(step, runtime, reasoning_model), central_reading_state)
        for step in steps
    ]
    journey_steps = _journey_steps(runtime, steps, reasoning_model, central_reading_state)
    completed = sum(1 for step in journey_steps if step["status"] == "completed")
    return {
        "version": THINKING_PROJECTION_VERSION,
        "reading_id": runtime.reading_id,
        "trace_id": runtime.trace_id,
        "mode": "professional_thinking",
        "title": "八字专业推演流",
        "summary": "将细粒度规则、画像、路径、用神和时运素材压缩成 7 个高层阶段；步骤页沉淀素材，最终由 Decision Engine 裁决。",
        "progress": {
            "completed_steps": completed,
            "total_steps": len(journey_steps),
            "label": f"阶段 {completed}/{len(journey_steps)}",
        },
        "credit_preview": _credit_preview(),
        "reasoning_model": reasoning_model,
        "central_reading_state": central_reading_state,
        "sidebar_memory": _sidebar_memory(runtime, reasoning_model, steps),
        "journey_steps": journey_steps,
        "steps": steps,
        "material_step_count": len(steps),
        "tabs": ["排盘", "结构用神", "素材", "路径时运", "校准", "裁决", "建议"],
        "boundary": "thinking_projection_explains_runtime_reasoning_without_becoming_hidden_chain_of_thought",
    }


def _attach_stage_question_opportunity(
    step: dict[str, object],
    central_reading_state: dict[str, object],
) -> dict[str, object]:
    step_id = str(step.get("step_id") or "")
    opportunities = _list(central_reading_state.get("stage_question_opportunities"))
    opportunity = next(
        (
            row for row in opportunities
            if isinstance(row, dict) and str(row.get("step_id") or "") == step_id
        ),
        None,
    )
    if not opportunity:
        return step
    return {
        **step,
        "stage_question_opportunity": opportunity,
        "next_action": _dict(central_reading_state.get("next_action")),
    }


def _journey_steps(
    runtime: CoreRuntimeResult,
    material_steps: list[dict[str, object]],
    reasoning_model: dict[str, object],
    central_reading_state: dict[str, object],
) -> list[dict[str, object]]:
    step_map = {str(step.get("step_id") or ""): step for step in material_steps}
    final_synthesis = _final_synthesis(runtime)
    verdicts = _list(central_reading_state.get("decision_verdicts"))
    conflicts = _list(_dict(central_reading_state.get("decision_input_bundle")).get("conflicts"))
    return [
        _journey_step(
            step_id="journey_chart_calibration",
            phase="校准",
            title="资料与排盘校准",
            summary=_summary_from_steps(step_map, ["chart_build"]),
            material_stage_ids=["chart_build"],
            source_steps=step_map,
            conclusion=_analysis_text(step_map, "chart_build", "conclusion"),
            advice="确认出生资料、四柱、日主和时间层边界，再进入结构判断。",
            points=_journey_points_from_steps(step_map, ["chart_build"], limit=3),
            evidence=_material_evidence(step_map, ["chart_build"]),
            confidence=_avg_confidence(step_map, ["chart_build"]),
        ),
        _journey_step(
            step_id="journey_structure_useful_god",
            phase="判断",
            title="结构、十神与用神候选",
            summary=_summary_from_steps(step_map, ["structure_reasoning", "useful_god_arbitration"]),
            material_stage_ids=["structure_reasoning", "useful_god_arbitration"],
            source_steps=step_map,
            conclusion=_join_short([
                _analysis_text(step_map, "structure_reasoning", "conclusion"),
                _analysis_text(step_map, "useful_god_arbitration", "conclusion"),
            ]),
            advice=_join_short([
                _analysis_text(step_map, "structure_reasoning", "next_focus"),
                _analysis_text(step_map, "useful_god_arbitration", "next_focus"),
            ]),
            points=_journey_points_from_steps(step_map, ["structure_reasoning", "useful_god_arbitration"], limit=4),
            evidence=_material_evidence(step_map, ["structure_reasoning", "useful_god_arbitration"]),
            confidence=_avg_confidence(step_map, ["structure_reasoning", "useful_god_arbitration"]),
        ),
        _journey_step(
            step_id="journey_material_candidates",
            phase="取材",
            title="规则、画像与特征素材",
            summary=_summary_from_steps(step_map, ["knowledge_library", "rule_matching", "feature_extraction", "portrait_projection"]),
            material_stage_ids=["knowledge_library", "rule_matching", "feature_extraction", "portrait_projection"],
            source_steps=step_map,
            conclusion="规则、画像和特征已经转成候选素材，本阶段只保留证据和分支，不做最终断语。",
            advice="优先看证据密度高、能被结构和路径同时解释的素材。",
            points=_journey_points_from_steps(step_map, ["rule_matching", "feature_extraction", "portrait_projection"], limit=4),
            evidence=_material_evidence(step_map, ["knowledge_library", "rule_matching", "feature_extraction", "portrait_projection"]),
            confidence=_avg_confidence(step_map, ["knowledge_library", "rule_matching", "feature_extraction", "portrait_projection"]),
        ),
        _journey_step(
            step_id="journey_path_timing_domain",
            phase="合成",
            title="做功路径、时运与领域触发",
            summary=_summary_from_steps(step_map, ["path_reasoning", "timing_layers", "domain_synthesis"]),
            material_stage_ids=["path_reasoning", "timing_layers", "domain_synthesis"],
            source_steps=step_map,
            conclusion=_join_short([
                _analysis_text(step_map, "path_reasoning", "conclusion"),
                _analysis_text(step_map, "timing_layers", "conclusion"),
                _analysis_text(step_map, "domain_synthesis", "conclusion"),
            ]),
            advice="把路径、时运和领域触发规整成候选，不在本阶段扩写成长篇结论。",
            points=_journey_points_from_steps(step_map, ["path_reasoning", "timing_layers", "domain_synthesis"], limit=4),
            evidence=_material_evidence(step_map, ["path_reasoning", "timing_layers", "domain_synthesis"]),
            confidence=_avg_confidence(step_map, ["path_reasoning", "timing_layers", "domain_synthesis"]),
        ),
        _journey_step(
            step_id="journey_branch_calibration",
            phase="校准",
            title="分支冲突与命理师校准",
            summary=_branch_summary(conflicts),
            material_stage_ids=["rule_matching", "useful_god_arbitration", "domain_synthesis"],
            source_steps=step_map,
            conclusion=_branch_conclusion(conflicts),
            advice=_branch_advice(conflicts),
            points=_branch_points(conflicts),
            evidence=_branch_evidence(conflicts),
            confidence=0.76 if conflicts else 0.88,
        ),
        _journey_step(
            step_id="journey_decision_verdicts",
            phase="裁决",
            title="Decision Engine 裁决",
            summary=_decision_summary(verdicts),
            material_stage_ids=["final_report"],
            source_steps=step_map,
            conclusion=_decision_conclusion(verdicts),
            advice=_decision_advice(verdicts),
            points=_decision_points(verdicts),
            evidence=_decision_evidence(verdicts),
            confidence=_decision_confidence(verdicts),
        ),
        _journey_step(
            step_id="journey_final_expression",
            phase="表达",
            title="最终断语、建议与智能对话",
            summary=_truncate(str(final_synthesis.get("customer_summary") or ""), 140) or "最终表达只消费 Decision Verdict，并在必要时进入智能对话。",
            material_stage_ids=["final_report"],
            source_steps=step_map,
            conclusion=str(final_synthesis.get("conclusion") or _decision_conclusion(verdicts)),
            advice=str(final_synthesis.get("advice") or _decision_advice(verdicts)),
            points=_final_expression_points(final_synthesis, verdicts),
            evidence=_final_synthesis_evidence(final_synthesis) or _decision_evidence(verdicts),
            confidence=0.88 if final_synthesis.get("status") == "ready" else _decision_confidence(verdicts),
        ),
    ]


def _journey_step(
    *,
    step_id: str,
    phase: str,
    title: str,
    summary: str,
    material_stage_ids: list[str],
    source_steps: dict[str, dict[str, object]],
    conclusion: str,
    advice: str,
    points: list[dict[str, object]],
    evidence: list[str],
    confidence: float,
) -> dict[str, object]:
    material_titles = [
        str(source_steps.get(stage_id, {}).get("title") or stage_id)
        for stage_id in material_stage_ids
        if source_steps.get(stage_id)
    ]
    final_decision = {
        "version": "v30.journey_stage_final_decision.v1",
        "conclusion": conclusion,
        "advice": advice,
        "stage_points": points,
        "boundary": "journey_stage_decision_is_material_or_verdict_projection_not_llm_longform",
    }
    option_source_points = [
        point for point in points
        if isinstance(point, dict) and _list(point.get("option_hints"))
    ]
    projection = build_text_option_projection_from_stage_points(
        option_source_points,
        stage_id=step_id,
        source="decision_centered_journey_step",
    )
    branch_option_sets = [
        option_set for option_set in _list(projection.get("option_sets"))
        if isinstance(option_set, dict) and str(option_set.get("source_type") or "") == "stage_point_branch"
    ]
    projection = {
        **projection,
        "option_sets": branch_option_sets,
        "option_set_count": len(branch_option_sets),
        "semantic_units": [],
        "semantic_unit_count": 0,
        "boundary": "journey_text_option_projection_keeps_explicit_branch_options_only",
    }
    analysis_result = {
        "version": "v30.journey_stage_analysis_result.v1",
        "conclusion": conclusion,
        "reasoning_points": material_titles[:4],
        "contradictions": [],
        "next_focus": advice,
        "user_summary": summary,
        "public_trace": _journey_public_trace(material_titles, evidence, points),
        "final_decision": final_decision,
        "boundary": "journey_stage_analysis_aggregates_clean_material_without_default_llm_explanation",
    }
    return {
        "step_id": step_id,
        "journey_stage": True,
        "phase": phase,
        "title": title,
        "status": "completed",
        "summary": summary,
        "tasks": material_titles,
        "material_stage_ids": material_stage_ids,
        "evidence": evidence[:8],
        "evidence_digest": _evidence_digest(step_id, evidence),
        "confidence": round(max(0.0, min(float(confidence), 1.0)), 2),
        "analysis_result": analysis_result,
        "summary_policy": _journey_summary_policy(step_id),
        "stage_point_set": {
            "version": "v30.journey_stage_point_set.v1",
            "stage_id": step_id,
            "source": "decision_centered_journey_step",
            "points": points,
            "selected_points": points,
            "text_option_projection": projection,
            "option_sets": projection["option_sets"],
            "semantic_units": projection["semantic_units"],
            "boundary": "journey_stage_point_set_is_projection_not_raw_material",
        },
        "stage_points": points,
        "summary_panel": {
            "version": "v30.stage_summary_panel.v1",
            "title": title,
            "body": _join_short([conclusion, advice]),
            "points": [str(point.get("text") or "") for point in points[:4] if isinstance(point, dict)],
            "summary_policy": _journey_summary_policy(step_id),
            "source": "decision_centered_journey_projection",
            "llm_metadata": {
                "status": "not_requested",
                "executed": False,
                "boundary": "journey_steps_do_not_call_llm_by_default",
            },
            "boundary": "journey_summary_panel_projects_material_and_verdicts_without_llm_longform",
        },
        "narration": _join_short([conclusion, advice]),
        "credit_preview": _credit_preview(),
        "boundary": "decision_centered_journey_step_compresses_material_steps_for_user_navigation",
    }


def _journey_summary_policy(step_id: str) -> dict[str, object]:
    return {
        "version": "v30.stage_summary_policy.v1",
        "mode": "compact",
        "display_summary": True,
        "llm_enhancement": "not_required",
        "prefetch_next": False,
        "reason": "DCA 7 阶段页只展示素材、分支或 Verdict，不默认调用 LLM 生成长文。",
        "signals": {
            "token_budget_class": "save",
            "llm_needed_reason": "decision_centered_journey_uses_structured_material",
            "focus_scope": "journey_stage",
            "central_brain_contract": "decision_engine_verdict_before_llm_expression",
            "provider_thinking_mode": "off",
            "prompt_profile": _stage_prompt_profile_signal(step_id),
        },
        "training_signal": {
            "signal_id": "v30.training_signal.decision_centered_journey_summary_policy",
            "trainable": True,
            "target": "journey_stage_material_projection_quality",
        },
        "boundary": "journey_summary_policy_blocks_default_per_step_llm_longform",
    }


def _summary_from_steps(step_map: dict[str, dict[str, object]], stage_ids: list[str]) -> str:
    rows = [
        str(step_map.get(stage_id, {}).get("summary") or "").strip()
        for stage_id in stage_ids
        if step_map.get(stage_id)
    ]
    return _truncate(_join_short(rows), 140)


def _analysis_text(step_map: dict[str, dict[str, object]], stage_id: str, key: str) -> str:
    return str(_dict(step_map.get(stage_id, {}).get("analysis_result")).get(key) or "").strip()


def _journey_points_from_steps(
    step_map: dict[str, dict[str, object]],
    stage_ids: list[str],
    *,
    limit: int,
) -> list[dict[str, object]]:
    points: list[dict[str, object]] = []
    for stage_id in stage_ids:
        step = step_map.get(stage_id, {})
        for point in _list(step.get("stage_points")):
            if not isinstance(point, dict):
                continue
            text = str(point.get("text") or "").strip()
            if not text:
                continue
            points.append(
                {
                    "kind": str(point.get("kind") or "mechanism"),
                    "kind_label": str(point.get("kind_label") or ""),
                    "short_label": str(point.get("short_label") or ""),
                    "text": text,
                    "source_stage_id": stage_id,
                    "confidence": point.get("confidence", step.get("confidence", 0.0)),
                    "boundary": "journey_point_is_selected_stage_material_not_llm_longform",
                }
            )
            if len(points) >= limit:
                return points
    if not points:
        for stage_id in stage_ids:
            conclusion = _analysis_text(step_map, stage_id, "conclusion")
            advice = _analysis_text(step_map, stage_id, "next_focus")
            for kind, text in (("verdict", conclusion), ("advice", advice)):
                if text:
                    points.append(
                        {
                            "kind": kind,
                            "short_label": str(step_map.get(stage_id, {}).get("title") or ""),
                            "text": text,
                            "source_stage_id": stage_id,
                            "boundary": "journey_point_falls_back_to_stage_analysis_result",
                        }
                    )
                if len(points) >= limit:
                    return points
    return points[:limit]


def _material_evidence(step_map: dict[str, dict[str, object]], stage_ids: list[str]) -> list[str]:
    rows: list[str] = []
    for stage_id in stage_ids:
        for item in _list(step_map.get(stage_id, {}).get("evidence")):
            text = str(item).strip()
            if text and text not in rows:
                rows.append(text)
    return rows[:8]


def _avg_confidence(step_map: dict[str, dict[str, object]], stage_ids: list[str]) -> float:
    values = [
        float(step_map.get(stage_id, {}).get("confidence") or 0.0)
        for stage_id in stage_ids
        if step_map.get(stage_id)
    ]
    return round(sum(values) / len(values), 2) if values else 0.5


def _branch_summary(conflicts: list[object]) -> str:
    display_conflicts = _branch_display_conflicts(conflicts)
    if not display_conflicts:
        return "当前分支冲突较少，可以进入 Decision Engine 裁决。"
    return f"发现 {len(display_conflicts)} 组需要校准的分支判断。"


def _branch_conclusion(conflicts: list[object]) -> str:
    display_conflicts = _branch_display_conflicts(conflicts)
    if not display_conflicts:
        return "本盘当前没有高优先级分支冲突，候选可以直接进入裁决。"
    first = _dict(display_conflicts[0])
    domain = _domain_label(str(first.get("domain") or "overview"))
    return f"{domain}判断存在主分支与备选分支，需要先保留两条线，再用反馈拉开权重。"


def _branch_advice(conflicts: list[object]) -> str:
    display_conflicts = _branch_display_conflicts(conflicts)
    if not display_conflicts:
        return "命理师模式可继续复核候选权重，普通用户可直接看裁决页。"
    first = _dict(display_conflicts[0])
    question = str(first.get("needed_question") or "")
    return question or "优先回答能降低分支冲突的一个关键问题。"


def _branch_points(conflicts: list[object]) -> list[dict[str, object]]:
    display_conflicts = _branch_display_conflicts(conflicts, limit=4)
    if not display_conflicts:
        return [
            {
                "kind": "verdict",
                "short_label": "暂无高冲突",
                "text": "当前候选之间没有明显高冲突，可以先交给 Decision Engine 裁决。",
                "boundary": "branch_stage_reports_absence_of_high_conflict",
            }
        ]
    rows: list[dict[str, object]] = []
    for raw in display_conflicts:
        conflict = _dict(raw)
        domain = _domain_label(str(conflict.get("domain") or "overview"))
        conflict_id = str(conflict.get("conflict_id") or f"conflict:{len(rows) + 1}")
        branch_a_id = str(conflict.get("branch_a_id") or "")
        branch_b_id = str(conflict.get("branch_b_id") or "")
        question = str(conflict.get("needed_question") or "")
        policy_label = _branch_resolution_label(str(conflict.get("resolution_policy") or ""))
        text = f"{domain}判断存在分支：{policy_label}"
        rows.append(
            {
                "point_id": f"journey.branch.{conflict_id}",
                "stage_id": "journey_branch_calibration",
                "kind": "branch",
                "short_label": domain,
                "text": f"{text}{' 关键问题：' + question if question else ''}",
                "source_conflict_id": conflict_id,
                "branch_probability": 0.62,
                "macro_domains": [str(conflict.get("domain") or "overview")],
                "evidence_refs": [
                    str(item)
                    for item in [*_list(conflict.get("evidence_for_a")), *_list(conflict.get("evidence_for_b"))]
                    if str(item)
                ][:5],
                "option_hints": _branch_conflict_option_hints(
                    domain=domain,
                    conflict_id=conflict_id,
                    branch_a_id=branch_a_id,
                    branch_b_id=branch_b_id,
                    question=question,
                ),
                "resolution_conditions": [
                    policy_label,
                    question,
                ],
                "boundary": "branch_point_preserves_conflict_for_practitioner_or_voi_dialogue",
            }
        )
    return rows


def _branch_display_conflicts(conflicts: list[object], *, limit: int = 6) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for raw in conflicts:
        conflict = _dict(raw)
        domain = str(conflict.get("domain") or "overview")
        question = str(conflict.get("needed_question") or "")
        key = f"{domain}:{question or conflict.get('branch_a_id') or conflict.get('top_candidate_id') or len(rows)}"
        if key in seen:
            continue
        seen.add(key)
        rows.append(conflict)
        if len(rows) >= limit:
            break
    return rows


def _branch_resolution_label(value: str) -> str:
    if "ask_only_if_value" in value:
        return "先不打扰用户，只有这个问题能明显改变判断时再追问。"
    if "downgrade_assertion" in value:
        return "反证没有解决前，断语先降一档，不急着下重结论。"
    if "keep_both_branches" in value:
        return "主分支和备选先同时保留，等待命理师或用户反馈拉开权重。"
    return "主分支和备选先同时保留，等待更多证据。"


def _branch_conflict_option_hints(
    *,
    domain: str,
    conflict_id: str,
    branch_a_id: str,
    branch_b_id: str,
    question: str,
) -> list[dict[str, object]]:
    primary_value = branch_a_id or f"{conflict_id}:primary_branch"
    secondary_value = branch_b_id or f"{conflict_id}:needs_question"
    hints = [
        {
            "label": "采纳主分支",
            "value": primary_value,
            "probability": 0.62,
            "meaning": f"命理师确认{domain}当前主分支可以升权。",
        },
        {
            "label": "保留备选",
            "value": secondary_value,
            "probability": 0.48,
            "meaning": f"保留{domain}备选分支，等待用户反馈或更多证据。",
        },
    ]
    if question:
        hints.append(
            {
                "label": "转为追问",
                "value": f"{conflict_id}:ask",
                "probability": 0.42,
                "meaning": question,
            }
        )
    return hints


def _branch_evidence(conflicts: list[object]) -> list[str]:
    rows: list[str] = []
    for raw in conflicts:
        conflict = _dict(raw)
        for key in ("evidence_for_a", "evidence_for_b"):
            for item in _list(conflict.get(key)):
                text = str(item).strip()
                if text and text not in rows:
                    rows.append(text)
    return rows[:8]


def _decision_summary(verdicts: list[object]) -> str:
    if not verdicts:
        return "Decision Engine 暂未形成可用 Verdict。"
    return f"Decision Engine 已形成 {len(verdicts)} 条 Verdict，最终表达必须以这些裁决为边界。"


def _decision_conclusion(verdicts: list[object]) -> str:
    top = _dict(verdicts[0]) if verdicts else {}
    if not top:
        return "当前素材不足，暂不形成最终断语。"
    return str(top.get("headline") or "")


def _decision_advice(verdicts: list[object]) -> str:
    top = _dict(verdicts[0]) if verdicts else {}
    advice = [str(row) for row in _list(top.get("advice_points")) if str(row)]
    return " ".join(advice[:2]) or "围绕 Verdict 的允许断语生成建议，不新增命盘事实。"


def _decision_points(verdicts: list[object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for raw in verdicts[:4]:
        verdict = _dict(raw)
        headline = str(verdict.get("headline") or "")
        if not headline:
            continue
        verdict_id = str(verdict.get("verdict_id") or "")
        primary_branch = str(verdict.get("primary_branch_id") or "")
        alternative_branches = [str(row) for row in _list(verdict.get("alternative_branch_ids")) if str(row)]
        option_hints = _decision_option_hints(
            primary_branch=primary_branch,
            alternative_branches=alternative_branches,
            confidence=_float(verdict.get("confidence"), 0.0),
        )
        rows.append(
            {
                "point_id": f"journey.decision.{verdict_id or len(rows) + 1}.verdict",
                "stage_id": "journey_decision_verdicts",
                "kind": "verdict" if str(verdict.get("assertion_level") or "") not in {"mixed", "weak_candidate"} else "branch",
                "short_label": _domain_label(str(verdict.get("domain") or "")),
                "text": headline,
                "confidence": verdict.get("confidence", 0.0),
                "branch_probability": verdict.get("confidence", 0.0),
                "evidence_refs": [str(row) for row in _list(verdict.get("evidence_refs"))[:3]],
                "macro_domains": [str(verdict.get("domain") or "")],
                "option_hints": option_hints,
                "boundary": "decision_point_comes_from_decision_engine_verdict",
            }
        )
        for advice in _list(verdict.get("advice_points"))[:1]:
            rows.append(
                {
                    "point_id": f"journey.decision.{verdict_id or len(rows) + 1}.advice",
                    "stage_id": "journey_decision_verdicts",
                    "kind": "advice",
                    "short_label": "建议",
                    "text": str(advice),
                    "source_verdict_id": verdict_id,
                    "macro_domains": [str(verdict.get("domain") or "")],
                    "boundary": "decision_advice_point_comes_from_decision_engine_verdict",
                }
            )
    return rows[:5]


def _decision_option_hints(
    *,
    primary_branch: str,
    alternative_branches: list[str],
    confidence: float,
) -> list[dict[str, object]]:
    if not primary_branch or not alternative_branches:
        return []
    hints = [
        {
            "label": "采纳主分支",
            "value": primary_branch,
            "probability": confidence,
            "meaning": "命理师确认当前 Verdict 主分支更贴合盘面和现实反馈",
        }
    ]
    for index, branch_id in enumerate(alternative_branches[:3], start=1):
        hints.append(
            {
                "label": f"保留备选{index}",
                "value": branch_id,
                "probability": max(0.18, round(confidence - index * 0.12, 2)),
                "meaning": "命理师认为该备选分支仍需保留或升权",
            }
        )
    return hints


def _decision_evidence(verdicts: list[object]) -> list[str]:
    rows: list[str] = []
    for raw in verdicts:
        verdict = _dict(raw)
        for key in ("evidence_refs", "counter_evidence_refs"):
            for item in _list(verdict.get(key)):
                text = str(item).strip()
                if text and text not in rows:
                    rows.append(text)
    return rows[:8]


def _decision_confidence(verdicts: list[object]) -> float:
    values = [_float(_dict(row).get("confidence"), 0.0) for row in verdicts if isinstance(row, dict)]
    return round(max(values), 2) if values else 0.45


def _final_expression_points(final_synthesis: dict[str, object], verdicts: list[object]) -> list[dict[str, object]]:
    conclusion = str(final_synthesis.get("conclusion") or "")
    advice = str(final_synthesis.get("advice") or "")
    rows = [
        {"kind": "verdict", "short_label": "最终断语", "text": conclusion, "boundary": "final_expression_uses_final_synthesis"},
        {"kind": "advice", "short_label": "行动建议", "text": advice, "boundary": "final_expression_uses_final_synthesis"},
    ]
    rows = [row for row in rows if row["text"]]
    return rows or _decision_points(verdicts)


def _journey_public_trace(material_titles: list[str], evidence: list[str], points: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if material_titles:
        rows.append(_trace("素材来源", "、".join(material_titles[:4])))
    if evidence:
        rows.append(_trace("证据摘要", "、".join(evidence[:3])))
    if points:
        rows.append(_trace("本阶段作用", str(points[0].get("text") or "")[:120]))
    return rows


def _join_short(rows: list[str]) -> str:
    clean: list[str] = []
    for row in rows:
        text = str(row or "").strip()
        if text and text not in clean:
            clean.append(text)
    return " ".join(clean)


def _chart_step(runtime: CoreRuntimeResult) -> dict[str, object]:
    chart = runtime.chart_context
    source = _dict(chart.input_pillars.get("chart_build_source"))
    conversion = _dict(chart.input_pillars.get("conversion_trace"))
    pillars = _dict(chart.natal_pillars)
    tasks = [
        f"读取出生资料与历法假设：{source.get('calendar_assumption') or 'explicit_pillars'}",
        f"确认四柱：{_pillar_summary(pillars)}",
        f"确定日主：{chart.day_master}（{chart.day_master_element}）",
    ]
    if conversion:
        tasks.insert(1, f"执行时区/历法校准：{conversion.get('status') or 'ready'}")
    return _step(
        step_id="chart_build",
        phase="思考",
        title="时空校准与四柱排盘",
        summary=f"命盘基础已建立，日主为 {chart.day_master}。",
        tasks=tasks,
        evidence=[
            f"context_id={chart.context_id}",
            f"source={source.get('source') or 'runtime'}",
        ],
        confidence=1.0 if source.get("status", "ready") == "ready" else 0.62,
    )


def _structure_step(
    runtime: CoreRuntimeResult,
    *,
    ranked: dict[str, Any],
    ten_god_summary: dict[str, Any],
) -> dict[str, object]:
    structure = runtime.structure_state
    structure_label = _structure_label(structure.semantic_label or structure.state)
    decision_rows = [
        _decision_line(key, value)
        for key, value in ranked.items()
        if isinstance(value, dict)
    ]
    top_energy = ten_god_summary.get("top_energy")
    tasks = [
        f"抽取特征证据：{len(runtime.feature_evidence)} 条",
        f"选择结构主线：{structure_label}",
        f"评估主链：{_chain_label(structure.primary_chain[:4]) if structure.primary_chain else structure_label}",
    ]
    if isinstance(top_energy, list) and top_energy:
        tasks.append(f"识别十神能量重点：{' / '.join(_ten_god_energy_label(row) for row in top_energy[:4])}")
    return _step(
        step_id="structure_reasoning",
        phase="分析",
        title="结构、十神与用神判断",
        summary=f"{structure_label}，置信度 {structure.confidence:.2f}。",
        tasks=tasks,
        evidence=[*decision_rows[:5], *_feature_lines(runtime)],
        confidence=structure.confidence,
    )


def _useful_god_step(*, reasoning_model: dict[str, object]) -> dict[str, object]:
    useful = _dict(reasoning_model.get("useful_god_model"))
    avoidance = _dict(useful.get("avoidance_model"))
    candidates = _list(useful.get("candidates"))
    primary_label = str(useful.get("primary_label") or "用神候选待复核")
    element_labels = _useful_element_labels(useful)
    family_labels = _useful_family_labels(useful)
    risks = [str(row) for row in _list(avoidance.get("primary_risks")) if str(row).strip()]
    tasks = [
        f"审定取用策略：{primary_label}",
        f"候选五行：{'、'.join(element_labels) or '待复核'}",
        f"候选十神族：{'、'.join(family_labels) or '待复核'}",
        f"忌避风险：{risks[0] if risks else '避免固定唯一用神'}",
    ]
    return _step(
        step_id="useful_god_arbitration",
        phase="分析",
        title="用神忌神与取舍",
        summary=f"当前用神取向优先看{primary_label}，忌避风险需结合反证保留。",
        tasks=tasks,
        evidence=_useful_god_lines(useful, candidates),
        confidence=0.86 if useful.get("status") == "ready" else 0.56,
    )


def _knowledge_step(runtime: CoreRuntimeResult) -> dict[str, object]:
    policy = runtime.question_plan.policy_effect
    units = _list(policy.get("krp_library_units"))
    summary = _dict(policy.get("krp_library_summary"))
    macro_summary = _dict(policy.get("core_macro_pack_summary"))
    tasks = [
        f"加载 KRP 知识单元：{len(units)} 条",
        f"校验宏观知识包：{macro_summary.get('status') or summary.get('status') or 'available'}",
        "仅使用 V30 知识接口，不读取 V20 运行态",
    ]
    return _step(
        step_id="knowledge_library",
        phase="思考",
        title="八字知识库装载",
        summary="先把可用的古籍、规则、画像与结构知识转成可调用的 V30 知识单元。",
        tasks=tasks,
        evidence=_knowledge_lines(units),
        confidence=0.88 if units else 0.55,
    )


def _rule_step(runtime: CoreRuntimeResult, *, diagnosis: dict[str, Any]) -> dict[str, object]:
    signals = runtime.question_plan.knowledge_rule_portrait_signals
    matches = _list(diagnosis.get("matched_rules"))
    tasks = [
        f"扫描规则画像信号：{len(signals)} 条",
        f"命中诊断规则：{len(matches)} 条",
        "规则只提供证据与倾向，不直接改写命盘事实",
    ]
    return _step(
        step_id="rule_matching",
        phase="分析",
        title="八字规则匹配",
        summary="把命盘结构与规则库逐条对照，筛出可解释的命中规则。",
        tasks=tasks,
        evidence=_rule_lines(signals, matches),
        confidence=0.84 if signals or matches else 0.52,
    )


def _feature_step(runtime: CoreRuntimeResult) -> dict[str, object]:
    domains = sorted({row.domain for row in runtime.feature_evidence if row.domain})
    kinds = sorted({row.kind for row in runtime.feature_evidence if row.kind})
    tasks = [
        f"抽取八字特征：{len(runtime.feature_evidence)} 条",
        f"覆盖领域：{', '.join(domains[:6]) or '基础结构'}",
        f"特征类型：{', '.join(kinds[:6]) or 'evidence'}",
    ]
    return _step(
        step_id="feature_extraction",
        phase="分析",
        title="八字特征抽取",
        summary="把四柱、十神、五行、结构和时运转成后续可消费的特征证据。",
        tasks=tasks,
        evidence=_feature_lines(runtime),
        confidence=0.86 if runtime.feature_evidence else 0.5,
    )


def _portrait_step(*, diagnosis: dict[str, Any]) -> dict[str, object]:
    portraits = _list(diagnosis.get("portraits"))
    domains = sorted({
        str(row.get("domain") or "")
        for row in portraits
        if isinstance(row, dict) and row.get("domain")
    })
    tasks = [
        f"生成八字画像：{len(portraits)} 条",
        f"画像领域：{', '.join(domains[:6]) or '待生成'}",
        "画像用于解释命主倾向，不作为固定事件预测",
    ]
    return _step(
        step_id="portrait_projection",
        phase="分析",
        title="八字画像投影",
        summary="把规则命中和特征证据合成为可读的人格、事业、财富、关系等画像。",
        tasks=tasks,
        evidence=_portrait_lines(portraits),
        confidence=0.8 if portraits else 0.5,
    )


def _path_step(runtime: CoreRuntimeResult, *, diagnosis: dict[str, Any]) -> dict[str, object]:
    diagnosis_paths = _list(diagnosis.get("paths"))
    graph_nodes = runtime.structure_state.graph_nodes
    graph_edges = runtime.structure_state.graph_edges
    path_scores = runtime.structure_state.path_scores
    tasks = [
        f"生成做功路径：{len(diagnosis_paths)} 条",
        f"结构图节点：{len(graph_nodes)} 个",
        f"结构图边：{len(graph_edges)} 条",
        f"动态路径分数：{len(path_scores)} 项",
    ]
    return _step(
        step_id="path_reasoning",
        phase="分析",
        title="做功路径与结构图",
        summary="把命局中的力量流向、领域牵引和时运触发整理成可解释路径。",
        tasks=tasks,
        evidence=_path_lines(diagnosis_paths, path_scores),
        confidence=0.82 if diagnosis_paths or path_scores else 0.52,
    )


def _timing_step(runtime: CoreRuntimeResult) -> dict[str, object]:
    layers = _dict(runtime.chart_context.time_layers)
    luck = _dict(layers.get("luck_cycle_context"))
    flow = _dict(layers.get("flow_context"))
    six = _dict(layers.get("six_pillar_context"))
    tasks = [
        f"确认时间层状态：{layers.get('status') or 'ready'}",
        f"定位当前大运：{luck.get('current_luck_pillar') or luck.get('luck_pillar') or '待确认'}",
        f"定位流年：{flow.get('flow_year_pillar') or '待确认'}",
    ]
    if six.get("status"):
        tasks.append(f"合成六柱上下文：{six.get('status')}")
    return _step(
        step_id="timing_layers",
        phase="分析",
        title="大运、流年与时间层",
        summary="把原局判断放入当前时运，形成年度分析框架。",
        tasks=tasks,
        evidence=[
            f"luck_start_year={luck.get('start_year') or '-'}",
            f"target_date={flow.get('target_date') or '-'}",
        ],
        confidence=0.86 if layers else 0.5,
    )


def _domain_step(
    runtime: CoreRuntimeResult,
    *,
    practical: dict[str, Any],
    diagnosis: dict[str, Any],
) -> dict[str, object]:
    domains = _dict(practical.get("domain_readings"))
    domain_names = list(domains)[:6]
    claims = diagnosis.get("claims")
    portraits = diagnosis.get("portraits")
    paths = diagnosis.get("paths")
    tasks = [
        f"生成领域解读：{len(domains)} 个领域",
        f"诊断画像：{len(portraits) if isinstance(portraits, list) else 0} 条",
        f"动态路径：{len(paths) if isinstance(paths, list) else 0} 条",
        f"可解释主张：{len(claims) if isinstance(claims, list) else 0} 条",
    ]
    return _step(
        step_id="domain_synthesis",
        phase="分析",
        title="领域专项与证据合成",
        summary=f"已形成 {', '.join(domain_names) if domain_names else '基础领域'} 的可读解读。",
        tasks=tasks,
        evidence=_domain_lines(domains),
        confidence=0.82 if domains else 0.58,
    )


def _report_step(runtime: CoreRuntimeResult) -> dict[str, object]:
    answer = runtime.answer_result
    answer_text = answer.text if answer is not None else ""
    final_synthesis = _final_synthesis(runtime)
    llm_status = _dict(answer.llm_metadata if answer is not None else {}).get("status", "")
    tasks = [
        "合并命盘事实、结构判断、时运和领域证据",
        "按中枢最终合成选择结论和建议",
        "保留证据链与边界说明",
    ]
    if llm_status:
        tasks.append(f"表达层状态：{llm_status}")
    return _step(
        step_id="final_report",
        phase="撰写报告",
        title="最终报告与行动建议",
        summary=_truncate(str(final_synthesis.get("customer_summary") or answer_text), 120) or "报告将在完成问题选择后生成。",
        tasks=tasks,
        evidence=_final_synthesis_evidence(final_synthesis) or (list(answer.evidence_ids[:6]) if answer is not None else []),
        confidence=0.88 if final_synthesis.get("status") == "ready" else 0.45,
    )


def _step(
    *,
    step_id: str,
    phase: str,
    title: str,
    summary: str,
    tasks: list[str],
    evidence: list[str],
    confidence: float,
) -> dict[str, object]:
    return {
        "step_id": step_id,
        "phase": phase,
        "title": title,
        "status": "completed",
        "summary": summary,
        "tasks": [row for row in tasks if row],
        "evidence": [row for row in evidence if row],
        "evidence_digest": _evidence_digest(step_id, evidence),
        "confidence": round(max(0.0, min(float(confidence), 1.0)), 2),
        "credit_preview": _credit_preview(),
        "boundary": "public_reasoning_step_summarizes_evidence_not_hidden_chain_of_thought",
    }


def _enrich_step(
    step: dict[str, object],
    runtime: CoreRuntimeResult,
    reasoning_model: dict[str, object],
) -> dict[str, object]:
    analysis_result = _analysis_result(step, runtime, reasoning_model)
    enriched_step = {
        **step,
        "analysis_result": analysis_result,
    }
    summary_policy = _summary_policy(enriched_step, runtime)
    stage_point_set = enrich_stage_point_set_with_text_options(build_stage_point_set(
        enriched_step,
        conclusion=str(analysis_result.get("conclusion") or ""),
        advice=str(analysis_result.get("next_focus") or ""),
        public_derivation=[
            str(row.get("text") or "")
            for row in _list(analysis_result.get("public_trace"))
            if isinstance(row, dict)
        ],
        stage_anchor_evidence=[
            str(row.get("label") or "") + "：" + str(row.get("text") or "")
            for row in _list(analysis_result.get("public_trace"))
            if isinstance(row, dict) and row.get("label") and row.get("text")
        ],
        used_evidence=[str(row) for row in _list(step.get("evidence"))[:4]],
        source="central_brain_rule_summary",
    ))
    return {
        **enriched_step,
        "summary_policy": summary_policy,
        "stage_point_set": stage_point_set,
        "stage_points": selected_stage_points(stage_point_set),
        "narration": _stage_narration(enriched_step),
        "summary_panel": _summary_panel(enriched_step, runtime, summary_policy=summary_policy),
    }


def _stage_narration(step: dict[str, object]) -> str:
    analysis = _dict(step.get("analysis_result"))
    conclusion = str(analysis.get("conclusion") or step.get("summary") or "").strip()
    advice = str(analysis.get("next_focus") or "").strip()
    boundary = ""
    contradictions = _list(analysis.get("contradictions"))
    if contradictions:
        boundary = str(contradictions[0] or "").strip()
    rows = [
        f"{conclusion}。" if conclusion and not conclusion.endswith(("。", "！", "？")) else conclusion,
        advice,
        f"边界：{boundary}" if boundary else "",
    ]
    return " ".join(row for row in rows if row)


def _analysis_result(
    step: dict[str, object],
    runtime: CoreRuntimeResult,
    reasoning_model: dict[str, object],
) -> dict[str, object]:
    step_id = str(step.get("step_id") or "")
    if step_id == "chart_build":
        return _chart_analysis_result(runtime, reasoning_model)
    if step_id == "knowledge_library":
        return _knowledge_analysis_result(step, runtime)
    if step_id == "rule_matching":
        return _rule_analysis_result(runtime)
    if step_id == "feature_extraction":
        return _feature_analysis_result(runtime)
    if step_id == "portrait_projection":
        return _portrait_analysis_result(runtime)
    if step_id == "path_reasoning":
        return _path_analysis_result(runtime, reasoning_model)
    if step_id == "structure_reasoning":
        return _structure_analysis_result(runtime, reasoning_model)
    if step_id == "useful_god_arbitration":
        return _useful_god_analysis_result(reasoning_model)
    if step_id == "timing_layers":
        return _timing_analysis_result(runtime, reasoning_model)
    if step_id == "domain_synthesis":
        return _domain_analysis_result(runtime)
    if step_id == "final_report":
        return _report_analysis_result(runtime)
    return _analysis(
        conclusion=str(step.get("title") or "本步已完成基础判断"),
        reasoning_points=[str(row) for row in _list(step.get("tasks"))[:3]],
        contradictions=["本步暂未形成足够的反证结构"],
        next_focus="继续进入下一步验证。",
        user_summary=str(step.get("summary") or ""),
        quality_flags=["generic_step_analysis"],
    )


def _chart_analysis_result(runtime: CoreRuntimeResult, reasoning_model: dict[str, object]) -> dict[str, object]:
    chart = runtime.chart_context
    axis = _dict(reasoning_model.get("chart_axis"))
    strength = _dict(reasoning_model.get("strength_model"))
    strongest = _list(strength.get("strongest_elements"))
    month_branch = str(axis.get("month_branch") or "-")
    day_pillar = str(axis.get("day_pillar") or "-")
    day_element = str(axis.get("day_master_element_label") or _element_label(chart.day_master_element))
    element_line = "、".join(
        str(row.get("label") or "")
        for row in strongest[:3]
        if isinstance(row, dict) and row.get("label")
    ) or "五行强弱资料不足"
    classification = str(strength.get("classification") or "待复核")
    strength_verdict = _customer_strength_verdict(
        day_master=str(chart.day_master or "-"),
        month_branch=month_branch,
        classification=classification,
        element_line=element_line,
    )
    conclusion = strength_verdict
    reasons = [
        f"日柱为{day_pillar}，日主是{chart.day_master or '-'}，五行属{day_element}。",
        f"月令落在{month_branch}，它是判断日主得令与否的第一入口。",
        f"当前五行分布重点：{element_line}；模型解释：{strength.get('explanation') or '继续复核'}",
    ]
    contradictions = [
        "排盘页只定入口，不直接定格局；格局、用神和领域判断要交给规则、十神和路径合参。",
        "印比、财官、食伤若在后面形成反向证据，本页强弱口径要下调权重。",
    ]
    next_focus = _customer_strength_next_focus(classification)
    user_summary = (
        f"这个盘的入口不是先断吉凶，而是先确定{chart.day_master or '-'}日主在{month_branch}月里的受力状态。"
        f"目前能看到的基础线索是：{element_line}；这说明后续必须围绕日主强弱、月令环境和四柱之间的生克关系展开。"
        f"本页先把“{classification}”作为强弱入口，而不是把它当成最终断语。"
    )
    return _analysis(
        conclusion,
        reasons,
        contradictions,
        next_focus,
        user_summary,
        ["chart_fact_based", "initial_strength_frame", "xuanming_core_model"],
        public_trace=[
            _trace("盘面入口", f"{chart.day_master or '-'}日主，月令为{month_branch}。"),
            _trace("强弱入口", f"{classification}，五行重点是{element_line}。"),
            _trace("测算作用", "为十神显隐、地支作用和用神取舍定第一层判断口径。"),
            _trace("执行建议", next_focus),
        ],
    )


def _customer_strength_verdict(
    *,
    day_master: str,
    month_branch: str,
    classification: str,
    element_line: str,
) -> str:
    if "中和" in classification:
        return (
            f"{day_master}日主生在{month_branch}月，盘面力量没有明显一边倒；"
            f"本页重点不是急着定身旺身弱，而是抓住{element_line}这条受力入口。"
        )
    if "旺" in classification:
        return (
            f"{day_master}日主生在{month_branch}月，盘面力量先向日主一侧集中；"
            f"{element_line}是判断印比是否过重、财官食伤能否承接的入口。"
        )
    if "弱" in classification or "受压" in classification:
        return (
            f"{day_master}日主生在{month_branch}月，日主承压感较明显；"
            f"{element_line}决定后面要优先看印比扶身，还是先疏通压力。"
        )
    return f"{day_master}日主生在{month_branch}月，强弱入口定为{classification}；{element_line}先作为本页主证。"


def _customer_strength_next_focus(classification: str) -> str:
    if "中和" in classification:
        return "先抓三件事：十神谁透出、地支有没有合冲刑害、用神候选能不能形成现实出口；证据不合的规则直接降权。"
    if "旺" in classification:
        return "重点核对财官食伤能否把旺气导出去；只增加印比的路径先降权，能形成职责、输出或收益承接的路径优先。"
    if "弱" in classification or "受压" in classification:
        return "重点核对印比有没有根、官杀压力是否过界；能补根、承压和化压力的路径优先，消耗日主的路径先降权。"
    return "围绕十神显隐、地支作用和用神候选继续合参；同向证据加权，反向证据降权。"


def _knowledge_analysis_result(step: dict[str, object], runtime: CoreRuntimeResult) -> dict[str, object]:
    units = _list(runtime.question_plan.policy_effect.get("krp_library_units"))
    families = _unique([
        _knowledge_family_label(str(row.get("family") or row.get("unit_type") or ""))
        for row in units
        if isinstance(row, dict)
    ])[:4]
    conclusion = "知识库已锁定本次可用规则边界，当前判断必须在这些规则内完成"
    reasons = [
        f"本次可调用知识单元约{len(units)}条。",
        f"覆盖知识族：{'、'.join(families) if families else '基础规则与边界'}。",
        "知识库负责限定怎么判断，不能替代命盘合参。",
    ]
    contradictions = ["如果知识单元覆盖不足，后续结论会偏保守。"]
    next_focus = "用已装载的知识单元筛出真实命中规则；没有命中证据的知识不得写进结论。"
    user_summary = "知识库页的结论很明确：本次测算只能使用已装载、可追溯的规则边界。它负责防止系统臆造命理事实，也负责把后续规则匹配限制在可验证范围内。"
    return _analysis(
        conclusion,
        reasons,
        contradictions,
        next_focus,
        user_summary,
        ["knowledge_boundary"],
        public_trace=[
            _trace("装载范围", f"可调用知识单元约{len(units)}条。"),
            _trace("知识族", "、".join(families) if families else "基础规则与判断边界。"),
            _trace("测算作用", "限定可用判断法门，排除无证据的泛化断语。"),
            _trace("执行建议", next_focus),
        ],
    )


def _rule_analysis_result(runtime: CoreRuntimeResult) -> dict[str, object]:
    diagnosis = _dict(runtime.question_plan.policy_effect.get("real_bazi_diagnosis"))
    matches = _list(diagnosis.get("matched_rules"))
    signals = runtime.question_plan.knowledge_rule_portrait_signals
    labels = _rule_public_matches(signals, matches)
    label_text = "、".join(labels) if labels else "用神、十神、地支关系和隐藏线索"
    impact_text = _rule_impact_text(labels)
    conclusion = f"本步匹配到的规则重点是：{label_text}"
    reasons = [
        f"规则画像信号约{len(signals)}条。",
        f"诊断规则命中约{len(matches)}条。",
        f"匹配重点：{label_text}。",
        f"测算作用：{impact_text}",
    ]
    contradictions = [
        "规则命中说明存在倾向，不等于该倾向已成为命局主线。",
        "如果结构路径或大运流年不支持，单条规则要降权。",
    ]
    next_focus = "立即把命中规则转成特征证据；能被特征支撑的进入画像和做功路径，不能支撑的降权。"
    user_summary = (
        f"规则页真正看的是“哪些命理机制被这个盘触发”。本步匹配重点是：{label_text}。"
        f"它们在测算里的作用是：{impact_text}。"
        "所以这里不是最终断语，而是把后续特征、画像、结构、路径要重点验证的方向先圈出来。"
    )
    return _analysis(
        conclusion,
        reasons,
        contradictions,
        next_focus,
        user_summary,
        ["rule_semantic_bridge"],
        public_trace=[
            _trace("匹配规则", label_text),
            _trace("测算作用", impact_text),
            _trace("命中规模", f"约{len(matches)}条诊断规则，约{len(signals)}条画像信号参与候选。"),
            _trace("判断边界", "规则命中只是候选证据，必须经过特征、画像、路径和时运交叉验证。"),
            _trace("执行建议", next_focus),
        ],
    )


def _feature_analysis_result(runtime: CoreRuntimeResult) -> dict[str, object]:
    domains = _unique([_domain_label(row.domain or row.kind) for row in runtime.feature_evidence])[:5]
    labels = _unique([_feature_public_label(row.label) for row in runtime.feature_evidence if row.label])[:5]
    label_text = "、".join(labels) if labels else "日主、十神、五行与结构证据"
    conclusion = f"核心特征已锁定：{label_text}"
    reasons = [
        f"当前抽取到{len(runtime.feature_evidence)}条特征。",
        f"覆盖领域：{'、'.join(domains) if domains else '基础结构'}。",
        f"代表性特征：{label_text}。",
    ]
    contradictions = ["特征数量不代表结论强弱，仍要看它们是否指向同一主线。"]
    next_focus = "用这些特征直接生成画像和路径权重；画像必须回扣这些特征，不能另起判断。"
    user_summary = f"特征页已经把零散四柱、十神、五行和时运线索压缩成可用证据：{label_text}。这些特征决定画像和路径是否有根，后续结论必须能回溯到这里。"
    return _analysis(
        conclusion,
        reasons,
        contradictions,
        next_focus,
        user_summary,
        ["feature_evidence_bridge"],
        public_trace=[
            _trace("特征数量", f"抽取到{len(runtime.feature_evidence)}条特征。"),
            _trace("核心特征", label_text),
            _trace("测算作用", "为画像、结构和做功路径提供可追溯证据。"),
            _trace("执行建议", next_focus),
        ],
    )


def _portrait_analysis_result(runtime: CoreRuntimeResult) -> dict[str, object]:
    diagnosis = _dict(runtime.question_plan.policy_effect.get("real_bazi_diagnosis"))
    portraits = _list(diagnosis.get("portraits"))
    user_portraits = [
        row for row in portraits
        if isinstance(row, dict) and str(row.get("domain") or "").lower() not in {"overview", "foundation", "boundary"}
    ] or [row for row in portraits if isinstance(row, dict)]
    domains = _unique([_domain_label(str(row.get("domain") or "")) for row in user_portraits])[:5]
    portrait_labels = _unique([
        _portrait_public_label(row)
        for row in user_portraits
        if isinstance(row, dict) and _portrait_public_label(row)
    ])[:4]
    portrait_text = "、".join(portrait_labels or domains) if (portrait_labels or domains) else "事业、关系、健康或结构倾向"
    conclusion = f"画像结论锁定为：{portrait_text}"
    reasons = [
        f"画像层生成{len(portraits)}条倾向，其中优先展示{len(user_portraits)}条命局相关画像。",
        f"覆盖领域：{'、'.join(domains) if domains else '事业、关系、健康或结构'}。",
        "画像来自规则和特征的合成，不允许反向改写命盘事实。",
    ]
    contradictions = ["画像若缺少路径支撑，只能作为性格/领域倾向，不能升级为事件判断。"]
    next_focus = "把画像逐项压到做功路径和现实领域；不能落到路径的画像只作为性格倾向保留。"
    user_summary = f"画像页回答“这个盘容易表现成什么样”。当前画像结论是：{portrait_text}。这些画像不是装饰标签，必须继续落到路径、时运和现实领域，才能变成有用建议。"
    return _analysis(
        conclusion,
        reasons,
        contradictions,
        next_focus,
        user_summary,
        ["portrait_tendency_only"],
        public_trace=[
            _trace("画像结论", portrait_text),
            _trace("画像数量", f"生成{len(portraits)}条倾向，前台优先展示命局相关画像。"),
            _trace("测算作用", "把规则和特征合成为用户能理解的人格、领域与结构倾向。"),
            _trace("判断边界", "画像是倾向，不是必然事件。"),
            _trace("执行建议", next_focus),
        ],
    )


def _portrait_public_label(row: dict[str, object]) -> str:
    dimension = str(row.get("dimension") or row.get("title") or row.get("label") or "").lower()
    domain = str(row.get("domain") or "")
    labels = {
        "branch_conflict": "地支关系画像",
        "structure_dynamic": "结构动态画像",
        "ten_god_energy": "十神能量画像",
        "career_path": "事业路径画像",
        "wealth_path": "财运路径画像",
        "relationship_pattern": "关系模式画像",
        "health_tendency": "健康倾向画像",
        "useful_god": "用神取向画像",
        "useful_god_gate": "用神取向画像",
        "strength_pattern": "旺衰结构画像",
        "strength_pattern_review": "旺衰结构画像",
    }
    if dimension in labels:
        return labels[dimension]
    if domain and domain.lower() not in {"overview", "foundation", "boundary"}:
        return f"{_domain_label(domain)}画像"
    statement = str(row.get("statement") or "").strip()
    if statement and not statement.startswith("Use ") and not statement.startswith("Never "):
        return statement.split("。", 1)[0][:28]
    return ""


def _feature_public_label(value: str) -> str:
    raw = str(value or "")
    lowered = raw.lower()
    if lowered.startswith("day_master:"):
        return f"日主{raw.split(':', 1)[1]}"
    if lowered.startswith("day_master_element:"):
        return f"日主五行{_element_label(raw.split(':', 1)[1])}"
    if lowered.startswith("visible_ten_gods:"):
        return f"天干显性十神{raw.split(':', 1)[1]}"
    if lowered.startswith("hidden_ten_gods:"):
        return f"地支藏干十神{raw.split(':', 1)[1]}"
    if lowered.startswith("elements:"):
        payload = raw.split(":", 1)[1]
        parts = dict(
            piece.split("=", 1)
            for piece in payload.split(";")
            if "=" in piece
        )
        strongest = _element_label(parts.get("strongest", ""))
        weakest = _element_label(parts.get("weakest", ""))
        spread = parts.get("spread", "")
        return f"五行分布：{strongest}最强、{weakest}最弱、差距{spread}"
    if lowered.startswith("strength_pattern:"):
        payload = raw.split(":", 1)[1]
        parts = dict(
            piece.split("=", 1)
            for piece in payload.split(";")
            if "=" in piece
        )
        return f"旺衰结构：日主{_element_label(parts.get('day_element', ''))}，季节{_element_label(parts.get('season', ''))}"
    if lowered.startswith("month_command:"):
        payload = raw.split(":", 1)[1]
        parts = dict(
            piece.split("=", 1)
            for piece in payload.split(";")
            if "=" in piece
        )
        return f"月令入口：{parts.get('branch', '-')}月，季节五行{_element_label(parts.get('season_element', ''))}"
    if lowered.startswith("wang_xiang_xiu_qiu_si:"):
        return "旺相休囚死状态已纳入强弱判断"
    if lowered.startswith("ten_god_role_set:"):
        return "十神显隐角色已纳入判断"
    if "element" in lowered:
        return raw.replace("_", " ").replace(":", "：")[:48]
    if "branch" in lowered or "relation" in lowered:
        return raw.replace("branch", "地支").replace("relation", "关系").replace("_", "")[:48]
    if "ten_god" in lowered:
        return raw.replace("ten_god", "十神").replace("_", "")[:48]
    return raw.replace("_", " ").replace(":", "：")[:48]


def _path_analysis_result(runtime: CoreRuntimeResult, reasoning_model: dict[str, object]) -> dict[str, object]:
    path_model = _dict(reasoning_model.get("path_model"))
    paths = _list(path_model.get("top_paths"))
    top_domains = _list(path_model.get("top_domains"))
    chain = runtime.structure_state.primary_chain[:4]
    first_path = _dict(paths[0]) if paths else {}
    domain_text = "、".join(
        str(row.get("domain") or "")
        for row in top_domains[:3]
        if isinstance(row, dict) and row.get("domain")
    ) or "领域落点待确认"
    mechanism = str(first_path.get("mechanism") or "结构流通")
    conclusion = f"做功路径主线锁定为{mechanism}，优先落点是{domain_text}"
    reasons = [
        f"诊断层整理出{path_model.get('path_count') or len(paths)}条路径。",
        f"结构主链：{_chain_label(chain) if chain else _structure_label(runtime.structure_state.semantic_label)}。",
        f"优先机制：{mechanism}；领域：{domain_text}。",
    ]
    contradictions = [
        "路径能解释力量流向，但仍要看时运是否激活。",
        "路径若只停留在结构图，不能直接变成领域结论。",
    ]
    next_focus = f"按{mechanism}解释力量流向；领域建议优先围绕{domain_text}展开，弱路径不抢主线。"
    user_summary = f"做功路径页直接回答力量怎么走：当前主线是{mechanism}，优先落点是{domain_text}。只有路径走通，事业、财运、关系等建议才有根据。"
    return _analysis(
        conclusion,
        reasons,
        contradictions,
        next_focus,
        user_summary,
        ["force_flow", "xuanming_core_model"],
        public_trace=[
            _trace("路径结论", f"{mechanism}。"),
            _trace("领域落点", domain_text),
            _trace("路径数量", f"整理出{path_model.get('path_count') or len(paths)}条候选路径。"),
            _trace("测算作用", "解释力量流向，并决定哪些领域建议能成为主线。"),
            _trace("执行建议", next_focus),
        ],
    )


def _structure_analysis_result(runtime: CoreRuntimeResult, reasoning_model: dict[str, object]) -> dict[str, object]:
    structure = runtime.structure_state
    structure_model = _dict(reasoning_model.get("structure_model"))
    mainline = _dict(reasoning_model.get("mainline"))
    structure_label = _structure_label(str(structure_model.get("semantic_label") or structure.semantic_label or structure.state))
    decision_labels = [
        _decision_candidate_label(str(row.get("candidate") or ""))
        for row in _list(structure_model.get("ranked_decisions"))[:4]
        if isinstance(row, dict) and row.get("candidate")
    ]
    conclusion = _clean_public_structure_text(str(mainline.get("thesis") or f"当前结构主线倾向于：{structure_label}"))
    reasons = [
        f"结构状态：{structure_label}，置信度{structure.confidence:.2f}。",
        f"主链：{' > '.join(str(row) for row in _list(structure_model.get('primary_chain'))[:4]) if structure_model.get('primary_chain') else '待路径层补强'}。",
        f"候选决策：{'、'.join(decision_labels) if decision_labels else '旺衰、格局、用神仍需合参'}。",
    ]
    contradictions = [
        "结构置信度不是百分百，代表仍有候选结构或反证需要保留。",
        "若大运流年触发另一条路径，结构结论要体现阶段变化。",
    ]
    next_focus = "以这条结构主线统领后续判断；大运流年只负责激活或削弱主线，不能另造结论。"
    user_summary = f"结构页已经形成主线：{structure_label}。当前判断以旺衰、格局、用神和动态路径合参为准；后续时运分析必须服务这条主线。"
    return _analysis(
        conclusion,
        reasons,
        contradictions,
        next_focus,
        user_summary,
        ["structure_mainline", "xuanming_core_model"],
        public_trace=[
            _trace("结构主线", structure_label),
            _trace("候选决策", "、".join(decision_labels) if decision_labels else "旺衰、格局、用神合参。"),
            _trace("测算作用", "统领用神、路径、时运和领域建议的取舍。"),
            _trace("执行建议", next_focus),
        ],
    )


def _useful_god_analysis_result(reasoning_model: dict[str, object]) -> dict[str, object]:
    useful = _dict(reasoning_model.get("useful_god_model"))
    avoidance = _dict(useful.get("avoidance_model"))
    primary_label = str(useful.get("primary_label") or "用神候选待复核")
    elements = "、".join(_useful_element_labels(useful)) or "候选五行待复核"
    families = "、".join(_useful_family_labels(useful)) or "十神族待复核"
    risks = [str(row) for row in _list(avoidance.get("primary_risks")) if str(row).strip()]
    risk_text = "；".join(risks[:2]) if risks else "避免把候选策略说成唯一用神。"
    cross_checks = [str(row) for row in _list(useful.get("cross_checks")) if str(row).strip()]
    conclusion = f"用神取向优先看{primary_label}，忌避重点是{risk_text}"
    reasons = [
        f"候选五行：{elements}。",
        f"候选十神族：{families}。",
        *(cross_checks[:3] or ["用神取舍必须同时看强弱、十神、结构反证和做功路径。"]),
    ]
    contradictions = [
        "用神和忌神都不是固定五行断语，只能作为当前证据下的取舍策略。",
        "若时运或用户反馈证明路径不落地，本页取向必须降权或调整排序。",
    ]
    next_focus = f"后续时运和领域建议都要围绕{primary_label}验证；凡是加重忌避风险的行动建议要降权。"
    user_summary = (
        f"用神忌神页负责做取舍：当前优先策略是{primary_label}，不是唯一用神定死。"
        f"它对应的候选五行是{elements}，十神族是{families}；同时要避开：{risk_text}"
        "后面的时运和领域建议，必须围绕这个取舍继续验证。"
    )
    return _analysis(
        conclusion,
        reasons,
        contradictions,
        next_focus,
        user_summary,
        ["useful_god_candidate_strategy", "avoidance_risk_boundary", "xuanming_core_model"],
        public_trace=[
            _trace("用神取向", primary_label),
            _trace("候选五行", elements),
            _trace("忌避风险", risk_text),
            _trace("测算作用", "为时运、领域建议和行动取舍提供核心上下文。"),
            _trace("执行建议", next_focus),
        ],
    )


def _timing_analysis_result(runtime: CoreRuntimeResult, reasoning_model: dict[str, object]) -> dict[str, object]:
    timing_model = _dict(reasoning_model.get("timing_model"))
    luck_pillar = str(timing_model.get("current_luck_pillar") or "")
    flow_pillar = str(timing_model.get("flow_year_pillar") or "")
    timing_ready = bool(luck_pillar and flow_pillar)
    conclusion = (
        f"当前时运入口锁定为大运{luck_pillar}与流年{flow_pillar}"
        if timing_ready
        else "时运资料不足，本页明确不做年份断语"
    )
    reasons = [
        f"大运定位：{luck_pillar or '缺失'}。",
        f"流年定位：{flow_pillar or '缺失'}。",
        str(timing_model.get("activation_summary") or "时运层负责判断哪些原局结构在当下被激活。"),
    ]
    contradictions = ["时运只能激活原局已有的结构，不应凭流年单独制造结论。"]
    next_focus = (
        "把被激活的原局结构直接落到事业、财运、关系等领域。"
        if timing_ready
        else "先补齐大运和流年定位；在补齐前，领域建议只采用原局和路径结论，不写具体年份。"
    )
    user_summary = (
        f"原局是底盘，大运{luck_pillar}与流年{flow_pillar}决定当前最容易被推到前台的主题。时运页负责判断哪条路径在此阶段最有力量。"
        if timing_ready
        else "时运页的结论很明确：当前缺少可用的大运或流年定位，因此不能负责任地写具体年份判断。系统会先用原局、结构和路径给建议，等时运资料补齐后再落到阶段主题。"
    )
    return _analysis(
        conclusion,
        reasons,
        contradictions,
        next_focus,
        user_summary,
        ["timing_activation", "xuanming_core_model"],
        public_trace=[
            _trace("时运入口", f"大运{luck_pillar or '缺失'}，流年{flow_pillar or '缺失'}。"),
            _trace("测算作用", "决定哪条原局路径在当前阶段被激活。"),
            _trace("执行建议", next_focus),
            _trace("判断边界", contradictions[0]),
        ],
    )


def _domain_analysis_result(runtime: CoreRuntimeResult) -> dict[str, object]:
    practical = _dict(runtime.question_plan.policy_effect.get("practical_reading_context"))
    domains = _dict(practical.get("domain_readings"))
    labels = [_domain_label(key) for key in list(domains)[:5]]
    label_text = "、".join(labels) if labels else "事业、财运、关系等基础领域"
    conclusion = f"领域结论优先落在：{label_text}"
    reasons = [
        f"当前形成{len(domains)}个领域解读。",
        f"覆盖领域：{label_text}。",
        "领域结论应回扣结构、路径和时运，而不是单独写泛泛建议。",
    ]
    contradictions = ["如果用户问题不明确，领域结论只能先给方向，不能替用户确定人生事件。"]
    next_focus = f"优先围绕{label_text}给建议；每条领域建议都必须回扣规则、路径或时运证据。"
    user_summary = f"领域页开始回答用户真正关心的问题。当前优先领域是：{label_text}。这些领域不是泛泛展开，必须能回溯到规则、路径和时运。"
    return _analysis(
        conclusion,
        reasons,
        contradictions,
        next_focus,
        user_summary,
        ["domain_grounding"],
        public_trace=[
            _trace("领域结论", label_text),
            _trace("领域数量", f"形成{len(domains)}个领域解读。"),
            _trace("测算作用", "把结构主线转成用户能执行的现实建议。"),
            _trace("执行建议", next_focus),
        ],
    )


def _report_analysis_result(runtime: CoreRuntimeResult) -> dict[str, object]:
    answer = runtime.answer_result
    text = answer.text if answer is not None else ""
    final_synthesis = _final_synthesis(runtime)
    conclusion = str(final_synthesis.get("conclusion") or "最终报告必须以结构主线、做功路径和领域建议收束，不允许黑盒重写")
    advice = str(final_synthesis.get("advice") or "生成报告时必须先给结论和建议，再列依据与边界；LLM只能润色，不能新增命盘事实。")
    reasons = [
        "报告继承排盘、规则、特征、画像、路径、时运和追问反馈后的权重。",
        f"中枢最终合成状态：{final_synthesis.get('status') or 'unknown'}。",
        f"当前报告文本长度：{len(text)}。",
        "表达层可以润色，但不能新增命盘事实。",
    ]
    contradictions = ["如果反馈信号与证据链冲突，结论只调整排序和边界，不改四柱和命盘事实。"]
    next_focus = advice
    user_summary = str(final_synthesis.get("customer_summary") or "报告页的标准很明确：先给结论和建议，再解释依据与边界。")
    return _analysis(
        conclusion,
        reasons,
        contradictions,
        next_focus,
        user_summary,
        ["report_synthesis"],
        public_trace=[
            _trace("报告结论", conclusion),
            _trace("输入来源", "排盘、规则、特征、画像、路径、时运、用户反馈权重和中枢最终合成。"),
            _trace("测算作用", "把分步推演收束成用户能理解、能执行的建议。"),
            _trace("执行建议", advice),
        ],
    )


def _final_synthesis(runtime: CoreRuntimeResult) -> dict[str, object]:
    central = _dict(runtime.question_plan.policy_effect.get("central_reading_state"))
    return _dict(central.get("final_synthesis"))


def _final_synthesis_evidence(final_synthesis: dict[str, object]) -> list[str]:
    rows: list[str] = []
    for row in _list(final_synthesis.get("evidence_chain")):
        if not isinstance(row, dict):
            continue
        domain = str(row.get("domain") or "")
        evidence = [str(item) for item in _list(row.get("evidence")) if item]
        if domain or evidence:
            rows.append(f"{domain}:{' / '.join(evidence[:2])}")
    return rows[:6]


def _sidebar_memory(
    runtime: CoreRuntimeResult,
    reasoning_model: dict[str, object],
    steps: list[dict[str, object]],
) -> dict[str, object]:
    policy = runtime.question_plan.policy_effect
    diagnosis = _dict(policy.get("real_bazi_diagnosis"))
    central = _dict(policy.get("central_reading_state"))
    verdicts = _list(central.get("decision_verdicts"))
    strength = _dict(reasoning_model.get("strength_model"))
    structure = _dict(reasoning_model.get("structure_model"))
    useful = _dict(reasoning_model.get("useful_god_model"))
    avoidance = _dict(useful.get("avoidance_model"))
    path_model = _dict(reasoning_model.get("path_model"))
    timing = _dict(reasoning_model.get("timing_model"))
    practical = _dict(policy.get("practical_reading_context"))
    domain_readings = _dict(practical.get("domain_readings"))
    steps_by_id = {str(step.get("step_id") or ""): step for step in steps if isinstance(step, dict)}
    items: list[dict[str, object]] = []

    day_master = runtime.chart_context.day_master or "-"
    month_branch = str(_dict(reasoning_model.get("chart_axis")).get("month_branch") or "-")
    items.append(_memory_item(
        "chart.axis",
        kind="chart",
        stage_id="chart_build",
        label="命盘入口",
        value=f"{day_master}日主 · {month_branch}月",
        detail=f"强弱先按{strength.get('classification') or '待复核'}处理。",
        chips=[str(strength.get("classification") or "强弱待复核"), *_string_list(strength.get("supporting_elements"))[:2]],
        evidence=_public_trace_texts(steps_by_id.get("chart_build")),
        confidence=float(steps_by_id.get("chart_build", {}).get("confidence") or 0.0),
        source_point_id=_source_stage_point_id(steps_by_id, "chart_build"),
    ))

    rule_labels = _rule_public_matches(
        runtime.question_plan.knowledge_rule_portrait_signals,
        _list(diagnosis.get("matched_rules")),
    )
    if rule_labels:
        items.append(_memory_item(
            "rule.matches",
            kind="rule",
            stage_id="rule_matching",
            label="规则命中",
            value="、".join(rule_labels[:3]),
            detail="这些规则进入后续特征、画像和路径验证。",
            chips=rule_labels[:4],
            evidence=_public_trace_texts(steps_by_id.get("rule_matching")),
            confidence=float(steps_by_id.get("rule_matching", {}).get("confidence") or 0.0),
            source_point_id=_source_stage_point_id(steps_by_id, "rule_matching"),
        ))

    feature_labels = _unique([_feature_public_label(row.label) for row in runtime.feature_evidence if row.label])[:4]
    if feature_labels:
        items.append(_memory_item(
            "feature.core",
            kind="feature",
            stage_id="feature_extraction",
            label="核心特征",
            value="、".join(feature_labels[:3]),
            detail="画像和路径必须回扣这些特征。",
            chips=feature_labels,
            evidence=_public_trace_texts(steps_by_id.get("feature_extraction")),
            confidence=float(steps_by_id.get("feature_extraction", {}).get("confidence") or 0.0),
            source_point_id=_source_stage_point_id(steps_by_id, "feature_extraction"),
        ))

    portraits = _list(diagnosis.get("portraits"))
    portrait_labels = _unique([
        _portrait_public_label(row)
        for row in portraits
        if isinstance(row, dict) and _portrait_public_label(row)
    ])[:4]
    if portrait_labels:
        items.append(_memory_item(
            "portrait.key",
            kind="portrait",
            stage_id="portrait_projection",
            label="画像关键词",
            value="、".join(portrait_labels[:3]),
            detail="画像是倾向，不是必然事件。",
            chips=portrait_labels,
            evidence=_public_trace_texts(steps_by_id.get("portrait_projection")),
            confidence=float(steps_by_id.get("portrait_projection", {}).get("confidence") or 0.0),
            source_point_id=_source_stage_point_id(steps_by_id, "portrait_projection"),
        ))

    top_paths = _list(path_model.get("top_paths"))
    primary_path = _dict(top_paths[0]) if top_paths else {}
    if primary_path:
        path_domains = [str(row) for row in _list(primary_path.get("domains")) if row]
        items.append(_memory_item(
            "path.primary",
            kind="path",
            stage_id="path_reasoning",
            label="做功路径",
            value=str(primary_path.get("mechanism") or "结构流通"),
            detail=f"优先落点：{'、'.join(path_domains[:3]) or '领域待确认'}。",
            chips=[str(primary_path.get("mechanism") or "路径"), *path_domains[:3]],
            evidence=_public_trace_texts(steps_by_id.get("path_reasoning")),
            confidence=float(steps_by_id.get("path_reasoning", {}).get("confidence") or 0.0),
            source_point_id=_source_stage_point_id(steps_by_id, "path_reasoning"),
        ))

    if structure:
        structure_label = _structure_label(str(structure.get("semantic_label") or runtime.structure_state.semantic_label))
        items.append(_memory_item(
            "structure.mainline",
            kind="structure",
            stage_id="structure_reasoning",
            label="结构主线",
            value=structure_label,
            detail="统领用神、时运和领域建议的取舍。",
            chips=[
                _decision_candidate_label(str(row.get("candidate") or ""))
                for row in _list(structure.get("ranked_decisions"))[:3]
                if isinstance(row, dict)
            ],
            evidence=_public_trace_texts(steps_by_id.get("structure_reasoning")),
            confidence=float(steps_by_id.get("structure_reasoning", {}).get("confidence") or 0.0),
            source_point_id=_source_stage_point_id(steps_by_id, "structure_reasoning"),
        ))

    if useful:
        risks = [str(row) for row in _list(avoidance.get("primary_risks")) if str(row).strip()]
        items.append(_memory_item(
            "useful_god.primary",
            kind="useful_god",
            stage_id="useful_god_arbitration",
            label="用神取舍",
            value=str(useful.get("primary_label") or "用神候选待复核"),
            detail=f"忌避：{risks[0] if risks else '避免固定唯一用神'}",
            chips=[
                *_useful_family_labels(useful)[:2],
                *_useful_element_labels(useful)[:2],
            ],
            evidence=[str(row) for row in _list(useful.get("cross_checks"))[:3]],
            counter_evidence=risks[:3],
            confidence=_float(_dict(useful.get("ranked_decision")).get("confidence"), 0.0),
            source_point_id=_source_stage_point_id(steps_by_id, "useful_god_arbitration"),
        ))

    if timing.get("activation_tags"):
        tags = [str(row) for row in _list(timing.get("activation_tags")) if row]
        items.append(_memory_item(
            "timing.activation",
            kind="timing",
            stage_id="timing_layers",
            label="时运触发",
            value="、".join(tags[:3]),
            detail=str(timing.get("activation_summary") or "时运用于激活原局路径。"),
            chips=tags[:4],
            evidence=_public_trace_texts(steps_by_id.get("timing_layers")),
            confidence=float(steps_by_id.get("timing_layers", {}).get("confidence") or 0.0),
            source_point_id=_source_stage_point_id(steps_by_id, "timing_layers"),
        ))

    domain_labels = [
        _domain_label(str(key))
        for key, value in domain_readings.items()
        if isinstance(value, dict) and value.get("state") == "active"
    ][:4]
    if domain_labels:
        items.append(_memory_item(
            "domain.focus",
            kind="domain",
            stage_id="domain_synthesis",
            label="现实领域",
            value="、".join(domain_labels[:3]),
            detail="领域建议必须回扣结构、路径和用神取舍。",
            chips=domain_labels,
            evidence=_public_trace_texts(steps_by_id.get("domain_synthesis")),
            confidence=float(steps_by_id.get("domain_synthesis", {}).get("confidence") or 0.0),
            source_point_id=_source_stage_point_id(steps_by_id, "domain_synthesis"),
        ))

    if verdicts:
        top_verdict = _dict(verdicts[0])
        items.append(_memory_item(
            "decision.verdict",
            kind="decision",
            stage_id="final_report",
            label="裁决摘要",
            value=str(top_verdict.get("headline") or "Decision Engine 已形成裁决"),
            detail=f"断语等级：{_assertion_level_label(str(top_verdict.get('assertion_level') or ''))}；LLM 只负责表达。",
            chips=[
                _domain_label(str(top_verdict.get("domain") or "")),
                _assertion_level_label(str(top_verdict.get("assertion_level") or "")),
                f"置信{_float(top_verdict.get('confidence'), 0.0):.2f}",
            ],
            evidence=[str(row) for row in _list(top_verdict.get("evidence_refs"))[:4]],
            counter_evidence=[str(row) for row in _list(top_verdict.get("counter_evidence_refs"))[:3]],
            confidence=_float(top_verdict.get("confidence"), 0.0),
            source_point_id=str(top_verdict.get("verdict_id") or ""),
            boundary="sidebar_memory_item_is_decision_verdict_projection_not_llm_text",
        ))

    return {
        "version": "v30.sidebar_memory.v1",
        "reading_id": runtime.reading_id,
        "item_count": len(items),
        "items": items,
        "training_signal": {
            "signal_id": "v30.training_signal.sidebar_memory",
            "trainable": True,
            "targets": [
                "sidebar_memory_priority",
                "useful_god_strategy_weight",
                "avoidance_risk_weight",
                "stage_visibility_weight",
            ],
            "blocked_targets": [
                "chart_facts",
                "pillar_calculation",
                "fixed_useful_god_verdict",
                "fixed_unfavorable_element_verdict",
            ],
        },
        "boundary": "sidebar_memory_projects_stage_key_context_without_mutating_chart_facts",
    }


def _memory_item(
    memory_id: str,
    *,
    kind: str,
    stage_id: str,
    label: str,
    value: str,
    detail: str,
    chips: list[str],
    evidence: list[str],
    confidence: float,
    counter_evidence: list[str] | None = None,
    source_point_id: str = "",
    boundary: str = "sidebar_memory_item_is_key_context_not_final_verdict",
) -> dict[str, object]:
    return {
        "memory_id": memory_id,
        "kind": kind,
        "stage_id": stage_id,
        "visibility_stage": stage_id,
        "label": label,
        "value": value,
        "detail": detail,
        "chips": [row for row in chips if row][:5],
        "evidence": [row for row in evidence if row][:4],
        "counter_evidence": [row for row in (counter_evidence or []) if row][:3],
        "confidence_band": _confidence_band(confidence),
        "source_point_id": source_point_id,
        "boundary": boundary,
    }


def _source_stage_point_id(steps_by_id: dict[str, dict[str, object]], stage_id: str) -> str:
    step = steps_by_id.get(stage_id) or {}
    for point in _list(step.get("stage_points")):
        if isinstance(point, dict) and point.get("sidebar_visible", True):
            return str(point.get("point_id") or "")
    return ""


def _public_trace_texts(step: dict[str, object] | None) -> list[str]:
    analysis = _dict(_dict(step).get("analysis_result"))
    rows = []
    for row in _list(analysis.get("public_trace")):
        if not isinstance(row, dict):
            continue
        label = str(row.get("label") or "").strip()
        text = str(row.get("text") or "").strip()
        if label and text:
            rows.append(f"{label}：{text}")
    return rows[:4]


def _confidence_band(value: float) -> str:
    if value >= 0.78:
        return "high"
    if value >= 0.58:
        return "medium"
    return "low"


def _string_list(value: Any) -> list[str]:
    return [str(row) for row in _list(value) if str(row).strip()]


def _analysis(
    conclusion: str,
    reasoning_points: list[str],
    contradictions: list[str],
    next_focus: str,
    user_summary: str,
    quality_flags: list[str],
    public_trace: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    public_rows = public_trace or _default_public_trace(conclusion, reasoning_points, contradictions, next_focus)
    return {
        "version": "v30.xuanming_step_analysis_result.v1",
        "conclusion": conclusion,
        "reasoning_points": [row for row in reasoning_points if row][:5],
        "contradictions": [row for row in contradictions if row][:3],
        "next_focus": next_focus,
        "user_summary": user_summary,
        "public_trace": public_rows,
        "summary_decision": _summary_decision(
            conclusion=conclusion,
            reasoning_points=reasoning_points,
            contradictions=contradictions,
            next_focus=next_focus,
            public_trace=public_rows,
        ),
        "quality_flags": [row for row in quality_flags if row],
        "boundary": "xuanming_analysis_result_is_public_reasoning_not_hidden_chain_of_thought",
    }


def _trace(label: str, text: str) -> dict[str, object]:
    return {
        "label": label,
        "text": text,
        "visibility": "public_reasoning",
    }


def _default_public_trace(
    conclusion: str,
    reasoning_points: list[str],
    contradictions: list[str],
    next_focus: str,
) -> list[dict[str, object]]:
    rows = [
        _trace("本步结论", conclusion),
        _trace("主要依据", reasoning_points[0] if reasoning_points else ""),
        _trace("判断边界", contradictions[0] if contradictions else ""),
        _trace("下一步", next_focus),
    ]
    return [row for row in rows if str(row.get("text") or "").strip()]


def _summary_decision(
    *,
    conclusion: str,
    reasoning_points: list[str],
    contradictions: list[str],
    next_focus: str,
    public_trace: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "version": "v30.central_brain_stage_summary_decision.v1",
        "owner": "central_brain",
        "user_value_order": ["conclusion", "advice", "evidence", "boundary"],
        "conclusion": conclusion,
        "advice": next_focus,
        "evidence": [row for row in reasoning_points if row][:3],
        "boundary_text": contradictions[0] if contradictions else "",
        "public_trace": public_trace[:5],
        "llm_task": {
            "mode": "expression_only",
            "input_source": "summary_decision",
            "must_preserve": ["conclusion", "advice", "evidence", "boundary_text"],
            "must_not_create": ["chart_fact", "event_year", "hidden_user_fact", "fixed_verdict"],
        },
        "training_target": {
            "signal_id": "v30.training_signal.central_brain_stage_summary_decision",
            "trainable": True,
            "target": "stage_conclusion_advice_evidence_boundary_selection",
        },
        "boundary": "central_brain_summary_decision_controls_user_value_not_hidden_chain_of_thought",
    }


def _summary_panel(
    step: dict[str, object],
    runtime: CoreRuntimeResult,
    *,
    summary_policy: dict[str, object] | None = None,
) -> dict[str, object]:
    step_id = str(step.get("step_id") or "")
    analysis = _dict(step.get("analysis_result"))
    if analysis.get("user_summary"):
        next_focus = str(analysis.get("next_focus") or "").strip()
        body = str(analysis.get("user_summary") or "").strip()
        if next_focus and next_focus not in body:
            body = f"{body} {next_focus}"
        return _summary(
            str(analysis.get("conclusion") or step.get("title") or "结论待形成"),
            body,
            [str(row) for row in _list(analysis.get("reasoning_points"))[:4]],
            summary_policy=summary_policy,
        )
    tasks = _list(step.get("tasks"))
    evidence = _list(step.get("evidence"))
    core = runtime.chart_context
    layers = _dict(core.time_layers)
    luck = _dict(layers.get("luck_cycle_context"))
    flow = _dict(layers.get("flow_context"))
    policy = runtime.question_plan.policy_effect
    practical = _dict(policy.get("practical_reading_context"))
    domain_readings = _dict(practical.get("domain_readings"))
    diagnosis = _dict(policy.get("real_bazi_diagnosis"))
    portraits = _list(diagnosis.get("portraits"))
    paths = _list(diagnosis.get("paths"))

    if step_id == "chart_build":
        return _summary(
            "盘面已经建立，先看日主与时间层",
            (
                f"这个盘的核心入口是 {core.day_master or '-'} 日主，系统已把原局、"
                f"大运和 {flow.get('target_year') or flow.get('target_date') or '-'} 流年放在同一张时间图里。"
                "接下来所有判断都会以这张盘为底，不会用追问去改写四柱事实。"
            ),
            [
                f"日主：{core.day_master or '-'}",
                f"五行：{_element_label(core.day_master_element)}",
                f"大运：{luck.get('current_luck_pillar') or luck.get('luck_pillar') or '待确认'}",
                f"流年：{flow.get('flow_year_pillar') or '待确认'}",
            ],
            summary_policy=summary_policy,
        )
    if step_id == "knowledge_library":
        return _summary(
            "知识库先定边界，再进入规则判断",
            "这一页不是直接下结论，而是先把古籍规则、结构知识、领域知识和事实边界装载好。它决定后面能怎么判断，也决定哪些内容必须等待用户校准。",
            [_task_number_text(tasks[0] if tasks else "", "知识单元"), "训练不改命盘", "规则只做证据", "边界先于结论"],
            summary_policy=summary_policy,
        )
    if step_id == "rule_matching":
        return _summary(
            "规则已经命中，但结论要看组合含义",
            f"本步命中 {len(evidence)} 条左右的规则证据。它们代表系统发现了可解释的十神、用神候选、地支关系或隐藏线索，但这些规则不是孤立判词，需要和后面的特征、画像、路径一起合参。",
            ["用神候选需复核", "十神显隐参与判断", "隐藏线索需追问", "反证会保留"],
            summary_policy=summary_policy,
        )
    if step_id == "feature_extraction":
        domains = _unique([_domain_label(row.domain or row.kind) for row in runtime.feature_evidence])[:4]
        return _summary(
            "特征抽取完成，后续画像和路径会用这些特征",
            f"四柱、十神、五行、结构和时间层已经整理出 {len(runtime.feature_evidence)} 条可用特征。建议把特征当作诊断线索，继续进入画像、做功路径和领域分析。",
            domains or ["日主", "十神", "五行", "结构"],
            summary_policy=summary_policy,
        )
    if step_id == "portrait_projection":
        domains = _unique([_domain_label(str(row.get("domain") or "")) for row in portraits if isinstance(row, dict)])[:4]
        return _summary(
            "画像是倾向，不是定论",
            f"本步把规则命中和特征证据合成为 {len(portraits)} 条画像倾向。它回答“这个人容易以什么方式表现”，但不会把倾向说成必然事件。",
            domains or ["事业画像", "关系画像", "健康画像", "结构画像"],
            summary_policy=summary_policy,
        )
    if step_id == "path_reasoning":
        return _summary(
            "做功路径说明力量怎么走",
            f"本步关注的不是单点吉凶，而是结构之间如何牵引、哪个领域被带动、何时更容易触发。当前整理出 {len(paths)} 条路径，用来解释后续领域结论的来源。",
            ["结构牵引", "领域落点", "时运触发", "行动建议"],
            summary_policy=summary_policy,
        )
    if step_id == "structure_reasoning":
        return _summary(
            "结构判断进入主线",
            "这一页把旺衰、格局、用神取向和结构动态合并，形成后续报告的主线。若有多个候选，系统会保留置信度和反证，不会强行给唯一判词。",
            ["旺衰", "格局", "用神", "动态路径"],
            summary_policy=summary_policy,
        )
    if step_id == "useful_god_arbitration":
        return _summary(
            "用神忌神负责取舍，不是固定断语",
            "这一页把强弱、十神、结构和做功路径合成取用策略，同时列出忌避风险。后续时运和领域建议都要围绕这个取舍验证，不能把候选五行说成唯一用神或永久忌神。",
            ["取用策略", "忌避风险", "反证边界", "时运验证"],
            summary_policy=summary_policy,
        )
    if step_id == "timing_layers":
        return _summary(
            "时运把原局放进当下",
            f"原局是底盘，大运和流年决定当下更容易被激活的主题。本步会把 {flow.get('target_year') or flow.get('target_date') or '-'} 和当前大运一起看，避免只看静态命局。",
            [
                f"大运：{luck.get('current_luck_pillar') or luck.get('luck_pillar') or '待确认'}",
                f"流年：{flow.get('flow_year_pillar') or '待确认'}",
                "阶段压力",
                "触发主题",
            ],
            summary_policy=summary_policy,
        )
    if step_id == "domain_synthesis":
        domain_names = [_domain_label(key) for key in list(domain_readings)[:4]]
        return _summary(
            "领域结论开始落到现实问题",
            f"前面的结构、画像、路径和时运已经合成到 {len(domain_readings)} 个现实领域。建议从这里开始回答事业、财运、关系等用户真正关心的问题。",
            domain_names,
            summary_policy=summary_policy,
        )
    if step_id == "final_report":
        return _summary(
            "最终报告合并前面所有步骤",
            "报告不是一次性生成的黑盒，而是把排盘、规则、特征、画像、路径、时运和追问校准统一收束成可读建议。",
            ["盘面", "规则", "路径", "建议"],
            summary_policy=summary_policy,
        )
    return _summary(str(step.get("title") or "本步总结"), str(step.get("summary") or ""), [], summary_policy=summary_policy)


def _summary(
    title: str,
    body: str,
    points: list[str],
    *,
    summary_policy: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "title": title,
        "body": body,
        "advice": _advice_from_body(body),
        "points": [point for point in points if point][:4],
        "summary_policy": summary_policy or {},
        "source": "central_brain_rule_summary",
        "llm_metadata": {
            "status": "not_requested",
            "executed": False,
            "boundary": "stage_summary_can_be_lazily_enhanced_by_llm_expression_layer",
        },
        "boundary": "stage_summary_is_customer_safe_interpretation_not_raw_trace",
    }


def _summary_policy(step: dict[str, object], runtime: CoreRuntimeResult) -> dict[str, object]:
    step_id = str(step.get("step_id") or "")
    analysis = _dict(step.get("analysis_result"))
    evidence = _list(step.get("evidence"))
    contradiction_count = len(_list(analysis.get("contradictions")))
    reasoning_count = len(_list(analysis.get("reasoning_points")))
    confidence = float(step.get("confidence") or 0.0)
    stage_importance = _stage_importance(step_id)
    information_gain = _information_gain(step_id, evidence, reasoning_count, contradiction_count, runtime)
    evidence_delta = min(1.0, round(len(evidence) / 6.0, 2))
    llm_gate = _stage_llm_gate(step_id, runtime)
    critical = llm_gate["requires_llm"] or contradiction_count >= 2 or information_gain >= 0.78
    low_value = information_gain < 0.45 and stage_importance < 0.65
    if critical:
        mode = "full"
    elif low_value:
        mode = "compact"
    else:
        mode = "compact"
    should_display = mode != "hidden"
    should_call_llm = should_display and bool(llm_gate["requires_llm"])
    return {
        "version": "v30.stage_summary_policy.v1",
        "mode": mode,
        "display_summary": should_display,
        "llm_enhancement": "auto" if should_call_llm else str(llm_gate["llm_enhancement"]),
        "prefetch_next": should_call_llm and step_id != "final_report",
        "reason": _summary_policy_reason(
            step_id,
            critical=critical,
            low_value=low_value,
            contradiction_count=contradiction_count,
            information_gain=information_gain,
            llm_gate=llm_gate,
        ),
        "signals": {
            "information_gain": round(information_gain, 2),
            "evidence_delta": evidence_delta,
            "confidence": round(confidence, 2),
            "contradiction_count": contradiction_count,
            "stage_importance": round(stage_importance, 2),
            "reasoning_point_count": reasoning_count,
            "token_budget_class": "spend" if should_call_llm else "save",
            "llm_needed_reason": llm_gate["reason"],
            "focus_scope": llm_gate["focus_scope"],
            "central_brain_contract": llm_gate["central_brain_contract"],
            "provider_thinking_mode": llm_gate["provider_thinking_mode"],
            "prompt_profile": llm_gate["prompt_profile"],
        },
        "training_signal": {
            "signal_id": "v30.training_signal.stage_summary_policy",
            "trainable": True,
            "target": "stage_local_llm_need_and_central_brain_summary_quality",
            "allowed_updates": [
                "summary_mode_weight",
                "llm_enhancement_stage_gate",
                "prefetch_next_weight",
                "stage_focus_scope_weight",
                "central_brain_review_threshold",
            ],
        },
        "boundary": "stage_summary_policy_controls_expression_cost_not_bazi_facts",
    }


def _stage_llm_gate(step_id: str, runtime: CoreRuntimeResult) -> dict[str, object]:
    practical = _dict(runtime.question_plan.policy_effect.get("practical_reading_context"))
    domain_readings = _dict(practical.get("domain_readings"))
    timing_layers = _dict(runtime.chart_context.time_layers)
    timing_has_pillars = bool(
        _dict(timing_layers.get("luck_cycle_context")).get("current_luck_pillar")
        or _dict(timing_layers.get("luck_cycle_context")).get("luck_pillar")
    ) and bool(_dict(timing_layers.get("flow_context")).get("flow_year_pillar"))
    if step_id == "domain_synthesis" and not domain_readings:
        return {
            "requires_llm": False,
            "llm_enhancement": "not_required",
            "reason": "领域素材不足时不调用 LLM，避免空泛建议。",
            "focus_scope": "等待领域素材形成后再进入用户建议。",
            "central_brain_contract": "central_brain_waits_for_domain_evidence_before_expression",
            "provider_thinking_mode": "off",
            "prompt_profile": _stage_prompt_profile_signal(step_id),
        }
    auto_stages = {
        "rule_matching": (
            "规则命中需要解释匹配项与命盘作用，避免只罗列规则。",
            "只解释本页命中的规则、规则作用和下一步验证方向。",
            "on",
        ),
        "portrait_projection": (
            "画像需要把规则与特征合成为用户能理解的倾向。",
            "只解释本页画像结论、画像依据和可执行提醒。",
            "on",
        ),
        "path_reasoning": (
            "做功路径决定力量流向和领域落点，需要推演增强。",
            "只解释本页路径机制、力量流向和领域落点。",
            "on",
        ),
        "structure_reasoning": (
            "旺衰、格局、用神取向是核心判断，需要中枢审定。",
            "只解释本页结构主线、候选取舍和用神边界。",
            "on",
        ),
        "useful_god_arbitration": (
            "用神忌神是用户关心的核心取舍，需要解释策略、风险和反证。",
            "只解释本页用神取向、忌避风险、取舍依据和后续验证边界。",
            "on",
        ),
        "domain_synthesis": (
            "领域页直接面向用户现实问题，需要把证据转成建议。",
            "只解释本页领域结论、现实影响和行动建议。",
            "on",
        ),
        "final_report": (
            "报告页需要收束所有已完成阶段，但不得新增命盘事实。",
            "只收束已完成页面的结论、建议、依据和边界。",
            "on",
        ),
    }
    if step_id == "timing_layers" and timing_has_pillars:
        auto_stages[step_id] = (
            "时运资料齐全时需要解释原局路径在当下如何被激活。",
            "只解释本页大运、流年、触发主题和阶段建议。",
            "on",
        )
    if step_id in auto_stages:
        reason, focus_scope, provider_thinking_mode = auto_stages[step_id]
        return {
            "requires_llm": True,
            "llm_enhancement": "auto",
            "reason": reason,
            "focus_scope": focus_scope,
            "central_brain_contract": "llm_derivation_returns_to_central_brain_for_stage_local_final_decision",
            "provider_thinking_mode": provider_thinking_mode,
            "prompt_profile": _stage_prompt_profile_signal(step_id),
        }
    return {
        "requires_llm": False,
        "llm_enhancement": "not_required",
        "reason": "本页以事实装载或证据整理为主，规则小结足够，节省 LLM 调用。",
        "focus_scope": "只展示本页确定事实、证据或边界，不做跨页推演。",
        "central_brain_contract": "central_brain_rule_summary_is_authoritative_for_fact_or_support_stage",
        "provider_thinking_mode": "off",
        "prompt_profile": _stage_prompt_profile_signal(step_id),
    }


def _stage_prompt_profile_signal(step_id: str) -> dict[str, object]:
    scenes = {
        "rule_matching": ("v30.stage_prompt.rule_matching.v1", "matched_rule_interpretation"),
        "portrait_projection": ("v30.stage_prompt.portrait_projection.v1", "portrait_tendency_synthesis"),
        "path_reasoning": ("v30.stage_prompt.path_reasoning.v1", "force_flow_path_derivation"),
        "structure_reasoning": ("v30.stage_prompt.structure_reasoning.v1", "structure_decision_review"),
        "useful_god_arbitration": ("v30.stage_prompt.useful_god_arbitration.v1", "useful_god_avoidance_arbitration"),
        "timing_layers": ("v30.stage_prompt.timing_layers.v1", "luck_flow_activation"),
        "domain_synthesis": ("v30.stage_prompt.domain_synthesis.v1", "practical_domain_advice"),
        "final_report": ("v30.stage_prompt.final_report.v1", "final_stage_synthesis"),
    }
    profile_id, scene = scenes.get(step_id, ("v30.stage_prompt.supporting_stage.v1", "supporting_stage_summary"))
    return {
        "profile_id": profile_id,
        "scene": scene,
        "trainable": True,
    }


def _stage_importance(step_id: str) -> float:
    weights = {
        "chart_build": 0.78,
        "knowledge_library": 0.42,
        "rule_matching": 0.86,
        "feature_extraction": 0.58,
        "portrait_projection": 0.82,
        "path_reasoning": 0.92,
        "structure_reasoning": 0.95,
        "useful_god_arbitration": 0.94,
        "timing_layers": 0.86,
        "domain_synthesis": 0.9,
        "final_report": 0.96,
    }
    return weights.get(step_id, 0.5)


def _information_gain(
    step_id: str,
    evidence: list[Any],
    reasoning_count: int,
    contradiction_count: int,
    runtime: CoreRuntimeResult,
) -> float:
    base = _stage_importance(step_id) * 0.55
    evidence_score = min(0.22, len(evidence) * 0.035)
    reasoning_score = min(0.16, reasoning_count * 0.04)
    contradiction_score = min(0.12, contradiction_count * 0.06)
    if step_id == "feature_extraction":
        evidence_score = min(0.28, len(runtime.feature_evidence) * 0.025)
    return max(0.0, min(1.0, base + evidence_score + reasoning_score + contradiction_score))


def _summary_policy_reason(
    step_id: str,
    *,
    critical: bool,
    low_value: bool,
    contradiction_count: int,
    information_gain: float,
    llm_gate: dict[str, object],
) -> str:
    if llm_gate.get("requires_llm"):
        return "stage_requires_llm_derivation_then_central_brain_review"
    if llm_gate.get("llm_enhancement") == "skip":
        return "stage_owned_by_dialogue_brain_not_summary_llm"
    if llm_gate.get("llm_enhancement") == "not_required":
        return "stage_uses_central_brain_rule_summary_without_llm"
    if critical:
        if contradiction_count >= 2:
            return "critical_stage_with_counterevidence_needs_visible_summary"
        return "high_information_gain_stage_needs_llm_expression"
    if low_value:
        return "supporting_stage_uses_compact_summary_to_save_tokens"
    return f"{step_id}_uses_compact_summary_until_more_user_context"


def _evidence_digest(step_id: str, evidence: list[str]) -> dict[str, object]:
    rows = [row for row in evidence if row]
    return {
        "title": "依据",
        "body": f"影响本步结论的关键依据有 {len(rows)} 条；只展示可读要点。",
        "items": [_readable_evidence_label(step_id, row) for row in rows[:5]],
        "raw_count": len(rows),
        "boundary": "evidence_digest_hides_internal_ids_for_customer_surface",
    }


def _advice_from_body(body: str) -> str:
    text = str(body or "")
    marker = "建议："
    if marker not in text:
        return ""
    return text.split(marker, 1)[1].strip()


def _readable_evidence_label(step_id: str, value: str) -> str:
    raw = str(value or "")
    if step_id == "chart_build":
        if "context_id" in raw:
            return "命盘上下文已建立"
        if "source=" in raw:
            return "出生资料来自本次用户输入"
        return "排盘基础证据"
    if step_id == "knowledge_library":
        if "branch_relation" in raw:
            return "地支关系与动态作用知识"
        if "career" in raw:
            return "事业路径判断知识"
        if "domain_rule" in raw:
            return "领域规则门槛"
        if "boundary" in raw:
            return "命盘事实边界规则"
        if "counterevidence" in raw:
            return "反证与复核规则"
        return "知识库条目"
    if step_id == "rule_matching":
        if "useful_god" in raw:
            return "用神候选需要复核"
        if "hidden_factor" in raw:
            return "存在需要用户校准的隐藏线索"
        if "ten_god" in raw:
            return "十神显隐关系参与判断"
        if "branch_relation" in raw:
            return "地支关系触发结构复核"
        return "规则命中项"
    if step_id == "feature_extraction":
        if "day_master" in raw:
            return "日主与五行基础特征"
        if "ten_god" in raw:
            return "十神显隐特征"
        if "element" in raw:
            return "五行分布特征"
        return "八字特征证据"
    if step_id == "portrait_projection":
        return "画像倾向证据"
    if step_id == "path_reasoning":
        return "结构或做功路径证据"
    if step_id == "structure_reasoning":
        if any(token in raw for token in ("旺衰", "strength", "strong", "weak")):
            return "旺衰候选参与结构判断"
        if any(token in raw for token in ("格局", "structure", "dynamic")):
            return "格局结构需要动态复核"
        if any(token in raw for token in ("用神", "useful_god", "god")):
            return "用神取向仍按候选处理"
        if any(token in raw for token in ("十神", "ten_god")):
            return "十神能量参与主线评分"
        return "结构主线证据"
    if step_id == "useful_god_arbitration":
        if "avoidance" in raw or "risk" in raw:
            return "忌避风险边界"
        if "candidate" in raw or "strategy" in raw:
            return "用神候选策略"
        if "cross_check" in raw:
            return "强弱十神路径交叉验证"
        return "用神忌神取舍证据"
    return _truncate(raw, 46)


def _credit_preview() -> dict[str, object]:
    return {
        "enabled": False,
        "status": "reserved",
        "estimated_credits": 0,
        "actual_credits": 0,
        "metering_basis": ["future_llm_tokens", "future_tool_calls", "future_report_export"],
        "boundary": "credit_metering_interface_reserved_without_charging_users",
    }


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _pillar_summary(pillars: dict[str, Any]) -> str:
    labels = []
    for key in ("year", "month", "day", "hour"):
        value = pillars.get(key)
        if value:
            labels.append(f"{key}={value}")
    return " ".join(labels) or "待确认"


def _decision_line(key: str, value: dict[str, Any]) -> str:
    primary = str(value.get("primary_candidate") or value.get("status") or "")
    confidence = value.get("confidence")
    suffix = f"，置信度 {float(confidence):.2f}" if isinstance(confidence, (int, float)) else ""
    return f"{_decision_domain_label(key)}：{_decision_candidate_label(primary)}{suffix}"


def _ten_god_energy_label(row: Any) -> str:
    if isinstance(row, dict):
        label = str(row.get("label") or row.get("ten_god") or "十神")
        energy = row.get("energy")
        if isinstance(energy, (int, float)):
            return f"{label}{float(energy):.2f}"
        return label
    return str(row or "十神能量")


def _feature_lines(runtime: CoreRuntimeResult) -> list[str]:
    return [
        f"{row.evidence_id}: {row.label} ({row.confidence:.2f})"
        for row in runtime.feature_evidence[:5]
    ]


def _knowledge_lines(units: list[Any]) -> list[str]:
    rows = []
    for unit in units[:6]:
        if isinstance(unit, dict):
            unit_id = str(unit.get("unit_id") or unit.get("id") or unit.get("source_id") or "knowledge_unit")
            family = str(unit.get("family") or unit.get("unit_type") or "")
            rows.append(f"{unit_id}: {family}".strip())
        else:
            rows.append(str(unit))
    return rows


def _rule_lines(signals: list[Any], matches: list[Any]) -> list[str]:
    rows = []
    for signal in signals[:3]:
        if hasattr(signal, "model_dump"):
            signal = signal.model_dump(mode="json")
        if isinstance(signal, dict):
            rows.append(str(signal.get("signal_id") or signal.get("rule_id") or signal.get("source_id") or "rule_signal"))
    for match in matches[:3]:
        if isinstance(match, dict):
            rows.append(str(match.get("rule_id") or match.get("rule_match_id") or "matched_rule"))
    return rows


def _portrait_lines(portraits: list[Any]) -> list[str]:
    rows = []
    for portrait in portraits[:6]:
        if isinstance(portrait, dict):
            portrait_id = str(portrait.get("portrait_id") or portrait.get("id") or "portrait")
            domain = str(portrait.get("domain") or "")
            dimension = str(portrait.get("dimension") or portrait.get("label") or "")
            rows.append(": ".join(part for part in [portrait_id, domain, dimension] if part))
    return rows


def _path_lines(paths: list[Any], scores: dict[str, Any]) -> list[str]:
    rows = []
    for path in paths[:4]:
        if isinstance(path, dict):
            path_id = str(path.get("path_id") or path.get("id") or "path")
            mechanism = str(path.get("mechanism") or path.get("label") or "")
            rows.append(": ".join(part for part in [path_id, mechanism] if part))
    for key, value in list(scores.items())[:3]:
        rows.append(f"{key}={value}")
    return rows


def _useful_god_lines(useful: dict[str, Any], candidates: list[Any]) -> list[str]:
    rows = []
    primary = str(useful.get("primary_label") or "")
    if primary:
        rows.append(f"useful_god_strategy={primary}")
    for element in _list(useful.get("primary_elements"))[:3]:
        rows.append(f"useful_god_element={element}")
    avoidance = _dict(useful.get("avoidance_model"))
    for risk in _list(avoidance.get("primary_risks"))[:2]:
        rows.append(f"avoidance_risk={risk}")
    for row in candidates[:2]:
        if isinstance(row, dict):
            rows.append(f"candidate={row.get('label') or row.get('strategy')}: score={row.get('score')}")
    return rows


def _useful_element_labels(useful: dict[str, Any]) -> list[str]:
    primary = _dict(_list(useful.get("candidates"))[0]) if _list(useful.get("candidates")) else {}
    labels = [str(row) for row in _list(primary.get("element_labels")) if str(row).strip()]
    if labels:
        return labels[:4]
    return [_element_label(str(row)) for row in _list(useful.get("primary_elements")) if str(row).strip()][:4]


def _useful_family_labels(useful: dict[str, Any]) -> list[str]:
    primary = _dict(_list(useful.get("candidates"))[0]) if _list(useful.get("candidates")) else {}
    labels = [str(row) for row in _list(primary.get("family_labels")) if str(row).strip()]
    if labels:
        return labels[:4]
    family_labels = {
        "self": "比劫",
        "output": "食伤",
        "wealth": "财星",
        "authority": "官杀",
        "resource": "印星",
    }
    return [family_labels.get(str(row), str(row)) for row in _list(useful.get("primary_families")) if str(row).strip()][:4]


def _domain_lines(domains: dict[str, Any]) -> list[str]:
    rows = []
    for key, value in list(domains.items())[:5]:
        value = _dict(value)
        label = str(value.get("title") or value.get("summary") or key)
        rows.append(f"{key}: {_truncate(label, 80)}")
    return rows


def _top_element_lines(distribution: dict[str, Any]) -> list[str]:
    rows: list[tuple[str, float]] = []
    for key, value in distribution.items():
        if isinstance(value, dict):
            raw = value.get("score") or value.get("weight") or value.get("count") or 0
        else:
            raw = value
        try:
            score = float(raw)
        except (TypeError, ValueError):
            continue
        rows.append((_element_label(str(key)), score))
    rows.sort(key=lambda row: row[1], reverse=True)
    return [f"{label}{score:g}" for label, score in rows[:5]]


def _rule_meaning_label(row: Any) -> str:
    if hasattr(row, "model_dump"):
        row = row.model_dump(mode="json")
    if not isinstance(row, dict):
        return "规则信号"
    raw = " ".join(
        str(row.get(key) or "")
        for key in ("signal_id", "rule_id", "source_id", "label", "family", "domain", "rule_type")
    ).lower()
    if "useful_god" in raw or "yong" in raw:
        return "用神候选"
    if "hidden" in raw:
        return "隐藏线索"
    if "ten_god" in raw or "ten-god" in raw:
        return "十神显隐"
    if "branch" in raw or "relation" in raw:
        return "地支关系"
    if "career" in raw:
        return "事业倾向"
    if "wealth" in raw:
        return "财运倾向"
    if "relationship" in raw or "romance" in raw:
        return "关系倾向"
    return "规则命中"


def _rule_public_matches(signals: list[Any], matches: list[Any]) -> list[str]:
    candidates = [*signals[:8], *matches[:8]]
    labels = _unique([_rule_meaning_label(row) for row in candidates])
    generic = [row for row in labels if row == "规则命中"]
    specific = [row for row in labels if row != "规则命中"]
    return (specific or generic)[:5]


def _rule_impact_text(labels: list[str]) -> str:
    impacts = []
    for label in labels:
        if label == "用神候选":
            impacts.append("用于判断用神取向是否能成立")
        elif label == "十神显隐":
            impacts.append("用于定位性格、事业、关系等表现入口")
        elif label == "地支关系":
            impacts.append("用于复核冲合刑害与结构做功路径")
        elif label == "隐藏线索":
            impacts.append("提示后续追问要校准现实背景")
        elif label == "事业倾向":
            impacts.append("把后续判断引向事业领域验证")
        elif label == "财运倾向":
            impacts.append("把后续判断引向财运领域验证")
        elif label == "关系倾向":
            impacts.append("把后续判断引向关系领域验证")
        elif label == "规则命中":
            impacts.append("提供候选证据，等待结构和时运确认")
    return "；".join(_unique(impacts)) or "提供候选证据，等待特征、画像、路径和时运确认。"


def _structure_label(value: str) -> str:
    raw = str(value or "").strip()
    lowered = raw.lower()
    traits: list[str] = []
    if any(token in lowered for token in ("branch", "dynamic")) or "地支关系" in raw or "动态" in raw:
        traits.append("地支动态")
    if any(token in lowered for token in ("strength", "pattern")) or "旺衰" in raw or "格局" in raw:
        traits.append("旺衰候选")
    if "ten-god" in lowered or "ten_god" in lowered or "十神" in raw:
        traits.append("十神评分")
    if "counter" in lowered or "反证" in raw:
        traits.append("反证")
    if any(token in lowered for token in ("path", "mechanism")) or "路径" in raw:
        traits.append("路径评分")
    if "time layer missing" in lowered or "时间层缺失" in raw or "时运" in raw:
        traits.append("时运待补")
    if any(token in lowered for token in ("evidence", "chart", "knowledge/rule/portrait", "rule evidence")) or "证据" in raw:
        traits.insert(0, "证据约束")
    priority = ["证据约束", "反证", "地支动态", "旺衰候选", "路径评分", "十神评分", "时运待补"]
    traits = [row for row in priority if row in _unique([item for item in traits if item])][:4]
    if traits:
        detail = "、".join(row for row in traits if row != "证据约束")
        if detail:
            return f"证据约束型结构（含{detail}）"
        return "证据约束型结构"
    return _clean_public_structure_text(raw[:80]) or "结构主线待确认"


def _clean_public_structure_text(text: str) -> str:
    replacements = {
        "evidence-bound chart structure": "证据约束型结构",
        "branch relations require dynamic review": "地支动态复核",
        "strength and pattern review remains candidate-bound": "旺衰格局候选",
        "ten-god energy model scored": "十神能量评分",
        "domain rules remain review candidates": "领域规则复核",
        "time layer missing": "时运资料待补",
        "knowledge/rule/portrait signals bound": "知识、规则、画像信号已绑定",
        "rule evidence executed": "规则证据已执行",
        "counter-evidence present": "存在反证",
        "mechanism paths scored": "机制路径已评分",
    }
    clean = str(text or "")
    for source, target in replacements.items():
        clean = clean.replace(source, target)
    return clean


def _chain_label(rows: list[str]) -> str:
    labels = {
        "chart_context": "命盘事实",
        "ten_god_visibility": "十神显隐",
        "ten_god_energy_model": "十神能量",
        "element_distribution": "五行分布",
        "branch_relation": "地支关系",
        "branch_relations": "地支关系",
        "rule_evidence": "规则证据",
        "mechanism_paths": "做功路径",
        "domain_rules": "领域规则",
    }
    translated = [labels.get(str(row), str(row).replace("_", " ")) for row in rows if row]
    return " > ".join(translated) or "待路径层补强"


def _decision_domain_label(value: str) -> str:
    labels = {
        "strength": "旺衰",
        "structure_pattern": "格局结构",
        "useful_god": "用神取向",
        "wealth": "财运",
        "career": "事业",
        "relationship": "关系",
        "health": "健康",
        "timing": "时运",
    }
    return labels.get(str(value or ""), str(value or "候选判断").replace("_", " "))


def _decision_candidate_label(value: str) -> str:
    raw = str(value or "")
    lowered = raw.lower()
    exact = {
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
    if lowered in exact:
        return exact[lowered]
    if lowered == "strong" or "strong_" in lowered:
        return "日主偏旺候选"
    if "balanced" in lowered or "balance" in lowered:
        return "平衡取向"
    if "ordinary" in lowered or "structure" in lowered:
        return "常规格局复核"
    if "strength" in lowered:
        return "旺衰复核"
    if "useful" in lowered or "god" in lowered:
        return "用神候选"
    if "review" in lowered:
        return "需要复核"
    return raw.replace("_", " ")[:40] or "候选判断"


def _knowledge_family_label(value: str) -> str:
    raw = str(value or "")
    lowered = raw.lower()
    labels = {
        "core_runtime": "核心运行规则",
        "domain_rule": "领域判断规则",
        "foundation_boundary": "基础边界规则",
        "domain_rule_gate": "领域准入门槛",
        "boundary": "边界规则",
        "counterevidence": "反证规则",
        "branch_relation": "地支关系规则",
        "career": "事业规则",
        "wealth": "财运规则",
        "relationship": "关系规则",
        "health": "健康规则",
    }
    return labels.get(lowered, raw.replace("_", " ")[:40] or "基础规则")


def _element_label(key: str) -> str:
    return {
        "wood": "木",
        "fire": "火",
        "earth": "土",
        "metal": "金",
        "water": "水",
    }.get(str(key or "").lower(), str(key or "-"))


def _domain_label(key: str) -> str:
    return {
        "career": "事业",
        "wealth": "财运",
        "relationship": "关系",
        "romance": "关系",
        "health": "健康",
        "timing": "时运",
        "structure": "结构",
        "useful_god": "用神取向",
        "hidden_factor": "隐藏线索",
        "decision": "决策",
        "risk": "风险",
        "overview": "总览",
    }.get(str(key or "").lower(), str(key or ""))


def _assertion_level_label(level: str) -> str:
    return {
        "confirmed": "可明确断",
        "supported": "证据支持",
        "mixed": "分支并存",
        "weak_candidate": "候选待复核",
        "blocked": "暂不下断",
    }.get(str(level or ""), str(level or "候选"))


def _task_number_text(value: Any, fallback: str) -> str:
    import re

    match = re.search(r"(\d+)", str(value or ""))
    return f"{fallback}：{match.group(1)} 条" if match else fallback


def _unique(rows: list[str]) -> list[str]:
    seen = set()
    result = []
    for row in rows:
        if not row or row in seen:
            continue
        seen.add(row)
        result.append(row)
    return result


def _truncate(value: str, limit: int) -> str:
    clean = " ".join(str(value or "").split())
    return clean if len(clean) <= limit else f"{clean[:limit - 1]}..."
