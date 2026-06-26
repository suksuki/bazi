from __future__ import annotations

from collections.abc import Callable
import re

from v20.answer.measurement_policy import (
    domain_label,
    feature_label,
    feature_public_summary,
    measurement_stage,
)
from v20.features.schema import FeatureLayer
from v20.interaction.questions import HOOK_DOMAIN_PREFERENCE, QUESTION_LABELS, QuestionCandidate
from v20.measurement.dimensions import dimension_payload
from v20.decision.question_config import QUESTION_STRATEGY


AttachQuestion = Callable[[QuestionCandidate, dict[str, object] | None, str], QuestionCandidate]
AlignQuestion = Callable[[QuestionCandidate], QuestionCandidate | None]
BaseScore = Callable[[dict[str, object]], float]
FeatureIds = Callable[[dict[str, object], FeatureLayer, str], tuple[str, ...]]
Boundary = Callable[[str], str]
CleanToken = Callable[[str], str]
ContainsChinese = Callable[[str], bool]
ClipText = Callable[[str, int], str]


def feature_hook_questions(
    decision_report: dict[str, object],
    feature_layer: FeatureLayer,
    *,
    attach_question: AttachQuestion,
    align_question: AlignQuestion,
    base_score: BaseScore,
    feature_ids: FeatureIds,
    boundary: Boundary,
    clean_token: CleanToken,
    contains_chinese: ContainsChinese,
    clip_text: ClipText,
    max_per_feature: int = 2,
    max_total: int = 18,
) -> list[QuestionCandidate]:
    rows: list[QuestionCandidate] = []
    if not feature_layer.features:
        return rows
    decisions = tuple(row for row in decision_report.get("decisions", ()) if isinstance(row, dict))
    decisions_by_domain: dict[str, list[dict[str, object]]] = {}
    for decision in decisions:
        domain = str(decision.get("domain", ""))
        if not domain:
            continue
        decisions_by_domain.setdefault(domain, []).append(decision)

    for feature in sorted(
        feature_layer.features,
        key=lambda row: (float(row.confidence or 0.0), len(getattr(row, "evidence_refs", ())), str(row.readiness)),
        reverse=True,
    ):
        if len(rows) >= max_total:
            break
        feature_id = str(getattr(feature, "feature_id", ""))
        feature_domain = str(getattr(feature, "domain", ""))
        source_decision = _source_decision_for_feature(feature_id, feature_domain, decisions_by_domain, decisions)
        hooks = tuple(str(row) for row in getattr(feature, "question_hooks", ()) if str(row))
        if not hooks:
            continue
        material = _feature_material_label(feature, clean_token=clean_token, contains_chinese=contains_chinese, clip_text=clip_text)
        for index, hook in enumerate(hooks[:max_per_feature]):
            if len(rows) >= max_total:
                break
            question_key = str(hook).strip()
            if not question_key:
                continue
            question_domain = HOOK_DOMAIN_PREFERENCE.get(question_key, feature_domain)
            if not question_domain:
                question_domain = feature_domain
            score = round(float(feature.confidence or 0.0) - 0.12 - index * 0.025, 3)
            if source_decision is not None:
                score = round(score + base_score(source_decision) * 0.025, 3)
            title = _feature_hook_question_title(question_key, material, feature)
            aligned = align_question(
                attach_question(
                    QuestionCandidate(
                        question_key=question_key,
                        title=title,
                        domain=question_domain,
                        score=score,
                        source_feature_ids=(feature_id,) if feature_id else feature_ids(source_decision or {}, feature_layer, question_domain),
                        boundary=boundary(question_domain),
                        measurement_topic=domain_label(question_domain),
                        measurement_stage=measurement_stage(question_domain),
                        **dimension_payload(question_domain),
                    ),
                    source_decision,
                    QUESTION_STRATEGY["feature_context"],
                )
            )
            if aligned:
                rows.append(aligned)
    return rows


def feature_context_material(feature: object) -> str:
    context = getattr(feature, "context", None)
    feature_id = str(getattr(feature, "feature_id", ""))
    if feature_id == "feature.wealth.visible_material":
        return "财星明透入局"
    if feature_id == "feature.wealth.hidden_material":
        return "财星藏而待引动"
    if feature_id == "feature.wealth.material_not_visible":
        return "财星不显，需转看通道"
    if feature_id.startswith("feature.ten_god.focus."):
        label = _state_value(str(getattr(feature, "calibration_state", "")), "label")
        return f"{label}成为十神焦点" if label else "十神焦点已入局"
    if feature_id.startswith("feature.element.prominent."):
        element = _element_name(_state_value(str(getattr(feature, "calibration_state", "")), "element"))
        return f"{element}气偏显" if element else "五行偏显"
    if feature_id.startswith("feature.element.weak."):
        element = _element_name(_state_value(str(getattr(feature, "calibration_state", "")), "element"))
        return f"{element}气偏弱" if element else "五行偏弱"
    if feature_id.startswith("feature.branch.relation_type."):
        relation = feature_id.rsplit(".", 1)[-1]
        return f"地支{_relation_name(relation)}牵动"
    if feature_id.startswith("feature.time.relation_type."):
        relation = feature_id.rsplit(".", 1)[-1]
        return f"岁运{_relation_name(relation)}触发"
    if feature_id.startswith("feature.time.ten_god."):
        state = str(getattr(feature, "calibration_state", ""))
        ten_god = _state_value(state, "ten_god")
        return f"时运见{ten_god}" if ten_god else "时运十神触发"
    if context:
        hooks = tuple(str(row) for row in getattr(context, "projection_hooks", ()) if str(row))
        if hooks:
            return _projection_hook_label(hooks[0])
    return ""


