from __future__ import annotations

from v20.core.schemas import ChartFacts
from v20.graph.schema import ChartGraph, GraphEdge, GraphNode


def build_chart_graph(facts: ChartFacts) -> ChartGraph:
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    tags: set[str] = set()
    for position, pillar in facts.pillars.items():
        pillar_id = f"pillar:{position}"
        stem_id = f"stem:{pillar.stem}:{position}"
        branch_id = f"branch:{pillar.branch}:{position}"
        nodes.extend(
            [
                GraphNode(pillar_id, "pillar", pillar.display),
                GraphNode(stem_id, "stem", pillar.stem),
                GraphNode(branch_id, "branch", pillar.branch),
            ]
        )
        edges.append(GraphEdge(pillar_id, stem_id, "has_stem"))
        edges.append(GraphEdge(pillar_id, branch_id, "has_branch"))
        tags.update({f"stem:{pillar.stem}", f"branch:{pillar.branch}", "pillar"})
    for row in facts.visible_ten_gods:
        tag = f"ten_god:{row.label}"
        tags.add(tag)
        nodes.append(GraphNode(tag, "ten_god", row.label))
    for relation in facts.relation_hits:
        tag = f"relation:{relation.relation_type}"
        tags.add(tag)
        nodes.append(GraphNode(tag, "relation", relation.relation_type))
    if facts.vault_branches:
        tags.add("vault")
    return ChartGraph(nodes=tuple(nodes), edges=tuple(edges), feature_tags=tuple(sorted(tags)))
