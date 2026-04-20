from __future__ import annotations

from typing import Dict, List

from v17_rebirth.backend.logic.core_engine.work_path_engine import WorkPath


def resolve_effect_scores(paths: List[WorkPath]) -> Dict[str, Dict[str, float]]:
    scores: Dict[str, Dict[str, float]] = {}
    for path in paths:
        bucket = scores.setdefault(
            path.target_god,
            {
                "benefit_score": 0.0,
                "harm_score": 0.0,
                "activation_score": 0.0,
                "stability_score": 0.0,
                "net_utility": 0.0,
            },
        )
        benefit = max(path.net_effect, 0.0)
        harm = max(-path.net_effect, 0.0) + max(path.loss, 0.0)
        bucket["benefit_score"] += benefit
        bucket["harm_score"] += harm
        bucket["activation_score"] = max(bucket["activation_score"], path.activation)
        bucket["stability_score"] = max(bucket["stability_score"], path.stability)
        bucket["net_utility"] = bucket["benefit_score"] - bucket["harm_score"]
    for row in scores.values():
        for key, value in list(row.items()):
            row[key] = round(float(value or 0.0), 4)
    return scores


def pick_god_candidates(effect_scores: Dict[str, Dict[str, float]]) -> Dict[str, object]:
    ranked_use = sorted(effect_scores.items(), key=lambda item: item[1].get("net_utility", 0.0), reverse=True)
    ranked_taboo = sorted(effect_scores.items(), key=lambda item: item[1].get("harm_score", 0.0), reverse=True)

    use_candidates = [
        {"god": god, "score": row.get("net_utility", 0.0)}
        for god, row in ranked_use[:3]
        if row.get("net_utility", 0.0) > 0
    ]
    taboo_candidates = [
        {"god": god, "score": row.get("harm_score", 0.0)}
        for god, row in ranked_taboo[:3]
        if row.get("harm_score", 0.0) > 0
    ]
    dual_role = [
        {"god": god, "benefit": row.get("benefit_score", 0.0), "risk": row.get("harm_score", 0.0)}
        for god, row in effect_scores.items()
        if row.get("benefit_score", 0.0) > 0 and row.get("harm_score", 0.0) > 0
    ]
    return {
        "use_candidates": use_candidates,
        "taboo_candidates": taboo_candidates,
        "dual_role_candidates": sorted(dual_role, key=lambda item: max(item["benefit"], item["risk"]), reverse=True)[:3],
    }
