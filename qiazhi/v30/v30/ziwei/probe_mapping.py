from __future__ import annotations

from v30.ziwei.contracts import ZiweiDomainKey, ZiweiProbeMapping, ZiweiSignal
from v30.ziwei.domain_rules import ZIWEI_V1_DOMAIN_RULES


def _mapping(rule) -> ZiweiProbeMapping:
    return ZiweiProbeMapping(
        claim_key=rule.claim_key,
        domain=rule.domain,
        probe_trigger=rule.probe_trigger,
        question_slot_key=f"ziwei:{rule.probe_trigger}",
        answer_signal_key=f"answer:{rule.claim_key}",
        hidden_attribute_keys=list(rule.target_hidden_attributes),
    )


ZIWEI_PROBE_MAPPINGS: tuple[ZiweiProbeMapping, ...] = tuple(_mapping(rule) for rule in ZIWEI_V1_DOMAIN_RULES)


def mapping_for_claim_key(claim_key: str) -> ZiweiProbeMapping | None:
    return next((row for row in ZIWEI_PROBE_MAPPINGS if row.claim_key == claim_key), None)


def probe_mappings_by_domain(domain: ZiweiDomainKey) -> list[ZiweiProbeMapping]:
    return [row for row in ZIWEI_PROBE_MAPPINGS if row.domain == domain]


def probe_mappings_for_signals(signals: list[ZiweiSignal]) -> list[ZiweiProbeMapping]:
    mappings: list[ZiweiProbeMapping] = []
    seen: set[str] = set()
    for signal in signals:
        mapping = mapping_for_claim_key(signal.claim_key)
        if mapping and mapping.claim_key not in seen:
            mappings.append(mapping)
            seen.add(mapping.claim_key)
    return mappings
