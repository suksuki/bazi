from __future__ import annotations

from collections import defaultdict
from typing import Any

from v20.answer.measurement_policy import domain_label, measurement_stage
from v20.features.schema import FeatureLayer
from v20.interaction.portrait_schema import PortraitAxis, PortraitItem, PortraitProjection
from v20.interaction.portrait_tags import build_portrait_tag_profile
from v20.measurement.domain_alignment import align_portrait_axis


PORTRAIT_PROJECTION_VERSION = "v20.portrait_projection.v1"

PORTRAIT_AXIS_TIER_MICRO = {
    "strength",
    "ten_god",
    "branch",
    "element",
    "pattern",
    "useful_god",
}

PORTRAIT_AXIS_TIER_MACRO = {
    "wealth",
    "career",
    "relationship",
    "health",
}

PORTRAIT_AXIS_SOURCE_ORDER = {
    "confirmed": 5,
    "chain_review": 4,
    "mixed": 4,
    "volatile": 4,
    "candidate": 3,
    "weak_candidate": 2,
    "requires_review": 2,
    "countered": 1,
}

PORTRAIT_TIER_LABEL = {
    "micro": "微观骨架",
    "decision": "裁决路径",
    "macro": "应用场景",
    "time": "时序引动",
}

PORTRAIT_AXIS_ANCHOR_BY_DOMAIN = {
    "strength": "日主承载与制约主轴",
    "ten_god": "十神显隐与作用主轴",
    "branch": "地支关系与牵引主轴",
    "element": "五行气势与失衡主轴",
    "pattern": "格局结构与秩序主轴",
    "useful_god": "用神调节方向主轴",
    "wealth": "财务结构与承接主轴",
    "career": "事业路径与执行主轴",
    "relationship": "关系互动与约束主轴",
    "health": "身心平衡与压力主轴",
    "time": "岁运流年与触发主轴",
    "romance": "关系关系与婚配主轴",
}

PORTRAIT_AXIS_STATE_ALIAS = {
    "confirmed": "confirmed",
    "chain_review": "chain_review",
    "mixed": "mixed",
    "candidate": "candidate",
    "weak_candidate": "weak_candidate",
    "requires_review": "requires_review",
    "volatile": "volatile",
    "countered": "countered",
    "blocked": "blocked",
    "out_of_scope": "candidate",
}

PORTRAIT_AXIS_STATE_LABEL = {
    "confirmed": "成已成立",
    "chain_review": "链式成形",
    "mixed": "成而不纯",
    "candidate": "方向成立",
    "weak_candidate": "偏弱成立",
    "requires_review": "低置信定向",
    "volatile": "时序触动",
    "countered": "被反证",
    "blocked": "被抑制",
}


def build_portrait_projection(
    feature_layer: FeatureLayer,
    decision_model: dict[str, Any],
    decision_report: dict[str, Any],
    *,
    runtime_decision_fusion: dict[str, Any] | None = None,
    runtime_policy_pointer: dict[str, Any] | None = None,
) -> dict[str, Any]:
    pointer, pointer_error = _load_portrait_runtime_pointer(runtime_policy_pointer)
    policy_index = _portrait_policy_index(pointer)
    axes = _axes(
        feature_layer,
        decision_model,
        decision_report,
        runtime_decision_fusion=runtime_decision_fusion,
        policy_index=policy_index,
    )
    items = _items(feature_layer, axes)
    portrait_policy_effect = _portrait_policy_effect(pointer, pointer_error, policy_index, axes)
    projection = PortraitProjection(
        version=PORTRAIT_PROJECTION_VERSION,
        status="ready" if axes else "empty",
        role="topic_projection_to_profile_tag_model",
        measurement_role="portrait_axes_are_profile_tags_backed_by_decisions_not_rule_debug",
        axes=axes,
        items=items,
        guardrails=(
            "PORTRAIT_IS_TOPIC_PROFILE_TAG_PROJECTION",
            "RULESPEC_DECISIONS_ANCHOR_AXES",
            "RULE_STATE_DEBUG_IS_NOT_PORTRAIT_LABEL",
            "KNOWLEDGE_SUPPORTS_LABELS_NOT_VERDICTS",
            "NO_PORTRAIT_DRIVEN_FORTUNE_VERDICT",
            "PORTRAIT_IS_DECISION_STATE_PROJECTION",
            "PORTRAIT_RUNTIME_CONSUMES_ACTIVE_PORTRAIT_POINTER",
        ),
    )
    payload = projection.to_dict()
    _annotate_axis_policy_effect(payload, policy_index)
    payload["source_decision_model_version"] = decision_model.get("version", "")
    payload["source_decision_report_version"] = decision_report.get("version", "")
    payload["axis_source"] = "DecisionState+MainlineDecision+TopicProjection"
    payload["portrait_model_source"] = "DecisionReport+TopicProjection+PortraitTagModel"
    payload["policy_effect"] = {
        "portrait_policy": portrait_policy_effect,
    }
    payload["runtime_policy_effect"] = portrait_policy_effect
    payload["runtime_decision_fusion_applied"] = bool(
        runtime_decision_fusion and bool(runtime_decision_fusion.get("decisions", ()))
    )
    payload["runtime_mutation"] = False
    return payload


