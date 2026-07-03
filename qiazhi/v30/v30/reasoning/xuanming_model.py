from __future__ import annotations

from typing import Any

from v30.contracts import CoreRuntimeResult
from v30.core.constants import CONTROLS, ELEMENTS, GENERATES


XUANMING_CORE_MODEL_VERSION = "v30.xuanming_core_model.v1"
ELEMENT_LABELS = {
    "wood": "木",
    "fire": "火",
    "earth": "土",
    "metal": "金",
    "water": "水",
}
TEN_GOD_FAMILY_LABELS = {
    "self": "比劫",
    "output": "食伤",
    "wealth": "财星",
    "authority": "官杀",
    "resource": "印星",
    "unknown": "未归类",
}
DOMAIN_LABELS = {
    "structure": "结构",
    "wealth": "财运",
    "career": "事业",
    "relationship": "关系",
    "health": "健康",
    "useful_god": "用神",
}
CHAIN_LABELS = {
    "chart_context": "命盘事实",
    "ten_god_visibility": "十神显隐",
    "ten_god_energy_model": "十神能量",
    "element_distribution": "五行分布",
    "branch_relation_review": "地支关系",
    "strength_pattern_candidate_review": "旺衰格局候选",
    "domain_rule_candidate_review": "领域规则候选",
    "time_context_boundary": "时间层边界",
    "rule_evidence_review": "规则证据",
    "rule_counterevidence_review": "反证复核",
    "knowledge_signal_review": "知识信号",
    "rule_signal_review": "规则信号",
    "portrait_signal_review": "画像信号",
    "mechanism_path_review": "机制路径",
    "dynamic_graph_review": "动态图复核",
}
SEASON_ELEMENT_BY_BRANCH = {
    "寅": "wood",
    "卯": "wood",
    "辰": "wood",
    "巳": "fire",
    "午": "fire",
    "未": "fire",
    "申": "metal",
    "酉": "metal",
    "戌": "metal",
    "亥": "water",
    "子": "water",
    "丑": "water",
}
SEASONAL_STATE_LABELS = {
    "wang": "旺",
    "xiang": "相",
    "xiu": "休",
    "qiu": "囚",
    "si": "死",
    "unknown": "未知",
}
SEASONAL_STATE_SCORE = {
    "wang": 0.28,
    "xiang": 0.18,
    "xiu": -0.08,
    "qiu": -0.18,
    "si": -0.24,
    "unknown": 0.0,
}
PILLAR_ROOT_WEIGHTS = {
    "month": 0.18,
    "day": 0.14,
    "hour": 0.1,
    "year": 0.08,
}
VISIBLE_STEM_WEIGHTS = {
    "month": 0.1,
    "year": 0.08,
    "hour": 0.08,
    "day": 0.0,
}
CONFLICT_RELATIONS = {"clash", "harm", "break", "punishment"}
ALIGNMENT_RELATIONS = {"harmony", "three_harmony", "three_meeting"}


def build_xuanming_core_model(runtime: CoreRuntimeResult) -> dict[str, object]:
    """Build a deterministic reasoning packet for customer-safe stage summaries."""

    chart_axis = _chart_axis(runtime)
    strength_model = _strength_model(runtime, chart_axis)
    ten_god_model = _ten_god_model(runtime)
    structure_model = _structure_model(runtime)
    path_model = _path_model(runtime)
    useful_god_model = _useful_god_model(
        runtime,
        chart_axis=chart_axis,
        strength_model=strength_model,
        ten_god_model=ten_god_model,
        structure_model=structure_model,
        path_model=path_model,
    )
    timing_model = _timing_model(runtime)
    mainline = _mainline(
        runtime,
        chart_axis=chart_axis,
        strength_model=strength_model,
        ten_god_model=ten_god_model,
        structure_model=structure_model,
        path_model=path_model,
        useful_god_model=useful_god_model,
        timing_model=timing_model,
    )
    return {
        "version": XUANMING_CORE_MODEL_VERSION,
        "reading_id": runtime.reading_id,
        "chart_axis": chart_axis,
        "strength_model": strength_model,
        "ten_god_model": ten_god_model,
        "structure_model": structure_model,
        "path_model": path_model,
        "useful_god_model": useful_god_model,
        "timing_model": timing_model,
        "mainline": mainline,
        "contracts": {
            "chart_fact_mutation_allowed": False,
            "llm_role": "expression_only_after_core_model",
            "confidence_policy": "score_is_model_signal_not_fate_probability",
        },
        "boundary": "xuanming_core_model_integrates_existing_v30_modules_without_mutating_chart_facts",
    }


def _chart_axis(runtime: CoreRuntimeResult) -> dict[str, object]:
    chart = runtime.chart_context
    natal = _dict(chart.natal_pillars)
    pillars = _dict(natal.get("pillars"))
    month = _dict(pillars.get("month"))
    day = _dict(pillars.get("day"))
    return {
        "day_master": chart.day_master,
        "day_master_element": chart.day_master_element,
        "day_master_element_label": _element_label(chart.day_master_element),
        "month_branch": str(month.get("branch") or ""),
        "day_pillar": str(day.get("display") or f"{day.get('stem') or chart.day_master}{day.get('branch') or ''}"),
        "pillars": {
            key: _pillar_display(_dict(pillars.get(key)))
            for key in ("year", "month", "day", "hour")
        },
        "source_status": str(_dict(chart.input_pillars.get("chart_build_source")).get("status") or "ready"),
        "boundary": "chart_axis_is_fact_snapshot",
    }


