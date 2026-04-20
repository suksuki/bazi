from __future__ import annotations

from typing import Any, Dict, Iterable, List

from v17_rebirth.backend.logic.core_engine.effect_resolver import pick_god_candidates, resolve_effect_scores
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
    candidates = pick_god_candidates(effect_scores)
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
        },
        "path_count": len(paths),
        "paths": [path.__dict__ for path in paths[:16]],
        "effect_scores": effect_scores,
        **candidates,
        "confidence": round(confidence, 4),
        "mode": "six_pillar_spacetime_core",
    }
