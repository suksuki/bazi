"""Blind-work evaluator for L2 semantic reasoning."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple
from app.core.config.physics_settings import resolve_physics_settings


from app.skills.relation_nodes import RelationNodeFactory

BODY_DEITIES = {"比肩", "劫财", "正印", "偏印"}
USE_DEITIES = {"食神", "伤官", "正财", "偏财", "正官", "七杀"}
ETA_MAP = {
    "穿": 0.95,
    "冲": 0.9,
    "刑": 0.75,
    "害": 0.7,
    "破": 0.65,
    "合": 0.85,
}
TOMB_BRANCHES = {"辰", "戌", "丑", "未"}
BODY_SENSITIVITY = {
    "禄神": 1.2,
    "正印": 0.8,
    "偏印": 0.8,
    "比肩": 0.5,
    "劫财": 0.5,
}
DEITY_TO_ELEMENT = {
    "比肩": "木",
    "劫财": "木",
    "食神": "火",
    "伤官": "火",
    "正财": "土",
    "偏财": "土",
    "正官": "金",
    "七杀": "金",
    "正印": "水",
    "偏印": "水",
}


def _extract_branches(detail: str) -> List[str]:
    return [ch for ch in str(detail or "") if ch in TOMB_BRANCHES]


def _unlock_confidence_by_abs(striker_abs: float) -> float:
    if striker_abs <= 0.5:
        return 0.2
    if striker_abs >= 5.0:
        return 0.95
    # piecewise linear mapping between 0.5 and 5.0
    ratio = (striker_abs - 0.5) / 4.5
    return round(0.2 + ratio * 0.75, 4)
def _sum_abs(deity_axes: Dict[str, Dict[str, float]], deities: set[str]) -> float:
    return sum(float((deity_axes.get(name) or {}).get("absolute_energy", 0.0) or 0.0) for name in deities)





def _pick_top_deity(deity_axes: Dict[str, Dict[str, float]], candidates: List[str]) -> str:
    best = ""
    best_abs = -1.0
    for name in candidates:
        val = float((deity_axes.get(name) or {}).get("absolute_energy", 0.0) or 0.0)
        if val > best_abs:
            best_abs = val
            best = name
    return best or (candidates[0] if candidates else "")


def _calculate_net_effect(
    *,
    released_energy: float,
    eta: float,
    body_abs: float,
    use_abs: float,
    base_risk: float,
    high_imbalance_risk: float,
) -> Tuple[float, float, float, float, str]:
    unlock_gain = released_energy * eta
    risk_factor = base_risk
    # 体弱用强时，提高反噬风险：小体量承接高释放，最容易“得财伤身”。
    if body_abs < 1.5 and released_energy > 4.0:
        risk_factor = high_imbalance_risk
    elif body_abs > 0 and use_abs > 0 and (use_abs / max(body_abs, 0.0001)) > 2.0:
        risk_factor = max(risk_factor, 0.28)
    backfire_risk = released_energy * risk_factor
    expected_work = unlock_gain - backfire_risk
    if expected_work > 0.3:
        net_effect = "gain"
    elif expected_work < -0.3:
        net_effect = "risk"
    else:
        net_effect = "neutral"
    return round(unlock_gain, 4), round(backfire_risk, 4), round(expected_work, 4), round(risk_factor, 4), net_effect


def evaluate_blind_work(metadata: Dict[str, Any], physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    conflict_points = (((metadata or {}).get("conflict_matrix") or {}).get("points") or [])
    deity_axes = ((physics_tensor or {}).get("deity_energy_axes") or {})
    runtime_cfg = (((physics_tensor or {}).get("meta") or {}).get("runtime_physics_config") or {})
    settings = resolve_physics_settings(runtime_cfg)
    body_abs = round(_sum_abs(deity_axes, BODY_DEITIES), 4)
    use_abs = round(_sum_abs(deity_axes, USE_DEITIES), 4)
    tomb_lock_rate = max(
        0.0,
        min(1.0, float(settings.get("MANGPAI_ETA_TOMB", settings.get("TOMB_LOCK_RATE", 0.9)))),
    )
    body_labels = ["比肩", "劫财", "正印", "偏印"]
    use_labels = ["食神", "伤官", "正财", "偏财", "正官", "七杀"]
    top_body = _pick_top_deity(deity_axes, body_labels)
    top_use = _pick_top_deity(deity_axes, use_labels)
    climate_factors = ((((physics_tensor or {}).get("meta") or {}).get("climate_adjustment") or {}).get("factors") or {})
    work_vectors: List[Dict[str, Any]] = []
    damage_nodes: Dict[str, float] = {k: 0.0 for k in body_labels}

    for point in conflict_points:
        if not isinstance(point, dict):
            continue
        detail = str(point.get("detail") or "")
        
        rule_node = RelationNodeFactory.get_rule_from_detail(detail)
        relation = rule_node.relation_key
        tomb_branches = _extract_branches(detail)

        evaluator_result = rule_node.apply_evaluator(
            detail=detail,
            base_eta=ETA_MAP.get(relation, 0.8),
            settings=settings,
            tomb_branches=tomb_branches
        )
        eta = evaluator_result.get("eta", ETA_MAP.get(relation, 0.8))
        unlock_source = evaluator_result.get("unlock_source", "")
        direction = "Host->Guest" if body_abs >= use_abs else "Guest->Host"
        host_abs = body_abs if body_abs >= use_abs else use_abs
        guest_abs = use_abs if body_abs >= use_abs else body_abs
        source_abs = float((deity_axes.get(top_body) or {}).get("absolute_energy", 0.0) or 0.0)
        target_abs = float((deity_axes.get(top_use) or {}).get("absolute_energy", 0.0) or 0.0)
        source_element = DEITY_TO_ELEMENT.get(top_body, "")
        climate_factor = float((climate_factors.get(source_element, 1.0) if isinstance(climate_factors, dict) else 1.0) or 1.0)
        abs_contribution = source_abs * eta * climate_factor * 0.1
        base_energy = max((host_abs * guest_abs) / 10.0, abs_contribution)
        potential_energy_locked = base_energy * tomb_lock_rate
        residual_energy = base_energy * (1.0 - tomb_lock_rate)
        
        striker_abs = max(host_abs, guest_abs)
        unlock_confidence = _unlock_confidence_by_abs(striker_abs) if unlock_source else 0.0
        released_energy = residual_energy + (potential_energy_locked * unlock_confidence if unlock_source else 0.0)
        unlock_gain_raw = potential_energy_locked * unlock_confidence if unlock_source else 0.0
        tomb_state = "Released" if unlock_source else "Locked"
        unlock_failed = bool(unlock_source) and unlock_confidence < 0.35
        unlock_gain, backfire_risk, expected_work, risk_factor, net_effect = _calculate_net_effect(
            released_energy=released_energy,
            eta=eta,
            body_abs=body_abs,
            use_abs=use_abs,
            base_risk=settings["BASE_BACKFIRE_RISK"],
            high_imbalance_risk=settings["HIGH_IMBALANCE_RISK"],
        )
        saturation_penalty = 0.0
        if source_abs > 15.0:
            saturation_penalty = (source_abs - 15.0) * 0.2 * backfire_risk
        backfire_risk = backfire_risk + saturation_penalty
        expected_work = unlock_gain - backfire_risk
        if expected_work > 0.3:
            net_effect = "gain"
        elif expected_work < -0.3:
            net_effect = "risk"
        else:
            net_effect = "neutral"
        is_micro_path = expected_work > 0 and expected_work < float(settings.get("WORK_MIN_THRESHOLD", 0.5))
        momentum_direction = "REBOUND" if backfire_risk >= unlock_gain else "FORWARD"
        rebound_work = max(0.0, backfire_risk - unlock_gain)
        source_deity = top_body
        vector_damage = {"node_id": source_deity, "delta_abs": 0.0, "critical_stress": False}
        if momentum_direction == "REBOUND" and rebound_work > 0:
            source_factor = float(BODY_SENSITIVITY.get(source_deity, 0.5))
            frontline_damage = rebound_work * source_factor
            damage_nodes[source_deity] = damage_nodes.get(source_deity, 0.0) + frontline_damage
            vector_damage["delta_abs"] = round(frontline_damage, 4)
            for node in body_labels:
                if node == source_deity:
                    continue
                collateral_factor = float(BODY_SENSITIVITY.get(node, 0.5)) * 0.35
                damage_nodes[node] = damage_nodes.get(node, 0.0) + (rebound_work * collateral_factor)
        abs_delta = expected_work
        work_vectors.append(
            {
                "type": relation,
                "detail": detail or "未命名冲合",
                "direction": direction,
                "eta": eta,
                "source_deity": source_deity,
                "target_deity": top_use,
                "source_abs": round(source_abs, 4),
                "target_abs": round(target_abs, 4),
                "climate_factor": round(climate_factor, 4),
                "abs_contribution": round(abs_contribution, 4),
                "host_abs": round(host_abs, 4),
                "guest_abs": round(guest_abs, 4),
                "tomb_state": tomb_state,
                "tomb_lock_rate": round(tomb_lock_rate, 4),
                "potential_energy_locked": round(potential_energy_locked, 4),
                "unlock_source": unlock_source,
                "unlock_confidence": round(unlock_confidence, 4),
                "unlock_failed": unlock_failed,
                "released_energy": round(released_energy, 4),
                "unlock_gain": round(unlock_gain_raw, 4),
                "backfire_risk": backfire_risk,
                "momentum_direction": momentum_direction,
                "is_micro_path": is_micro_path,
                "saturation_penalty": round(saturation_penalty, 4),
                "body_damage_estimation": vector_damage,
                "risk_factor": risk_factor,
                "expected_work": round(expected_work, 4),
                "abs_delta": abs_delta,
                "net_effect": net_effect,
            }
        )

    total_gain = round(sum(float(v.get("unlock_gain", 0.0) or 0.0) for v in work_vectors), 4)
    total_risk = round(sum(float(v.get("backfire_risk", 0.0) or 0.0) for v in work_vectors), 4)
    total_work = round(sum(float(v.get("expected_work", 0.0) or 0.0) for v in work_vectors), 4)
    total_locked = round(sum(float(v.get("potential_energy_locked", 0.0) or 0.0) for v in work_vectors), 4)
    total_released = round(sum(float(v.get("released_energy", 0.0) or 0.0) for v in work_vectors), 4)
    verdict = "取财有道" if total_work > 0 else "劳而无功"
    risk_ratio = round((total_risk / max(total_gain, 0.0001)), 4) if total_gain > 0 else 1.0
    morphing_hints: List[str] = []
    if total_work > 0 and total_released > 5.0:
        morphing_hints.append("[POTENTIAL_FOLLOWER_STRUCTURE]")
    if total_risk > total_gain * 0.5 and total_gain > 0:
        morphing_hints.append("[DANGEROUS_TURBULENCE]")
    if any(bool(v.get("unlock_failed", False)) for v in work_vectors):
        morphing_hints.append("[BROKEN_LINK]")
    rebound_count = sum(1 for v in work_vectors if v.get("momentum_direction") == "REBOUND")
    damage_payload_nodes: List[Dict[str, Any]] = []
    total_damage = 0.0
    for node in body_labels:
        node_abs = float((deity_axes.get(node) or {}).get("absolute_energy", 0.0) or 0.0)
        delta = float(damage_nodes.get(node, 0.0) or 0.0)
        ratio = (delta / node_abs) if node_abs > 0 else 0.0
        critical = ratio > 0.4
        if critical:
            morphing_hints.append("[CRITICAL_STRESS]")
        damage_payload_nodes.append(
            {
                "node_id": node,
                "delta_abs": round(delta, 4),
                "source_abs": round(node_abs, 4),
                "damage_ratio": round(ratio, 4),
                "critical_stress": critical,
            }
        )
        total_damage += delta
    collapse_ratio = (total_damage / body_abs) if body_abs > 0 else 0.0
    collapse_triggered = collapse_ratio >= 0.7
    morphing_hints = list(dict.fromkeys(morphing_hints))
    return {
        "body_labels": body_labels,
        "use_labels": use_labels,
        "host_abs": body_abs,
        "guest_abs": use_abs,
        "body_use_ratio": round((body_abs / use_abs), 4) if use_abs > 0 else 0.0,
        "work_vectors": work_vectors,
        "potential_energy_locked": total_locked,
        "released_energy": total_released,
        "unlock_gain": total_gain,
        "backfire_risk": total_risk,
        "risk_ratio": risk_ratio,
        "net_effect": "gain" if total_work > 0.3 else ("risk" if total_work < -0.3 else "neutral"),
        "work_expectation": total_work,
        "llm_hint": verdict,
        "morphing_hints": morphing_hints,
        "body_damage_estimation": {
            "nodes": damage_payload_nodes,
            "total_damage": round(total_damage, 4),
            "collapse_ratio": round(collapse_ratio, 4),
            "collapse_triggered": collapse_triggered,
        },
        "topology_audit": {
            "rebound_count": rebound_count,
            "momentum_directions": [str(v.get("momentum_direction", "FORWARD")) for v in work_vectors],
        },
        "runtime_physics_config": settings,
    }


def build_mangpai_interaction_hub_overlay(work_vector: Dict[str, Any]) -> Dict[str, Any]:
    """宾主红利写入 work_vector 时，同步生成可并入 interaction_hub 的审计切片。"""
    raw = (work_vector or {}).get("causal_dividend_index")
    if not isinstance(raw, (int, float)):
        return {}
    v = float(raw)
    return {
        "causal_dividend_index": round(v, 4),
        "sovereignty_dominant": v > 0.8,
    }