def _strength_model(runtime: CoreRuntimeResult, chart_axis: dict[str, object]) -> dict[str, object]:
    natal = _dict(runtime.chart_context.natal_pillars)
    base_summary = _dict(natal.get("base_fact_summary"))
    root_summary = _dict(base_summary.get("root_fact_summary"))
    distribution = {
        element: _float(_dict(natal.get("element_distribution")).get(element), 0.0)
        for element in ELEMENTS
    }
    total = round(sum(distribution.values()), 3)
    day_element = str(chart_axis.get("day_master_element") or "")
    day_score = distribution.get(day_element, 0.0)
    supporters = _supporting_elements(day_element)
    drains = _draining_elements(day_element)
    supporter_score = round(sum(distribution.get(element, 0.0) for element in supporters), 3)
    pressure_score = round(sum(distribution.get(element, 0.0) for element in drains), 3)
    ratio = round(day_score / total, 3) if total else 0.0
    support_ratio = round(supporter_score / total, 3) if total else 0.0
    pressure_ratio = round(pressure_score / total, 3) if total else 0.0
    seasonal_model = _seasonal_model(day_element, str(chart_axis.get("month_branch") or ""))
    root_model = _root_model(root_summary)
    stem_model = _stem_model(natal, day_element)
    relation_model = _relation_model(natal, day_element)
    distribution_component = round((support_ratio - pressure_ratio) * 0.42, 3)
    seasonal_component = _float(seasonal_model.get("score_adjustment"), 0.0)
    root_component = _float(root_model.get("score_adjustment"), 0.0)
    stem_component = _float(stem_model.get("score_adjustment"), 0.0)
    relation_component = _float(relation_model.get("score_adjustment"), 0.0)
    raw_balance_score = round(
        0.5
        + distribution_component
        + seasonal_component
        + root_component
        + stem_component
        + relation_component,
        3,
    )
    net_score = round(max(0.0, min(1.0, raw_balance_score)), 3)
    classification = _strength_classification(net_score, ratio, support_ratio, pressure_ratio)
    strongest = _top_elements(distribution, reverse=True)
    weakest = _top_elements(distribution, reverse=False)
    return {
        "status": "ready" if total else "partial",
        "algorithm": "weighted_month_root_stem_relation_v1",
        "classification": classification,
        "net_score": net_score,
        "raw_balance_score": raw_balance_score,
        "day_element_ratio": ratio,
        "support_ratio": support_ratio,
        "pressure_ratio": pressure_ratio,
        "scoring_components": {
            "distribution": distribution_component,
            "seasonal": seasonal_component,
            "root": root_component,
            "visible_stem": stem_component,
            "relation": relation_component,
        },
        "seasonal_model": seasonal_model,
        "root_model": root_model,
        "stem_model": stem_model,
        "relation_model": relation_model,
        "element_distribution": distribution,
        "strongest_elements": strongest,
        "weakest_elements": weakest,
        "supporting_elements": [_element_label(element) for element in supporters if element],
        "draining_or_controlling_elements": [_element_label(element) for element in drains if element],
        "explanation": _strength_explanation(classification, day_element, strongest, weakest),
        "boundary": "strength_model_is_scored_judgment_not_chart_fact",
    }


def _ten_god_model(runtime: CoreRuntimeResult) -> dict[str, object]:
    natal = _dict(runtime.chart_context.natal_pillars)
    visible = _list(natal.get("visible_ten_gods"))
    hidden = _list(natal.get("hidden_ten_gods"))
    summary = _dict(runtime.question_plan.policy_effect.get("ten_god_energy_summary"))
    top_energy = [_top_energy_row(row) for row in _list(summary.get("top_energy")) if isinstance(row, dict)]
    family_scores: dict[str, float] = {}
    for row in top_energy:
        family = str(row.get("family") or "unknown")
        family_scores[family] = max(family_scores.get(family, 0.0), _float(row.get("energy"), 0.0))
    visible_labels = _unique(_ten_god_label(row) for row in visible)[:8]
    hidden_labels = _unique(_ten_god_label(row) for row in hidden)[:8]
    dominant_roles = [
        {
            "family": family,
            "label": TEN_GOD_FAMILY_LABELS.get(family, family),
            "score": round(score, 3),
        }
        for family, score in sorted(family_scores.items(), key=lambda item: (-item[1], item[0]))[:4]
    ]
    return {
        "status": str(summary.get("status") or ("ready" if visible or hidden else "partial")),
        "visible_labels": visible_labels,
        "hidden_labels": hidden_labels,
        "dominant_roles": dominant_roles,
        "top_energy": top_energy[:4],
        "volatility_alerts": [str(row) for row in _list(summary.get("high_volatility_ten_gods"))[:4]],
        "stability_alerts": [str(row) for row in _list(summary.get("low_stability_ten_gods"))[:4]],
        "role_balance": _role_balance(visible_labels, hidden_labels, dominant_roles),
        "boundary": "ten_god_model_consumes_visibility_and_energy_signals_not_final_outcome",
    }


