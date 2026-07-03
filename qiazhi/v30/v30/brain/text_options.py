from __future__ import annotations

import re
from typing import Any


TEXT_SEMANTIC_UNIT_VERSION = "v30.text_semantic_unit.v1"
OPTION_SET_VERSION = "v30.option_set.v1"
TEXT_OPTION_PROJECTION_VERSION = "v30.text_option_projection.v1"
PRACTITIONER_SELECTION_VERSION = "v30.practitioner_selection.v1"

_USER_VISIBLE_ROLES = {"guest", "user"}
_DIAGNOSTIC_ROLES = {"practitioner", "admin", "analyst", "lab"}

_INTERNAL_TOKENS = (
    "context_id",
    "evidence_id",
    "source_id",
    "trace_id",
    "metadata",
    "fallback",
    "json",
    "v30.",
    "krp.",
    "quality gate",
)

_ELEMENTS = {
    "木": "生发、规划、关系生机",
    "火": "温煦、表达、激活",
    "土": "承接、稳定、落地",
    "金": "规则、边界、执行",
    "水": "流动、压力、信息",
}

_TEN_GODS = {
    "比劫": "自我、同类、竞争和承担",
    "食伤": "输出、表达、技能和方案",
    "财星": "资源、收入、分配和现实结果",
    "官杀": "压力、规则、职责和约束",
    "印星": "资质、学习、承接和保护",
}

_DOMAINS = {
    "事业": "career",
    "工作": "career",
    "职位": "career",
    "职责": "career",
    "财运": "wealth",
    "财务": "wealth",
    "收入": "wealth",
    "关系": "relationship",
    "感情": "relationship",
    "合作": "relationship",
    "健康": "health",
    "身体": "health",
    "压力": "health",
    "亲情": "family",
    "家庭": "family",
    "大运": "timing",
    "流年": "timing",
    "年份": "timing",
    "时运": "timing",
}

_DOMAIN_LABELS = {
    "career": "事业",
    "wealth": "财运",
    "relationship": "关系",
    "health": "健康",
    "family": "家庭",
    "timing": "时运",
}

_ACTION_TOKENS = ("优先", "避免", "不要", "建议", "先看", "重点", "需要", "落到", "执行")
_RISK_TOKENS = ("风险", "忌避", "过旺", "过弱", "反证", "边界", "不能", "不宜", "避免")
_QUESTION_TOKENS = ("需要确认", "需要补充", "确认", "补充", "明显年份", "待问", "追问")
_ALTERNATIVE_CONNECTORS = ("或", "或者", "与", "和", "、", "/", "以及", "二者")


def enrich_stage_point_set_with_text_options(point_set: dict[str, object] | None) -> dict[str, object]:
    if not isinstance(point_set, dict):
        return {}
    stage_id = str(point_set.get("stage_id") or "")
    source = str(point_set.get("source") or "stage_point_set")
    points = _dict_rows(point_set.get("points"))
    selected = _dict_rows(point_set.get("selected_points"))
    projection = build_text_option_projection_from_stage_points(
        selected or points,
        stage_id=stage_id,
        source=source,
    )
    all_points = _attach_option_refs(points, projection)
    selected_points = _attach_option_refs(selected, projection)
    return {
        **point_set,
        "points": all_points,
        "selected_points": selected_points,
        "text_option_projection": projection,
        "option_sets": projection["option_sets"],
        "semantic_units": projection["semantic_units"],
    }


def build_text_option_projection_from_stage_points(
    points: list[dict[str, object]],
    *,
    stage_id: str = "",
    source: str = "stage_point",
) -> dict[str, object]:
    units: list[dict[str, object]] = []
    discarded: list[dict[str, object]] = []
    option_sets: list[dict[str, object]] = []
    for point in points:
        point_units = extract_text_semantic_units(
            str(point.get("text") or ""),
            source_type="stage_point",
            source_id=str(point.get("point_id") or ""),
            stage_id=str(point.get("stage_id") or stage_id),
            bazi_terms=[str(row) for row in _list(point.get("bazi_terms")) if row],
            macro_domains=[str(row) for row in _list(point.get("macro_domains")) if row],
            evidence_refs=[str(row) for row in _list(point.get("evidence_refs")) if row],
        )
        units.extend(point_units["semantic_units"])
        discarded.extend(point_units["discarded_units"])
    for index, point in enumerate(points, start=1):
        hinted_option_set = _option_set_from_point_hints(
            point,
            index=index,
            default_stage_id=stage_id,
        )
        if not hinted_option_set:
            continue
        gated = _gate_option_set(hinted_option_set)
        if gated["accepted"]:
            option_sets.append(gated["option_set"])
        else:
            discarded.append({
                "source_id": str(point.get("point_id") or ""),
                "unit_type": "explicit_branch_options",
                "reason": str(gated["reason"]),
                "text_preview": str(point.get("text") or "")[:80],
            })
    for index, unit in enumerate(units, start=len(option_sets) + 1):
        option_set = _option_set_from_unit(unit, index=index)
        if not option_set:
            continue
        gated = _gate_option_set(option_set)
        if gated["accepted"]:
            option_sets.append(gated["option_set"])
        else:
            discarded.append(_discarded_unit(unit, str(gated["reason"])))
    return {
        "version": TEXT_OPTION_PROJECTION_VERSION,
        "stage_id": stage_id,
        "source": source,
        "semantic_unit_count": len(units),
        "option_set_count": len(option_sets),
        "semantic_units": units[:12],
        "option_sets": option_sets[:8],
        "discarded_units": discarded[:10],
        "training_signal": _training_signal(),
        "boundary": "text_option_projection_extracts_interaction_candidates_without_mutating_chart_facts",
    }