def _source_decision_for_feature(
    feature_id: str,
    feature_domain: str,
    decisions_by_domain: dict[str, list[dict[str, object]]],
    all_decisions: tuple[dict[str, object], ...],
) -> dict[str, object] | None:
    if feature_id:
        for row in decisions_by_domain.get(feature_domain, ()):
            if feature_id in tuple(str(item) for item in row.get("feature_ids", ())):
                return row
        for row in all_decisions:
            if feature_id in tuple(str(item) for item in row.get("feature_ids", ())):
                return row
    rows = decisions_by_domain.get(feature_domain, ())
    if rows:
        return rows[0]
    return all_decisions[0] if all_decisions else None


def _feature_hook_question_title(question_key: str, material: str, feature: object) -> str:
    hook = str(question_key).strip()
    if not hook:
        return ""
    context_title = _feature_context_question_title(hook, feature)
    if context_title:
        return context_title
    label = QUESTION_LABELS.get(hook, hook)
    stem = str(label).rstrip("？?")
    if material and material not in stem:
        return f"{material}，{stem}"
    return stem


def _feature_material_label(
    feature: object,
    *,
    clean_token: CleanToken,
    contains_chinese: ContainsChinese,
    clip_text: ClipText,
) -> str:
    context_material = feature_context_material(feature)
    if context_material:
        return context_material
    raw = [
        feature_label(feature),
        feature_public_summary(feature),
        str(getattr(feature, "boundary", "")),
    ]
    materials: list[str] = []
    for item in raw:
        token = clean_token(item)
        if (
            token
            and contains_chinese(token)
            and not re.search(r"\d", token)
            and token not in materials
        ):
            materials.append(token)
    if not materials:
        return ""
    return clip_text(materials[0], 18)


def _feature_context_question_title(question_key: str, feature: object) -> str:
    domain = str(getattr(feature, "domain", ""))
    focus = feature_context_material(feature)
    if question_key == "q_income_stability":
        return f"{focus or '财富结构'}，先看机会、承接还是波动？"
    if question_key == "q_income_factors":
        return f"{focus or '财务路径'}，限制来自承接、竞争还是时运牵动？"
    if question_key == "q_career_structure":
        return f"{focus or '事业结构'}，先分角色压力、表达还是缓冲？"
    if question_key == "q_relationship_structure":
        return f"{focus or '关系结构'}，先看互动方式、承接边界还是冲突处理？"
    if question_key == "q_health_balance_boundary":
        return f"{focus or '身心平衡'}，先看偏枯、压力还是恢复节律？"
    if question_key == "q_time_layer_context":
        return f"{focus or '时运触发'}，先看大运、流年还是原局回响？"
    if question_key == "q_time_relation_triggers":
        return f"{focus or '岁运引动'}，会先牵动事业、财运还是关系？"
    if question_key == "q_element_balance":
        return f"{focus or '五行配置'}，偏旺偏弱会先影响哪条主线？"
    if question_key == "q_element_support_pressure":
        return f"{focus or '五行压力'}，优势和压力分别落在哪里？"
    if question_key == "q_branch_relation_detail":
        return f"{focus or '地支互动'}，冲合刑害里哪类牵动最大？"
    if question_key == "q_ten_god_focus":
        return f"{focus or '十神分工'}，先看透出、藏干还是制化关系？"
    if question_key == "q_hidden_stem_role":
        return f"{focus or '藏干线索'}，哪些暗线会改变主题判断？"
    if question_key == "q_useful_god_candidates":
        return f"{focus or '用神取向'}，这个盘的用神和调节方向是什么？"
    if question_key == "q_useful_god_evidence_gaps":
        return f"{focus or '取用方向'}，还需要补哪类结构证据？"
    if question_key == "q_pattern_structure":
        return f"{focus or '格局秩序'}，先看主轴、做功还是破局点？"
    if domain:
        return f"{focus or domain_label(domain)}，下一步先沿哪条结构展开？"
    return ""


def _state_value(raw: str, key: str) -> str:
    for item in raw.split(";"):
        name, _, value = item.partition("=")
        if name == key:
            return value
    return ""


def _element_name(value: str) -> str:
    return {
        "wood": "木",
        "fire": "火",
        "earth": "土",
        "metal": "金",
        "water": "水",
    }.get(value, value)


def _relation_name(value: str) -> str:
    return {
        "clash": "冲",
        "harmony": "合",
        "harm": "害",
        "break": "破",
        "punishment": "刑",
        "three_harmony": "三合",
        "three_meeting": "三会",
    }.get(value, value)


def _projection_hook_label(value: str) -> str:
    return {
        "capacity_profile": "日主承载轴",
        "useful_god_direction": "用神取向轴",
        "wealth_opportunity": "财富机会轴",
        "wealth_capacity": "财富承接轴",
        "wealth_volatility": "财富波动轴",
        "career_role": "事业角色轴",
        "career_pressure": "事业压力轴",
        "career_expression": "事业表达轴",
        "relationship_interaction": "关系互动轴",
        "relationship_boundary": "关系边界轴",
        "wellbeing_pressure": "身心压力轴",
        "balance_boundary": "平衡边界轴",
        "role_visibility": "十神显隐轴",
        "element_pressure": "五行压力轴",
        "branch_trigger": "地支牵引轴",
        "timing_trigger": "岁运触发轴",
        "support_release_choice": "扶泄取舍轴",
        "pattern_order": "格局秩序轴",
    }.get(value, value.replace("_", ""))
