from __future__ import annotations

from typing import Any, Dict, List

from v17_rebirth.backend.plugins.spec import V17Fact
from v17_rebirth.backend.services.target_god_resolver import resolve_target_god

CLAIM_JSON_SCHEMA: Dict[str, Any] = {
    "title": "V17Claim",
    "type": "object",
    "required": [
        "claim_id",
        "plugin_id",
        "claim_text",
        "claim_type",
        "entity_scope",
        "logic_level",
        "intent_vector",
        "priority",
        "confidence",
    ],
    "properties": {
        "claim_id": {"type": "string"},
        "plugin_id": {"type": "string"},
        "claim_text": {"type": "string"},
        "claim_type": {"type": "string"},
        "entity_scope": {"type": "string"},
        "logic_level": {"type": "string"},
        "source_event": {"type": "string"},
        "exclusivity_key": {"type": "string"},
        "target_god": {"type": "string"},
        "arbiter_type": {"type": "string"},
        "intent_vector": {"type": "object"},
        "priority": {"type": "number"},
        "confidence": {"type": "number"},
        "match_ratio": {"type": "number"},
        "origin_type": {"type": "string"},
        "origin_multiplier": {"type": "number"},
    },
}


def _logic_level_from_tier(causal_tier: int) -> str:
    tier = int(causal_tier or 0)
    if tier >= 4:
        return "L1"
    if tier == 3:
        return "L2"
    return "L3"


def _claim_type_from_meta(meta: Dict[str, Any], impact_ratio: float) -> str:
    explicit = str(meta.get("claim_type") or "").strip()
    if explicit:
        return explicit
    if impact_ratio > 0:
        return "enhance"
    if impact_ratio < 0:
        return "weaken"
    return "diagnostic"


def _entity_scope_from_meta(meta: Dict[str, Any], target_god: str) -> str:
    explicit = str(meta.get("entity_scope") or "").strip()
    if explicit:
        return explicit
    if target_god:
        return "ten_god"
    if meta.get("risk_signal"):
        return "risk_structure"
    return "diagnostic"


def _source_event(plugin_id: str, meta: Dict[str, Any], fact: V17Fact) -> str:
    return (
        str(meta.get("source_event") or "").strip()
        or str(meta.get("source_key") or "").strip()
        or str(meta.get("exclusivity_key") or "").strip()
        or f"{plugin_id}:{str(fact.text or '').strip()[:48]}"
    )


def _exclusivity_key(plugin_id: str, meta: Dict[str, Any], target_god: str, source_event: str) -> str:
    explicit = str(meta.get("exclusivity_key") or "").strip()
    if explicit:
        return explicit
    if source_event:
        return source_event
    return f"{plugin_id}|{target_god}"


def _derive_match_ratio(
    *,
    meta: Dict[str, Any],
    claim_type: str,
    plugin_id: str,
    impact_ratio: float,
    salience_weight: float,
) -> float:
    if "match_ratio" in meta:
        try:
            value = float(meta.get("match_ratio", 0.0) or 0.0)
        except (TypeError, ValueError):
            value = 0.0
        return max(0.0, min(1.0, value))

    confidence = 0.0
    try:
        confidence = float(meta.get("confidence", salience_weight or 0.5) or 0.5)
    except (TypeError, ValueError):
        confidence = float(salience_weight or 0.5)
    confidence = max(0.0, min(1.0, confidence))

    if claim_type == "pattern_candidate":
        return max(0.45, min(0.9, confidence))
    if impact_ratio:
        return max(0.4, min(0.92, abs(impact_ratio) * 2.5))
    if str(plugin_id).startswith("l0.foundation."):
        return max(0.5, min(0.72, confidence))
    return max(0.35, min(0.78, confidence))


def compile_claims(*, facts: List[V17Fact], physics_tensor: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    claims: List[Dict[str, Any]] = []
    for idx, fact in enumerate(facts):
        meta = dict(fact.meta or {}) if isinstance(fact.meta, dict) else {}
        plugin_id = str(fact.plugin_id or "").strip()
        target_god = resolve_target_god(
            row_target=fact.target_god,
            impact=meta,
            meta=meta,
            title=fact.text,
            label=fact.decision_hint or fact.text,
            plugin_id=plugin_id,
            physics_tensor=physics_tensor,
        )
        try:
            impact_ratio = float(meta.get("impact_ratio", 0.0) or 0.0)
        except (TypeError, ValueError):
            impact_ratio = 0.0
        source_event = _source_event(plugin_id, meta, fact)
        claim_type = _claim_type_from_meta(meta, impact_ratio)
        match_ratio = _derive_match_ratio(
            meta=meta,
            claim_type=claim_type,
            plugin_id=plugin_id,
            impact_ratio=impact_ratio,
            salience_weight=float(fact.salience_weight or 0.5),
        )
        entity_scope = _entity_scope_from_meta(meta, target_god)
        intent_vector = meta.get("intent_vector") if isinstance(meta.get("intent_vector"), dict) else {}
        if not intent_vector and target_god and impact_ratio:
            intent_vector = {target_god: round(impact_ratio, 4)}
        claims.append(
            {
                "claim_id": f"{plugin_id}_claim_{idx}",
                "plugin_id": plugin_id,
                "claim_text": str(fact.text or "").strip(),
                "claim_type": claim_type,
                "entity_scope": entity_scope,
                "logic_level": str(meta.get("logic_level") or _logic_level_from_tier(int(fact.causal_tier or 0))),
                "source_event": source_event,
                "exclusivity_key": _exclusivity_key(plugin_id, meta, target_god, source_event),
                "target_god": target_god,
                "arbiter_type": str(getattr(fact.suggested_arbiter, "value", fact.suggested_arbiter) or "system"),
                "intent_vector": intent_vector,
                "priority": float(fact.priority or 0.0),
                "confidence": float(meta.get("confidence", fact.salience_weight or 0.5) or 0.5) * max(0.35, match_ratio),
                "match_ratio": match_ratio,
                "origin_type": str(meta.get("origin_type") or "").strip(),
                "origin_multiplier": float(meta.get("origin_multiplier", 1.0) or 1.0),
                "causal_tier": int(fact.causal_tier or 0),
            }
        )
    return claims
