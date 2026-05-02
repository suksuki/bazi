from __future__ import annotations

from collections import defaultdict
from typing import Any

from v20.answer.measurement_policy import domain_label, measurement_focus, measurement_stage
from v20.features.schema import FeatureLayer
from v20.interaction.portrait_schema import PortraitAxis, PortraitItem, PortraitProjection
from v20.measurement.domain_alignment import align_portrait_axis


PORTRAIT_PROJECTION_VERSION = "v20.portrait_projection.v1"


def build_portrait_projection(
    feature_layer: FeatureLayer,
    decision_model: dict[str, Any],
    decision_report: dict[str, Any],
) -> dict[str, Any]:
    axes = _axes(feature_layer, decision_model, decision_report)
    items = _items(feature_layer)
    projection = PortraitProjection(
        version=PORTRAIT_PROJECTION_VERSION,
        status="ready" if axes else "empty",
        role="decision_state_to_portrait_axis_projection",
        measurement_role="portrait_axes_are_runtime_structure_views_not_personality_truth",
        axes=axes,
        items=items,
        guardrails=(
            "PORTRAIT_IS_DECISION_STATE_PROJECTION",
            "RULESPEC_DECISIONS_ANCHOR_AXES",
            "KNOWLEDGE_SUPPORTS_LABELS_NOT_VERDICTS",
            "NO_PORTRAIT_DRIVEN_FORTUNE_VERDICT",
        ),
    )
    payload = projection.to_dict()
    payload["source_decision_model_version"] = decision_model.get("version", "")
    payload["source_decision_report_version"] = decision_report.get("version", "")
    payload["axis_source"] = "DecisionState+MainlineDecision+TopicProjection"
    payload["runtime_mutation"] = False
    return payload


def _axes(
    feature_layer: FeatureLayer,
    decision_model: dict[str, Any],
    decision_report: dict[str, Any],
) -> tuple[PortraitAxis, ...]:
    arguments = tuple(row for row in decision_model.get("argument_nodes", ()) if isinstance(row, dict))
    mainlines = tuple(row for row in decision_report.get("mainlines", ()) if isinstance(row, dict))
    by_domain: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in arguments:
        if str(row.get("state", "")) in {"blocked", "out_of_scope"}:
            continue
        by_domain[str(row.get("domain", ""))].append(row)
    for row in mainlines:
        by_domain[str(row.get("domain", ""))].append(row)
    rows: list[PortraitAxis] = []
    for domain, source_rows in sorted(by_domain.items()):
        if not domain:
            continue
        feature_ids = _feature_ids(feature_layer, domain, source_rows)
        score = round(max(float(row.get("score", 0.0) or 0.0) for row in source_rows), 3)
        label = _axis_label(domain, source_rows)
        alignment = align_portrait_axis(
            domain=domain,
            feature_ids=feature_ids,
            label=label,
            calibration_prompt="；".join(_boundaries(source_rows)),
        )
        if not alignment.ok:
            continue
        rows.append(
            PortraitAxis(
                axis_id=f"portrait.axis.{domain}",
                domain=domain,
                label=label,
                measurement_stage=measurement_stage(domain),
                feature_ids=feature_ids,
                feature_count=len(feature_ids),
                peak_confidence=score,
                calibration_state=_calibration_state(source_rows),
                knowledge_links=(),
                evidence_boundaries=_boundaries(source_rows),
                calibration_prompt=f"{label} 是否贴合该盘当前证据链？",
                alignment_status=alignment.status,
                bazi_focus=alignment.focus,
                alignment_score=alignment.score,
            )
        )
    return tuple(sorted(rows, key=lambda row: (row.peak_confidence, row.feature_count), reverse=True)[:12])


def _items(feature_layer: FeatureLayer) -> tuple[PortraitItem, ...]:
    rows = []
    for feature in feature_layer.features[:24]:
        alignment = align_portrait_axis(
            domain=feature.domain,
            feature_ids=(feature.feature_id,),
            label=feature.title,
            calibration_prompt=feature.boundary,
        )
        if not alignment.ok:
            continue
        rows.append(
            PortraitItem(
                feature_id=feature.feature_id,
                title=feature.title,
                domain=feature.domain,
                measurement_topic=domain_label(feature.domain),
                measurement_stage=measurement_stage(feature.domain),
                measurement_focus=measurement_focus(feature),
                confidence=feature.confidence,
                calibration_state=feature.calibration_state,
                knowledge_links=(),
                alignment_status=alignment.status,
                bazi_focus=alignment.focus,
                alignment_score=alignment.score,
            )
        )
    return tuple(rows)


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


def _axis_label(domain: str, source_rows: list[dict[str, Any]]) -> str:
    states = {
        str(row.get("state") or row.get("status", ""))
        for row in source_rows
        if row.get("state") or row.get("status")
    }
    if "mixed" in states:
        suffix = "成而不纯"
    elif "volatile" in states:
        suffix = "岁运引动"
    elif "requires_review" in states:
        suffix = "需要复核"
    elif "weak_candidate" in states:
        suffix = "弱候选"
    else:
        suffix = "结构候选"
    return f"{domain_label(domain)}画像轴：{suffix}"


def _boundaries(source_rows: list[dict[str, Any]]) -> tuple[str, ...]:
    rows = []
    for row in source_rows:
        boundary = str(row.get("boundary", ""))
        if boundary:
            rows.append(boundary)
        summary = str(row.get("summary", ""))
        if summary:
            rows.append(summary)
    if not rows:
        rows.append("画像轴只表达结构状态，不输出固定吉凶。")
    return tuple(dict.fromkeys(rows))[:4]


def _calibration_state(source_rows: list[dict[str, Any]]) -> str:
    states = sorted(
        {
            str(row.get("state") or row.get("status", ""))
            for row in source_rows
            if row.get("state") or row.get("status")
        }
    )
    return "decision_states:" + ",".join(states) if states else "decision_states:unknown"
