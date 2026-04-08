"""StructureResolverV0: infer structure candidates from L1+L2 signals."""
from __future__ import annotations

from typing import Any, Dict, List


def _safe_float(v: Any) -> float:
    try:
        return float(v)
    except Exception:
        return 0.0


def resolve_structure_candidates_v0(
    *,
    physics_tensor: Dict[str, Any],
    work_vector: Dict[str, Any],
) -> Dict[str, Any]:
    deity_axes = ((physics_tensor or {}).get("deity_energy_axes") or {})
    deity_components = ((physics_tensor or {}).get("deity_components") or {})
    morphing_hints = list((work_vector or {}).get("morphing_hints") or [])
    net_effect = str((work_vector or {}).get("net_effect") or "neutral")
    released_energy = _safe_float((work_vector or {}).get("released_energy"))

    self_abs = _safe_float((deity_axes.get("比肩") or {}).get("absolute_energy")) + _safe_float(
        (deity_axes.get("劫财") or {}).get("absolute_energy")
    )
    root_score = _safe_float((deity_components.get("比肩") or {}).get("root_score")) + _safe_float(
        (deity_components.get("劫财") or {}).get("root_score")
    )

    candidates: List[Dict[str, Any]] = []
    stable_score = 0.0
    follower_score = 0.0
    leap_score = 0.0

    # A) 从势/从财官倾向
    if self_abs < 0.5 and net_effect == "gain":
        follower_score = 0.82
        candidates.append(
            {
                "name": "FOLLOW_WEALTH_POWER",
                "state": "CollapsedState",
                "match_score": follower_score,
                "morphing_hints": morphing_hints,
                "reason": f"Self_Abs={self_abs:.2f} and net_effect=gain",
            }
        )

    # B) 身强结构倾向
    if self_abs > 4.0 and root_score > 1.5:
        stable_score = 0.78
        candidates.append(
            {
                "name": "STRONG_STRUCTURE",
                "state": "StableState",
                "match_score": stable_score,
                "morphing_hints": morphing_hints,
                "reason": f"Self_Abs={self_abs:.2f}, Root_Score={root_score:.2f}",
            }
        )

    # C) 跃迁态（震荡/开库）
    if "[DANGEROUS_TURBULENCE]" in morphing_hints or released_energy > 0:
        leap_score = 0.86 if "[DANGEROUS_TURBULENCE]" in morphing_hints else 0.68
        candidates.append(
            {
                "name": "QUANTUM_LEAP",
                "state": "QuantumLeap",
                "match_score": leap_score,
                "morphing_hints": morphing_hints,
                "reason": f"released_energy={released_energy:.2f}, hints={','.join(morphing_hints)}",
            }
        )

    if not candidates:
        stable_score = 0.55
        candidates.append(
            {
                "name": "REGULAR_STRUCTURE",
                "state": "StableState",
                "match_score": stable_score,
                "morphing_hints": morphing_hints,
                "reason": "No collapse or leap signal detected.",
            }
        )

    total = max(stable_score + follower_score + leap_score, 0.0001)
    hud = {
        "stable_pct": round((stable_score / total) * 100, 2),
        "follower_pct": round((follower_score / total) * 100, 2),
        "leap_pct": round((leap_score / total) * 100, 2),
    }
    return {
        "self_abs": round(self_abs, 4),
        "root_score": round(root_score, 4),
        "candidates": candidates,
        "hud": hud,
    }
