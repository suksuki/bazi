from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence

from v17_rebirth.backend.plugins.spec import V17Fact

EVIDENCE_BUNDLE_CONTRACT = "v17.evidence.bundle.v1"

_DETAIL_KEYS: tuple[str, ...] = (
    "work_evidence",
    "static_basis",
    "zaqi_evidence",
    "follow_evidence",
    "self_party_evidence",
    "structure_evidence",
    "blade_branch",
    "blade_scopes",
    "natal_blade_scopes",
    "runtime_blade_scopes",
    "blade_scope_label",
    "clash_pairs",
    "scope_weights",
    "pattern_scope",
    "pattern_scope_label",
    "pattern_break_risks",
    "pattern_gate",
    "pattern_gate_reason",
    "cluster_projection",
    "projection_share",
    "origin_type",
    "manifestation_state",
    "bazi_image",
    "wealth_profile",
)

_ROW_META_KEYS: tuple[str, ...] = (
    "pattern_candidate",
    "pattern_name",
    "target_god",
    "match_ratio",
    "claim_type",
    "entity_scope",
    "candidate_status",
    "observe_only",
    "source_event",
    "risk_driver",
    "macro_topic",
    "macro_topic_label",
    "topic_profile",
    "topic_profile_label",
    "symbolic_layer",
    "origin_type",
    "manifestation_state",
    "pattern_confidence",
    "pattern_confidence_percent",
    "pattern_scope",
    "pattern_scope_label",
    "scope_weights",
)


def _clean_str(value: Any, *, limit: int = 240) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _safe_float(value: Any, fallback: float = 0.0) -> float:
    try:
        next_value = float(value)
    except (TypeError, ValueError):
        return fallback
    if next_value != next_value:
        return fallback
    return round(next_value, 4)


def _compact_value(value: Any, *, depth: int = 0) -> Any:
    if depth >= 3:
        return _clean_str(value, limit=120)
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return _safe_float(value) if isinstance(value, float) else value
    if isinstance(value, str):
        return _clean_str(value)
    if isinstance(value, Mapping):
        return {
            _clean_str(key, limit=80): _compact_value(raw, depth=depth + 1)
            for key, raw in list(value.items())[:24]
            if _clean_str(key, limit=80)
        }
    if isinstance(value, (list, tuple, set)):
        return [_compact_value(item, depth=depth + 1) for item in list(value)[:10]]
    return _clean_str(value, limit=120)


def compact_fact_meta(meta: Mapping[str, Any]) -> Dict[str, Any]:
    """A small public projection for plugin rows. The full evidence lives in the bundle."""
    return {
        key: _compact_value(meta[key])
        for key in _ROW_META_KEYS
        if key in meta and _compact_value(meta[key]) not in ("", [], {})
    }


