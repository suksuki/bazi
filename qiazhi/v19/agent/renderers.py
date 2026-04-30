from __future__ import annotations

from typing import Any, Dict


SIGNAL_LABELS = {
    "self_capacity": {"zh": "自我承载能力", "en": "Self capacity", "ko": "자기 수용력"},
    "wealth_presence": {"zh": "财富结构存在度", "en": "Wealth-structure presence", "ko": "재성 구조 출현도"},
    "wealth_accessibility": {"zh": "财富结构可及性", "en": "Wealth-structure accessibility", "ko": "재성 구조 접근성"},
    "volatility": {"zh": "结构波动性", "en": "Structural volatility", "ko": "구조 변동성"},
    "structure_binding": {"zh": "结构绑定", "en": "Structural binding", "ko": "구조 결속"},
    "income_stability": {"zh": "收入稳定性结构信号", "en": "Income-stability structural signal", "ko": "소득 안정성 구조 신호"},
}

VALUE_LABELS = {
    "none": {"zh": "无", "en": "none", "ko": "없음"},
    "low": {"zh": "低", "en": "low", "ko": "낮음"},
    "medium": {"zh": "中", "en": "medium", "ko": "중간"},
    "high": {"zh": "高", "en": "high", "ko": "높음"},
    "clear": {"zh": "清晰", "en": "clear", "ko": "명확"},
    "bound": {"zh": "被绑定", "en": "bound", "ko": "묶임"},
    "disrupted": {"zh": "被冲动/扰动", "en": "disrupted", "ko": "흔들림"},
    "conflicted": {"zh": "冲合并见", "en": "mixed clash and combination", "ko": "충합 혼재"},
    "not_applicable": {"zh": "不适用", "en": "not applicable", "ko": "해당 없음"},
    "present": {"zh": "存在", "en": "present", "ko": "존재"},
    "stable": {"zh": "稳定", "en": "stable", "ko": "안정"},
    "unstable": {"zh": "不稳定", "en": "unstable", "ko": "불안정"},
    "mixed": {"zh": "混合", "en": "mixed", "ko": "혼재"},
}


def render_income_stability_answer(bundle: Dict[str, Any], locale: str = "zh") -> str:
    locale = _normalize_locale(locale)
    signals = {str(row.get("key") or ""): dict(row) for row in bundle.get("signals", []) if isinstance(row, dict)}
    value = _value(signals, "income_stability")
    evidence = bundle.get("evidence_summary") if isinstance(bundle.get("evidence_summary"), list) else []
    touched = bundle.get("touched_wealth_pillars") if isinstance(bundle.get("touched_wealth_pillars"), list) else []
    wealth_element = str(bundle.get("wealth_element") or "")

    if locale == "en":
        lines = [
            f"This chart's income-stability structure is read as: {_label_value(value, locale)}.",
            "",
            "This only describes income-stability clues inside the natal structure. Specific wealth events require separate timing and factual context.",
            "",
            "Main basis:",
        ]
        for key in ["self_capacity", "wealth_presence", "wealth_accessibility", "volatility", "structure_binding"]:
            row = signals.get(key, {})
            reason = _signal_reason(key, row, touched, locale)
            suffix = f". {reason}" if reason else "."
            lines.append(f"- {_signal_label(key, locale)}: {_label_value(str(row.get('value') or ''), locale)}{suffix}")
        lines.extend(
            [
                "",
                "Structural clues:",
                f"- Wealth element: {_element_label(wealth_element, locale)}.",
                f"- Positions touching the wealth element: {_pillar_list(touched, locale)}.",
            ]
        )
        relation_text = _branch_relation_summary(bundle.get("branch_relations"), locale)
        if relation_text:
            lines.append(f"- Natal branch relations: {relation_text}.")
        if evidence:
            lines.append(f"- Summary: {_evidence_summary_text(evidence, locale)}.")
        lines.extend(["", "Reading boundary: luck cycles and flow years stay as timing context here; they do not directly rewrite the natal income-structure result."])
        return "\n".join(lines)

    if locale == "ko":
        lines = [
            f"이 명식의 소득 안정성 구조는 {_label_value(value, locale)}으로 읽습니다.",
            "",
            "이 결과는 원국 구조 안의 소득 안정성 단서만 설명합니다. 구체적인 재물 사건은 시간 배경과 사실 조건을 따로 보아야 합니다.",
            "",
            "주요 근거:",
        ]
        for key in ["self_capacity", "wealth_presence", "wealth_accessibility", "volatility", "structure_binding"]:
            row = signals.get(key, {})
            reason = _signal_reason(key, row, touched, locale)
            suffix = f". {reason}" if reason else "."
            lines.append(f"- {_signal_label(key, locale)}: {_label_value(str(row.get('value') or ''), locale)}{suffix}")
        lines.extend(
            [
                "",
                "구조 단서:",
                f"- 재성 오행: {_element_label(wealth_element, locale)}.",
                f"- 재성 오행과 닿는 위치: {_pillar_list(touched, locale)}.",
            ]
        )
        relation_text = _branch_relation_summary(bundle.get("branch_relations"), locale)
        if relation_text:
            lines.append(f"- 원국 지지 관계: {relation_text}.")
        if evidence:
            lines.append(f"- 요약: {_evidence_summary_text(evidence, locale)}.")
        lines.extend(["", "읽기 경계: 여기서는 대운과 세운을 시간 배경으로만 두며, 원국의 소득 구조 결과를 직접 바꾸지 않습니다."])
        return "\n".join(lines)

    lines = [
        f"这张命盘的收入稳定性结构先看作：{_label_value(value, locale)}。",
        "",
        "这个结果只说明本命结构里的收入稳定性线索，具体财富事件需要另按时间与事实条件分析。",
        "",
        "主要依据：",
    ]
    for key in ["self_capacity", "wealth_presence", "wealth_accessibility", "volatility", "structure_binding"]:
        row = signals.get(key, {})
        reason = _signal_reason(key, row, touched, locale)
        suffix = f"。{reason}" if reason else "。"
        lines.append(f"- {_signal_label(key, locale)}：{_label_value(str(row.get('value') or ''), locale)}{suffix}")

    lines.extend(
        [
            "",
            "结构线索：",
            f"- 财富元素：{_element_label(wealth_element, locale)}。",
            f"- 触及财富元素的位置：{_pillar_list(touched, locale)}。",
        ]
    )
    relation_text = _branch_relation_summary(bundle.get("branch_relations"), locale)
    if relation_text:
        lines.append(f"- 本命地支关系：{relation_text}。")
    if evidence:
        lines.append(f"- 摘要：{_evidence_summary_text(evidence, locale)}。")

    lines.extend(
        [
            "",
            "阅读边界：这里先不把大运、流年改写成收入结果；它们可以作为时间背景另看，但不能直接替代本命结构。",
        ]
    )
    return "\n".join(lines)


