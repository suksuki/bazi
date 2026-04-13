"""终判 / 压测：结构候选与 primary 字段由 L2 法典（pattern_thresholds）驱动。"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.logic.patterns.l2_summary import affinity_for_pattern_row, l2_result_summary_zh, sanitize_pattern_headline_zh
from app.skills.structure_final_decision import build_structure_final_decision_v0


def _safe_float(v: Any) -> float:
    try:
        return float(v)
    except Exception:
        return 0.0


def resolve_structure_candidates_l2(
    *,
    physics_tensor: Dict[str, Any],
    work_vector: Dict[str, Any],
) -> Dict[str, Any]:
    """返回与终判 ``structure_candidates`` 同形对象；candidates 来自 ``meta.pattern_thresholds``。"""
    deity_axes = ((physics_tensor or {}).get("deity_energy_axes") or {})
    deity_components = ((physics_tensor or {}).get("deity_components") or {})
    morphing_hints = list((work_vector or {}).get("morphing_hints") or [])

    self_abs = _safe_float((deity_axes.get("比肩") or {}).get("absolute_energy")) + _safe_float(
        (deity_axes.get("劫财") or {}).get("absolute_energy")
    )
    root_score = _safe_float((deity_components.get("比肩") or {}).get("root_score")) + _safe_float(
        (deity_components.get("劫财") or {}).get("root_score")
    )

    meta = (physics_tensor or {}).get("meta") or {}
    rows = [r for r in (meta.get("pattern_thresholds") or []) if isinstance(r, dict)]

    candidates: List[Dict[str, Any]] = []
    for r in rows:
        pid = str(r.get("pattern_id") or "").strip()
        if not pid:
            continue
        aff = affinity_for_pattern_row(r)
        candidates.append(
            {
                "name": pid,
                "state": "ManifestHit",
                "match_score": aff if aff > 0 else 1e-6,
                "morphing_hints": morphing_hints,
                "reason": f"L2 pattern_id={pid} affinity={aff:.4f}",
            }
        )

    if not candidates:
        candidates.append(
            {
                "name": "REGULAR_STRUCTURE",
                "state": "StableState",
                "match_score": 0.5,
                "morphing_hints": morphing_hints,
                "reason": "L2 pattern_thresholds empty (no manifest hit).",
            }
        )

    return {
        "self_abs": round(self_abs, 4),
        "root_score": round(root_score, 4),
        "candidates": candidates,
        "hud": {"stable_pct": 0.0, "follower_pct": 0.0, "leap_pct": 0.0},
    }


def apply_l2_primary_to_final_decision(physics_tensor: Dict[str, Any], final_decision: Dict[str, Any]) -> None:
    """用 ``meta.l2_pattern_result_summary_v1`` / ``pattern_thresholds`` 覆盖 primary_*。"""
    meta = (physics_tensor or {}).get("meta") or {}
    rows = [r for r in (meta.get("pattern_thresholds") or []) if isinstance(r, dict)]
    summary = str(meta.get("l2_pattern_result_summary_v1") or "").strip()
    if not summary and rows:
        summary = l2_result_summary_zh(rows)
    summary = sanitize_pattern_headline_zh(summary if summary else "常规格")
    if summary != "常规格":
        final_decision["primary_structure_humanized"] = summary
        if rows:
            top = max(rows, key=affinity_for_pattern_row)
            pid = str(top.get("pattern_id") or "").strip()
            if pid:
                final_decision["primary_structure"] = pid
        return
    final_decision["primary_structure"] = "REGULAR_NO_SIGNIFICANT_PATTERN"
    final_decision["primary_structure_humanized"] = "常规格"


def build_structure_bundle_with_l2(
    *,
    physics_tensor: Dict[str, Any],
    work_vector: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    structure_l2 = resolve_structure_candidates_l2(physics_tensor=physics_tensor, work_vector=work_vector)
    final_decision = build_structure_final_decision_v0(
        structure_candidates_v0=structure_l2,
        work_vector=work_vector,
    )
    apply_l2_primary_to_final_decision(physics_tensor, final_decision)
    return structure_l2, final_decision