def _structure_model(runtime: CoreRuntimeResult) -> dict[str, object]:
    structure = runtime.structure_state
    ranked = _dict(runtime.question_plan.policy_effect.get("ranked_decisions"))
    ranked_rows = []
    for key, value in ranked.items():
        if not isinstance(value, dict):
            continue
        ranked_rows.append({
            "domain": str(key),
            "candidate": _candidate_label(str(value.get("primary_candidate") or value.get("status") or key)),
            "confidence": round(_float(value.get("confidence"), 0.0), 3),
        })
    return {
        "state": structure.state,
        "semantic_label": _structure_label(structure.semantic_label or structure.state),
        "confidence": round(structure.confidence, 3),
        "primary_chain": [_chain_label(row) for row in structure.primary_chain[:8]],
        "candidate_chain_count": len(structure.candidate_chains),
        "ranked_decisions": ranked_rows[:5],
        "counter_evidence_count": int(_float(structure.path_scores.get("rule_countered_count"), 0.0)),
        "blocked_rule_count": int(_float(structure.path_scores.get("rule_blocked_count"), 0.0)),
        "boundary": "structure_model_is_arbitration_signal_with_counterevidence",
    }


def _path_model(runtime: CoreRuntimeResult) -> dict[str, object]:
    diagnosis = _dict(runtime.question_plan.policy_effect.get("real_bazi_diagnosis"))
    paths = _list(diagnosis.get("paths"))
    rows = []
    domain_scores: dict[str, float] = {}
    mechanism_counts: dict[str, int] = {}
    for path in paths[:10]:
        if not isinstance(path, dict):
            continue
        mechanism = str(path.get("mechanism") or path.get("title") or "结构流通路径")
        score = round(_float(path.get("score"), 0.0), 3)
        domains = [str(row) for row in _list(path.get("domain_targets")) if row]
        for domain in domains:
            domain_scores[domain] = max(domain_scores.get(domain, 0.0), score)
        mechanism_counts[mechanism] = mechanism_counts.get(mechanism, 0) + 1
        rows.append({
            "mechanism": mechanism,
            "domains": [_domain_label(domain) for domain in domains],
            "score": score,
            "statement": str(path.get("diagnosis_statement") or "")[:120],
            "risk": str(path.get("risk_statement") or "")[:120],
        })
    top_domains = [
        {"domain": _domain_label(domain), "score": round(score, 3)}
        for domain, score in sorted(domain_scores.items(), key=lambda item: (-item[1], item[0]))[:5]
    ]
    return {
        "status": "ready" if rows else "partial",
        "path_count": len(paths),
        "top_paths": rows[:4],
        "top_domains": top_domains,
        "mechanism_counts": dict(sorted(mechanism_counts.items())),
        "graph_density": {
            "nodes": len(runtime.structure_state.graph_nodes),
            "edges": len(runtime.structure_state.graph_edges),
            "dynamic_paths": int(_float(runtime.structure_state.path_scores.get("dynamic_path_count"), 0.0)),
        },
        "boundary": "path_model_explains_force_flow_not_event_prediction",
    }


def _useful_god_model(
    runtime: CoreRuntimeResult,
    *,
    chart_axis: dict[str, object],
    strength_model: dict[str, object],
    ten_god_model: dict[str, object],
    structure_model: dict[str, object],
    path_model: dict[str, object],
) -> dict[str, object]:
    ranked = _dict(runtime.question_plan.policy_effect.get("ranked_decisions"))
    ranked_useful = _dict(ranked.get("useful_god"))
    day_element = str(chart_axis.get("day_master_element") or "")
    net_score = _float(strength_model.get("net_score"), 0.5)
    weakest = [
        str(row.get("element") or "")
        for row in _list(strength_model.get("weakest_elements"))
        if isinstance(row, dict) and row.get("element")
    ]
    candidates = [
        _candidate_support(day_element, net_score),
        _candidate_release(day_element, net_score, path_model),
        _candidate_regulate(day_element, net_score, path_model),
        _candidate_climate(day_element, strength_model, weakest),
        _candidate_mediation(day_element, path_model, structure_model),
        _candidate_balance(day_element, weakest),
    ]
    candidates = [_candidate_with_ranked_signal(row, ranked_useful) for row in candidates if row["score"] > 0.0]
    candidates.sort(key=lambda row: (-_float(row.get("score"), 0.0), str(row.get("strategy"))))
    primary = candidates[0] if candidates else {}
    dominant_roles = _list(ten_god_model.get("dominant_roles"))
    role_text = "、".join(
        str(row.get("label") or "")
        for row in dominant_roles[:3]
        if isinstance(row, dict) and row.get("label")
    )
    avoidance_model = _avoidance_model(
        primary,
        candidates,
        strength_model=strength_model,
        structure_model=structure_model,
        path_model=path_model,
    )
    return {
        "status": "ready" if candidates else "partial",
        "algorithm": "multi_strategy_useful_god_candidate_v1",
        "primary_strategy": str(primary.get("strategy") or "candidate_review"),
        "primary_label": str(primary.get("label") or "用神候选待复核"),
        "primary_elements": _list(primary.get("elements")),
        "primary_families": _list(primary.get("families")),
        "candidates": candidates[:5],
        "ranked_decision": {
            "primary_candidate": _candidate_label(str(ranked_useful.get("primary_candidate") or "")),
            "confidence": round(_float(ranked_useful.get("confidence"), 0.0), 3),
            "boundary": str(ranked_useful.get("boundary") or ""),
        },
        "avoidance_model": avoidance_model,
        "cross_checks": [
            f"强弱模型：{strength_model.get('classification') or '待复核'}，净分{strength_model.get('net_score')}",
            f"十神重点：{role_text or '待聚焦'}",
            f"结构反证：{structure_model.get('counter_evidence_count') or 0}条",
            f"做功路径：{path_model.get('path_count') or 0}条",
        ],
        "risks": [
            "用神只能作为候选策略，不能在证据不足时固定为唯一五行。",
            "调候、扶抑、通关、制化可能同时存在，需要按路径和时运取舍。",
            "若后续用户反馈显示现实路径不吻合，应调整候选权重而不是改写命盘事实。",
        ],
        "training_signal": {
            "signal_id": "v30.training_signal.useful_god_arbitration",
            "trainable": True,
            "targets": [
                "useful_god_strategy_weight",
                "avoidance_risk_weight",
                "counterevidence_penalty",
                "timing_activation_weight",
                "sidebar_memory_priority",
            ],
            "blocked_targets": [
                "chart_facts",
                "pillar_calculation",
                "fixed_useful_god_verdict",
                "fixed_unfavorable_element_verdict",
            ],
        },
        "boundary": "useful_god_model_outputs_ranked_candidate_strategies_not_fixed_favorable_verdict",
    }


