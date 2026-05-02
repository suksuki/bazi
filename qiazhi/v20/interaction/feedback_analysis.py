from __future__ import annotations

import hashlib
import re
from typing import Any

from v20.interaction.feedback import FeatureCalibrationSignal
from v20.learning.ledger import LedgerEntry
from v20.learning.proposal import LearningProposal
from v20.llm.tasks import summarize_feedback


def analyze_feedback(
    *,
    input_id: str,
    source_role: str,
    feedback_text: str,
    feature_ids: tuple[str, ...] = (),
    locale: str = "zh",
) -> dict[str, object]:
    redacted = _redact_feedback(feedback_text)
    source_hash = _source_hash(input_id, source_role, feedback_text)
    llm_summary = summarize_feedback(redacted, locale=locale)
    domains = tuple(llm_summary["result"]["candidate_domains"])
    conflict_profile = _build_conflict_profile(
        redacted=redacted,
        candidate_domains=domains,
        feature_ids=feature_ids,
    )
    signals = tuple(
        FeatureCalibrationSignal(
            feature_id=feature_id,
            profile_id=source_hash,
            signal="needs_review",
            source_role=source_role,
            note="feedback_signal_anonymized",
        )
        for feature_id in feature_ids[:12]
    )
    proposal = LearningProposal(
        proposal_id=f"v20.feedback.proposal.{source_hash}",
        proposal_type="feedback_calibration_review",
        summary=f"Review anonymized feedback domains: {', '.join(domains) if domains else 'open'}",
        risk="low" if signals else "medium",
    )
    ledger = LedgerEntry(
        run_id=f"v20.feedback.run.{source_hash}",
        source="feedback_analyzer",
        input_hash=source_hash,
        artifact_hash=_source_hash(redacted, ",".join(domains), ",".join(feature_ids)),
    )
    return {
        "version": "v20.feedback_analysis_report.v1",
        "source_hash": source_hash,
        "raw_feedback_retained": False,
        "redacted_summary": redacted[:240],
        "llm_summary": llm_summary,
        "candidate_domains": list(domains),
        "conflict_profile": conflict_profile,
        "follow_up_questions": conflict_profile["follow_up_questions"],
        "calibration_signals": [row.to_dict() for row in signals],
        "learning_proposal": proposal.to_dict(),
        "ledger_entry": ledger.to_dict(),
        "runtime_mutation": False,
        "guardrails": [
            "FEEDBACK_ANALYSIS_ONLY",
            "RAW_FEEDBACK_NOT_RETAINED",
            "CALIBRATION_SIGNAL_REQUIRES_VALIDATION",
            "NO_AUTOMATIC_PROMOTION",
        ],
    }


def _source_hash(*values: str) -> str:
    raw = "|".join(values)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _redact_feedback(text: str) -> str:
    value = text.strip()
    value = re.sub(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", "[email]", value)
    value = re.sub(r"\b(?:\+?\d[\d -]{6,}\d)\b", "[number]", value)
    value = re.sub(r"(姓名|名字|name)\s*[:：]\s*[\w\u4e00-\u9fff]+", r"\1:[redacted]", value, flags=re.IGNORECASE)
    return value


def _build_conflict_profile(
    *,
    redacted: str,
    candidate_domains: tuple[str, ...],
    feature_ids: tuple[str, ...],
) -> dict[str, Any]:
    risk_signals: list[str] = []
    follow_up_questions: list[str] = []
    feature_domains = _extract_feature_domains(feature_ids)
    overlap = tuple(domain for domain in candidate_domains if domain in feature_domains)
    missing = tuple(domain for domain in candidate_domains if domain not in feature_domains)
    certainty = _contains_certainty_claim(redacted)
    if certainty:
        risk_signals = risk_signals + ("overclaim_confidence_term",)
        follow_up_questions = follow_up_questions + ("你提到较强断言，我先确认：这句反馈是事实经历还是期望预期？",)
    if missing:
        risk_signals = risk_signals + ("domain_feature_coverage_gap",)
        follow_up_questions = follow_up_questions + tuple(
            f"这个'{_domain_label(domain)}'反馈我先按候选线索收，是否要我换成基于你的当前盘结构做一版更稳的解读？"
            for domain in missing
        )
    if not overlap and candidate_domains and feature_ids:
        risk_signals = risk_signals + ("candidate_domain_not_in_current_features",)
        follow_up_questions = follow_up_questions + ("我未发现你反馈涉及主题在当前结构里的直接证据位点，我先按问题优先级重排后再确认。",)
    if not risk_signals:
        risk_signals = ("low_conflict",)

    return {
        "candidate_domains": candidate_domains,
        "feature_domains": feature_domains,
        "risk_level": "high" if "overclaim_confidence_term" in risk_signals else "low",
        "risk_signals": tuple(dict.fromkeys(risk_signals)),
        "follow_up_questions": tuple(dict.fromkeys(follow_up_questions)),
    }


def _extract_feature_domains(feature_ids: tuple[str, ...]) -> tuple[str, ...]:
    domains: list[str] = []
    for feature_id in feature_ids:
        lower = feature_id.lower()
        if "wealth" in lower:
            domains.append("wealth")
        if "career" in lower:
            domains.append("career")
        if "relationship" in lower or "ren" in lower:
            domains.append("relationship")
        if "health" in lower:
            domains.append("health")
        if "strength" in lower:
            domains.append("strength")
        if "useful_god" in lower:
            domains.append("useful_god")
        if "branch" in lower:
            domains.append("branch")
        if "element" in lower:
            domains.append("element")
        if "time" in lower:
            domains.append("time")
        if "ten_god" in lower:
            domains.append("ten_god")
        if "pattern" in lower:
            domains.append("pattern")
    return tuple(dict.fromkeys(domains))


def _contains_certainty_claim(text: str) -> bool:
    lowered = text.lower()
    return any(mark in lowered for mark in ("一定", "必然", "肯定", "必定", "铁定", "百分百", "肯定会", "一定会", "绝对"))


def _domain_label(domain: str) -> str:
    return {
        "strength": "强弱与承载",
        "ten_god": "十神",
        "branch": "地支关系",
        "element": "五行",
        "wealth": "财运",
        "career": "事业",
        "relationship": "感情",
        "health": "健康",
        "useful_god": "用神",
        "pattern": "格局",
        "time": "时间",
    }.get(domain, domain)
