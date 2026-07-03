from __future__ import annotations

from typing import Any


STAGE_POINT_SET_VERSION = "v30.stage_point_set.v1"
STAGE_POINT_VERSION = "v30.stage_point.v1"

_KIND_PRIORITY = {
    "verdict": 0,
    "branch": 1,
    "mechanism": 2,
    "evidence": 3,
    "advice": 4,
    "risk": 5,
    "question": 6,
}

_KIND_LABELS = {
    "verdict": "断",
    "branch": "枝",
    "mechanism": "机",
    "evidence": "证",
    "advice": "策",
    "risk": "戒",
    "question": "问",
}

_BAZI_TERMS = (
    "日主",
    "月令",
    "天干",
    "地支",
    "藏干",
    "十神",
    "比劫",
    "食伤",
    "财星",
    "官杀",
    "印星",
    "官印相生",
    "食伤生财",
    "财官",
    "印比",
    "合冲",
    "刑害",
    "冲合",
    "用神",
    "忌神",
    "取用",
    "格局",
    "旺衰",
    "大运",
    "流年",
    "流通",
    "做功",
    "泄秀",
    "生财",
    "扶身",
    "承接",
    "反证",
    "路径",
)

_STEMS_BRANCHES = tuple("甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥")

_MACRO_DOMAIN_TERMS = {
    "career": ("事业", "工作", "职位", "职责", "平台", "资质", "专业", "规则"),
    "wealth": ("财", "收益", "赚钱", "收入", "分配", "资源"),
    "relationship": ("关系", "感情", "伴侣", "合作", "边界"),
    "health": ("健康", "身体", "负荷", "压力", "消耗"),
    "family": ("家庭", "亲情", "父母", "子女"),
    "timing": ("大运", "流年", "年份", "阶段", "时运"),
}

_INTERNAL_TOKENS = (
    "context_id",
    "evidence_id",
    "source_id",
    "trace_id",
    "v30.",
    "krp.",
    "json",
    "metadata",
    "fallback",
    "quality gate",
)

_TEMPLATE_TOKENS = (
    "综合来看",
    "当前阶段",
    "目前阶段",
    "本次分析",
    "需要进一步分析",
    "可以参考",
    "后续继续",
    "仅供参考",
)

_STAGE_FORBIDDEN = {
    "chart_build": ("最终报告", "事业一定", "财运一定", "婚姻一定", "具体年份"),
    "rule_matching": ("最终报告", "完整报告", "具体年份", "必然发生"),
    "portrait_projection": ("必然事件", "一定发生", "具体年份"),
    "path_reasoning": ("完整报告", "所有领域", "具体年份"),
    "useful_god_arbitration": ("永久为忌", "唯一用神已定", "某五行永久"),
    "timing_layers": ("凭空", "必然发生"),
}