def extract_text_semantic_units(
    text: str,
    *,
    source_type: str,
    source_id: str,
    stage_id: str = "",
    bazi_terms: list[str] | None = None,
    macro_domains: list[str] | None = None,
    evidence_refs: list[str] | None = None,
) -> dict[str, object]:
    clean = _clean_text(text)
    if not clean:
        return {
            "version": "v30.text_semantic_unit_extraction.v1",
            "semantic_units": [],
            "discarded_units": [],
        }
    if _contains_internal_token(clean):
        return {
            "version": "v30.text_semantic_unit_extraction.v1",
            "semantic_units": [],
            "discarded_units": [_discarded_text(source_id, "internal_or_engineering_language", clean)],
        }

    common = {
        "source_type": source_type,
        "source_id": source_id,
        "stage_id": stage_id,
        "bazi_terms": _unique([*(bazi_terms or []), *_detect_bazi_terms(clean)])[:8],
        "macro_domains": _unique([*(macro_domains or []), *_detect_macro_domains(clean)])[:6],
        "evidence_refs": _unique(evidence_refs or [])[:6],
    }
    units: list[dict[str, object]] = []

    units.extend(_extract_alternative_units(clean, common))
    units.extend(_extract_ranked_units(clean, common))
    units.extend(_extract_numeric_units(clean, common))
    units.extend(_extract_action_or_risk_units(clean, common))
    units.extend(_extract_question_need_units(clean, common))

    deduped: list[dict[str, object]] = []
    seen: set[str] = set()
    for index, unit in enumerate(units, start=1):
        key = f"{unit.get('unit_type')}:{','.join(_list(unit.get('normalized_terms')))}:{unit.get('text_span')}"
        if key in seen:
            continue
        seen.add(key)
        deduped.append({
            **unit,
            "unit_id": str(unit.get("unit_id") or f"tsu.{stage_id or 'text'}.{index:03d}"),
        })
    return {
        "version": "v30.text_semantic_unit_extraction.v1",
        "semantic_units": deduped[:8],
        "discarded_units": [],
    }


def build_response_option_set_for_question(
    question: dict[str, object],
    *,
    stage_id: str = "",
    role_key: str = "user",
) -> dict[str, object]:
    if not isinstance(question, dict) or not question.get("question_id"):
        return {}
    options = _question_options(question)
    if not options:
        return {}
    topic = str(question.get("topic") or question.get("domain") or "dialogue")
    option_set = {
        "version": OPTION_SET_VERSION,
        "option_set_id": f"opt.dialogue.{_slug(str(question.get('question_id') or 'question'))}",
        "source_unit_ids": [],
        "source_type": "current_dialogue_turn",
        "source_id": str(question.get("question_id") or ""),
        "stage_id": stage_id,
        "topic": topic,
        "title": _topic_title(topic),
        "question": str(question.get("label") or question.get("question") or question.get("question_id") or ""),
        "selection_mode": _question_selection_mode(question),
        "visibility": _visibility(user_interactive=True),
        "options": options[:6],
        "option_value_score": 0.82,
        "score_breakdown": {
            "evidence_binding": 0.45,
            "ambiguity_reduction": 0.82,
            "practitioner_actionability": 0.62,
            "downstream_impact": 0.74,
            "bazi_specificity": 0.42,
            "user_cost_saving": 0.88,
            "fact_mutation_risk": 0.0,
            "ui_noise_risk": 0.08 if len(options) <= 4 else 0.22,
        },
        "display": {
            "max_visible_options": 4 if role_key in _USER_VISIBLE_ROLES else 6,
            "compact": role_key in _USER_VISIBLE_ROLES,
        },
        "training_tags": [
            "dialogue_option_information_gain",
            "text_option_extraction",
        ],
        "boundary": "dialogue_response_option_set_records_user_background_without_mutating_chart_facts",
    }
    return option_set