def _value(signals: Dict[str, Dict[str, Any]], key: str) -> str:
    return str((signals.get(key) or {}).get("value") or "")


def _label_value(value: str, locale: str = "zh") -> str:
    row = VALUE_LABELS.get(value)
    if isinstance(row, dict):
        return row.get(_normalize_locale(locale)) or row.get("zh") or value
    fallback = {"zh": "未知", "en": "unknown", "ko": "알 수 없음"}[_normalize_locale(locale)]
    return value or fallback


def _signal_label(key: str, locale: str = "zh") -> str:
    row = SIGNAL_LABELS.get(key)
    if isinstance(row, dict):
        return row.get(_normalize_locale(locale)) or row.get("zh") or key
    return key


def _signal_reason(key: str, row: Dict[str, Any], touched_wealth_pillars: list[Any], locale: str = "zh") -> str:
    locale = _normalize_locale(locale)
    metrics = row.get("metrics") if isinstance(row.get("metrics"), dict) else {}
    if key == "self_capacity":
        support = _percent(metrics.get("support_score"))
        pressure = _percent(metrics.get("pressure_score"))
        if support or pressure:
            if locale == "en":
                return f"support is about {support or 'unknown'}, pressure is about {pressure or 'unknown'}"
            if locale == "ko":
                return f"지지는 약 {support or '알 수 없음'}, 압력은 약 {pressure or '알 수 없음'}"
            return f"支持约{support or '未知'}，压力约{pressure or '未知'}"
    if key == "wealth_presence":
        count = metrics.get("count")
        if isinstance(count, (int, float)):
            if locale == "en":
                return f"{int(count)} visible wealth-element clue(s) appear in stems or branches"
            if locale == "ko":
                return f"천간과 지지에서 재성 오행 단서가 {int(count)}곳 보입니다"
            return f"可见天干地支里财富元素线索为{int(count)}处"
    if key == "wealth_accessibility":
        clash = _count_text(metrics.get("clash"), locale)
        combination = _count_text(metrics.get("combination"), locale)
        if not touched_wealth_pillars:
            if locale == "en":
                return "no pillar directly touches the wealth element, so this signal is not judged by itself"
            if locale == "ko":
                return "재성 오행과 직접 닿는 주가 없어 이 항목만 따로 판단하지 않습니다"
            return "当前未见直接触及财富元素的柱位，所以这项暂不单独判断"
        if locale == "en":
            return f"within wealth-touching positions, combinations are {combination} and clashes are {clash}"
        if locale == "ko":
            return f"재성 오행과 닿는 위치에서 연결은 {combination}, 충동은 {clash}입니다"
        return f"触及财富元素的位置里，连接{combination}、冲动{clash}"
    if key == "volatility":
        count = _count_text(metrics.get("clash_count"), locale)
        if locale == "en":
            return f"natal branches show {count} clash relation(s)"
        if locale == "ko":
            return f"원국 지지에서 충 관계가 {count} 감지됩니다"
        return f"本命地支里检测到冲动关系{count}"
    if key == "structure_binding":
        count = _count_text(metrics.get("three_harmony_count"), locale)
        if locale == "en":
            return f"natal branches show {count} three-harmony binding relation(s)"
        if locale == "ko":
            return f"원국 지지에서 삼합 결속이 {count} 감지됩니다"
        return f"本命地支里检测到三合牵制{count}"
    return ""


