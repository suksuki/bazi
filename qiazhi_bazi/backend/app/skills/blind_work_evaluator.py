"""Blind-work evaluator for L2 semantic reasoning."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple
from app.core.config.physics_settings import resolve_physics_settings


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
def _sum_abs(deity_axes: Dict[str, Dict[str, float]], deities: set[str]) -> float:
    return sum(float((deity_axes.get(name) or {}).get("absolute_energy", 0.0) or 0.0) for name in deities)


def _relation_type(detail: str) -> str:
    for key in ("穿", "冲", "刑", "害", "破", "合"):
        if key in detail:
            return key
    return "冲"


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
    work_vectors: List[Dict[str, Any]] = []

    for point in conflict_points:
        if not isinstance(point, dict):
            continue
        detail = str(point.get("detail") or "")
        relation = _relation_type(detail)
        eta = ETA_MAP.get(relation, 0.8)
        direction = "Host->Guest" if body_abs >= use_abs else "Guest->Host"
        host_abs = body_abs if body_abs >= use_abs else use_abs
        guest_abs = use_abs if body_abs >= use_abs else body_abs
        released_energy = (host_abs * guest_abs) / 10.0
        unlock_gain, backfire_risk, expected_work, risk_factor, net_effect = _calculate_net_effect(
            released_energy=released_energy,
            eta=eta,
            body_abs=body_abs,
            use_abs=use_abs,
            base_risk=settings["BASE_BACKFIRE_RISK"],
            high_imbalance_risk=settings["HIGH_IMBALANCE_RISK"],
        )
        abs_delta = expected_work
        work_vectors.append(
            {
                "type": relation,
                "detail": detail or "未命名冲合",
                "direction": direction,
                "eta": eta,
                "host_abs": round(host_abs, 4),
                "guest_abs": round(guest_abs, 4),
                "released_energy": round(released_energy, 4),
                "unlock_gain": unlock_gain,
                "backfire_risk": backfire_risk,
                "risk_factor": risk_factor,
                "expected_work": round(expected_work, 4),
                "abs_delta": abs_delta,
                "net_effect": net_effect,
            }
        )

    total_gain = round(sum(float(v.get("unlock_gain", 0.0) or 0.0) for v in work_vectors), 4)
    total_risk = round(sum(float(v.get("backfire_risk", 0.0) or 0.0) for v in work_vectors), 4)
    total_work = round(sum(float(v.get("expected_work", 0.0) or 0.0) for v in work_vectors), 4)
    verdict = "取财有道" if total_work > 0 else "劳而无功"
    risk_ratio = round((total_risk / max(total_gain, 0.0001)), 4) if total_gain > 0 else 1.0
    return {
        "host_abs": body_abs,
        "guest_abs": use_abs,
        "body_use_ratio": round((body_abs / use_abs), 4) if use_abs > 0 else 0.0,
        "work_vectors": work_vectors,
        "unlock_gain": total_gain,
        "backfire_risk": total_risk,
        "risk_ratio": risk_ratio,
        "net_effect": "gain" if total_work > 0.3 else ("risk" if total_work < -0.3 else "neutral"),
        "work_expectation": total_work,
        "llm_hint": verdict,
        "runtime_physics_config": settings,
    }