def build_stage_point_set(
    step: dict[str, object],
    *,
    candidate_points: list[object] | None = None,
    public_derivation: list[object] | None = None,
    conclusion: str = "",
    advice: str = "",
    stage_anchor_evidence: list[object] | None = None,
    used_evidence: list[object] | None = None,
    source: str = "central_brain_rule_summary",
) -> dict[str, object]:
    """Create selected, sidebar-ready StagePoints for one thinking stage."""

    stage_id = str(step.get("step_id") or "")
    analysis = _dict(step.get("analysis_result"))
    anchors = [str(row).strip() for row in (stage_anchor_evidence or []) if str(row).strip()]
    used = [str(row).strip() for row in (used_evidence or []) if str(row).strip()]
    raw_candidates = _candidate_rows(
        candidate_points or [],
        conclusion=conclusion or str(analysis.get("conclusion") or ""),
        advice=advice or str(analysis.get("next_focus") or ""),
        public_derivation=public_derivation or _public_trace_texts(analysis),
        stage_anchor_evidence=anchors,
    )

    points: list[dict[str, object]] = []
    discarded: list[dict[str, object]] = []
    seen: set[str] = set()
    for index, candidate in enumerate(raw_candidates, start=1):
        point = _normalize_candidate_point(
            candidate,
            stage_id=stage_id,
            index=index,
            source=source,
            stage_anchor_evidence=anchors,
            used_evidence=used,
        )
        if not point:
            continue
        key = _dedupe_key(str(point.get("text") or ""))
        if key in seen:
            discarded.append(_discard(stage_id, candidate, "duplicate_stage_point"))
            continue
        seen.add(key)
        gate = _scope_gate(stage_id, str(point.get("text") or ""))
        if not gate["accepted"]:
            discarded.append(_discard(stage_id, candidate, str(gate["reason"])))
            continue
        scored = _score_point(point, stage_id=stage_id, stage_anchor_evidence=anchors)
        points.append(scored)

    selected = _select_points(points)
    return {
        "version": STAGE_POINT_SET_VERSION,
        "stage_id": stage_id,
        "source": source,
        "candidate_count": len(raw_candidates),
        "selected_count": len(selected),
        "points": points,
        "selected_points": selected,
        "discarded_noise": discarded[:8],
        "quality_summary": _quality_summary(points, selected, discarded),
        "training_signal": {
            "signal_id": "v30.training_signal.stage_point_quality",
            "trainable": True,
            "targets": [
                "stage_point_quality",
                "evidence_binding",
                "sidebar_memory_priority",
                "template_risk_penalty",
                "overclaim_risk_penalty",
            ],
            "blocked_targets": [
                "chart_facts",
                "pillar_calculation",
                "calendar_conversion",
                "raw_rule_mutation",
            ],
        },
        "boundary": "stage_points_are_customer_facing_judgment_units_not_chart_facts",
    }


def selected_stage_points(point_set: dict[str, object] | None) -> list[dict[str, object]]:
    if not isinstance(point_set, dict):
        return []
    rows = point_set.get("selected_points")
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def point_text(point: dict[str, object]) -> str:
    return _clean_text(str(point.get("text") or ""))