def _timing_model(runtime: CoreRuntimeResult) -> dict[str, object]:
    layers = _dict(runtime.chart_context.time_layers)
    luck = _dict(layers.get("luck_cycle_context"))
    flow = _dict(layers.get("flow_context"))
    six = _dict(layers.get("six_pillar_context"))
    status = str(layers.get("status") or luck.get("status") or flow.get("status") or "ready")
    luck_pillar = str(luck.get("current_luck_pillar") or luck.get("luck_pillar") or "")
    flow_pillar = str(flow.get("flow_year_pillar") or "")
    activation_tags = []
    if luck_pillar:
        activation_tags.append(f"大运{luck_pillar}")
    if flow_pillar:
        activation_tags.append(f"流年{flow_pillar}")
    if six.get("status"):
        activation_tags.append("六柱合参")
    return {
        "status": status,
        "current_luck_pillar": luck_pillar,
        "flow_year_pillar": flow_pillar,
        "target_date": str(flow.get("target_date") or ""),
        "activation_tags": activation_tags,
        "activation_summary": "、".join(activation_tags) + "用于判断原局哪条路径被推到前台" if activation_tags else "时间层资料不足，当前只保留原局结构判断",
        "boundary": "timing_model_can_activate_but_not_invent_natal_structure",
    }


def _mainline(
    runtime: CoreRuntimeResult,
    *,
    chart_axis: dict[str, object],
    strength_model: dict[str, object],
    ten_god_model: dict[str, object],
    structure_model: dict[str, object],
    path_model: dict[str, object],
    useful_god_model: dict[str, object],
    timing_model: dict[str, object],
) -> dict[str, object]:
    day_master = str(chart_axis.get("day_master") or "-")
    month_branch = str(chart_axis.get("month_branch") or "月令")
    strength = str(strength_model.get("classification") or "待判")
    structure = str(structure_model.get("semantic_label") or runtime.structure_state.state)
    roles = _list(ten_god_model.get("dominant_roles"))
    role_text = "、".join(str(row.get("label")) for row in roles[:2] if isinstance(row, dict) and row.get("label")) or "十神角色待聚焦"
    top_paths = _list(path_model.get("top_paths"))
    path_text = str(top_paths[0].get("mechanism")) if top_paths and isinstance(top_paths[0], dict) else "结构路径待补强"
    useful_text = str(useful_god_model.get("primary_label") or "用神候选待复核")
    timing_text = str(timing_model.get("activation_summary") or "时运层待补")
    confidence = round(
        (
            _confidence_from_status(strength_model.get("status"))
            + _confidence_from_status(ten_god_model.get("status"))
            + _float(structure_model.get("confidence"), 0.0)
            + _confidence_from_status(path_model.get("status"))
            + _confidence_from_status(timing_model.get("status"))
        )
        / 5,
        3,
    )
    thesis = (
        f"{day_master}日主以{month_branch}月为入口，当前先按{strength}处理；"
        f"十神重点落在{role_text}，结构主线为{structure}，做功路径优先看{path_text}，用神策略先取{useful_text}。"
    )
    return {
        "thesis": thesis,
        "confidence": confidence,
        "key_reasons": [
            str(strength_model.get("explanation") or ""),
            f"十神角色：{role_text}。",
            f"结构合参：{structure}。",
            f"路径重点：{path_text}。",
            f"用神候选：{useful_text}。",
            timing_text,
        ],
        "risks": _mainline_risks(strength_model, structure_model, path_model, timing_model),
        "next_questions": _next_questions(path_model, timing_model),
        "quality_gate": "evidence_bound_model_ready" if confidence >= 0.64 else "needs_more_calibration",
        "boundary": "mainline_is_current_best_synthesis_not_single_rule_verdict",
    }


def _supporting_elements(day_element: str) -> tuple[str, str]:
    if day_element not in ELEMENTS:
        return ("", "")
    generator = next((left for left, right in GENERATES.items() if right == day_element), "")
    return (day_element, generator)


def _draining_elements(day_element: str) -> tuple[str, str, str]:
    if day_element not in ELEMENTS:
        return ("", "", "")
    output = GENERATES.get(day_element, "")
    controlled_by_day = CONTROLS.get(day_element, "")
    controller = next((left for left, right in CONTROLS.items() if right == day_element), "")
    return (output, controlled_by_day, controller)


