"""StructureFinalDecisionV0: choose a single auditable structure decision."""
from __future__ import annotations

from typing import Any, Dict, List
from app.skills.nomenclature import map_structure_nomenclature
from app.skills.nomenclature_logic_splitter import split_balance_and_work_verdict


def _safe_float(v: Any) -> float:
    try:
        return float(v)
    except Exception:
        return 0.0


def _extract_trigger_tokens(trigger: str) -> List[str]:
    text = str(trigger or "").lower()
    tokens: List[str] = []
    if "self_abs" in text:
        tokens.append("比劫")
    if "released_energy" in text:
        tokens.append("食伤")
    if "backfire_risk" in text:
        tokens.append("官杀")
    if "follower" in text:
        tokens.append("财星")
    if "strong" in text:
        tokens.append("印星")
    return tokens


def build_structure_final_decision_v0(
    *,
    structure_candidates_v0: Dict[str, Any],
    work_vector: Dict[str, Any],
) -> Dict[str, Any]:
    candidates = list((structure_candidates_v0 or {}).get("candidates") or [])
    best = max(
        [c for c in candidates if isinstance(c, dict)],
        key=lambda c: _safe_float(c.get("match_score")),
        default={"name": "REGULAR_STRUCTURE", "state": "StableState", "match_score": 0.5, "reason": "fallback"},
    )
    match_score = _safe_float(best.get("match_score"))
    net_effect = str((work_vector or {}).get("net_effect") or "neutral")
    self_abs = _safe_float((structure_candidates_v0 or {}).get("self_abs"))
    released_energy = _safe_float((work_vector or {}).get("released_energy"))
    hints = list((work_vector or {}).get("morphing_hints") or [])
    runtime_cfg = dict((work_vector or {}).get("runtime_physics_config") or {})

    confidence = match_score
    if net_effect == "gain":
        confidence += 0.08
    elif net_effect == "risk":
        confidence -= 0.08
    confidence = round(max(0.05, min(0.99, confidence)), 2)

    stability_risk = "Low"
    if "[DANGEROUS_TURBULENCE]" in hints or str(best.get("state")) == "QuantumLeap":
        stability_risk = "High"
    elif released_energy > 3.0:
        stability_risk = "Medium"

    rollback_triggers: List[str] = []
    name = str(best.get("name") or "REGULAR_STRUCTURE")
    if name == "FOLLOW_WEALTH_POWER":
        rollback_triggers.append("if Self_Abs > 1.2 -> CollapseFollowerStructure")
    if name == "STRONG_STRUCTURE":
        rollback_triggers.append("if Self_Abs < 2.0 -> CollapseStrongStructure")
    if str(best.get("state")) == "QuantumLeap":
        rollback_triggers.append("if released_energy > 6.0 and backfire_risk > unlock_gain*0.5 -> InstabilityEscalation")
    if not rollback_triggers:
        rollback_triggers.append("if net_effect == risk for 2 consecutive cycles -> Re-evaluate")

    month_deity = str((structure_candidates_v0 or {}).get("month_deity") or "")
    heterogeneous_abs = _safe_float((work_vector or {}).get("guest_abs"))
    work_net = _safe_float((work_vector or {}).get("work_expectation"))
    split_verdicts = split_balance_and_work_verdict(
        self_abs=self_abs,
        work_net=work_net,
        net_effect=net_effect,
    )
    naming = map_structure_nomenclature(
        code_name=name,
        self_abs=self_abs,
        deity_axes=None,
        work_net=work_net,
        month_deity=month_deity,
        heterogeneous_abs=heterogeneous_abs,
    )
    classical_name = naming["humanized"]

    reasoning_chain = [
        f"[L1] Self_Abs={self_abs:.2f}, state={best.get('state')}",
        f"[L2] Work_Net={_safe_float((work_vector or {}).get('work_expectation')):.2f}, net_effect={net_effect}",
        f"[Result] primary_structure={classical_name}, confidence={confidence:.2f}",
    ]
    work_vectors = list((work_vector or {}).get("work_vectors") or [])
    supportive: List[str] = []
    for item in work_vectors:
        if not isinstance(item, dict):
            continue
        if _safe_float(item.get("expected_work")) > 0:
            supportive.extend([str(x) for x in (item.get("contributors") or []) if str(x)])
    core_useful = sorted(list({x for x in supportive}))[:5]
    core_obstacles = sorted(
        list({token for trigger in rollback_triggers for token in _extract_trigger_tokens(trigger)})
    )
    utility_god = core_useful or ["食伤", "财星", "官杀"]
    obstacle_god = core_obstacles or ["印星", "比劫"]
    if self_abs > 5.0:
        # 身强时禁止继续生扶，必须走克泄耗路径。
        utility_god = ["食伤", "财星", "官杀"]
        obstacle_god = sorted(list(set(obstacle_god + ["印星", "比劫"])))
    strategy_line = f"推荐岁运路径：优先泄耗（{','.join(utility_god)}）；规避生扶（{','.join(obstacle_god)})"

    climate_intensity = _safe_float(runtime_cfg.get("CLIMATE_INTENSITY"))
    climate_adjustment = {
        "intensity": round(climate_intensity, 2),
        "summary": f"调候修正强度 {round(climate_intensity, 2)}（硬修正已生效）",
    }
    if climate_intensity >= 0.8:
        climate_adjustment["summary"] = "调候修正强（约❄️/☀️ 15%量级），需优先服从季节阻力"

    return {
        "primary_structure": name,
        "primary_structure_humanized": classical_name,
        "primary_structure_status": naming["status"],
        "balance_verdict": split_verdicts["balance_verdict"],
        "work_verdict": split_verdicts["work_verdict"],
        "decision_confidence": confidence,
        "logical_reasoning_chain": reasoning_chain,
        "rollback_triggers": rollback_triggers,
        "stability_risk": stability_risk,
        "strategic_advice": {
            "core_useful_gods": utility_god,
            "core_obstacle_gods": obstacle_god,
            "recommendation": strategy_line,
        },
        "utility_god": utility_god,
        "obstacle_god": obstacle_god,
        "climate_adjustment": climate_adjustment,
    }
