from __future__ import annotations

from typing import Any, Dict


SIGNAL_LABELS = {
    "self_capacity": "自我承载能力",
    "wealth_presence": "财富结构存在度",
    "wealth_accessibility": "财富结构可及性",
    "volatility": "结构波动性",
    "structure_binding": "结构绑定",
    "income_stability": "收入稳定性结构信号",
}

VALUE_LABELS = {
    "none": "无",
    "low": "低",
    "medium": "中",
    "high": "高",
    "clear": "清晰",
    "bound": "被绑定",
    "disrupted": "被冲动/扰动",
    "conflicted": "冲合并见",
    "not_applicable": "不适用",
    "present": "存在",
    "stable": "稳定",
    "unstable": "不稳定",
    "mixed": "混合",
}


def render_income_stability_answer(bundle: Dict[str, Any]) -> str:
    signals = {str(row.get("key") or ""): dict(row) for row in bundle.get("signals", []) if isinstance(row, dict)}
    value = _value(signals, "income_stability")
    evidence = bundle.get("evidence_summary") if isinstance(bundle.get("evidence_summary"), list) else []
    touched = bundle.get("touched_wealth_pillars") if isinstance(bundle.get("touched_wealth_pillars"), list) else []
    wealth_element = str(bundle.get("wealth_element") or "")

    lines = [
        f"这张命盘的收入稳定性结构先看作：{_label_value(value)}。",
        "",
        "这个结果只说明本命结构里的收入稳定性线索，具体财富事件需要另按时间与事实条件分析。",
        "",
        "主要依据：",
    ]
    for key in ["self_capacity", "wealth_presence", "wealth_accessibility", "volatility", "structure_binding"]:
        row = signals.get(key, {})
        reason = _signal_reason(key, row, touched)
        suffix = f"。{reason}" if reason else "。"
        lines.append(f"- {SIGNAL_LABELS[key]}：{_label_value(str(row.get('value') or ''))}{suffix}")

    lines.extend(
        [
            "",
            "结构线索：",
            f"- 财富元素：{_element_label(wealth_element)}。",
            f"- 触及财富元素的位置：{_pillar_list(touched)}。",
        ]
    )
    relation_text = _branch_relation_summary(bundle.get("branch_relations"))
    if relation_text:
        lines.append(f"- 本命地支关系：{relation_text}。")
    if evidence:
        lines.append(f"- 摘要：{_evidence_summary_text(evidence)}。")

    lines.extend(
        [
            "",
            "阅读边界：这里先不把大运、流年改写成收入结果；它们可以作为时间背景另看，但不能直接替代本命结构。",
        ]
    )
    return "\n".join(lines)


def _value(signals: Dict[str, Dict[str, Any]], key: str) -> str:
    return str((signals.get(key) or {}).get("value") or "")


def _label_value(value: str) -> str:
    return VALUE_LABELS.get(value, value or "未知")


def _signal_reason(key: str, row: Dict[str, Any], touched_wealth_pillars: list[Any]) -> str:
    metrics = row.get("metrics") if isinstance(row.get("metrics"), dict) else {}
    if key == "self_capacity":
        support = _percent(metrics.get("support_score"))
        pressure = _percent(metrics.get("pressure_score"))
        if support or pressure:
            return f"支持约{support or '未知'}，压力约{pressure or '未知'}"
    if key == "wealth_presence":
        count = metrics.get("count")
        if isinstance(count, (int, float)):
            return f"可见天干地支里财富元素线索为{int(count)}处"
    if key == "wealth_accessibility":
        clash = _count_text(metrics.get("clash"))
        combination = _count_text(metrics.get("combination"))
        if not touched_wealth_pillars:
            return "当前未见直接触及财富元素的柱位，所以这项暂不单独判断"
        return f"触及财富元素的位置里，连接{combination}、冲动{clash}"
    if key == "volatility":
        return f"本命地支里检测到冲动关系{_count_text(metrics.get('clash_count'))}"
    if key == "structure_binding":
        return f"本命地支里检测到三合牵制{_count_text(metrics.get('three_harmony_count'))}"
    return ""


def _percent(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return ""
    return f"{round(float(value) * 100)}%"


def _count_text(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{int(value)}组"
    return "0组"


def _element_label(value: str) -> str:
    labels = {
        "wood": "木",
        "fire": "火",
        "earth": "土",
        "metal": "金",
        "water": "水",
    }
    return labels.get(value, "未识别")


def _pillar_list(items: list[Any]) -> str:
    labels = {
        "year": "年柱",
        "month": "月柱",
        "day": "日柱",
        "hour": "时柱",
    }
    values = [labels.get(str(item), str(item)) for item in items if str(item)]
    return "、".join(values) if values else "未见直接触及"


def _branch_relation_summary(value: Any) -> str:
    if not isinstance(value, list):
        return ""
    parts = []
    for row in value:
        if not isinstance(row, dict):
            continue
        branches = str(row.get("branches") or "")
        relation = _relation_label(str(row.get("type") or ""))
        if branches and relation:
            parts.append(f"{branches}{relation}")
    return "、".join(parts)


def _relation_label(value: str) -> str:
    labels = {
        "six_clash": "冲",
        "six_combination": "合",
        "three_harmony": "三合",
    }
    return labels.get(value, "")


def _evidence_summary_text(items: list[Any]) -> str:
    parts = []
    for item in items:
        text = str(item or "")
        if not text:
            continue
        if "=" in text:
            key, raw_value = text.split("=", 1)
            parts.append(f"{SIGNAL_LABELS.get(key, key)}为{_label_value(raw_value)}")
        else:
            parts.append(text)
    return "；".join(parts)