def _axes(
    feature_layer: FeatureLayer,
    decision_model: dict[str, Any],
    decision_report: dict[str, Any],
    runtime_decision_fusion: dict[str, Any] | None = None,
    policy_index: dict[str, dict[str, Any]] | None = None,
) -> tuple[PortraitAxis, ...]:
    arguments = tuple(row for row in decision_model.get("argument_nodes", ()) if isinstance(row, dict))
    mainlines = tuple(row for row in decision_report.get("mainlines", ()) if isinstance(row, dict))
    by_domain: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in arguments:
        if str(row.get("state", "")) in {"blocked", "out_of_scope"}:
            continue
        by_domain[str(row.get("domain", ""))].append(_tag_source_row(row, "argument"))
    _append_runtime_fusion_rows(by_domain, runtime_decision_fusion)
    for row in mainlines:
        by_domain[str(row.get("domain", ""))].append(_tag_source_row(row, "mainline"))
    rows: list[PortraitAxis] = []
    for domain, source_rows in sorted(by_domain.items()):
        if not domain:
            continue
        feature_ids = _feature_ids(feature_layer, domain, source_rows)
        base_score = round(max(float(row.get("score", 0.0) or 0.0) for row in source_rows), 3)
        score = _apply_portrait_policy_score(base_score, policy_index.get(domain) if policy_index else None)
        axis_tier = _axis_tier(domain, source_rows)
        axis_state = _axis_state(source_rows)
        structural_anchor = _structural_anchor(domain, axis_tier, axis_state, source_rows)
        tag_profile = build_portrait_tag_profile(
            domain,
            source_rows,
            axis_tier=axis_tier,
            score=score,
        )
        alignment = align_portrait_axis(
            domain=domain,
            feature_ids=feature_ids,
            label=tag_profile.label,
            calibration_prompt=tag_profile.profile_summary,
        )
        if not alignment.ok:
            continue
        rows.append(
            PortraitAxis(
                axis_id=f"portrait.axis.{domain}",
                domain=domain,
                label=tag_profile.label,
                profile_tag=tag_profile.profile_tag,
                profile_tags=tag_profile.profile_tags,
                profile_summary=tag_profile.profile_summary,
                attention_level=tag_profile.attention_level,
                portrait_intent_type=tag_profile.portrait_intent_type,
                measurement_stage=measurement_stage(domain),
                feature_ids=feature_ids,
                feature_count=len(feature_ids),
                peak_confidence=score,
                calibration_state=tag_profile.calibration_state,
                axis_tier=axis_tier,
                axis_state=axis_state,
                structural_anchor=structural_anchor,
                knowledge_links=(),
                evidence_boundaries=_boundaries(source_rows),
                calibration_prompt=f"{tag_profile.label} 是否贴合该盘画像定性？",
                alignment_status=alignment.status,
                bazi_focus=alignment.focus,
                alignment_score=alignment.score,
            )
        )
    return tuple(sorted(rows, key=lambda row: (row.peak_confidence, row.feature_count), reverse=True)[:12])