def _candidate_support(day_element: str, net_score: float) -> dict[str, object]:
    elements = [row for row in _supporting_elements(day_element) if row]
    score = 0.34 + max(0.0, 0.5 - net_score) * 0.72
    return _useful_candidate(
        strategy="support",
        label="扶抑补身",
        elements=elements,
        families=["self", "resource"],
        score=score,
        reasons=[
            "日主偏弱或承载不足时，先看比劫与印星是否能扶身。",
            "通根、透干和月令若不足，扶抑候选需要上升。",
        ],
        counter_evidence=[
            "若日主已偏旺，继续扶身会加重失衡。",
            "若财官食伤路径已经走通，未必优先补身。",
        ],
    )


def _candidate_release(day_element: str, net_score: float, path_model: dict[str, object]) -> dict[str, object]:
    output = GENERATES.get(day_element, "")
    wealth = CONTROLS.get(day_element, "")
    mechanism_bonus = _mechanism_bonus(path_model, {"食伤生财", "比劫争财"})
    score = 0.3 + max(0.0, net_score - 0.5) * 0.58 + mechanism_bonus
    return _useful_candidate(
        strategy="release",
        label="泄秀生财",
        elements=[row for row in (output, wealth) if row],
        families=["output", "wealth"],
        score=score,
        reasons=[
            "日主偏旺时，食伤泄秀、财星承接更容易成为取用方向。",
            "若做功路径出现食伤生财，输出到财的路径优先级提高。",
        ],
        counter_evidence=[
            "若日主偏弱，食伤财星过重会继续消耗承载。",
            "财星路径不能直接等同于收入结果，仍需看行业和时运。",
        ],
    )


def _candidate_regulate(day_element: str, net_score: float, path_model: dict[str, object]) -> dict[str, object]:
    authority = next((left for left, right in CONTROLS.items() if right == day_element), "")
    mechanism_bonus = _mechanism_bonus(path_model, {"官印相生", "食伤制官杀", "财官印制化", "制化转生"})
    score = 0.28 + max(0.0, net_score - 0.56) * 0.42 + mechanism_bonus
    return _useful_candidate(
        strategy="regulate",
        label="官杀制衡",
        elements=[authority] if authority else [],
        families=["authority"],
        score=score,
        reasons=[
            "日主偏旺或结构需要约束时，官杀可作为规制与压力边界。",
            "若路径出现官印、食伤制杀或财官印，官杀不是单独使用，而要看承接。",
        ],
        counter_evidence=[
            "若印星承接不足，官杀容易只表现为压力。",
            "官杀候选不能直接转成职位、权力或婚恋结论。",
        ],
    )


def _candidate_climate(day_element: str, strength_model: dict[str, object], weakest: list[str]) -> dict[str, object]:
    seasonal = _dict(strength_model.get("seasonal_model"))
    season_element = str(seasonal.get("season_element") or "")
    targets = [element for element in ("fire", "water") if element in weakest]
    if season_element == "fire" and "water" not in targets:
        targets.append("water")
    if season_element == "water" and "fire" not in targets:
        targets.append("fire")
    score = 0.24 + (0.22 if targets else 0.0)
    return _useful_candidate(
        strategy="climate",
        label="调候候选",
        elements=targets,
        families=[_family_for_element(day_element, element) for element in targets],
        score=score,
        reasons=[
            "火水失衡或寒暖偏颇时，调候候选需要单独保留。",
            "调候不是固定用神，需要继续看结构是否允许该五行落地。",
        ],
        counter_evidence=[
            "若火水并非薄弱或过偏，调候只作为辅助策略。",
            "调候不能绕过强弱、通关和做功路径直接定论。",
        ],
    )


def _candidate_mediation(day_element: str, path_model: dict[str, object], structure_model: dict[str, object]) -> dict[str, object]:
    resource = next((left for left, right in GENERATES.items() if right == day_element), "")
    output = GENERATES.get(day_element, "")
    mechanisms = {
        str(row.get("mechanism") or "")
        for row in _list(path_model.get("top_paths"))
        if isinstance(row, dict)
    }
    mediation_hit = bool(mechanisms & {"印星通关", "制化转生", "财官印制化", "官印相生", "食伤制官杀"})
    counter_evidence = int(_float(structure_model.get("counter_evidence_count"), 0.0))
    score = 0.26 + (0.24 if mediation_hit else 0.0) + min(0.12, counter_evidence * 0.03)
    return _useful_candidate(
        strategy="mediation",
        label="通关制化",
        elements=[row for row in (resource, output) if row],
        families=["resource", "output"],
        score=score,
        reasons=[
            "结构出现冲突或财官印、食伤制杀等路径时，重点不是单补某五行，而是找能承接压力的中介。",
            "印星通关、食伤制官杀、财官印制化都属于路径型用神候选。",
        ],
        counter_evidence=[
            "若路径证据不足，通关制化只能作为候选，不可升级为唯一取用。",
            "制化需要看时运是否激活，不能只凭原局名词定论。",
        ],
    )


def _candidate_balance(day_element: str, weakest: list[str]) -> dict[str, object]:
    families = [_family_for_element(day_element, element) for element in weakest]
    return _useful_candidate(
        strategy="balance",
        label="补偏平衡",
        elements=weakest[:3],
        families=families[:3],
        score=0.36 + min(0.12, len(weakest) * 0.03),
        reasons=[
            "当强弱未形成明确方向时，先保留薄弱五行作为平衡候选。",
            "补偏平衡适合中和待复核的盘，不急着给唯一用神。",
        ],
        counter_evidence=[
            "薄弱不等于一定可用，还要看月令、透干、通根和路径是否接得住。",
            "若薄弱五行被冲克或不透，落地能力需要降低。",
        ],
    )