def build_practitioner_selection(
    option_set: dict[str, object],
    *,
    selected_option_ids: list[str],
    action: str = "select",
    ranked_option_ids: list[str] | None = None,
    rejected_option_ids: list[str] | None = None,
    note: str = "",
    confidence: float = 0.0,
) -> dict[str, object]:
    option_set_id = str(option_set.get("option_set_id") or "")
    selected = _unique([str(row) for row in selected_option_ids if row])
    ranked = _unique([str(row) for row in (ranked_option_ids or selected) if row])
    rejected = _unique([str(row) for row in (rejected_option_ids or []) if row])
    return {
        "version": PRACTITIONER_SELECTION_VERSION,
        "selection_id": f"sel.{option_set_id or 'option'}.{_slug(action)}",
        "option_set_id": option_set_id,
        "actor_role": "practitioner",
        "action": action if action in {"select", "rank", "reject", "downrank", "needs_question", "note"} else "select",
        "selected_option_ids": selected,
        "ranked_option_ids": ranked,
        "rejected_option_ids": rejected,
        "note": _clean_text(note)[:240],
        "confidence": _bounded_float(confidence),
        "effect_targets": [
            "belief_state.option_candidate_weight",
            "stage_point.display_priority",
            "final_synthesis.evidence_order",
            "training_signal.practitioner_selection_alignment",
        ],
        "forbidden_effect_targets": [
            "four_pillars",
            "calendar_conversion",
            "birth_time",
            "raw_rule_truth",
            "luck_cycle_calculation",
        ],
        "boundary": "practitioner_selection_updates_belief_and_weight_not_chart_facts",
    }


def role_visible_option_sets(option_sets: list[dict[str, object]], *, role_key: str) -> list[dict[str, object]]:
    rows = []
    for option_set in option_sets:
        visibility = _dict(option_set.get("visibility"))
        state = str(visibility.get(role_key) or ("diagnostic" if role_key in _DIAGNOSTIC_ROLES else "hidden"))
        if state == "hidden":
            continue
        rows.append({**option_set, "role_visibility": state})
    return rows


def _option_set_from_point_hints(
    point: dict[str, object],
    *,
    index: int,
    default_stage_id: str,
) -> dict[str, object] | None:
    hints = _dict_rows(point.get("option_hints"))
    if len(hints) < 2:
        return None
    stage_id = str(point.get("stage_id") or default_stage_id)
    point_id = str(point.get("point_id") or f"stage_point_{index}")
    topic = _branch_topic(point)
    options = _options_from_point_hints(point, hints)
    if len(options) < 2:
        return None
    return {
        "version": OPTION_SET_VERSION,
        "option_set_id": f"opt.{_slug(stage_id or 'stage')}.{_slug(topic)}.{_slug(point_id) or f'{index:03d}'}",
        "source_unit_ids": [],
        "source_type": "stage_point_branch",
        "source_id": point_id,
        "stage_id": stage_id,
        "topic": topic,
        "title": _topic_title(topic),
        "question": _branch_option_question(point, topic),
        "selection_mode": "rank_one_or_more",
        "visibility": _visibility(user_interactive=False),
        "options": options[:6],
        "option_value_score": 0.0,
        "score_breakdown": {},
        "display": {
            "max_visible_options": 6,
            "compact": False,
            "role_projection": {
                "user": "read_only_primary_branch",
                "practitioner": "selectable_branch_calibration",
            },
        },
        "training_tags": [
            "text_option_extraction",
            "branch_probability_calibration",
            "practitioner_selection_feedback",
            f"{topic}_option",
        ],
        "boundary": "branch_option_set_is_practitioner_calibration_not_customer_choice",
    }


