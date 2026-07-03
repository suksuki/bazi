from __future__ import annotations

from typing import Any


BRAIN_JUDGE_VERSION = "v30.central_brain_judge.v1"


def judge_final_synthesis_quality(
    *,
    conclusion: str,
    advice: str,
    evidence_chain: list[dict[str, object]],
    top_claims: list[dict[str, object]],
    feedback_summary: dict[str, object] | None = None,
) -> dict[str, object]:
    feedback_summary = feedback_summary if isinstance(feedback_summary, dict) else {}
    evidence_score = _evidence_score(evidence_chain=evidence_chain, top_claims=top_claims)
    conclusion_score = _conclusion_score(conclusion)
    advice_score = _advice_score(advice)
    template_risk = _template_risk(" ".join([conclusion, advice]))
    overclaim_risk = _overclaim_risk(" ".join([conclusion, advice]), top_claims)
    feedback_alignment = min(1.0, _float(feedback_summary.get("active_signal_count"), 0.0) / 4.0)
    quality_score = round(
        max(
            0.0,
            min(
                1.0,
                evidence_score * 0.30
                + conclusion_score * 0.24
                + advice_score * 0.24
                + feedback_alignment * 0.08
                - template_risk * 0.20
                - overclaim_risk * 0.14,
            ),
        ),
        3,
    )
    failures = _quality_failures(
        evidence_score=evidence_score,
        conclusion_score=conclusion_score,
        advice_score=advice_score,
        template_risk=template_risk,
        overclaim_risk=overclaim_risk,
        conclusion=conclusion,
        advice=advice,
    )
    return {
        "version": BRAIN_JUDGE_VERSION,
        "judge_type": "final_synthesis_quality",
        "accepted": not failures and quality_score >= 0.58,
        "quality_score": quality_score,
        "scores": {
            "evidence_binding": round(evidence_score, 3),
            "conclusion_strength": round(conclusion_score, 3),
            "advice_actionability": round(advice_score, 3),
            "feedback_alignment": round(feedback_alignment, 3),
            "template_risk": round(template_risk, 3),
            "overclaim_risk": round(overclaim_risk, 3),
        },
        "failures": failures,
        "reason_codes": _reason_codes(
            evidence_score=evidence_score,
            conclusion_score=conclusion_score,
            advice_score=advice_score,
            template_risk=template_risk,
            overclaim_risk=overclaim_risk,
        ),
        "training_signal": {
            "version": "v30.training_signal.central_brain_judge.v1",
            "trainable": True,
            "targets": [
                "final_synthesis_quality_weight",
                "conclusion_strength_weight",
                "advice_actionability_weight",
                "template_risk_penalty",
                "overclaim_risk_penalty",
            ],
            "blocked_targets": [
                "chart_facts",
                "pillar_calculation",
                "calendar_conversion",
                "base_diagnosis_claim_text",
            ],
        },
        "chart_fact_mutation_allowed": False,
        "boundary": "central_brain_judge_scores_expression_and_decision_quality_without_generating_facts",
    }


def judge_llm_derivation_quality(
    *,
    derived_conclusion: str,
    derived_advice: str,
    public_thinking_lines: list[object],
    used_evidence: list[object],
) -> dict[str, object]:
    text = " ".join(
        [
            str(derived_conclusion or ""),
            str(derived_advice or ""),
            *[str(row) for row in public_thinking_lines],
        ]
    )
    evidence_score = min(1.0, len([row for row in used_evidence if str(row)]) / 3.0)
    conclusion_score = _conclusion_score(derived_conclusion)
    advice_score = _advice_score(derived_advice)
    thinking_score = min(1.0, len([row for row in public_thinking_lines if str(row).strip()]) / 2.0)
    template_risk = _template_risk(text)
    quality_score = round(
        max(0.0, min(1.0, evidence_score * 0.28 + conclusion_score * 0.24 + advice_score * 0.24 + thinking_score * 0.14 - template_risk * 0.20)),
        3,
    )
    failures: list[str] = []
    if evidence_score < 0.34:
        failures.append("llm_derivation_missing_used_evidence")
    if conclusion_score < 0.45:
        failures.append("llm_derivation_weak_conclusion")
    if advice_score < 0.45:
        failures.append("llm_derivation_weak_advice")
    if thinking_score < 0.5:
        failures.append("llm_derivation_missing_public_thinking")
    if template_risk >= 0.55:
        failures.append("llm_derivation_template_or_filler_language")
    return {
        "version": BRAIN_JUDGE_VERSION,
        "judge_type": "llm_derivation_quality",
        "accepted": not failures and quality_score >= 0.56,
        "quality_score": quality_score,
        "scores": {
            "evidence_binding": round(evidence_score, 3),
            "conclusion_strength": round(conclusion_score, 3),
            "advice_actionability": round(advice_score, 3),
            "public_thinking": round(thinking_score, 3),
            "template_risk": round(template_risk, 3),
        },
        "failures": failures,
        "reason_codes": _reason_codes(
            evidence_score=evidence_score,
            conclusion_score=conclusion_score,
            advice_score=advice_score,
            template_risk=template_risk,
            overclaim_risk=0.0,
        ),
        "chart_fact_mutation_allowed": False,
        "boundary": "central_brain_judge_scores_llm_derivation_candidate_without_accepting_new_facts",
    }