def _percent(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return ""
    return f"{round(float(value) * 100)}%"


def _count_text(value: Any, locale: str = "zh") -> str:
    if isinstance(value, (int, float)):
        if _normalize_locale(locale) == "zh":
            return f"{int(value)}组"
        return str(int(value))
    return "0组" if _normalize_locale(locale) == "zh" else "0"


def _element_label(value: str, locale: str = "zh") -> str:
    labels = {
        "wood": {"zh": "木", "en": "wood", "ko": "목"},
        "fire": {"zh": "火", "en": "fire", "ko": "화"},
        "earth": {"zh": "土", "en": "earth", "ko": "토"},
        "metal": {"zh": "金", "en": "metal", "ko": "금"},
        "water": {"zh": "水", "en": "water", "ko": "수"},
    }
    row = labels.get(value)
    if isinstance(row, dict):
        return row.get(_normalize_locale(locale)) or row.get("zh") or value
    return {"zh": "未识别", "en": "unrecognized", "ko": "인식되지 않음"}[_normalize_locale(locale)]


def _pillar_list(items: list[Any], locale: str = "zh") -> str:
    labels = {
        "year": {"zh": "年柱", "en": "year pillar", "ko": "연주"},
        "month": {"zh": "月柱", "en": "month pillar", "ko": "월주"},
        "day": {"zh": "日柱", "en": "day pillar", "ko": "일주"},
        "hour": {"zh": "时柱", "en": "hour pillar", "ko": "시주"},
    }
    locale = _normalize_locale(locale)
    values = [(labels.get(str(item), {}) or {}).get(locale) or str(item) for item in items if str(item)]
    if locale == "zh":
        return "、".join(values) if values else "未见直接触及"
    return ", ".join(values) if values else ("no direct contact" if locale == "en" else "직접 닿는 위치 없음")


def _branch_relation_summary(value: Any, locale: str = "zh") -> str:
    if not isinstance(value, list):
        return ""
    parts = []
    for row in value:
        if not isinstance(row, dict):
            continue
        branches = str(row.get("branches") or "")
        relation = _relation_label(str(row.get("type") or ""), locale)
        if branches and relation:
            parts.append(f"{branches}{relation}" if _normalize_locale(locale) == "zh" else f"{branches} {relation}")
    return "、".join(parts) if _normalize_locale(locale) == "zh" else ", ".join(parts)


def _relation_label(value: str, locale: str = "zh") -> str:
    labels = {
        "six_clash": {"zh": "冲", "en": "clash", "ko": "충"},
        "six_combination": {"zh": "合", "en": "combination", "ko": "합"},
        "three_harmony": {"zh": "三合", "en": "three-harmony", "ko": "삼합"},
    }
    row = labels.get(value)
    return (row or {}).get(_normalize_locale(locale), "") if isinstance(row, dict) else ""


def _evidence_summary_text(items: list[Any], locale: str = "zh") -> str:
    locale = _normalize_locale(locale)
    parts = []
    for item in items:
        text = str(item or "")
        if not text:
            continue
        if "=" in text:
            key, raw_value = text.split("=", 1)
            if locale == "en":
                parts.append(f"{_signal_label(key, locale)} is {_label_value(raw_value, locale)}")
            elif locale == "ko":
                parts.append(f"{_signal_label(key, locale)}: {_label_value(raw_value, locale)}")
            else:
                parts.append(f"{_signal_label(key, locale)}为{_label_value(raw_value, locale)}")
        else:
            parts.append(text)
    return "；".join(parts) if locale == "zh" else "; ".join(parts)


def _normalize_locale(value: str) -> str:
    clean = str(value or "zh").strip().lower()
    if clean in {"en", "en-us", "english"}:
        return "en"
    if clean in {"ko", "ko-kr", "kr", "korean"}:
        return "ko"
    return "zh"