def _options_from_point_hints(point: dict[str, object], hints: list[dict[str, object]]) -> list[dict[str, object]]:
    point_text = str(point.get("text") or "")
    point_probability = _bounded_float(
        point.get("branch_probability") or point.get("probability") or point.get("confidence"),
        default=0.0,
    )
    point_evidence = [str(row) for row in _list(point.get("evidence_refs")) if row][:4]
    point_bazi_terms = _unique([
        *[str(row) for row in _list(point.get("bazi_terms")) if row],
        *_detect_bazi_terms(point_text),
    ])[:6]
    point_domains = _unique([
        *[str(row) for row in _list(point.get("macro_domains")) if row],
        *_detect_macro_domains(point_text),
    ])[:4]
    rows: list[dict[str, object]] = []
    for hint_index, hint in enumerate(hints, start=1):
        raw_label = str(
            hint.get("label")
            or hint.get("title")
            or hint.get("value")
            or hint.get("option_id")
            or ""
        ).strip()
        raw_value = str(hint.get("value") or hint.get("option_id") or raw_label).strip()
        if not raw_label and not raw_value:
            continue
        label = _clean_text(raw_label or raw_value)[:32]
        value = _clean_text(raw_value or raw_label)[:80]
        option_id = _slug(str(hint.get("option_id") or raw_value or raw_label)) or f"branch_{hint_index}"
        hint_evidence = _unique([
            *point_evidence,
            *[str(row) for row in _list(hint.get("evidence_refs")) if row],
        ])[:5]
        hint_terms = _unique([
            *point_bazi_terms,
            *[str(row) for row in _list(hint.get("bazi_terms")) if row],
            *_detect_bazi_terms(f"{label}{value}"),
        ])[:6]
        hint_domains = _unique([
            *point_domains,
            *[str(row) for row in _list(hint.get("macro_domains")) if row],
            *_detect_macro_domains(f"{label}{value}"),
        ])[:4]
        default_weight = _bounded_float(
            hint.get("probability") or hint.get("score") or hint.get("weight"),
            default=max(0.38, (point_probability or 0.70) - (hint_index - 1) * 0.08),
        )
        rows.append({
            "option_id": option_id,
            "label": label or value,
            "value": value or label,
            "meaning": _clean_text(str(hint.get("meaning") or hint.get("description") or _branch_hint_meaning(label or value)))[:120],
            "bazi_terms": hint_terms,
            "macro_domains": hint_domains,
            "evidence_refs": hint_evidence,
            "risk_refs": [str(row) for row in _list(hint.get("risk_refs")) if row][:4],
            "resolution_conditions": [
                str(row).strip()
                for row in [*_list(point.get("resolution_conditions")), *_list(hint.get("resolution_conditions"))]
                if str(row).strip()
            ][:4],
            "default_weight": default_weight,
            "branch_probability": default_weight,
        })
    return rows


def _branch_topic(point: dict[str, object]) -> str:
    text = str(point.get("text") or "")
    terms = _unique([*[str(row) for row in _list(point.get("bazi_terms")) if row], *_detect_bazi_terms(text)])
    domains = _unique([*[str(row) for row in _list(point.get("macro_domains")) if row], *_detect_macro_domains(text)])
    if any(term in {"用神", "忌神", "取用"} for term in terms):
        return "useful_god"
    if any(term in _TEN_GODS for term in terms):
        return "ten_god_path"
    if len(domains) == 1:
        return domains[0]
    if len(domains) > 1:
        return "domain_focus"
    return "branch_candidate"


def _branch_option_question(point: dict[str, object], topic: str) -> str:
    label = _clean_text(str(point.get("short_label") or ""))
    if label:
        normalized = label[:-2] if label.endswith("分支") else label
        return f"这组{normalized}分支如何取舍？"
    return _option_question(topic, "branch_candidate")


def _branch_hint_meaning(label: str) -> str:
    text = str(label or "")
    terms = _detect_bazi_terms(text)
    if terms:
        return f"作为{terms[0]}相关的候选分支，只调整判断权重"
    return "作为当前页的候选分支，只调整判断权重"


def _extract_alternative_units(text: str, common: dict[str, object]) -> list[dict[str, object]]:
    units: list[dict[str, object]] = []
    elements = [term for term in _ELEMENTS if term in text]
    ten_gods = [term for term in _TEN_GODS if term in text]
    domain_terms = _detect_macro_domains(text)
    has_connector = any(token in text for token in _ALTERNATIVE_CONNECTORS)
    has_useful_god = any(token in text for token in ("用神", "忌神", "取用", "候选"))
    if len(elements) >= 2 and (has_connector or has_useful_god):
        units.append(_unit(
            common,
            unit_type="alternative",
            text_span="、".join(elements[:5]),
            normalized_terms=elements[:5],
            topic="useful_god" if has_useful_god else "five_elements",
            confidence=0.78,
        ))
    if len(ten_gods) >= 2 and has_connector:
        units.append(_unit(
            common,
            unit_type="alternative",
            text_span="、".join(ten_gods[:5]),
            normalized_terms=ten_gods[:5],
            topic="ten_god_path",
            confidence=0.74,
        ))
    if len(domain_terms) >= 2 and (has_connector or any(token in text for token in ("领域", "重点", "先看"))):
        labels = [_DOMAIN_LABELS.get(domain, domain) for domain in domain_terms[:5]]
        units.append(_unit(
            common,
            unit_type="domain_focus",
            text_span="、".join(labels),
            normalized_terms=domain_terms[:5],
            topic="domain_focus",
            confidence=0.72,
        ))
    return units


