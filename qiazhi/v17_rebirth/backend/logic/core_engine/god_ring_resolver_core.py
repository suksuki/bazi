from __future__ import annotations

from typing import Any, Dict, Iterable, List

from v17_rebirth.backend.logic.core_engine.effect_resolver import pick_god_candidates, resolve_effect_scores
from v17_rebirth.backend.logic.core_engine.flux_solver import solve_dynamic_flux
from v17_rebirth.backend.logic.core_engine.pillar_graph_kernel import build_six_pillar_graph
from v17_rebirth.backend.logic.core_engine.work_path_engine import build_work_paths, collect_effect_maps


def resolve_god_ring_core(
    *,
    four_pillars: Dict[str, str],
    deity_scores: Dict[str, float],
    luck_pillar: str = "",
    flow_pillar: str = "",
    decision_rows: Iterable[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    graph = build_six_pillar_graph(
        four_pillars=four_pillars,
        luck_pillar=luck_pillar,
        flow_pillar=flow_pillar,
    )
    paths = build_work_paths(
        graph=graph,
        deity_scores=deity_scores,
        decision_rows=decision_rows or [],
    )
    positive, negative = collect_effect_maps(decision_rows or [])
    effect_scores = resolve_effect_scores(paths)
    flux_meta = solve_dynamic_flux(
        paths=paths,
        deity_scores=deity_scores,
        effect_scores=effect_scores,
        graph=graph,
        max_depth=3,
    )
    candidates = pick_god_candidates(effect_scores)
    path_family_profile = _build_path_family_profile(paths)
    path_role_profile = _build_path_role_profile(paths)
    path_type_profile = _build_path_type_profile(paths)
    top_use = candidates["use_candidates"][0]["score"] if candidates["use_candidates"] else 0.0
    evidence_count = len([path for path in paths if path.path_type != "static_basis"])
    confidence = min(0.94, 0.54 + float(top_use) * 0.33 + min(0.12, evidence_count * 0.02))
    return {
        "graph_meta": {
            "node_count": len(graph.nodes),
            "edge_count": len(graph.edges),
            "position_weights": dict(graph.position_weights),
            "distance_weights": dict(graph.distance_weights),
            "positive_targets": {key: round(value, 4) for key, value in positive.items()},
            "negative_targets": {key: round(value, 4) for key, value in negative.items()},
            "path_family_profile": path_family_profile,
            "path_role_profile": path_role_profile,
            "path_type_profile": path_type_profile,
            "flux_enabled": bool(flux_meta.get("enabled")),
            "flux_edge_count": int(flux_meta.get("edge_count") or 0),
            "flux_chain_count": int(flux_meta.get("chain_count") or 0),
            "flux_seed_count": int(flux_meta.get("seed_count") or 0),
            "flux_sink_count": len(flux_meta.get("sink_summary") or {}),
            "flux_node_edge_count": int(flux_meta.get("node_edge_count") or 0),
            "flux_node_chain_count": int(flux_meta.get("node_chain_count") or 0),
            "flux_projected_chain_count": int(flux_meta.get("projected_chain_count") or 0),
            "flux_interaction_count": int(flux_meta.get("interaction_count") or 0),
            "flux_tension_pair_count": int(flux_meta.get("tension_pair_count") or 0),
        },
        "path_count": len(paths),
        "paths": [path.__dict__ for path in paths[:16]],
        "effect_scores": effect_scores,
        "flux_meta": flux_meta,
        **candidates,
        "confidence": round(confidence, 4),
        "mode": "six_pillar_spacetime_core",
    }


def _build_path_family_profile(paths: Iterable[Any]) -> Dict[str, Dict[str, float | int]]:
    family_profile: Dict[str, Dict[str, float | int]] = {}
    for path in paths:
        family = str(getattr(path, "path_family", "dynamic_work") or "dynamic_work").strip().lower() or "dynamic_work"
        family_entry = family_profile.setdefault(
            family,
            {"count": 0, "net_utility": 0.0, "benefit": 0.0, "harm": 0.0, "activation": 0.0, "stability": 0.0},
        )
        net_effect = float(getattr(path, "net_effect", 0.0) or 0.0)
        activation = float(getattr(path, "activation", 0.0) or 0.0)
        stability = float(getattr(path, "stability", 0.0) or 0.0)
        loss = float(getattr(path, "loss", 0.0) or 0.0)
        family_entry["count"] = int(family_entry["count"]) + 1
        family_entry["net_utility"] = float(family_entry["net_utility"]) + net_effect
        family_entry["benefit"] = float(family_entry["benefit"]) + max(net_effect, 0.0)
        family_entry["harm"] = float(family_entry["harm"]) + max(-net_effect, 0.0) + max(loss, 0.0)
        family_entry["activation"] = float(family_entry["activation"]) + activation
        family_entry["stability"] = float(family_entry["stability"]) + stability
    return {
        key: {
            "count": int(value["count"]),
            "net_utility": round(float(value["net_utility"]), 4),
            "benefit": round(float(value["benefit"]), 4),
            "harm": round(float(value["harm"]), 4),
            "activation": round(float(value["activation"]) / max(1, int(value["count"])), 4),
            "stability": round(float(value["stability"]) / max(1, int(value["count"])), 4),
        }
        for key, value in family_profile.items()
    }


def _build_path_role_profile(paths: Iterable[Any]) -> Dict[str, Dict[str, float | int]]:
    role_profile: Dict[str, Dict[str, float | int]] = {}
    for path in paths:
        role = str(getattr(path, "path_role", "unknown") or "unknown").strip().lower() or "unknown"
        role_entry = role_profile.setdefault(
            role,
            {"count": 0, "count_benefit": 0, "count_harm": 0, "net_utility": 0.0, "avg_abs_utility": 0.0, "abs_utility": 0.0},
        )
        net_effect = float(getattr(path, "net_effect", 0.0) or 0.0)
        abs_utility = abs(net_effect)
        role_entry["count"] = int(role_entry["count"]) + 1
        if net_effect >= 0:
            role_entry["count_benefit"] = int(role_entry["count_benefit"]) + 1
        else:
            role_entry["count_harm"] = int(role_entry["count_harm"]) + 1
        role_entry["net_utility"] = float(role_entry["net_utility"]) + net_effect
        role_entry["abs_utility"] = float(role_entry["abs_utility"]) + abs_utility
        role_entry["avg_abs_utility"] = round(float(role_entry["abs_utility"]) / max(1, int(role_entry["count"])), 4)
    return {
        key: {
            "count": int(value["count"]),
            "count_benefit": int(value["count_benefit"]),
            "count_harm": int(value["count_harm"]),
            "net_utility": round(float(value["net_utility"]), 4),
            "avg_abs_utility": round(float(value["avg_abs_utility"]), 4),
        }
        for key, value in role_profile.items()
    }


def _build_path_type_profile(paths: Iterable[Any]) -> Dict[str, int]:
    type_profile: Dict[str, int] = {}
    for path in paths:
        path_type = str(getattr(path, "path_type", "dynamic_work") or "dynamic_work").strip() or "dynamic_work"
        type_profile[path_type] = int(type_profile.get(path_type, 0)) + 1
    return type_profile