def _candidate_rows(
    candidate_points: list[object],
    *,
    conclusion: str,
    advice: str,
    public_derivation: list[object],
    stage_anchor_evidence: list[str],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for candidate in candidate_points:
        if isinstance(candidate, dict):
            rows.append(dict(candidate))
        elif str(candidate).strip():
            rows.append({"kind": "mechanism", "text": str(candidate).strip()})
    has_verdict = any(str(row.get("kind") or "").lower() in {"verdict", "conclusion", "decision"} for row in rows)
    has_advice = any(str(row.get("kind") or "").lower() in {"advice", "recommendation", "action"} for row in rows)
    if conclusion and not has_verdict:
        rows.insert(0, {"kind": "verdict", "text": conclusion})
    if advice and not has_advice:
        rows.append({"kind": "advice", "text": advice})
    if not rows:
        for line in public_derivation[:3]:
            text = str(line).strip()
            if text:
                rows.append({"kind": "mechanism", "text": text})
    if stage_anchor_evidence and not any(str(row.get("kind") or "") == "evidence" for row in rows):
        rows.append({"kind": "evidence", "text": stage_anchor_evidence[0], "evidence_refs": stage_anchor_evidence[:2]})
    return rows


def _normalize_candidate_point(
    candidate: dict[str, object],
    *,
    stage_id: str,
    index: int,
    source: str,
    stage_anchor_evidence: list[str],
    used_evidence: list[str],
) -> dict[str, object] | None:
    text = _clean_text(str(candidate.get("text") or candidate.get("body") or candidate.get("summary") or ""))
    if not text:
        return None
    kind = _normalize_kind(str(candidate.get("kind") or ""))
    bazi_terms = _unique([
        *[str(row).strip() for row in _list(candidate.get("bazi_terms")) if str(row).strip()],
        *_detect_bazi_terms(text),
    ])[:8]
    macro_domains = _unique([
        *[str(row).strip() for row in _list(candidate.get("macro_domains")) if str(row).strip()],
        *_detect_macro_domains(text),
    ])[:5]
    evidence_refs = _unique([
        *[str(row).strip() for row in _list(candidate.get("evidence_refs")) if str(row).strip()],
        *used_evidence[:4],
        *stage_anchor_evidence[:2],
    ])[:6]
    point_id = str(candidate.get("point_id") or f"stage.{stage_id}.{index:03d}")
    short_label = _short_label(str(candidate.get("short_label") or ""), text, bazi_terms)
    score_seed = _float(candidate.get("confidence"), 0.0)
    is_branch_candidate = kind == "branch" or _looks_like_branch_text(text)
    probability = _branch_probability(candidate)
    if is_branch_candidate and probability == 0.0 and score_seed > 0:
        probability = round(max(0.0, min(1.0, score_seed)), 3)
    return {
        "version": STAGE_POINT_VERSION,
        "point_id": point_id,
        "stage_id": stage_id,
        "kind": kind,
        "kind_label": _KIND_LABELS.get(kind, "点"),
        "text": text,
        "short_label": short_label,
        "bazi_terms": bazi_terms,
        "macro_domains": macro_domains,
        "evidence_refs": evidence_refs,
        "counter_refs": [str(row).strip() for row in _list(candidate.get("counter_refs")) if str(row).strip()][:4],
        "branch_role": str(candidate.get("branch_role") or ("primary" if kind == "verdict" else "candidate" if is_branch_candidate else "")),
        "branch_probability": probability,
        "resolution_conditions": [
            str(row).strip()
            for row in _list(candidate.get("resolution_conditions"))[:4]
            if str(row).strip()
        ],
        "is_branch_candidate": is_branch_candidate,
        "option_hints": [
            row for row in _list(candidate.get("option_hints"))[:4]
            if isinstance(row, dict)
        ],
        "scope": "stage_local",
        "confidence": score_seed,
        "actionability": _actionability_score(text, kind),
        "display_priority": 0.0,
        "sidebar_visible": True,
        "selectable": kind in {"verdict", "branch", "mechanism", "advice", "risk"},
        "selected_default": False,
        "source": source,
        "training_tags": [
            "stage_point_quality",
            "evidence_binding",
            "sidebar_memory_priority",
            *(
                ["branch_probability_calibration", "practitioner_selection_feedback"]
                if is_branch_candidate
                else []
            ),
        ],
        "boundary": "stage_point_is_user_facing_judgment_not_chart_fact",
    }


def _normalize_kind(value: str) -> str:
    kind = value.strip().lower()
    aliases = {
        "conclusion": "verdict",
        "summary": "verdict",
        "decision": "verdict",
        "reasoning": "mechanism",
        "path": "mechanism",
        "basis": "evidence",
        "proof": "evidence",
        "alternative": "branch",
        "option": "branch",
        "candidate": "branch",
        "branch_candidate": "branch",
        "recommendation": "advice",
        "action": "advice",
        "boundary": "risk",
        "uncertainty": "branch",
        "followup": "question",
    }
    return aliases.get(kind, kind if kind in _KIND_PRIORITY else "mechanism")


def _branch_probability(candidate: dict[str, object]) -> float:
    for key in ("branch_probability", "probability", "weight"):
        value = candidate.get(key)
        if value is None:
            continue
        score = _float(value, -1.0)
        if score >= 0:
            return round(max(0.0, min(1.0, score)), 3)
    return 0.0


def _looks_like_branch_text(text: str) -> bool:
    return any(token in str(text or "") for token in ("候选", "分支", "概率", "置信", "权重", "评分", "可能", "取向", "降权", "升权"))


def _scope_gate(stage_id: str, text: str) -> dict[str, object]:
    lowered = text.lower()
    if any(token in lowered for token in _INTERNAL_TOKENS):
        return {"accepted": False, "reason": "internal_identifier_or_engineering_language"}
    forbidden = _STAGE_FORBIDDEN.get(stage_id, ())
    for token in forbidden:
        if token and token in text:
            return {"accepted": False, "reason": f"stage_scope_forbidden:{token}"}
    if stage_id != "final_report" and "完整报告" in text:
        return {"accepted": False, "reason": "cross_stage_full_report"}
    return {"accepted": True, "reason": "stage_scope_passed"}


def _score_point(point: dict[str, object], *, stage_id: str, stage_anchor_evidence: list[str]) -> dict[str, object]:
    text = str(point.get("text") or "")
    stage_scope_score = 0.86
    evidence_binding = _evidence_binding_score(point, text, stage_anchor_evidence)
    bazi_specificity = min(1.0, len(_list(point.get("bazi_terms"))) / 3.0)
    mechanism_clarity = 0.82 if any(term in text for term in ("因为", "通过", "形成", "转成", "承接", "流通", "牵引")) else 0.52
    customer_value = 0.78 if _list(point.get("macro_domains")) or any(term in text for term in ("建议", "优先", "注意", "风险", "行动")) else 0.58
    actionability = _float(point.get("actionability"), 0.0)
    template_risk = _template_risk(text)
    overclaim_risk = _overclaim_risk(text)
    score = max(
        0.0,
        min(
            1.0,
            stage_scope_score * 0.22
            + evidence_binding * 0.22
            + bazi_specificity * 0.16
            + mechanism_clarity * 0.14
            + customer_value * 0.14
            + actionability * 0.10
            - template_risk * 0.16
            - overclaim_risk * 0.18,
        ),
    )
    confidence = _float(point.get("confidence"), 0.0) or min(0.95, max(0.42, score))
    return {
        **point,
        "confidence": round(confidence, 3),
        "display_priority": round(score, 3),
        "score_breakdown": {
            "stage_scope": round(stage_scope_score, 3),
            "evidence_binding": round(evidence_binding, 3),
            "bazi_specificity": round(bazi_specificity, 3),
            "mechanism_clarity": round(mechanism_clarity, 3),
            "customer_value": round(customer_value, 3),
            "actionability": round(actionability, 3),
            "template_risk": round(template_risk, 3),
            "overclaim_risk": round(overclaim_risk, 3),
        },
    }


def _select_points(points: list[dict[str, object]]) -> list[dict[str, object]]:
    if not points:
        return []
    by_kind: dict[str, list[dict[str, object]]] = {}
    for point in sorted(points, key=lambda row: (-_float(row.get("display_priority"), 0.0), _KIND_PRIORITY.get(str(row.get("kind")), 9))):
        by_kind.setdefault(str(point.get("kind") or ""), []).append(point)
    selected: list[dict[str, object]] = []
    for kind in ("verdict", "advice"):
        if by_kind.get(kind):
            selected.append(by_kind[kind][0])
    for point in sorted(points, key=lambda row: (_KIND_PRIORITY.get(str(row.get("kind")), 9), -_float(row.get("display_priority"), 0.0))):
        if len(selected) >= 4:
            break
        if point in selected:
            continue
        if str(point.get("kind") or "") in {"branch", "mechanism", "evidence", "risk"} or _float(point.get("display_priority"), 0.0) >= 0.72:
            selected.append(point)
    return [
        {
            **point,
            "selected_default": True,
            "sidebar_visible": bool(point.get("sidebar_visible", True)) and index < 3,
        }
        for index, point in enumerate(selected[:4])
    ]


def _quality_summary(points: list[dict[str, object]], selected: list[dict[str, object]], discarded: list[dict[str, object]]) -> dict[str, object]:
    selected_scores = [_float(row.get("display_priority"), 0.0) for row in selected]
    all_breakdowns = [_dict(row.get("score_breakdown")) for row in points]
    return {
        "version": "v30.stage_point_quality_summary.v1",
        "point_count": len(points),
        "selected_count": len(selected),
        "discarded_noise_count": len(discarded),
        "average_selected_priority": round(sum(selected_scores) / len(selected_scores), 3) if selected_scores else 0.0,
        "average_evidence_binding": _average_score(all_breakdowns, "evidence_binding"),
        "average_template_risk": _average_score(all_breakdowns, "template_risk"),
        "average_overclaim_risk": _average_score(all_breakdowns, "overclaim_risk"),
    }


def _evidence_binding_score(point: dict[str, object], text: str, stage_anchor_evidence: list[str]) -> float:
    score = 0.0
    if _list(point.get("evidence_refs")):
        score += 0.45
    if _list(point.get("bazi_terms")):
        score += 0.25
    if stage_anchor_evidence:
        anchor_hits = sum(1 for row in stage_anchor_evidence if _anchor_key(row) and _anchor_key(row) in text)
        score += min(0.20, anchor_hits * 0.10)
    if not score and any(term in text for term in _BAZI_TERMS):
        score += 0.22
    return min(1.0, score)


def _clean_text(value: str) -> str:
    import re

    clean = " ".join(str(value or "").split())
    clean = re.sub(r"^(结论|建议|依据|判断|要点)\s*[：:]\s*", "", clean)
    replacements = {
        "综合来看，": "",
        "综合来看": "",
        "当前阶段": "",
        "目前阶段": "",
        "本次分析": "",
        "请注意，": "",
        "请注意": "",
        "请您": "",
        "后续的分析": "",
        "后续分析": "",
        "后续": "",
    }
    for old, new in replacements.items():
        clean = clean.replace(old, new)
    return re.sub(r"\s+", " ", clean).strip(" ，,。")


def _short_label(explicit: str, text: str, bazi_terms: list[str]) -> str:
    clean = _clean_text(explicit)
    if clean:
        return clean[:28]
    prefix = "、".join(bazi_terms[:2])
    body = text.split("。", 1)[0].split("；", 1)[0].strip()
    if prefix and prefix not in body:
        return f"{prefix}：{body[:18]}".strip("：")
    return body[:28]


def _detect_bazi_terms(text: str) -> list[str]:
    hits = [term for term in _BAZI_TERMS if term and term in text]
    hits.extend([char for char in _STEMS_BRANCHES if char in text])
    return _unique(hits)


def _detect_macro_domains(text: str) -> list[str]:
    rows: list[str] = []
    for domain, terms in _MACRO_DOMAIN_TERMS.items():
        if any(term in text for term in terms):
            rows.append(domain)
    return rows


def _actionability_score(text: str, kind: str) -> float:
    if kind == "advice":
        return 0.78
    if any(token in text for token in ("优先", "避免", "先看", "重点", "不要", "需要", "落到", "执行")):
        return 0.68
    return 0.42


def _template_risk(text: str) -> float:
    hits = sum(1 for token in _TEMPLATE_TOKENS if token and token in text)
    return min(1.0, hits / 2.0)


def _overclaim_risk(text: str) -> float:
    hard_terms = ("一定", "必然", "永远", "绝对", "必定", "肯定会")
    return min(1.0, sum(1 for term in hard_terms if term in text) / 2.0)


def _discard(stage_id: str, candidate: object, reason: str) -> dict[str, object]:
    text = ""
    if isinstance(candidate, dict):
        text = str(candidate.get("text") or candidate.get("summary") or "")[:80]
    else:
        text = str(candidate)[:80]
    return {
        "stage_id": stage_id,
        "reason": reason,
        "text_preview": text,
    }


def _public_trace_texts(analysis: dict[str, object]) -> list[str]:
    rows: list[str] = []
    for row in _list(analysis.get("public_trace")):
        if isinstance(row, dict):
            label = str(row.get("label") or "").strip()
            text = str(row.get("text") or "").strip()
            if label and text:
                rows.append(f"{label}：{text}")
    return rows[:4]


def _anchor_key(value: str) -> str:
    text = str(value or "")
    if "：" in text:
        return text.split("：", 1)[0]
    if ":" in text:
        return text.split(":", 1)[0]
    return text[:8]


def _dedupe_key(value: str) -> str:
    return "".join(ch for ch in _clean_text(value) if ch not in "，。；;,. ")[:36]


def _average_score(rows: list[dict[str, object]], key: str) -> float:
    values = [_float(row.get(key), 0.0) for row in rows if key in row]
    return round(sum(values) / len(values), 3) if values else 0.0


def _dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


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