def _useful_candidate(
    *,
    strategy: str,
    label: str,
    elements: list[str],
    families: list[str],
    score: float,
    reasons: list[str],
    counter_evidence: list[str],
) -> dict[str, object]:
    clean_elements = _unique(elements)
    clean_families = _unique(families)
    return {
        "strategy": strategy,
        "label": label,
        "elements": clean_elements,
        "element_labels": [_element_label(element) for element in clean_elements],
        "families": clean_families,
        "family_labels": [TEN_GOD_FAMILY_LABELS.get(family, family) for family in clean_families],
        "score": round(max(0.0, min(1.0, score)), 3),
        "reasons": reasons[:3],
        "counter_evidence": counter_evidence[:3],
        "boundary": "useful_god_candidate_strategy_not_fixed_verdict",
    }


def _avoidance_model(
    primary: dict[str, object],
    candidates: list[dict[str, object]],
    *,
    strength_model: dict[str, object],
    structure_model: dict[str, object],
    path_model: dict[str, object],
) -> dict[str, object]:
    strategy = str(primary.get("strategy") or "candidate_review")
    strategy_risks = {
        "support": ["避免继续耗泄日主", "避免财官食伤过重而无印比承载"],
        "release": ["避免继续叠加印比", "避免输出与财星没有现实承接"],
        "regulate": ["避免官杀无印承接只变压力", "避免把规则压力直接断成职位或关系结果"],
        "climate": ["避免寒暖反向取用", "避免绕过强弱与路径只谈调候"],
        "mediation": ["避免跳过通关直接补单一五行", "避免制化路径未成就先下定论"],
        "balance": ["避免只因薄弱就补", "避免把补偏平衡说成唯一用神"],
    }
    risks = [str(row) for row in strategy_risks.get(strategy, ["避免固定唯一用神", "避免把候选策略说成定论"])]
    for row in _list(primary.get("counter_evidence")):
        if str(row).strip():
            risks.append(str(row).strip())
    if _float(structure_model.get("counter_evidence_count"), 0.0) > 0:
        risks.append("结构层存在反证，取用策略必须保留降权空间。")
    if _dict(path_model.get("graph_density")).get("dynamic_paths") in {None, 0}:
        risks.append("做功路径未充分展开，忌避风险不能升级为固定忌神。")
    alternatives = [
        str(row.get("label") or "")
        for row in candidates[1:4]
        if isinstance(row, dict) and row.get("label")
    ]
    keywords = _unique([
        *[str(row) for row in _list(primary.get("family_labels")) if row],
        *[str(row) for row in _list(primary.get("element_labels")) if row],
        "忌避风险",
        "反证边界",
    ])[:6]
    return {
        "version": "v30.useful_god_avoidance_model.v1",
        "status": "ready" if primary else "partial",
        "primary_strategy": strategy,
        "primary_label": str(primary.get("label") or "用神候选待复核"),
        "primary_risks": risks[:5],
        "risk_keywords": keywords,
        "alternative_labels": alternatives,
        "strength_context": str(strength_model.get("classification") or ""),
        "boundary": "avoidance_model_flags_contextual_risks_not_fixed_unfavorable_elements",
    }


def _candidate_with_ranked_signal(candidate: dict[str, object], ranked_useful: dict[str, Any]) -> dict[str, object]:
    primary = str(ranked_useful.get("primary_candidate") or "")
    if not primary:
        return candidate
    families = set(_list(candidate.get("families")))
    bonus = 0.0
    if "resource" in primary and "resource" in families:
        bonus = 0.035
    elif "self" in primary and "self" in families:
        bonus = 0.035
    elif "output" in primary and "output" in families:
        bonus = 0.035
    elif "wealth" in primary and "wealth" in families:
        bonus = 0.035
    elif "authority" in primary and "authority" in families:
        bonus = 0.035
    if not bonus:
        return candidate
    return {
        **candidate,
        "score": round(min(1.0, _float(candidate.get("score"), 0.0) + bonus), 3),
        "reasons": [*_list(candidate.get("reasons")), f"既有用神候选与该策略部分一致：{_candidate_label(primary)}。"][:3],
    }


def _mechanism_bonus(path_model: dict[str, object], mechanisms: set[str]) -> float:
    bonus = 0.0
    for row in _list(path_model.get("top_paths")):
        if not isinstance(row, dict):
            continue
        if str(row.get("mechanism") or "") in mechanisms:
            bonus += min(0.12, _float(row.get("score"), 0.0) * 0.12)
    return round(min(0.2, bonus), 3)


def _family_for_element(day_element: str, element: str) -> str:
    if not day_element or not element:
        return "balance_review"
    if element == day_element:
        return "self"
    if GENERATES.get(element) == day_element:
        return "resource"
    if GENERATES.get(day_element) == element:
        return "output"
    if CONTROLS.get(day_element) == element:
        return "wealth"
    if CONTROLS.get(element) == day_element:
        return "authority"
    return "balance_review"


def _seasonal_model(day_element: str, month_branch: str) -> dict[str, object]:
    season_element = SEASON_ELEMENT_BY_BRANCH.get(month_branch, "")
    seasonal_state = _seasonal_state(day_element, season_element)
    adjustment = SEASONAL_STATE_SCORE.get(seasonal_state, 0.0)
    return {
        "month_branch": month_branch,
        "season_element": season_element,
        "season_element_label": _element_label(season_element),
        "seasonal_state": seasonal_state,
        "seasonal_state_label": SEASONAL_STATE_LABELS.get(seasonal_state, seasonal_state),
        "score_adjustment": adjustment,
        "explanation": _seasonal_explanation(day_element, month_branch, season_element, seasonal_state),
        "boundary": "seasonal_model_scores_month_command_without_final_strength_verdict",
    }