def _extract_ranked_units(text: str, common: dict[str, object]) -> list[dict[str, object]]:
    if not any(token in text for token in ("先", "再", "其次", "最后")):
        return []
    terms = _unique([
        *_detect_bazi_terms(text),
        *_detect_macro_domains(text),
    ])
    if len(terms) < 2:
        return []
    return [_unit(
        common,
        unit_type="ranked_list",
        text_span=" -> ".join(terms[:5]),
        normalized_terms=terms[:5],
        topic="priority_order",
        confidence=0.70,
    )]


def _extract_numeric_units(text: str, common: dict[str, object]) -> list[dict[str, object]]:
    units: list[dict[str, object]] = []
    for match in re.finditer(r"(置信度|证据链|证据|规则|路径|画像|特征|第)\s*([0-9]+(?:\.[0-9]+)?|[一二三四五六七八九十]+)", text):
        label = match.group(1)
        value = match.group(2)
        units.append(_unit(
            common,
            unit_type="numeric_marker",
            text_span=f"{label}{value}",
            normalized_terms=[label, value],
            topic="numeric_marker",
            confidence=0.64,
        ))
    return units[:3]


def _extract_action_or_risk_units(text: str, common: dict[str, object]) -> list[dict[str, object]]:
    units: list[dict[str, object]] = []
    if any(token in text for token in _ACTION_TOKENS):
        phrase = _first_clause(text, _ACTION_TOKENS)
        units.append(_unit(
            common,
            unit_type="action_item",
            text_span=phrase,
            normalized_terms=_unique([*_detect_bazi_terms(phrase), *_detect_macro_domains(phrase)])[:5],
            topic="action_item",
            confidence=0.68,
        ))
    if any(token in text for token in _RISK_TOKENS):
        phrase = _first_clause(text, _RISK_TOKENS)
        units.append(_unit(
            common,
            unit_type="risk_boundary",
            text_span=phrase,
            normalized_terms=_unique([*_detect_bazi_terms(phrase), *_detect_macro_domains(phrase)])[:5],
            topic="risk_boundary",
            confidence=0.66,
        ))
    return units


def _extract_question_need_units(text: str, common: dict[str, object]) -> list[dict[str, object]]:
    if not any(token in text for token in _QUESTION_TOKENS):
        return []
    return [_unit(
        common,
        unit_type="question_need",
        text_span=_first_clause(text, _QUESTION_TOKENS),
        normalized_terms=_unique([*_detect_bazi_terms(text), *_detect_macro_domains(text)])[:5],
        topic="question_need",
        confidence=0.64,
    )]


def _option_set_from_unit(unit: dict[str, object], *, index: int) -> dict[str, object] | None:
    unit_type = str(unit.get("unit_type") or "")
    terms = [str(row) for row in _list(unit.get("normalized_terms")) if str(row).strip()]
    if unit_type in {"alternative", "ranked_list", "domain_focus"} and len(terms) < 2:
        return None
    if unit_type not in {"alternative", "ranked_list", "domain_focus", "numeric_marker", "action_item", "risk_boundary", "question_need"}:
        return None
    topic = str(unit.get("topic") or unit_type)
    stage_id = str(unit.get("stage_id") or "")
    options = _options_from_terms(unit, terms)
    if not options:
        return None
    selection_mode = {
        "alternative": "rank_one_or_more",
        "ranked_list": "ranked_choice",
        "domain_focus": "multi_select",
        "numeric_marker": "numeric_marker",
        "action_item": "action_risk_pair",
        "risk_boundary": "mark_risk",
        "question_need": "needs_question",
    }.get(unit_type, "single_choice")
    return {
        "version": OPTION_SET_VERSION,
        "option_set_id": f"opt.{_slug(stage_id or 'stage')}.{_slug(topic)}.{index:03d}",
        "source_unit_ids": [str(unit.get("unit_id") or "")],
        "source_type": str(unit.get("source_type") or ""),
        "source_id": str(unit.get("source_id") or ""),
        "stage_id": stage_id,
        "topic": topic,
        "title": _topic_title(topic),
        "question": _option_question(topic, unit_type),
        "selection_mode": selection_mode,
        "visibility": _visibility(user_interactive=False),
        "options": options[:6],
        "option_value_score": 0.0,
        "score_breakdown": {},
        "display": {"max_visible_options": 4, "compact": True},
        "training_tags": [
            "text_option_extraction",
            "practitioner_selection",
            f"{topic}_option",
        ],
        "boundary": "option_set_changes_interpretation_weight_not_chart_fact",
    }


