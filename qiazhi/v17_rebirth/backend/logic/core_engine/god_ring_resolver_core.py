from __future__ import annotations

from typing import Any, Dict, Iterable, List

from v17_rebirth.backend.logic.runtime_field_protocol import runtime_field_protocol_payload
from v17_rebirth.backend.logic.core_engine.effect_resolver import pick_god_candidates, resolve_effect_scores
from v17_rebirth.backend.logic.core_engine.flux_solver import solve_dynamic_flux
from v17_rebirth.backend.logic.core_engine.pillar_graph_kernel import build_six_pillar_graph
from v17_rebirth.backend.logic.core_engine.work_path_engine import build_work_paths, collect_effect_maps


CORE_EXECUTION_AUDIT_PROTOCOL = "v17.core_execution_audit.v1"
WORK_PATH_EXECUTION_SUMMARY_PROTOCOL = "v17.work_path_execution_summary.v1"
FLUX_EXECUTION_SUMMARY_PROTOCOL = "v17.flux_execution_summary.v1"


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
    work_path_summary = _build_work_path_execution_summary(paths=paths, decision_rows=decision_rows or [])
    flux_summary = _build_flux_execution_summary(flux_meta)
    core_execution_audit = _build_core_execution_audit(
        graph=graph,
        work_path_summary=work_path_summary,
        flux_summary=flux_summary,
        effect_scores=effect_scores,
        candidates=candidates,
    )
    path_family_profile = _build_path_family_profile(paths)
    path_role_profile = _build_path_role_profile(paths)
    path_type_profile = _build_path_type_profile(paths)
    top_use = candidates["use_candidates"][0]["score"] if candidates["use_candidates"] else 0.0
    top_stability = candidates["use_candidates"][0].get("authority_stability", 0.0) if candidates["use_candidates"] else 0.0
    top_volatility = candidates["use_candidates"][0].get("authority_volatility", 0.0) if candidates["use_candidates"] else 0.0
    evidence_count = len([path for path in paths if path.path_type != "static_basis"])
    confidence = min(
        0.94,
        0.52
        + float(top_use) * 0.28
        + min(0.12, evidence_count * 0.02)
        + min(0.10, float(top_stability) * 0.12)
        - min(0.06, float(top_volatility) * 0.08),
    )
    return {
        "graph_meta": {
            "node_count": len(graph.nodes),
            "edge_count": len(graph.edges),
            "position_weights": dict(graph.position_weights),
            "distance_weights": dict(graph.distance_weights),
            "runtime_field_protocol": runtime_field_protocol_payload(),
            "dynamic_mode_profile": _build_dynamic_mode_profile(graph.edges),
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
            "work_path_execution_summary": work_path_summary,
            "flux_execution_summary": flux_summary,
            "core_execution_audit": core_execution_audit,
        },
        "path_count": len(paths),
        "paths": [path.__dict__ for path in paths[:16]],
        "effect_scores": effect_scores,
        "flux_meta": flux_meta,
        "core_execution_audit": core_execution_audit,
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


def _build_dynamic_mode_profile(edges: Iterable[Any]) -> Dict[str, Dict[str, float | int]]:
    mode_profile: Dict[str, Dict[str, float | int]] = {}
    for edge in edges:
        metadata = getattr(edge, "metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        mode = str(metadata.get("coupling_mode") or "").strip()
        if not mode:
            continue
        entry = mode_profile.setdefault(
            mode,
            {
                "count": 0,
                "avg_weight": 0.0,
                "total_weight": 0.0,
                "min_priority": 99,
            },
        )
        weight = float(getattr(edge, "weight", 0.0) or 0.0)
        priority = int(metadata.get("coupling_priority") or 99)
        entry["count"] = int(entry["count"]) + 1
        entry["total_weight"] = float(entry["total_weight"]) + weight
        entry["min_priority"] = min(int(entry["min_priority"]), priority)
        entry["avg_weight"] = round(float(entry["total_weight"]) / max(1, int(entry["count"])), 4)
    return {
        key: {
            "count": int(value["count"]),
            "avg_weight": round(float(value["avg_weight"]), 4),
            "min_priority": int(value["min_priority"]),
        }
        for key, value in mode_profile.items()
    }


def _build_work_path_execution_summary(
    *,
    paths: Iterable[Any],
    decision_rows: Iterable[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    rows = [path for path in paths]
    family_counts: Dict[str, int] = {}
    type_counts: Dict[str, int] = {}
    positive_count = 0
    negative_count = 0
    dynamic_count = 0
    basis_count = 0
    bridge_count = 0
    for path in rows:
        path_family = str(getattr(path, "path_family", "dynamic_work") or "dynamic_work").strip().lower()
        path_type = str(getattr(path, "path_type", "dynamic_work") or "dynamic_work").strip().lower()
        net_effect = float(getattr(path, "net_effect", 0.0) or 0.0)
        family_counts[path_family] = int(family_counts.get(path_family, 0)) + 1
        type_counts[path_type] = int(type_counts.get(path_type, 0)) + 1
        if path_type == "static_basis":
            basis_count += 1
        else:
            dynamic_count += 1
        if path_family == "bridge" or path_type.startswith("tongguan"):
            bridge_count += 1
        if net_effect >= 0:
            positive_count += 1
        else:
            negative_count += 1
    return {
        "protocol": WORK_PATH_EXECUTION_SUMMARY_PROTOCOL,
        "decision_row_count": len([row for row in (decision_rows or []) if isinstance(row, dict)]),
        "path_count": len(rows),
        "dynamic_path_count": dynamic_count,
        "basis_path_count": basis_count,
        "bridge_path_count": bridge_count,
        "positive_path_count": positive_count,
        "negative_path_count": negative_count,
        "family_counts": dict(sorted(family_counts.items())),
        "type_counts": dict(sorted(type_counts.items())),
    }


def _build_flux_execution_summary(flux_meta: Dict[str, Any]) -> Dict[str, Any]:
    source = flux_meta if isinstance(flux_meta, dict) else {}
    return {
        "protocol": FLUX_EXECUTION_SUMMARY_PROTOCOL,
        "enabled": bool(source.get("enabled")),
        "edge_count": int(source.get("edge_count") or 0),
        "chain_count": int(source.get("chain_count") or 0),
        "node_edge_count": int(source.get("node_edge_count") or 0),
        "node_chain_count": int(source.get("node_chain_count") or 0),
        "projected_chain_count": int(source.get("projected_chain_count") or 0),
        "interaction_count": int(source.get("interaction_count") or 0),
        "tension_pair_count": int(source.get("tension_pair_count") or 0),
        "sink_count": len(source.get("sink_summary") or {}),
    }


def _build_core_execution_audit(
    *,
    graph: Any,
    work_path_summary: Dict[str, Any],
    flux_summary: Dict[str, Any],
    effect_scores: Dict[str, Dict[str, Any]],
    candidates: Dict[str, Any],
) -> Dict[str, Any]:
    completed_steps: List[str] = []
    watch_steps: List[str] = []
    dependency_watch_edges: List[str] = []

    graph_built = bool(getattr(graph, "nodes", None)) and bool(getattr(graph, "edges", None))
    work_paths_built = int(work_path_summary.get("path_count") or 0) > 0
    effect_scores_resolved = bool(effect_scores)
    flux_solved = bool(flux_summary.get("enabled")) and int(flux_summary.get("chain_count") or 0) > 0
    authority_candidates_picked = bool(candidates.get("use_candidates")) and bool(candidates.get("taboo_candidates"))

    if graph_built:
        completed_steps.append("graph_built")
    else:
        watch_steps.append("graph_built")
    if work_paths_built:
        completed_steps.append("work_paths_built")
    else:
        watch_steps.append("work_paths_built")
    if effect_scores_resolved:
        completed_steps.append("effect_scores_resolved")
    else:
        watch_steps.append("effect_scores_resolved")
    if flux_solved:
        completed_steps.append("flux_solved")
    else:
        watch_steps.append("flux_solved")
    if authority_candidates_picked:
        completed_steps.append("authority_candidates_picked")
    else:
        watch_steps.append("authority_candidates_picked")

    if not graph_built and work_paths_built:
        dependency_watch_edges.append("graph_built->work_paths_built")
    if not work_paths_built and effect_scores_resolved:
        dependency_watch_edges.append("work_paths_built->effect_scores_resolved")
    if not effect_scores_resolved and flux_solved:
        dependency_watch_edges.append("effect_scores_resolved->flux_solved")
    if not flux_solved and authority_candidates_picked:
        dependency_watch_edges.append("flux_solved->authority_candidates_picked")

    critical_steps = [
        "graph_built",
        "work_paths_built",
        "effect_scores_resolved",
        "flux_solved",
        "authority_candidates_picked",
    ]
    critical_path_ok = not watch_steps and not dependency_watch_edges
    summary = "healthy" if critical_path_ok else ("partial" if completed_steps else "needs_review")
    return {
        "protocol": CORE_EXECUTION_AUDIT_PROTOCOL,
        "critical_steps": critical_steps,
        "completed_steps": completed_steps,
        "watch_steps": watch_steps,
        "dependency_watch_edges": dependency_watch_edges,
        "critical_path_ok": bool(critical_path_ok),
        "work_path_execution_summary_protocol": work_path_summary.get("protocol"),
        "flux_execution_summary_protocol": flux_summary.get("protocol"),
        "summary": summary,
    }
