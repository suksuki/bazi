from __future__ import annotations

from v20.graph.schema import ChartGraph, RulePath


def score_path(graph: ChartGraph, path: RulePath) -> RulePath:
    tag_score = sum(1 for ref in path.evidence_refs if ref in graph.feature_tags) * 0.12
    return RulePath(
        path_id=path.path_id,
        domain=path.domain,
        title=path.title,
        score=round(min(1.0, path.score + tag_score), 3),
        evidence_refs=path.evidence_refs,
        boundary=path.boundary,
        runtime_allowed=path.runtime_allowed,
    )