def _gate_option_set(option_set: dict[str, object]) -> dict[str, object]:
    text = " ".join([
        str(option_set.get("title") or ""),
        str(option_set.get("question") or ""),
        " ".join(str(row.get("label") or "") for row in _dict_rows(option_set.get("options"))),
    ])
    if _contains_internal_token(text):
        return {"accepted": False, "reason": "internal_or_engineering_language", "option_set": option_set}
    option_count = len(_dict_rows(option_set.get("options")))
    evidence_binding = 0.70 if any(_list(row.get("evidence_refs")) for row in _dict_rows(option_set.get("options"))) else 0.38
    ambiguity_reduction = 0.82 if option_count >= 2 else 0.42
    practitioner_actionability = 0.78 if str(option_set.get("selection_mode")) in {"rank_one_or_more", "ranked_choice", "multi_select"} else 0.58
    downstream_impact = 0.74 if str(option_set.get("topic")) in {
        "useful_god",
        "ten_god_path",
        "domain_focus",
        "question_need",
        "branch_candidate",
        *_DOMAIN_LABELS,
    } else 0.56
    bazi_specificity = 0.76 if any(_list(row.get("bazi_terms")) for row in _dict_rows(option_set.get("options"))) else 0.44
    user_cost_saving = 0.62 if option_count <= 4 else 0.42
    fact_mutation_risk = 0.0
    ui_noise_risk = 0.08 if 2 <= option_count <= 4 else 0.24 if option_count <= 6 else 0.48
    score = max(0.0, min(
        1.0,
        evidence_binding * 0.24
        + ambiguity_reduction * 0.20
        + practitioner_actionability * 0.18
        + downstream_impact * 0.16
        + bazi_specificity * 0.12
        + user_cost_saving * 0.10
        - fact_mutation_risk * 0.30
        - ui_noise_risk * 0.18,
    ))
    updated = {
        **option_set,
        "option_value_score": round(score, 3),
        "score_breakdown": {
            "evidence_binding": round(evidence_binding, 3),
            "ambiguity_reduction": round(ambiguity_reduction, 3),
            "practitioner_actionability": round(practitioner_actionability, 3),
            "downstream_impact": round(downstream_impact, 3),
            "bazi_specificity": round(bazi_specificity, 3),
            "user_cost_saving": round(user_cost_saving, 3),
            "fact_mutation_risk": round(fact_mutation_risk, 3),
            "ui_noise_risk": round(ui_noise_risk, 3),
        },
    }
    return {
        "accepted": score >= 0.42,
        "reason": "option_value_score_passed" if score >= 0.42 else "low_option_value_score",
        "option_set": updated,
    }


def _options_from_terms(unit: dict[str, object], terms: list[str]) -> list[dict[str, object]]:
    unit_type = str(unit.get("unit_type") or "")
    evidence_refs = [str(row) for row in _list(unit.get("evidence_refs")) if row][:4]
    bazi_terms = [str(row) for row in _list(unit.get("bazi_terms")) if row][:6]
    if unit_type in {"action_item", "risk_boundary", "question_need", "numeric_marker"}:
        label = str(unit.get("text_span") or _topic_title(str(unit.get("topic") or unit_type)))
        return [{
            "option_id": _slug(label) or unit_type,
            "label": label[:36],
            "value": label[:80],
            "meaning": _unit_meaning(unit_type),
            "bazi_terms": bazi_terms,
            "macro_domains": [str(row) for row in _list(unit.get("macro_domains")) if row][:4],
            "evidence_refs": evidence_refs,
            "risk_refs": evidence_refs if unit_type == "risk_boundary" else [],
            "default_weight": 0.58,
        }]
    rows = []
    for term in terms[:6]:
        label = _term_label(term)
        rows.append({
            "option_id": _slug(term),
            "label": label,
            "value": term,
            "meaning": _term_meaning(term),
            "bazi_terms": _unique([term, *bazi_terms])[:6],
            "macro_domains": [term] if term in _DOMAIN_LABELS else [str(row) for row in _list(unit.get("macro_domains")) if row][:4],
            "evidence_refs": evidence_refs,
            "risk_refs": [],
            "default_weight": 0.62 if len(rows) == 0 else max(0.42, 0.62 - len(rows) * 0.06),
        })
    return rows