def _root_model(root_summary: dict[str, Any]) -> dict[str, object]:
    exact_roots = _list(root_summary.get("day_master_roots"))
    same_element_roots = _list(root_summary.get("same_element_roots"))
    exact_score = sum(_root_weight(row, exact=True) for row in exact_roots if isinstance(row, dict))
    same_score = sum(_root_weight(row, exact=False) for row in same_element_roots if isinstance(row, dict))
    adjustment = round(min(0.28, exact_score + same_score), 3)
    root_count = int(root_summary.get("day_master_root_count", len(exact_roots)) or 0)
    same_count = int(root_summary.get("same_element_root_count", len(same_element_roots)) or 0)
    return {
        "day_master_root_count": root_count,
        "same_element_root_count": same_count,
        "score_adjustment": adjustment,
        "root_positions": _unique(
            str(row.get("pillar") or "")
            for row in [*exact_roots, *same_element_roots]
            if isinstance(row, dict)
        ),
        "explanation": f"通根复核：本气同干根{root_count}个，同五行根{same_count}个，作为日主承载力加分。",
        "boundary": str(root_summary.get("boundary") or "root_model_uses_root_fact_summary_without_useful_god_verdict"),
    }


def _stem_model(natal: dict[str, Any], day_element: str) -> dict[str, object]:
    visible = _list(natal.get("visible_ten_gods"))
    support_rows = []
    pressure_rows = []
    support_score = 0.0
    pressure_score = 0.0
    supporting = set(_supporting_elements(day_element))
    drains = set(_draining_elements(day_element))
    for row in visible:
        if not isinstance(row, dict):
            continue
        pillar = str(row.get("pillar") or "")
        if pillar == "day":
            continue
        element = str(row.get("element") or "")
        label = str(row.get("label") or "")
        weight = VISIBLE_STEM_WEIGHTS.get(pillar, 0.06)
        if element in supporting:
            support_score += weight
            support_rows.append(f"{pillar}:{label or _element_label(element)}")
        elif element in drains:
            pressure_score += weight
            pressure_rows.append(f"{pillar}:{label or _element_label(element)}")
    adjustment = round(max(-0.18, min(0.18, support_score - pressure_score)), 3)
    return {
        "supporting_visible_stems": support_rows[:5],
        "pressuring_visible_stems": pressure_rows[:5],
        "score_adjustment": adjustment,
        "explanation": f"透干复核：生扶透干{len(support_rows)}处，泄耗财官透干{len(pressure_rows)}处。",
        "boundary": "visible_stem_model_scores_expression_of_element_power_not_chart_fact_mutation",
    }


def _relation_model(natal: dict[str, Any], day_element: str) -> dict[str, object]:
    relations = [row for row in _list(natal.get("relation_hits")) if isinstance(row, dict)]
    conflict_count = sum(1 for row in relations if str(row.get("relation_type")) in CONFLICT_RELATIONS)
    alignment_rows = [
        row for row in relations
        if str(row.get("relation_type")) in ALIGNMENT_RELATIONS
    ]
    day_alignment_count = sum(1 for row in alignment_rows if str(row.get("element") or "") == day_element)
    other_alignment_count = len(alignment_rows) - day_alignment_count
    adjustment = round(max(-0.16, min(0.16, day_alignment_count * 0.06 - conflict_count * 0.035 - other_alignment_count * 0.025)), 3)
    return {
        "conflict_count": conflict_count,
        "alignment_count": len(alignment_rows),
        "day_element_alignment_count": day_alignment_count,
        "score_adjustment": adjustment,
        "explanation": f"地支关系复核：冲刑害破{conflict_count}处，合会{len(alignment_rows)}处，其中同日主五行合会{day_alignment_count}处。",
        "boundary": "relation_model_adjusts_stability_not_event_prediction",
    }


def _strength_classification(net_score: float, ratio: float, support_ratio: float, pressure_ratio: float) -> str:
    if net_score >= 0.72:
        return "偏旺"
    if net_score >= 0.6:
        return "有根有助"
    if net_score <= 0.28:
        return "明显偏弱或受压"
    if net_score <= 0.4:
        return "偏弱或受压"
    if support_ratio >= pressure_ratio + 0.18 and ratio >= 0.24:
        return "偏旺"
    if pressure_ratio >= support_ratio + 0.18 and ratio <= 0.2:
        return "偏弱或受压"
    return "中和待复核"


def _strength_explanation(classification: str, day_element: str, strongest: list[dict[str, object]], weakest: list[dict[str, object]]) -> str:
    strong_text = "、".join(str(row.get("label")) for row in strongest[:2]) or "五行资料不足"
    weak_text = "、".join(str(row.get("label")) for row in weakest[:2]) or "薄弱项待查"
    return f"日主五行为{_element_label(day_element)}，当前五行偏重在{strong_text}，薄弱项在{weak_text}，所以强弱先判为{classification}。"


def _seasonal_state(day_element: str, season_element: str) -> str:
    if not day_element or not season_element:
        return "unknown"
    if day_element == season_element:
        return "wang"
    if GENERATES.get(day_element) == season_element:
        return "xiu"
    if GENERATES.get(season_element) == day_element:
        return "xiang"
    if CONTROLS.get(day_element) == season_element:
        return "qiu"
    return "si"


