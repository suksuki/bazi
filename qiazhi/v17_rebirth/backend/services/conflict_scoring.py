from __future__ import annotations

from typing import Any, Dict, List, Tuple


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = lo
    return max(lo, min(hi, parsed))


def _severity_score(value: str) -> float:
    mapping = {"P1": 1.0, "P2": 0.75, "P3": 0.4}
    return mapping.get(str(value or "").strip().upper(), 0.6)


def _conflict_type_score(value: str) -> float:
    mapping = {"same_event_duplicate": 0.2, "same_target_opposite_sign": 0.4, "cross_layer_override": 0.55}
    return mapping.get(str(value or "").strip(), 0.3)


def _claim_signal_score(claim: Dict[str, Any]) -> float:
    confidence = _clamp(float(claim.get("confidence", 0.0) or 0.0), 0.0, 1.0)
    priority_raw = _clamp(float(claim.get("priority", 0.0) or 0.0), 0.0, 1.0)
    intent_total = 0.0
    vector = claim.get("intent_vector")
    if isinstance(vector, dict):
        for raw in vector.values():
            try:
                intent_total += abs(float(raw))
            except (TypeError, ValueError):
                continue
    intent_strength = _clamp(intent_total, 0.0, 1.0)
    return 0.5 * confidence + 0.3 * priority_raw + 0.2 * intent_strength


def _claim_row_count_map(claim_rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {
        str(row.get("claim_id") or "").strip(): dict(row)
        for row in claim_rows
        if str(row.get("claim_id") or "").strip()
    }


def _safe_set(value: Any) -> Tuple[str, ...]:
    if value is None:
        return tuple()
    if isinstance(value, (list, tuple)):
        return tuple(str(x).strip() for x in value if str(x).strip())
    return tuple()


def build_conflict_scores(
    *,
    conflicts: List[Dict[str, Any]],
    claim_rows: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    claim_index = _claim_row_count_map(claim_rows)
    out: List[Dict[str, Any]] = []

    for row in conflicts:
        conflict = dict(row)
        conflict_id = str(conflict.get("conflict_id") or "").strip()
        severity = str(conflict.get("severity") or "").strip()
        conflict_type = str(conflict.get("conflict_type") or "").strip()
        claim_ids = _safe_set(conflict.get("claims"))

        ranked_claims = [claim_index[cid] for cid in claim_ids if cid in claim_index]
        if not ranked_claims:
            signal = 0.5
            plugin_diversity = 0.0
            logic_diversity = 0.0
        else:
            claim_scores = [_claim_signal_score(c) for c in ranked_claims]
            signal = sum(claim_scores) / len(claim_scores)
            plugin_set = {str(c.get("plugin_id") or "").strip() for c in ranked_claims if str(c.get("plugin_id") or "").strip()}
            plugin_diversity = min(1.0, len(plugin_set) / max(1, len(ranked_claims)))
            logic_set = {str(c.get("logic_level") or "").strip() for c in ranked_claims}
            logic_diversity = min(1.0, len([x for x in logic_set if x]) / 3.0)

        conflict_level = _severity_score(severity)
        type_level = _conflict_type_score(conflict_type)
        evidence_level = (0.62 * signal + 0.38 * (plugin_diversity * 0.8 + logic_diversity * 0.2))
        raw_score = 0.58 * conflict_level + 0.22 * evidence_level + 0.20 * type_level
        score = _clamp(raw_score)

        confidence_band = "medium"
        if score >= 0.82:
            confidence_band = "high"
        elif score <= 0.38:
            confidence_band = "low"

        conflict["conflict_score"] = round(score, 6)
        conflict["conflict_score_breakdown"] = {
            "severity_score": conflict_level,
            "evidence_score": round(evidence_level, 6),
            "type_score": type_level,
            "claim_count": len(ranked_claims),
            "plugin_diversity": plugin_diversity,
            "logic_diversity": logic_diversity,
        }
        conflict["confidence_band"] = confidence_band
        if conflict_id:
            conflict["conflict_id"] = conflict_id
        out.append(conflict)

    return out