def _question_options(question: dict[str, object]) -> list[dict[str, object]]:
    raw_options = _list(question.get("options"))
    constraints = _dict(question.get("answer_constraints"))
    if not raw_options and constraints.get("constraint_type") == "structured_hidden_factor":
        raw_options = _list(constraints.get("allowed_state_tags"))
    rows: list[dict[str, object]] = []
    for index, option in enumerate(raw_options, start=1):
        if isinstance(option, dict):
            label = str(option.get("label") or option.get("value") or option.get("option_id") or "").strip()
            value = str(option.get("value") or option.get("option_id") or label).strip()
            option_id = str(option.get("option_id") or value or f"option_{index}").strip()
        else:
            label = str(option).strip()
            value = label
            option_id = label or f"option_{index}"
        if not label and not value:
            continue
        rows.append({
            "option_id": _slug(option_id) or f"option_{index}",
            "label": label[:32],
            "value": value[:80],
            "meaning": _question_option_meaning(str(question.get("topic") or ""), label),
            "bazi_terms": _detect_bazi_terms(label),
            "macro_domains": _detect_macro_domains(label),
            "evidence_refs": [],
            "risk_refs": [],
            "default_weight": round(max(0.42, 0.72 - index * 0.05), 3),
        })
    return rows


def _attach_option_refs(points: list[dict[str, object]], projection: dict[str, object]) -> list[dict[str, object]]:
    units = _dict_rows(projection.get("semantic_units"))
    option_sets = _dict_rows(projection.get("option_sets"))
    units_by_source: dict[str, list[str]] = {}
    options_by_source: dict[str, list[str]] = {}
    for unit in units:
        source_id = str(unit.get("source_id") or "")
        if source_id:
            units_by_source.setdefault(source_id, []).append(str(unit.get("unit_id") or ""))
    for option_set in option_sets:
        source_id = str(option_set.get("source_id") or "")
        if source_id:
            options_by_source.setdefault(source_id, []).append(str(option_set.get("option_set_id") or ""))
    enriched: list[dict[str, object]] = []
    for point in points:
        point_id = str(point.get("point_id") or "")
        enriched.append({
            **point,
            "semantic_unit_ids": units_by_source.get(point_id, []),
            "option_set_ids": options_by_source.get(point_id, []),
            "practitioner_selectable": bool(options_by_source.get(point_id)) or bool(point.get("selectable")),
        })
    return enriched


def _unit(common: dict[str, object], *, unit_type: str, text_span: str, normalized_terms: list[str], topic: str, confidence: float) -> dict[str, object]:
    return {
        "version": TEXT_SEMANTIC_UNIT_VERSION,
        "unit_id": "",
        "source_type": str(common.get("source_type") or ""),
        "source_id": str(common.get("source_id") or ""),
        "stage_id": str(common.get("stage_id") or ""),
        "unit_type": unit_type,
        "topic": topic,
        "text_span": _clean_text(text_span)[:120],
        "normalized_terms": _unique([str(row) for row in normalized_terms if row])[:8],
        "bazi_terms": [str(row) for row in _list(common.get("bazi_terms")) if row][:8],
        "macro_domains": [str(row) for row in _list(common.get("macro_domains")) if row][:6],
        "evidence_refs": [str(row) for row in _list(common.get("evidence_refs")) if row][:6],
        "confidence": _bounded_float(confidence),
        "boundary": "text_semantic_unit_is_extracted_from_text_not_new_chart_fact",
    }


def _training_signal() -> dict[str, object]:
    return {
        "signal_id": "v30.training_signal.text_option_extraction_quality",
        "trainable": True,
        "targets": [
            "text_option_extraction_quality",
            "practitioner_selection_alignment",
            "dialogue_option_information_gain",
            "option_ui_noise_penalty",
        ],
        "blocked_targets": [
            "chart_facts",
            "calendar_conversion",
            "four_pillars",
            "luck_cycle_calculation",
            "raw_rule_truth",
        ],
    }


def _visibility(*, user_interactive: bool) -> dict[str, str]:
    return {
        "guest": "interactive" if user_interactive else "hidden",
        "user": "interactive" if user_interactive else "hidden",
        "practitioner": "interactive",
        "admin": "interactive",
        "analyst": "diagnostic",
        "lab": "diagnostic",
    }


def _detect_bazi_terms(text: str) -> list[str]:
    terms = []
    for term in [*_ELEMENTS, *_TEN_GODS, "用神", "忌神", "取用", "格局", "旺衰", "做功", "路径", "大运", "流年", "合冲", "刑害"]:
        if term and term in text:
            terms.append(term)
    return _unique(terms)


def _detect_macro_domains(text: str) -> list[str]:
    rows: list[str] = []
    for label, domain in _DOMAINS.items():
        if label in text:
            rows.append(domain)
    return _unique(rows)


def _first_clause(text: str, tokens: tuple[str, ...]) -> str:
    parts = re.split(r"[。；;]", text)
    for part in parts:
        if any(token in part for token in tokens):
            return _clean_text(part)[:100]
    return _clean_text(text)[:100]