def _seasonal_explanation(day_element: str, month_branch: str, season_element: str, seasonal_state: str) -> str:
    if not season_element:
        return "月令季气不足，强弱只能先看五行分布、通根和透干。"
    return (
        f"{month_branch}月属{_element_label(season_element)}气，"
        f"{_element_label(day_element)}日主在此为{SEASONAL_STATE_LABELS.get(seasonal_state, seasonal_state)}，"
        "月令只作为强弱权重，不单独定格局。"
    )


def _root_weight(row: dict[str, Any], *, exact: bool) -> float:
    pillar = str(row.get("pillar") or "")
    hidden_weight = _float(row.get("weight"), 0.0)
    position_weight = PILLAR_ROOT_WEIGHTS.get(pillar, 0.06)
    multiplier = 1.0 if exact else 0.55
    return position_weight * hidden_weight * multiplier


def _top_elements(distribution: dict[str, float], *, reverse: bool) -> list[dict[str, object]]:
    rows = [
        {"element": element, "label": _element_label(element), "score": round(score, 3)}
        for element, score in distribution.items()
    ]
    return sorted(rows, key=lambda row: (-float(row["score"]), str(row["element"])) if reverse else (float(row["score"]), str(row["element"])))[:3]


def _top_energy_row(row: dict[str, Any]) -> dict[str, object]:
    family = str(row.get("family") or "unknown")
    return {
        "label": str(row.get("label") or ""),
        "family": family,
        "family_label": TEN_GOD_FAMILY_LABELS.get(family, family),
        "energy": round(_float(row.get("energy"), 0.0), 3),
        "stability": round(_float(row.get("stability"), 0.0), 3),
        "volatility": round(_float(row.get("volatility"), 0.0), 3),
    }


def _role_balance(visible_labels: list[str], hidden_labels: list[str], dominant_roles: list[dict[str, object]]) -> str:
    if dominant_roles:
        labels = "、".join(str(row.get("label")) for row in dominant_roles[:2] if row.get("label"))
        return f"能量重点集中在{labels}，需结合显干与藏干确认能否落地。"
    if visible_labels:
        return "十神显干较清楚，但能量模型仍需时运和藏干补充。"
    if hidden_labels:
        return "十神多在藏干，需要通过路径和时运判断是否被引动。"
    return "十神资料不足，保守进入结构判断。"


def _mainline_risks(
    strength_model: dict[str, object],
    structure_model: dict[str, object],
    path_model: dict[str, object],
    timing_model: dict[str, object],
) -> list[str]:
    risks = [
        "不能把单条规则命中直接当成最终断语。",
        "LLM 只能表达中枢模型已有判断，不能新增四柱事实。",
    ]
    if structure_model.get("counter_evidence_count"):
        risks.append("结构层存在反证，需要降低过度确定的结论。")
    if path_model.get("status") != "ready":
        risks.append("做功路径不足时，领域结论只能先给方向。")
    if str(timing_model.get("status")) not in {"ready", "completed"}:
        risks.append("时运资料不足时，不做阶段性事件判断。")
    if strength_model.get("classification") == "中和待复核":
        risks.append("日主强弱仍需后续规则与路径复核。")
    return risks[:5]


def _next_questions(path_model: dict[str, object], timing_model: dict[str, object]) -> list[str]:
    domains = _list(path_model.get("top_domains"))
    domain_text = "、".join(str(row.get("domain")) for row in domains[:3] if isinstance(row, dict) and row.get("domain"))
    rows = []
    if domain_text:
        rows.append(f"优先追问{domain_text}中哪一个是用户当前最关心的现实问题。")
    if not timing_model.get("current_luck_pillar"):
        rows.append("补充出生时间或排运资料，以确认当前大运。")
    rows.append("追问近期三年实际事件，用于校准路径是否被时运激活。")
    return rows[:3]


def _pillar_display(payload: dict[str, Any]) -> str:
    return str(payload.get("display") or f"{payload.get('stem') or ''}{payload.get('branch') or ''}").strip()


def _ten_god_label(row: Any) -> str:
    if isinstance(row, dict):
        return str(row.get("label") or row.get("ten_god") or "")
    return str(getattr(row, "label", "") or getattr(row, "ten_god", "") or "")


def _candidate_label(value: str) -> str:
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
    if value in exact:
        return exact[value]
    replacements = {
        "useful_god": "用神候选",
        "structure": "结构候选",
        "strength": "旺衰候选",
        "wealth": "财运候选",
        "career": "事业候选",
        "relationship": "关系候选",
        "health": "健康候选",
    }
    label = value
    for key, text in replacements.items():
        label = label.replace(key, text)
    return label


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
    return raw[:80] or "结构待复核"


def _chain_label(value: str) -> str:
    return CHAIN_LABELS.get(value, value)


def _domain_label(value: str) -> str:
    return DOMAIN_LABELS.get(value, value)


def _element_label(value: str) -> str:
    return ELEMENT_LABELS.get(value, value or "未知")


def _confidence_from_status(value: object) -> float:
    status = str(value or "")
    if status in {"ready", "completed"}:
        return 0.84
    if status in {"partial", "pending"}:
        return 0.56
    return 0.68 if status else 0.48


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _unique(rows: Any) -> list[str]:
    seen: set[str] = set()
    values: list[str] = []
    for row in rows:
        value = str(row or "")
        if not value or value in seen:
            continue
        seen.add(value)
        values.append(value)
    return values
