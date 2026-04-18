from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple


def clone_score_map(raw: Any) -> Dict[str, float]:
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, float] = {}
    for k, v in raw.items():
        key = str(k).strip()
        if not key:
            continue
        try:
            out[key] = float(v)
        except (TypeError, ValueError):
            continue
    return out


def read_runtime_scores(physics_tensor: Dict[str, Any]) -> Dict[str, float]:
    if not isinstance(physics_tensor, dict):
        return {}
    return clone_score_map(
        physics_tensor.get("ten_gods_runtime")
        or physics_tensor.get("ten_gods_absolute")
        or physics_tensor.get("ten_gods_absolute_intensity")
        or physics_tensor.get("deity_scores")
    )


def read_base_scores(physics_tensor: Dict[str, Any]) -> Dict[str, float]:
    if not isinstance(physics_tensor, dict):
        return {}
    return clone_score_map(
        physics_tensor.get("ten_gods_base_l0")
        or physics_tensor.get("ten_gods_runtime")
        or physics_tensor.get("ten_gods_absolute")
        or physics_tensor.get("ten_gods_absolute_intensity")
        or physics_tensor.get("deity_scores")
    )


def sync_runtime_aliases(physics_tensor: Dict[str, Any], runtime_scores: Dict[str, float]) -> Dict[str, float]:
    runtime = clone_score_map(runtime_scores)
    physics_tensor["ten_gods_runtime"] = dict(runtime)
    physics_tensor["ten_gods_absolute"] = dict(runtime)
    physics_tensor["ten_gods_absolute_intensity"] = dict(runtime)
    physics_tensor["deity_scores"] = dict(runtime)
    return runtime


def build_narrative_scores(runtime_scores: Dict[str, float], will_proxy: str) -> Dict[str, float]:
    narrative = clone_score_map(runtime_scores)
    mode = str(will_proxy or "stable").strip().lower()
    if mode == "stable":
        boosted = {"正官", "七杀", "正印", "偏印", "比肩", "劫财"}
        factor = 1.15
    elif mode == "aggressive":
        boosted = {"食神", "伤官", "正财", "偏财"}
        factor = 1.25
    else:
        boosted = set()
        factor = 1.0
    if factor != 1.0:
        for god in boosted:
            if god in narrative:
                narrative[god] = round(float(narrative[god]) * factor, 2)
    return narrative


def proposal_signature(proposal: Dict[str, Any]) -> str:
    impact_ratio = float(proposal.get("impact_ratio", 0.0) or 0.0)
    significance_weight = float(proposal.get("significance_weight", 1.0) or 1.0)
    return "|".join(
        [
            str(proposal.get("plugin_id") or "").strip(),
            str(proposal.get("target_god") or "").strip(),
            f"{impact_ratio:.6f}",
            f"{significance_weight:.6f}",
            str(proposal.get("reason") or proposal.get("title") or "").strip(),
            str(proposal.get("arbiter_type") or "").strip(),
        ]
    )


def settle_modifier_proposals(
    runtime_scores: Dict[str, float],
    proposals: List[Dict[str, Any]],
) -> Tuple[Dict[str, float], Dict[str, float], List[Dict[str, Any]]]:
    runtime = clone_score_map(runtime_scores)
    ratio_totals: Dict[str, float] = {}
    applied: List[Dict[str, Any]] = []

    for proposal in proposals:
        if not isinstance(proposal, dict):
            continue
        if str(proposal.get("arbiter_type") or "").strip().lower() != "system":
            continue
        target_god = str(proposal.get("target_god") or "").strip()
        if not target_god or target_god not in runtime:
            continue
        try:
            impact_ratio = float(proposal.get("impact_ratio", 0.0) or 0.0)
            significance_weight = float(proposal.get("significance_weight", 1.0) or 1.0)
        except (TypeError, ValueError):
            continue
        ratio_applied = impact_ratio * significance_weight
        if not math.isfinite(ratio_applied) or abs(ratio_applied) <= 0.0001:
            continue
        ratio_totals[target_god] = ratio_totals.get(target_god, 0.0) + ratio_applied

    for target_god, ratio_total in ratio_totals.items():
        before = float(runtime.get(target_god, 0.0))
        after = round(before * (1.0 + ratio_total), 2)
        if not math.isfinite(after):
            continue
        runtime[target_god] = after
        applied.append(
            {
                "target_god": target_god,
                "before": before,
                "after": after,
                "ratio_total": ratio_total,
            }
        )

    return runtime, ratio_totals, applied
