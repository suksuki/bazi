from __future__ import annotations

from typing import Any

from v20.answer.measurement_policy import domain_label
from v20.interaction.questions import QuestionCandidate


PORTRAIT_GRAPH_SUMMARY_VERSION = "v20.portrait_graph_summary.v1"


def build_portrait_graph_summary(
    portrait_projection: dict[str, object],
    decision_report: dict[str, object],
    questions: tuple[QuestionCandidate, ...],
) -> dict[str, object]:
    axes = tuple(row for row in portrait_projection.get("axes", ()) if isinstance(row, dict))
    if not axes:
        return {
            "version": PORTRAIT_GRAPH_SUMMARY_VERSION,
            "status": "empty",
            "runtime_mutation": False,
            "guardrails": _guardrails(),
        }

    primary = _primary_axis(axes)
    domain_summaries = tuple(_domain_summary(row) for row in axes[:8])
    profile_tags = tuple(dict.fromkeys(tag for row in axes[:8] for tag in _list(row.get("profile_tags", ())) if tag))[:12]
    strengths = _mechanism_lines(axes, include=("证据成立", "链条成形", "主线成形"))
    pressure = _mechanism_lines(axes, include=("主次并存", "主题入局", "命理师可调权"))
    timing = _timing_lines(axes, decision_report)
    suggested_questions = _suggested_questions(questions)
    headline = _headline(primary, profile_tags)

    return {
        "version": PORTRAIT_GRAPH_SUMMARY_VERSION,
        "status": "ready",
        "headline": headline,
        "primary_axis": _domain_summary(primary),
        "profile_tags": profile_tags,
        "domain_summaries": domain_summaries,
        "strength_lines": strengths,
        "pressure_lines": pressure,
        "timing_triggers": timing,
        "suggested_questions": suggested_questions,
        "graph_nodes": _graph_nodes(primary, axes, suggested_questions),
        "source": "PortraitProjection+DecisionReport+QuestionCandidate",
        "runtime_mutation": False,
        "guardrails": _guardrails(),
    }


def _primary_axis(axes: tuple[dict[str, object], ...]) -> dict[str, object]:
    def key(row: dict[str, object]) -> tuple[int, float, int]:
        attention = {"high": 3, "medium": 2, "normal": 1}.get(str(row.get("attention_level", "")), 0)
        return (
            attention,
            float(row.get("peak_confidence", 0.0) or 0.0),
            int(row.get("feature_count", 0) or 0),
        )

    return sorted(axes, key=key, reverse=True)[0]


def _domain_summary(axis: dict[str, object]) -> dict[str, object]:
    domain = str(axis.get("domain", ""))
    return {
        "domain": domain,
        "domain_label": domain_label(domain),
        "label": str(axis.get("label", "")),
        "profile_tag": str(axis.get("profile_tag", "")),
        "summary": str(axis.get("profile_summary", "")),
        "attention_level": str(axis.get("attention_level", "")),
        "score": round(float(axis.get("peak_confidence", 0.0) or 0.0), 3),
    }


def _headline(primary: dict[str, object], profile_tags: tuple[str, ...]) -> str:
    label = str(primary.get("label", "")) or domain_label(str(primary.get("domain", "")))
    tag = str(primary.get("profile_tag", "")).replace("：", "，")
    if tag:
        return f"这个盘先按「{label}」读，主标签是「{tag}」。"
    if profile_tags:
        return f"这个盘先按「{label}」读，重点看{'、'.join(profile_tags[:3])}。"
    return f"这个盘先按「{label}」读，再分主题展开。"


def _mechanism_lines(axes: tuple[dict[str, object], ...], *, include: tuple[str, ...]) -> tuple[str, ...]:
    rows: list[str] = []
    for axis in axes:
        tags = _list(axis.get("profile_tags", ()))
        if not any(tag in tags or tag in str(axis.get("profile_tag", "")) for tag in include):
            continue
        label = str(axis.get("label", "")) or domain_label(str(axis.get("domain", "")))
        tag = str(axis.get("profile_tag", ""))
        rows.append(f"{label}：{tag}" if tag else label)
        if len(rows) >= 4:
            break
    return tuple(dict.fromkeys(rows))


def _timing_lines(axes: tuple[dict[str, object], ...], decision_report: dict[str, object]) -> tuple[str, ...]:
    rows: list[str] = []
    for axis in axes:
        if str(axis.get("domain", "")) == "time":
            rows.append(str(axis.get("profile_tag", "")) or "时间层已进入本次画像")
    fusion = decision_report.get("runtime_decision_fusion", {})
    if isinstance(fusion, dict):
        for row in fusion.get("decisions", ()):
            if isinstance(row, dict) and str(row.get("structural_state", "")) == "volatile":
                decision = str(row.get("user_facing_decision", ""))
                if decision:
                    rows.append(decision)
    return tuple(dict.fromkeys(row for row in rows if row))[:3]


def _suggested_questions(questions: tuple[QuestionCandidate, ...]) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for question in questions[:6]:
        rows.append(
            {
                "question_key": question.question_key,
                "title": question.title,
                "domain": question.domain,
                "domain_label": domain_label(question.domain),
                "score": round(float(question.score or 0.0), 3),
            }
        )
    return tuple(rows)


def _graph_nodes(
    primary: dict[str, object],
    axes: tuple[dict[str, object], ...],
    questions: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    nodes: list[dict[str, object]] = [
        {
            "node_id": "portrait.primary_axis",
            "node_type": "portrait_axis",
            "label": str(primary.get("label", "")),
            "domain": str(primary.get("domain", "")),
        }
    ]
    for axis in axes[:5]:
        nodes.append(
            {
                "node_id": f"portrait.domain.{axis.get('domain', '')}",
                "node_type": "topic_axis",
                "label": str(axis.get("profile_tag", "")) or str(axis.get("label", "")),
                "domain": str(axis.get("domain", "")),
            }
        )
    for question in questions[:3]:
        nodes.append(
            {
                "node_id": f"portrait.question.{question.get('question_key', '')}",
                "node_type": "question",
                "label": str(question.get("title", "")),
                "domain": str(question.get("domain", "")),
            }
        )
    return tuple(nodes)


def _list(value: object) -> tuple[str, ...]:
    if not isinstance(value, (tuple, list)):
        return ()
    return tuple(str(row) for row in value if str(row))


def _guardrails() -> tuple[str, ...]:
    return (
        "PORTRAIT_GRAPH_IS_USER_SUMMARY_NOT_INTERNAL_GRAPH",
        "PORTRAIT_GRAPH_USES_TAGS_NOT_RULE_DEBUG",
        "NO_FIXED_FORTUNE_CONCLUSION",
        "QUESTIONS_REMAIN_EVIDENCE_BACKED",
    )
