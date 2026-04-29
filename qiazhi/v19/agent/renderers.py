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
        "Income Stability deterministic review",
        "",
        "结论边界：这是财富域的结构信号，不是财富预测、不是今年财运判断、不是传统断语。",
        f"当前 income_stability: {_label_value(value)} ({value or 'unknown'})",
        f"作用范围：{bundle.get('scope') or 'unknown'}；is_prediction={str(bool(bundle.get('is_prediction'))).lower()}。",
        "",
        "规则依据：",
    ]
    for key in ["self_capacity", "wealth_presence", "wealth_accessibility", "volatility", "structure_binding"]:
        row = signals.get(key, {})
        metrics = row.get("metrics") if isinstance(row.get("metrics"), dict) else {}
        sources = row.get("sources") if isinstance(row.get("sources"), list) else []
        inputs = row.get("inputs") if isinstance(row.get("inputs"), list) else []
        lines.append(f"- {SIGNAL_LABELS[key]}: {_label_value(str(row.get('value') or ''))} ({row.get('value') or 'unknown'})")
        lines.append(f"  rule: {row.get('rule_id') or 'unknown'}@v{row.get('rule_version') or '?'}")
        if row.get("condition"):
            lines.append(f"  condition: {row.get('condition')}")
        if inputs:
            lines.append(f"  inputs: {_compact_inputs(inputs)}")
        if metrics:
            lines.append(f"  metrics: {_compact_metrics(metrics)}")
        if sources:
            lines.append(f"  sources: {_compact_sources(sources)}")

    lines.extend(
        [
            "",
            "结构命中：",
            f"- wealth_element: {wealth_element or 'unknown'}",
            f"- touched_wealth_pillars: {', '.join(str(item) for item in touched) if touched else 'none'}",
        ]
    )
    if evidence:
        lines.append(f"- evidence_summary: {', '.join(str(item) for item in evidence)}")

    lines.extend(
        [
            "",
            "禁止解释：不输出 good/bad、favorable/unfavorable、今年财运、发财/破财、传统预测文本。",
            "后续若要让流年/大运影响该信号，必须进入 P5 time-aware inference，不能在 P4 直接混入。",
        ]
    )
    return "\n".join(lines)


def _value(signals: Dict[str, Dict[str, Any]], key: str) -> str:
    return str((signals.get(key) or {}).get("value") or "")


def _label_value(value: str) -> str:
    return VALUE_LABELS.get(value, value or "unknown")


def _compact_metrics(metrics: Dict[str, Any]) -> str:
    parts = []
    for key in sorted(metrics):
        value = metrics[key]
        if isinstance(value, list):
            value = "[" + ", ".join(str(item) for item in value) + "]"
        parts.append(f"{key}={value}")
    return "; ".join(parts)


def _compact_inputs(inputs: list[Dict[str, Any]]) -> str:
    parts = []
    for item in inputs:
        if not isinstance(item, dict):
            continue
        parts.append(f"{item.get('path')}={item.get('value')}")
    return "; ".join(parts)


def _compact_sources(sources: list[Any]) -> str:
    parts = []
    for item in sources:
        if isinstance(item, dict):
            parts.append(f"{item.get('path')}={item.get('value')}")
        else:
            parts.append(str(item))
    return "; ".join(parts)
