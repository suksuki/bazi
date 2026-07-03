from __future__ import annotations

import re

from v30.production.contracts import (
    BaziDomain,
    BaziSignal,
    BaziTopic,
    SignalSourceType,
    SourceModule,
)
from v30.ziwei.contracts import ZiweiDomainKey, ZiweiDomainRule, ZiweiSignal


def ziwei_signal_from_rule(*, reading_id: str, rule: ZiweiDomainRule, source_ref: str | None = None) -> ZiweiSignal:
    ref = source_ref or rule.rule_id
    return ZiweiSignal(
        signal_id=f"ziwei:{reading_id}:{rule.rule_id}",
        reading_id=reading_id,
        rule_id=rule.rule_id,
        source_ref=ref,
        domain=rule.domain,
        claim=rule.claim,
        claim_key=rule.claim_key,
        palace_refs=list(rule.palace_refs),
        star_refs=list(rule.star_refs),
        transform_refs=list(rule.transform_refs),
        related_palaces=list(rule.related_palaces),
        polarity=rule.polarity,
        strength=rule.strength_hint,
        confidence=rule.confidence_hint,
        assertion_level_hint=rule.assertion_level_hint,
        probe_trigger=rule.probe_trigger,
        target_hidden_attributes=list(rule.target_hidden_attributes),
        evidence_refs=[f"ziwei_rule:{rule.rule_id}", f"ziwei_source:{ref}"],
    )


def ziwei_signal_to_bazi_signal(signal: ZiweiSignal) -> BaziSignal:
    return BaziSignal(
        signal_id=_signal_id(signal.signal_id),
        source_module=SourceModule.ZIWEI_DOMAIN_LENS,
        source_type=SignalSourceType.ZIWEI_SIGNAL,
        source_ref=signal.source_ref,
        topic=_topic(signal.domain),
        domain=_domain(signal.domain),
        role_visibility=list(signal.role_visibility),
        claim=signal.claim,
        claim_key=signal.claim_key,
        polarity=signal.polarity,
        strength=signal.strength,
        confidence=signal.confidence,
        assertion_level_hint=signal.assertion_level_hint,
        evidence_refs=list(signal.evidence_refs),
        counter_evidence_refs=list(signal.counter_evidence_refs),
        branch_group_id=f"ziwei:{signal.domain}:{signal.probe_trigger}",
        conflict_group_id=f"ziwei:{signal.claim_key}" if signal.counter_evidence_refs else "",
        training_targets=[
            "ziwei_signal_quality",
            "ziwei_probe_trigger_quality",
            "ziwei_bazi_alignment_quality",
        ],
        boundary="ziwei_domain_lens_signal_is_observation_only_decision_weight_zero",
        raw_ref=signal.signal_id,
    )


def ziwei_signals_to_bazi_signals(signals: list[ZiweiSignal]) -> list[BaziSignal]:
    return [ziwei_signal_to_bazi_signal(signal) for signal in signals]


def _domain(domain: ZiweiDomainKey) -> BaziDomain:
    return {
        "wealth": BaziDomain.WEALTH,
        "career": BaziDomain.CAREER,
        "relationship": BaziDomain.RELATIONSHIP,
        "mobility": BaziDomain.MOBILITY,
        "health_pressure": BaziDomain.HEALTH,
        "property": BaziDomain.PROPERTY,
    }.get(domain, BaziDomain.UNKNOWN)


def _topic(domain: ZiweiDomainKey) -> BaziTopic:
    return {
        "wealth": BaziTopic.WEALTH,
        "career": BaziTopic.CAREER,
        "relationship": BaziTopic.RELATIONSHIP,
        "mobility": BaziTopic.MOBILITY,
        "health_pressure": BaziTopic.HEALTH,
        "property": BaziTopic.PROPERTY,
    }.get(domain, BaziTopic.UNKNOWN)


def _signal_id(ref: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.:\-\u4e00-\u9fff]+", "_", ref or "unknown")
    return f"signal:{SignalSourceType.ZIWEI_SIGNAL.value}:{safe[:140]}"