def _quality_failures(
    *,
    evidence_score: float,
    conclusion_score: float,
    advice_score: float,
    template_risk: float,
    overclaim_risk: float,
    conclusion: str,
    advice: str,
) -> list[str]:
    failures: list[str] = []
    if evidence_score < 0.34:
        failures.append("weak_evidence_binding")
    if conclusion_score < 0.45:
        failures.append("weak_or_missing_conclusion")
    if advice_score < 0.45:
        failures.append("weak_or_missing_actionable_advice")
    if template_risk >= 0.55:
        failures.append("template_or_filler_language")
    if overclaim_risk >= 0.55:
        failures.append("overclaim_or_fixed_verdict_risk")
    if not str(conclusion or "").startswith("结论："):
        failures.append("conclusion_not_first")
    if not str(advice or "").startswith("建议："):
        failures.append("advice_not_explicit")
    return failures


def _reason_codes(
    *,
    evidence_score: float,
    conclusion_score: float,
    advice_score: float,
    template_risk: float,
    overclaim_risk: float,
) -> list[str]:
    codes: list[str] = []
    if evidence_score >= 0.67:
        codes.append("evidence_chain_bound")
    if conclusion_score >= 0.67:
        codes.append("conclusion_is_decisive")
    if advice_score >= 0.67:
        codes.append("advice_is_actionable")
    if template_risk < 0.34:
        codes.append("template_risk_low")
    if overclaim_risk < 0.34:
        codes.append("overclaim_risk_low")
    return codes or ["quality_requires_review"]


def _evidence_score(*, evidence_chain: list[dict[str, object]], top_claims: list[dict[str, object]]) -> float:
    if not top_claims:
        return 0.0
    claim_trace = sum(1 for row in top_claims if isinstance(row, dict) and str(row.get("claim_id") or "") and _float(row.get("score"), 0.0) > 0)
    evidence_rows = sum(1 for row in evidence_chain if isinstance(row, dict) and _list(row.get("evidence")))
    expected_evidence_rows = max(1, min(4, len(top_claims[:4])))
    return min(1.0, claim_trace / max(1, len(top_claims[:4])) * 0.55 + evidence_rows / expected_evidence_rows * 0.45)


def _conclusion_score(text: str) -> float:
    clean = str(text or "").strip()
    if not clean:
        return 0.0
    score = 0.25
    if clean.startswith("结论："):
        score += 0.18
    if _has_any(clean, ("核心依据", "主线", "优先", "重点", "落在", "适合", "不宜")):
        score += 0.24
    if _has_any(clean, ("事业", "财", "关系", "健康", "时运", "结构", "路径", "画像", "规则", "十神")):
        score += 0.18
    if _is_evidence_bound_branch(clean):
        score += 0.10
    if len(clean) >= 28:
        score += 0.12
    if _is_unbound_soft(clean):
        score -= 0.24
    return max(0.0, min(1.0, score))


def _advice_score(text: str) -> float:
    clean = str(text or "").strip()
    if not clean:
        return 0.0
    score = 0.2
    if clean.startswith("建议："):
        score += 0.18
    if _has_any(clean, ("先", "避免", "减少", "确认", "选择", "建立", "拆成", "聚焦", "边界", "节奏", "执行")):
        score += 0.28
    if _has_any(clean, ("事业", "财", "关系", "健康", "时运", "职责", "平台", "风险", "合作", "作息")):
        score += 0.18
    if _is_evidence_bound_branch(clean):
        score += 0.08
    if len(clean) >= 24:
        score += 0.12
    if _is_unbound_soft(clean):
        score -= 0.18
    return max(0.0, min(1.0, score))


def _template_risk(text: str) -> float:
    clean = str(text or "")
    risk = 0.0
    filler = (
        "综合来看",
        "可以参考",
        "需要进一步",
        "不能作为",
        "不是最终定论",
        "当前阶段",
        "本次分析",
        "系统正在",
        "模型认为",
        "优先阅读",
        "流程",
        "token",
    )
    risk += sum(0.18 for token in filler if token in clean)
    if clean.count("可能") + clean.count("潜在") + clean.count("初步") >= 2 and not _is_evidence_bound_branch(clean):
        risk += 0.28
    if len(set(clean)) < 12 and len(clean) > 20:
        risk += 0.25
    return min(1.0, risk)


def _overclaim_risk(text: str, top_claims: list[dict[str, object]]) -> float:
    clean = str(text or "")
    risk = 0.0
    high_risk_terms = ("必然", "一定", "百分百", "必死", "必离婚", "一定发财", "灾祸")
    risk += sum(0.35 for token in high_risk_terms if token in clean)
    if any(isinstance(row, dict) and row.get("requires_question") is True for row in top_claims[:3]):
        if _has_any(clean, ("必然", "一定", "定会")):
            risk += 0.35
    return min(1.0, risk)


def _is_unbound_soft(text: str) -> bool:
    clean = str(text or "")
    soft_terms = ("可能", "大概", "潜在", "初步", "无法定论", "不好说", "仅供参考")
    return _has_any(clean, soft_terms) and not _is_evidence_bound_branch(clean)


def _is_evidence_bound_branch(text: str) -> bool:
    clean = str(text or "")
    branch_terms = ("候选", "分支", "概率", "置信", "权重", "评分", "可能", "倾向", "取向", "优先看")
    evidence_terms = (
        "证据",
        "反证",
        "路径",
        "十神",
        "用神",
        "忌神",
        "日主",
        "月令",
        "官杀",
        "印星",
        "财星",
        "食伤",
        "比劫",
        "地支",
        "规则",
        "画像",
        "大运",
        "流年",
        "结构",
        "确认",
        "降权",
        "升权",
    )
    return _has_any(clean, branch_terms) and _has_any(clean, evidence_terms)


def _has_any(text: str, tokens: tuple[str, ...]) -> bool:
    return any(token in text for token in tokens)


def _list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
