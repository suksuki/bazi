from __future__ import annotations

from v30.production.contracts import (
    BaziDomain,
    BaziSignal,
    BaziTopic,
    SignalRegistry,
    SignalSourceType,
)


def build_signal_registry(
    *,
    reading_id: str,
    signals: list[BaziSignal] | None = None,
    registry_id: str | None = None,
) -> SignalRegistry:
    registry = SignalRegistry(
        registry_id=registry_id or f"{reading_id}:production-signal-registry",
        reading_id=reading_id,
    )
    return registry.register_many(signals or [])


def signals_by_source_type(registry: SignalRegistry, source_type: SignalSourceType) -> list[BaziSignal]:
    return registry.by_source_type(source_type)


def signals_by_topic(registry: SignalRegistry, topic: BaziTopic) -> list[BaziSignal]:
    return registry.by_topic(topic)


def signals_by_domain(registry: SignalRegistry, domain: BaziDomain) -> list[BaziSignal]:
    return registry.by_domain(domain)


def signals_by_claim_key(registry: SignalRegistry, claim_key: str) -> list[BaziSignal]:
    return registry.by_claim_key(claim_key)
