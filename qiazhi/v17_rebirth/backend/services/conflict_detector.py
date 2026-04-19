from __future__ import annotations

from typing import Any, Dict, List, Tuple


def _intent_sign(claim: Dict[str, Any]) -> int:
    vector = claim.get("intent_vector") if isinstance(claim.get("intent_vector"), dict) else {}
    values = []
    for raw in vector.values():
        try:
            values.append(float(raw))
        except (TypeError, ValueError):
            continue
    if not values:
        return 0
    score = sum(values)
    if score > 0:
        return 1
    if score < 0:
        return -1
    return 0


def _logic_rank(level: str) -> int:
    normalized = str(level or "").strip().upper()
    order = {"L1": 3, "L2": 2, "L3": 1}
    return order.get(normalized, 0)


def _conflict_row(*, conflict_type: str, severity: str, claims: List[Dict[str, Any]], why_conflict: str, recommended_arbiter: str, anchor: str = "") -> Dict[str, Any]:
    claim_ids = [str(c.get("claim_id") or "").strip() for c in claims if str(c.get("claim_id") or "").strip()]
    return {
        "conflict_id": f"{conflict_type}:{anchor or '|'.join(claim_ids[:2])}",
        "conflict_type": conflict_type,
        "severity": severity,
        "claims": claim_ids,
        "plugins": [str(c.get("plugin_id") or "").strip() for c in claims],
        "target_god": str(next((c.get("target_god") for c in claims if str(c.get("target_god") or "").strip()), "") or ""),
        "why_conflict": why_conflict,
        "recommended_arbiter": recommended_arbiter,
    }


def _claim_rank_tuple(claim: Dict[str, Any]) -> Tuple[float, float, int, str]:
    try:
        priority = float(claim.get("priority", 0.0) or 0.0)
    except (TypeError, ValueError):
        priority = 0.0
    try:
        confidence = float(claim.get("confidence", 0.0) or 0.0)
    except (TypeError, ValueError):
        confidence = 0.0
    logic = _logic_rank(str(claim.get("logic_level") or ""))
    claim_id = str(claim.get("claim_id") or "").strip()
    return (priority, confidence, logic, claim_id)


def detect_claim_conflicts(claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    seen: set[Tuple[str, str]] = set()

    # Rule 1: same_event_duplicate
    by_event: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    for claim in claims:
        source_event = str(claim.get("source_event") or "").strip()
        target_god = str(claim.get("target_god") or "").strip()
        if not source_event:
            continue
        by_event.setdefault((source_event, target_god), []).append(claim)
    for (source_event, target_god), rows in by_event.items():
        if len(rows) < 2:
            continue
        key = ("same_event_duplicate", f"{source_event}|{target_god}")
        if key in seen:
            continue
        seen.add(key)
        out.append(
            _conflict_row(
                conflict_type="same_event_duplicate",
                severity="P3",
                claims=rows[:4],
                why_conflict="同一 source_event 被多个插件重复解释，存在重复处罚或重复增益风险。",
                recommended_arbiter="system",
                anchor=f"{source_event}|{target_god}",
            )
        )

    # Rule 1.5: pattern family exclusivity
    by_exclusive: Dict[str, List[Dict[str, Any]]] = {}
    for claim in claims:
        claim_type = str(claim.get("claim_type") or "").strip()
        entity_scope = str(claim.get("entity_scope") or "").strip()
        ex_key = str(claim.get("exclusivity_key") or "").strip()
        if claim_type != "pattern_candidate" or entity_scope != "pattern" or not ex_key:
            continue
        by_exclusive.setdefault(ex_key, []).append(claim)
    for ex_key, rows in by_exclusive.items():
        unique_plugins = {str(c.get("plugin_id") or "").strip() for c in rows}
        if len(rows) < 2 or len(unique_plugins) < 2:
            continue
        key = ("pattern_family_exclusive", ex_key)
        if key in seen:
            continue
        seen.add(key)
        out.append(
            _conflict_row(
                conflict_type="pattern_family_exclusive",
                severity="P1",
                claims=rows[:6],
                why_conflict="格局候选属于同一互斥家族，不能在同轮内同时成立。",
                recommended_arbiter="user",
                anchor=ex_key,
            )
        )

    # Rule 2 & 3 on pairwise claims
    for idx, left in enumerate(claims):
        left_target = str(left.get("target_god") or "").strip()
        if not left_target:
            continue
        for right in claims[idx + 1 :]:
            right_target = str(right.get("target_god") or "").strip()
            if left_target != right_target or not right_target:
                continue
            left_sign = _intent_sign(left)
            right_sign = _intent_sign(right)
            if left_sign == 0 or right_sign == 0 or left_sign == right_sign:
                continue
            pair_anchor = "|".join(sorted([str(left.get("claim_id") or ""), str(right.get("claim_id") or "")]))
            key = ("same_target_opposite_sign", pair_anchor)
            if key not in seen:
                seen.add(key)
                out.append(
                    _conflict_row(
                        conflict_type="same_target_opposite_sign",
                        severity="P2",
                        claims=[left, right],
                        why_conflict="同一 target_god 在同轮内收到相反方向的位移主张。",
                        recommended_arbiter="llm",
                        anchor=pair_anchor,
                    )
                )
            if _logic_rank(str(left.get("logic_level") or "")) != _logic_rank(str(right.get("logic_level") or "")):
                layer_key = ("cross_layer_override", pair_anchor)
                if layer_key in seen:
                    continue
                seen.add(layer_key)
                out.append(
                    _conflict_row(
                        conflict_type="cross_layer_override",
                        severity="P1",
                        claims=[left, right],
                        why_conflict="不同 logic_level 对同一目标神提出相反主张，存在跨层解释权冲突。",
                        recommended_arbiter="user",
                        anchor=pair_anchor,
                    )
                )

    return out


def recommend_conflict_resolutions(claims: List[Dict[str, Any]], conflicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    claim_index = {
        str(claim.get("claim_id") or "").strip(): claim
        for claim in claims
        if str(claim.get("claim_id") or "").strip()
    }
    out: List[Dict[str, Any]] = []

    for conflict in conflicts:
        conflict_type = str(conflict.get("conflict_type") or "").strip()
        if conflict_type not in {"same_event_duplicate", "pattern_family_exclusive"}:
            continue
        claim_ids = [
            str(cid).strip()
            for cid in (conflict.get("claims") or [])
            if str(cid).strip() and str(cid).strip() in claim_index
        ]
        if len(claim_ids) < 2:
            continue
        rows = [claim_index[cid] for cid in claim_ids]
        winner = max(rows, key=_claim_rank_tuple)
        winner_id = str(winner.get("claim_id") or "").strip()
        dropped = [str(row.get("claim_id") or "").strip() for row in rows if str(row.get("claim_id") or "").strip() != winner_id]
        out.append(
            {
                "resolution_id": f"resolve:{str(conflict.get('conflict_id') or '').strip()}",
                "conflict_id": str(conflict.get("conflict_id") or "").strip(),
                "conflict_type": conflict_type,
                "status": "suggested",
                "resolved_by": "system",
                "applied_to_settlement": False,
                "winner_claim_id": winner_id,
                "dropped_claim_ids": dropped,
                "reason": (
                    "同一 source_event 的重复主张已归并，建议保留优先级/置信度更高的一条。"
                    if conflict_type == "same_event_duplicate"
                    else "同一格局家族的候选互斥，建议先保留优先级/置信度更高的一条。"
                ),
                "policy": "keep_highest_priority_claim",
            }
        )

    return out