def _load_portrait_runtime_pointer(pointer: dict[str, Any] | None) -> tuple[dict[str, Any], str]:
    if pointer is not None:
        return pointer, ""
    try:
        from v20.learning.portrait_runtime_pointer import build_portrait_runtime_pointer

        return build_portrait_runtime_pointer(), ""
    except Exception as exc:
        return (
            {
                "version": "v20.portrait_runtime_pointer_unavailable.v1",
                "status": "error",
                "runtime_applied": False,
                "runtime_allowed": False,
                "blocking_gate": f"portrait_runtime_pointer_failed:{exc}",
                "policy_payload": {},
                "runtime_mutation": False,
            },
            str(exc),
        )


def _portrait_policy_index(pointer: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if pointer.get("runtime_applied") is not True:
        return {}
    payload = pointer.get("policy_payload", {})
    if not isinstance(payload, dict):
        return {}
    rows = payload.get("portrait_axis_weight_policy", ())
    index: dict[str, dict[str, Any]] = {}
    for row in rows if isinstance(rows, list | tuple) else ():
        if not isinstance(row, dict):
            continue
        domain = str(row.get("domain", ""))
        if domain:
            index[domain] = row
    return index


def _apply_portrait_policy_score(base_score: float, policy_row: dict[str, Any] | None) -> float:
    if not policy_row:
        return base_score
    try:
        axis_delta = float(policy_row.get("axis_weight_delta", 0.0) or 0.0)
    except (TypeError, ValueError):
        axis_delta = 0.0
    try:
        floor_delta = float(policy_row.get("confidence_floor_delta", 0.0) or 0.0)
    except (TypeError, ValueError):
        floor_delta = 0.0
    bounded_delta = max(-0.08, min(0.08, axis_delta))
    adjusted = max(base_score + bounded_delta, base_score + max(0.0, min(0.04, floor_delta)))
    return round(max(0.0, min(0.98, adjusted)), 3)


def _portrait_policy_effect(
    pointer: dict[str, Any],
    pointer_error: str,
    policy_index: dict[str, dict[str, Any]],
    axes: tuple[PortraitAxis, ...],
) -> dict[str, Any]:
    axis_domains = {axis.domain for axis in axes}
    applied_domains = tuple(domain for domain in sorted(policy_index) if domain in axis_domains)
    if pointer_error:
        status = "pointer_error"
    elif pointer.get("runtime_applied") is not True:
        status = "not_applied"
    elif policy_index and not applied_domains:
        status = "active_no_matching_axis"
    else:
        status = "applied" if applied_domains else "empty_payload"
    return {
        "version": "v20.portrait_runtime_policy_effect.v1",
        "status": status,
        "active_policy_version": pointer.get("active_policy_version", ""),
        "candidate_policy_version": pointer.get("candidate_policy_version", ""),
        "policy_count": len(policy_index),
        "applied_axis_count": len(applied_domains),
        "applied_domains": applied_domains,
        "target": "portrait_axis_weight_policy",
        "blocking_gate": str(pointer.get("blocking_gate", "")),
        "runtime_mutation": False,
        "guardrails": (
            "PORTRAIT_POLICY_IS_POINTER_DRIVEN",
            "PORTRAIT_POLICY_ADJUSTS_AXIS_SCORE_ONLY",
            "PORTRAIT_POLICY_DOES_NOT_ESCALATE_ROLE_VISIBILITY",
        ),
    }


def _annotate_axis_policy_effect(payload: dict[str, Any], policy_index: dict[str, dict[str, Any]]) -> None:
    axes = payload.get("axes", ())
    if not isinstance(axes, list):
        return
    for axis in axes:
        if not isinstance(axis, dict):
            continue
        policy = policy_index.get(str(axis.get("domain", "")))
        if not policy:
            axis["policy_applied"] = False
            axis["policy_axis_weight_delta"] = 0.0
            axis["policy_role_depth_hint"] = ""
            continue
        axis["policy_applied"] = True
        axis["policy_axis_weight_delta"] = float(policy.get("axis_weight_delta", 0.0) or 0.0)
        axis["policy_confidence_floor_delta"] = float(policy.get("confidence_floor_delta", 0.0) or 0.0)
        axis["policy_role_depth_hint"] = str(policy.get("role_depth_hint", ""))


def _axis_tier(domain: str, rows: list[dict[str, Any]]) -> str:
    if domain == "time":
        return "time"
    if domain in PORTRAIT_AXIS_TIER_MACRO:
        if _has_source(rows, "argument") and _has_source(rows, "mainline"):
            return "macro"
        return "macro"
    if domain in PORTRAIT_AXIS_TIER_MICRO:
        return "micro"
    if _has_source(rows, "runtime") or _has_source(rows, "mainline"):
        return "decision"
    return "macro"


def _has_source(rows: list[dict[str, Any]], source: str) -> bool:
    return any(str(row.get("source_type", "")) == source or str(row.get("source", "")) == source for row in rows)


def _axis_state(rows: list[dict[str, Any]]) -> str:
    states = {str(row.get("state", "")).strip() for row in rows if str(row.get("state", "")).strip()}
    ordered = sorted(
        ((PORTRAIT_AXIS_SOURCE_ORDER.get(item, 0), item) for item in states if PORTRAIT_AXIS_SOURCE_ORDER.get(item, 0)),
        reverse=True,
    )
    if ordered:
        return PORTRAIT_AXIS_STATE_ALIAS.get(ordered[0][1], "candidate")
    return "candidate"


def _structural_anchor(
    domain: str,
    axis_tier: str,
    axis_state: str,
    rows: list[dict[str, Any]],
) -> str:
    base = PORTRAIT_AXIS_ANCHOR_BY_DOMAIN.get(domain, f"{domain_label(domain)}主轴")
    state = PORTRAIT_AXIS_STATE_LABEL.get(axis_state, "结构状态")
    if axis_tier == "time":
        return f"{base}｜{state}"
    if _is_mixed_path(rows):
        return f"{base}｜关键是冲突修复"
    return f"{base}｜{state}"


def _is_mixed_path(rows: list[dict[str, Any]]) -> bool:
    states = {str(row.get("state", "")) for row in rows}
    return "mixed" in states or "requires_review" in states or "countered" in states or "volatile" in states


def _append_runtime_fusion_rows(
    by_domain: dict[str, list[dict[str, Any]]],
    runtime_decision_fusion: dict[str, Any] | None,
) -> None:
    if not runtime_decision_fusion:
        return
    rows = tuple(row for row in runtime_decision_fusion.get("decisions", ()) if isinstance(row, dict))
    if not rows:
        return
    for row in rows:
        domain = str(row.get("domain", ""))
        if not domain:
            continue
        structural_state = str(row.get("structural_state", ""))
        by_domain[domain].append(
            {
                "domain": domain,
                "state": structural_state or "candidate",
                "status": structural_state or "candidate",
                "score": float(row.get("confidence", 0.0) or 0.0),
                "feature_ids": tuple(str(item) for item in row.get("feature_ids", ()) if str(item)),
                "label": str(row.get("user_facing_decision", "")),
                "summary": str(row.get("user_facing_boundary", "")),
                "boundary": str(row.get("user_facing_boundary", "")),
                "source_decision_key": str(row.get("source_decision_key", "")),
                "decision_key": str(row.get("decision_key", "")),
                "rule_key": str(row.get("source_rule_key", "")),
                "source": "runtime_decision_fusion",
                "source_type": "runtime",
            }
        )


def _tag_source_row(row: dict[str, Any], source_type: str) -> dict[str, Any]:
    tagged = dict(row)
    tagged["source_type"] = source_type
    return tagged


def _items(feature_layer: FeatureLayer, axes: tuple[PortraitAxis, ...]) -> tuple[PortraitItem, ...]:
    rows = []
    if axes:
        for axis in axes:
            feature_id = axis.feature_ids[0] if axis.feature_ids else f"portrait.item.{axis.domain}"
            title = _portrait_item_title(axis)
            alignment = align_portrait_axis(
                domain=axis.domain,
                feature_ids=axis.feature_ids or (feature_id,),
                label=title,
                calibration_prompt=axis.profile_summary,
            )
            if not alignment.ok:
                continue
            rows.append(
                PortraitItem(
                    feature_id=feature_id,
                    title=title,
                    domain=axis.domain,
                    measurement_topic=domain_label(axis.domain),
                    measurement_stage=measurement_stage(axis.domain),
                    measurement_focus=_portrait_item_focus(axis),
                    confidence=axis.peak_confidence,
                    calibration_state=axis.calibration_state,
                    knowledge_links=(),
                    alignment_status=alignment.status,
                    bazi_focus=alignment.focus,
                    alignment_score=alignment.score,
                )
            )
        return tuple(rows[:12])

    for feature in feature_layer.features[:24]:
        context = getattr(feature, "context", None)
        title = _context_item_title(feature)
        alignment = align_portrait_axis(
            domain=feature.domain,
            feature_ids=(feature.feature_id,),
            label=title,
            calibration_prompt=str(getattr(context, "mechanism", "")) or feature.boundary,
        )
        if not alignment.ok:
            continue
        rows.append(
            PortraitItem(
                feature_id=feature.feature_id,
                title=title,
                domain=feature.domain,
                measurement_topic=domain_label(feature.domain),
                measurement_stage=measurement_stage(feature.domain),
                measurement_focus=_context_item_focus(feature),
                confidence=feature.confidence,
                calibration_state=feature.calibration_state,
                knowledge_links=(),
                alignment_status=alignment.status,
                bazi_focus=alignment.focus,
                alignment_score=alignment.score,
            )
        )
    return tuple(rows)


def _portrait_item_title(axis: PortraitAxis) -> str:
    tags = tuple(tag for tag in axis.profile_tags if tag)
    detail = "、".join(tags[:3]) if tags else axis.profile_tag
    state = PORTRAIT_AXIS_STATE_LABEL.get(axis.axis_state, "结构定性")
    if detail and detail not in axis.label:
        return f"{axis.label}：{detail}（{state}）"
    return f"{axis.label}（{state}）"


def _portrait_item_focus(axis: PortraitAxis) -> str:
    summary = axis.profile_summary.strip()
    if summary:
        return summary
    return f"{domain_label(axis.domain)}画像已经完成主题投射，用于后续问题推荐和回答规划。"


def _context_item_title(feature: object) -> str:
    context = getattr(feature, "context", None)
    domain = str(getattr(feature, "domain", ""))
    state = str(getattr(context, "decision_state", "")) if context else ""
    state_label = PORTRAIT_AXIS_STATE_LABEL.get(state, "结构定性")
    hooks = tuple(str(row) for row in getattr(context, "projection_hooks", ()) if str(row)) if context else ()
    hook_text = "、".join(hooks[:2]) if hooks else domain_label(domain)
    return f"{domain_label(domain)}画像：{hook_text}（{state_label}）"


def _context_item_focus(feature: object) -> str:
    context = getattr(feature, "context", None)
    if context:
        mechanism = str(getattr(context, "mechanism", ""))
        affected = "、".join(str(row) for row in getattr(context, "affected_domains", ())[:3])
        if mechanism and affected:
            return f"计算元数据聚合：{mechanism}；影响主题：{affected}。"
    return f"{domain_label(str(getattr(feature, 'domain', '')))}画像从特征元数据聚合，不直接复用规则标题。"


def _feature_ids(
    feature_layer: FeatureLayer,
    domain: str,
    source_rows: list[dict[str, Any]],
) -> tuple[str, ...]:
    ids: list[str] = []
    for row in source_rows:
        ids.extend(str(item) for item in row.get("feature_ids", ()) if str(item))
    if not ids:
        ids.extend(feature.feature_id for feature in feature_layer.features if feature.domain == domain)
    if not ids:
        ids.extend(feature.feature_id for feature in feature_layer.features[:4])
    return tuple(dict.fromkeys(ids))[:8]


def _boundaries(source_rows: list[dict[str, Any]]) -> tuple[str, ...]:
    rows = []
    ignored = (
        "该规则只输出结构状态",
        "该规则只能作为结构候选",
        "已形成可复核结构路径",
        "当前偏结构候选",
        "需要补齐",
        "不做确定事件断言",
    )
    for row in source_rows:
        boundary = str(row.get("boundary", ""))
        if boundary and not any(token in boundary for token in ignored):
            rows.append(boundary)
        summary = str(row.get("summary", ""))
        if summary and not any(token in summary for token in ignored):
            rows.append(summary)
    if not rows:
        rows.append("系统已完成画像定性；命理师可基于经验修订权重，不替代八字事实。")
    return tuple(dict.fromkeys(rows))[:4]