def _question_selection_mode(question: dict[str, object]) -> str:
    constraint_type = str(_dict(question.get("answer_constraints")).get("constraint_type") or "")
    if constraint_type == "structured_hidden_factor":
        return "structured_hidden_factor"
    if constraint_type in {"timing_context_check", "year_input"}:
        return "single_choice_with_optional_year"
    return "single_choice"


def _topic_title(topic: str) -> str:
    labels = {
        "useful_god": "用神候选取舍",
        "five_elements": "五行候选",
        "ten_god_path": "十神路径取舍",
        "domain_focus": "领域焦点选择",
        "priority_order": "判断顺序",
        "numeric_marker": "数字化标记",
        "action_item": "行动建议",
        "risk_boundary": "风险边界",
        "question_need": "待补背景",
        "career": "事业选项",
        "wealth": "财运选项",
        "relationship": "关系选项",
        "health": "健康选项",
        "timing": "时运选项",
        "hidden_factor": "隐藏线索校准",
        "decision": "决策选项",
        "branch_candidate": "分支候选取舍",
    }
    return labels.get(str(topic or ""), "测算选项")


def _option_question(topic: str, unit_type: str) -> str:
    if topic == "useful_god":
        return "这一步更应采纳哪条取用方向？"
    if topic == "ten_god_path":
        return "这条判断里哪组十神路径更应优先？"
    if topic == "domain_focus":
        return "这一步更应优先落到哪个现实领域？"
    if topic == "branch_candidate":
        return "这组分支更应采纳、降权还是转追问？"
    if unit_type == "ranked_list":
        return "这组判断的先后顺序是否需要调整？"
    if unit_type == "risk_boundary":
        return "这条风险边界是否需要保留或加重？"
    if unit_type == "question_need":
        return "这里是否应转成下一轮追问？"
    return "这条文本里哪些候选需要采纳或降权？"


def _term_label(term: str) -> str:
    if term in _DOMAIN_LABELS:
        return _DOMAIN_LABELS[term]
    return term


def _term_meaning(term: str) -> str:
    if term in _ELEMENTS:
        return _ELEMENTS[term]
    if term in _TEN_GODS:
        return _TEN_GODS[term]
    if term in _DOMAIN_LABELS:
        return f"把判断落到{_DOMAIN_LABELS[term]}领域"
    return "作为当前判断的可选方向"


def _unit_meaning(unit_type: str) -> str:
    labels = {
        "numeric_marker": "记录数字化证据或置信标记",
        "action_item": "可执行建议，可采纳或降权",
        "risk_boundary": "风险边界，可保留或加重",
        "question_need": "待补背景，可转成追问",
    }
    return labels.get(unit_type, "文本语义候选")


def _question_option_meaning(topic: str, label: str) -> str:
    if topic == "hidden_factor":
        return "作为隐藏线索校准，不改写命盘事实"
    if topic in _DOMAIN_LABELS:
        return f"把下一轮判断收束到{_DOMAIN_LABELS[topic]}：{label}"
    return "作为用户背景线索进入中枢判断"


def _discarded_unit(unit: dict[str, object], reason: str) -> dict[str, object]:
    return {
        "source_id": str(unit.get("source_id") or ""),
        "unit_type": str(unit.get("unit_type") or ""),
        "reason": reason,
        "text_preview": str(unit.get("text_span") or "")[:80],
    }


def _discarded_text(source_id: str, reason: str, text: str) -> dict[str, object]:
    return {
        "source_id": source_id,
        "reason": reason,
        "text_preview": text[:80],
    }


def _contains_internal_token(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in _INTERNAL_TOKENS)


def _clean_text(value: str) -> str:
    clean = " ".join(str(value or "").split())
    clean = re.sub(r"^(结论|建议|依据|判断|要点)\s*[：:]\s*", "", clean)
    return clean.strip(" ，,。")


def _slug(value: str) -> str:
    raw = str(value or "").strip().lower()
    if not raw:
        return ""
    mapped = {
        "木": "wood",
        "火": "fire",
        "土": "earth",
        "金": "metal",
        "水": "water",
        "比劫": "peer",
        "食伤": "output",
        "财星": "wealth_star",
        "官杀": "officer_killing",
        "印星": "resource_star",
    }
    if raw in mapped:
        return mapped[raw]
    ascii_slug = re.sub(r"[^a-z0-9_]+", "_", raw).strip("_")
    if ascii_slug:
        return ascii_slug[:64]
    return f"zh_{abs(hash(raw)) % 1000000}"


def _bounded_float(value: object, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return round(max(0.0, min(1.0, number)), 3)


def _dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _dict_rows(value: object) -> list[dict[str, object]]:
    return [row for row in _list(value) if isinstance(row, dict)]


def _unique(rows: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for row in rows:
        value = str(row or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