def _extract_details(meta: Mapping[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key in _DETAIL_KEYS:
        if key not in meta:
            continue
        value = _compact_value(meta.get(key))
        if value in ("", [], {}):
            continue
        out[key] = value
    return out


def _evidence_type(plugin_id: str, meta: Mapping[str, Any]) -> str:
    claim_type = _clean_str(meta.get("claim_type")).lower()
    risk_driver = _clean_str(meta.get("risk_driver")).lower()
    pid = plugin_id.lower()
    if risk_driver or "risk" in claim_type or "risk" in pid or "break_guard" in pid:
        return "risk"
    if _clean_str(meta.get("pattern_candidate")) or pid.startswith("classical.pattern"):
        return "pattern"
    if isinstance(meta.get("work_evidence"), Mapping):
        return "work"
    if "climate" in pid:
        return "climate"
    if "xiangfa" in pid:
        return "semantic"
    if "symbolic" in pid or "symbolic" in claim_type:
        return "symbolic"
    if "macro" in pid or "macro" in claim_type:
        return "macro"
    if "topic_profile" in claim_type or "modern.topic." in pid:
        return "topic"
    return "diagnostic"


def _claim_maps(claim_rows: Sequence[Any]) -> tuple[Dict[str, Dict[str, Any]], Dict[tuple[str, str], Dict[str, Any]]]:
    by_id: Dict[str, Dict[str, Any]] = {}
    by_signature: Dict[tuple[str, str], Dict[str, Any]] = {}
    for row in claim_rows:
        if not isinstance(row, Mapping):
            continue
        item = dict(row)
        claim_id = _clean_str(item.get("claim_id"))
        plugin_id = _clean_str(item.get("plugin_id"))
        claim_text = _clean_str(item.get("claim_text"))
        if claim_id:
            by_id[claim_id] = item
        if plugin_id and claim_text:
            by_signature[(plugin_id, claim_text)] = item
    return by_id, by_signature


def _item_title(fact: V17Fact, meta: Mapping[str, Any], claim: Mapping[str, Any]) -> str:
    return (
        _clean_str(meta.get("pattern_candidate"))
        or _clean_str(meta.get("pattern_name"))
        or _clean_str(meta.get("risk_driver"))
        or _clean_str(claim.get("claim_text"), limit=96)
        or _clean_str(fact.decision_hint, limit=96)
        or _clean_str(fact.text, limit=96)
    )


def build_evidence_bundle(
    facts: Sequence[V17Fact],
    *,
    physics_tensor: Mapping[str, Any] | None = None,
    max_items: int = 96,
) -> Dict[str, Any]:
    pt = physics_tensor if isinstance(physics_tensor, Mapping) else {}
    meta_root = pt.get("meta") if isinstance(pt.get("meta"), Mapping) else {}
    claims = meta_root.get("plugin_claims") if isinstance(meta_root.get("plugin_claims"), list) else []
    claims_by_id, claims_by_signature = _claim_maps(claims)
    items: List[Dict[str, Any]] = []

    for idx, fact in enumerate(facts):
        if not isinstance(fact, V17Fact):
            continue
        plugin_id = _clean_str(fact.plugin_id)
        fact_meta = dict(fact.meta or {}) if isinstance(fact.meta, Mapping) else {}
        claim_id = f"{plugin_id}_claim_{idx}"
        claim = claims_by_id.get(claim_id) or claims_by_signature.get((plugin_id, _clean_str(fact.text))) or {}
        details = _extract_details(fact_meta)
        has_signal = bool(details) or bool(fact_meta.get("pattern_candidate")) or bool(fact_meta.get("risk_driver"))
        has_claim_signal = bool(claim.get("claim_type")) and _clean_str(claim.get("claim_type")) != "diagnostic"
        if not has_signal and not has_claim_signal:
            continue

        evidence_type = _evidence_type(plugin_id, fact_meta)
        match_ratio = _safe_float(claim.get("match_ratio", fact_meta.get("match_ratio", 0.0)))
        confidence = _safe_float(
            claim.get(
                "confidence",
                fact_meta.get("pattern_confidence", fact_meta.get("confidence", fact.salience_weight or 0.0)),
            )
        )
        target_god = _clean_str(claim.get("target_god") or fact_meta.get("target_god") or fact.target_god)
        item = {
            "evidence_id": f"{plugin_id}_evidence_{idx}",
            "claim_id": _clean_str(claim.get("claim_id")) or claim_id,
            "source_plugin": plugin_id,
            "title": _item_title(fact, fact_meta, claim),
            "summary": _clean_str(claim.get("claim_text") or fact.text),
            "evidence_type": evidence_type,
            "claim_type": _clean_str(claim.get("claim_type") or fact_meta.get("claim_type") or "diagnostic"),
            "entity_scope": _clean_str(claim.get("entity_scope") or fact_meta.get("entity_scope") or ""),
            "target_god": target_god,
            "priority": _safe_float(fact.priority),
            "weight": _safe_float(fact.salience_weight),
            "confidence": confidence,
            "match_ratio": match_ratio,
            "candidate_status": _clean_str(
                fact_meta.get("candidate_status") or fact_meta.get("manifestation_state") or ""
            ),
            "observe_only": bool(fact_meta.get("observe_only")),
            "source_event": _clean_str(claim.get("source_event") or fact_meta.get("source_event") or ""),
            "origin_type": _clean_str(claim.get("origin_type") or fact_meta.get("origin_type") or ""),
            "manifestation_state": _clean_str(fact_meta.get("manifestation_state") or ""),
            "details": details,
            "detail_keys": list(details.keys()),
        }
        items.append(item)

    items.sort(key=lambda row: (_safe_float(row.get("weight")), _safe_float(row.get("confidence"))), reverse=True)
    trimmed = items[: max(0, int(max_items or 0))]
    counts_by_type: Dict[str, int] = {}
    for item in trimmed:
        kind = _clean_str(item.get("evidence_type")) or "diagnostic"
        counts_by_type[kind] = counts_by_type.get(kind, 0) + 1

    summary = {
        "total": len(trimmed),
        "source_fact_count": len(facts),
        "counts_by_type": counts_by_type,
        "candidate_count": sum(1 for item in trimmed if item.get("evidence_type") == "pattern"),
        "risk_count": sum(1 for item in trimmed if item.get("evidence_type") == "risk"),
        "observe_only_count": sum(1 for item in trimmed if item.get("observe_only")),
    }
    return {
        "contract": EVIDENCE_BUNDLE_CONTRACT,
        "summary": summary,
        "items": trimmed,
    }
