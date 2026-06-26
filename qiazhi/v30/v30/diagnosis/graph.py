from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from v30.diagnosis.contracts import (
    DiagnosisClaim,
    DiagnosisFeature,
    DiagnosisGraph,
    DiagnosisGraphEdge,
    DiagnosisGraphNode,
    DiagnosisPath,
    DiagnosisPortrait,
    MatchedRule,
)


DIAGNOSIS_GRAPH_VERSION = "v30.real_bazi_diagnosis.graph.v1"


def build_diagnosis_graph(
    *,
    reading_id: str,
    matched_rules: Sequence[MatchedRule],
    features: Sequence[DiagnosisFeature],
    paths: Sequence[DiagnosisPath],
    portraits: Sequence[DiagnosisPortrait],
    claims: Sequence[DiagnosisClaim],
    graph_id: str | None = None,
) -> DiagnosisGraph:
    nodes: list[DiagnosisGraphNode] = []
    edges: list[DiagnosisGraphEdge] = []
    node_ids: set[str] = set()
    evidence_node_by_id: dict[str, str] = {}
    feature_node_by_id: dict[str, str] = {}
    rule_node_by_id: dict[str, str] = {}
    path_node_by_id: dict[str, str] = {}
    portrait_node_by_id: dict[str, str] = {}
    claim_node_by_id: dict[str, str] = {}

    def add_node(node: DiagnosisGraphNode) -> None:
        if node.node_id in node_ids:
            return
        node_ids.add(node.node_id)
        nodes.append(node)

    def add_edge(
        *,
        source: str,
        target: str,
        kind: str,
        weight: float,
        evidence_ids: Sequence[str] = (),
    ) -> None:
        if source not in node_ids or target not in node_ids:
            return
        edge_id = f"edge:{kind}:{source}->{target}"
        edges.append(
            DiagnosisGraphEdge(
                edge_id=edge_id,
                source_node_id=source,
                target_node_id=target,
                edge_kind=kind,  # type: ignore[arg-type]
                weight=round(max(0.01, min(1.0, weight)), 3),
                evidence_ids=_dedupe(evidence_ids),
            )
        )

    for feature in features:
        for evidence_id in feature.evidence_ids:
            node_id = f"node:evidence:{_safe_id(evidence_id)}"
            evidence_node_by_id[evidence_id] = node_id
            add_node(
                DiagnosisGraphNode(
                    node_id=node_id,
                    node_kind="chart_fact" if feature.domain == "overview" and "不可改写" in feature.statement else "feature",
                    ref_id=evidence_id,
                    domain=feature.domain,
                    weight=_band_weight(feature.confidence_band),
                    metadata={"source": "feature_evidence"},
                )
            )

    for feature in features:
        node_id = f"node:feature:{_safe_id(feature.feature_id)}"
        feature_node_by_id[feature.feature_id] = node_id
        add_node(
            DiagnosisGraphNode(
                node_id=node_id,
                node_kind="feature",
                ref_id=feature.feature_id,
                domain=feature.domain,
                weight=_band_weight(feature.confidence_band),
                metadata={"family": feature.family, "supports_claim_types": feature.supports_claim_types},
            )
        )
        for evidence_id in feature.evidence_ids:
            add_edge(
                source=evidence_node_by_id.get(evidence_id, ""),
                target=node_id,
                kind="supports",
                weight=_band_weight(feature.confidence_band),
                evidence_ids=[evidence_id],
            )
        if feature.counter_notes:
            add_edge(
                source=node_id,
                target=node_id,
                kind="blocks",
                weight=0.45,
                evidence_ids=feature.evidence_ids,
            )

    for rule in matched_rules:
        node_id = f"node:rule:{_safe_id(rule.rule_match_id)}"
        rule_node_by_id[rule.rule_id] = node_id
        add_node(
            DiagnosisGraphNode(
                node_id=node_id,
                node_kind="matched_rule",
                ref_id=rule.rule_id,
                domain=rule.domain_targets[0] if rule.domain_targets else "overview",
                weight=rule.match_strength,
                metadata={
                    "can_generate_claim": rule.can_generate_claim,
                    "requires_user_calibration": rule.requires_user_calibration,
                    "blocked_claims": rule.blocked_claims,
                },
            )
        )
        for evidence_id in rule.evidence_ids:
            add_edge(
                source=evidence_node_by_id.get(evidence_id, ""),
                target=node_id,
                kind="supports" if rule.can_generate_claim else "blocks",
                weight=rule.match_strength,
                evidence_ids=[evidence_id],
            )

    for path in paths:
        node_id = f"node:path:{_safe_id(path.path_id)}"
        path_node_by_id[path.path_id] = node_id
        add_node(
            DiagnosisGraphNode(
                node_id=node_id,
                node_kind="path",
                ref_id=path.path_id,
                domain=path.domain_targets[0] if path.domain_targets else "structure",
                weight=path.score,
                metadata={"mechanism": path.mechanism, "domain_targets": path.domain_targets},
            )
        )
        for evidence_id in path.evidence_ids:
            add_edge(
                source=evidence_node_by_id.get(evidence_id, ""),
                target=node_id,
                kind="supports",
                weight=path.score,
                evidence_ids=[evidence_id],
            )
        for rule in matched_rules:
            if path.path_id in rule.path_ids:
                add_edge(
                    source=rule_node_by_id.get(rule.rule_id, ""),
                    target=node_id,
                    kind="explains",
                    weight=min(1.0, (rule.match_strength + path.score) / 2),
                    evidence_ids=_dedupe([*rule.evidence_ids, *path.evidence_ids]),
                )

    for portrait in portraits:
        node_id = f"node:portrait:{_safe_id(portrait.portrait_id)}"
        portrait_node_by_id[portrait.portrait_id] = node_id
        add_node(
            DiagnosisGraphNode(
                node_id=node_id,
                node_kind="portrait",
                ref_id=portrait.portrait_id,
                domain=portrait.domain,
                weight=_band_weight(portrait.confidence_band),
                metadata={"dimension": portrait.dimension},
            )
        )
        for evidence_id in portrait.evidence_ids:
            add_edge(
                source=evidence_node_by_id.get(evidence_id, ""),
                target=node_id,
                kind="supports",
                weight=_band_weight(portrait.confidence_band),
                evidence_ids=[evidence_id],
            )
        for path_id in portrait.path_ids:
            add_edge(
                source=path_node_by_id.get(path_id, ""),
                target=node_id,
                kind="explains",
                weight=_band_weight(portrait.confidence_band),
                evidence_ids=portrait.evidence_ids,
            )

    for claim in claims:
        node_id = f"node:claim:{_safe_id(claim.claim_id)}"
        claim_node_by_id[claim.claim_id] = node_id
        add_node(
            DiagnosisGraphNode(
                node_id=node_id,
                node_kind="claim",
                ref_id=claim.claim_id,
                domain=claim.domain,
                weight=_claim_weight(claim),
                metadata={
                    "claim_level": claim.claim_level,
                    "needs_user_calibration": claim.needs_user_calibration,
                    "blocked_overclaim": claim.blocked_overclaim,
                },
            )
        )
        for evidence_id in claim.evidence_ids:
            add_edge(
                source=evidence_node_by_id.get(evidence_id, ""),
                target=node_id,
                kind="supports",
                weight=_claim_weight(claim),
                evidence_ids=[evidence_id],
            )
        for rule_id in claim.rule_ids:
            add_edge(
                source=rule_node_by_id.get(rule_id, ""),
                target=node_id,
                kind="supports",
                weight=_claim_weight(claim),
                evidence_ids=claim.evidence_ids,
            )
        for path_id in claim.path_ids:
            add_edge(
                source=path_node_by_id.get(path_id, ""),
                target=node_id,
                kind="activates" if claim.claim_level == "timing" else "explains",
                weight=_claim_weight(claim),
                evidence_ids=claim.evidence_ids,
            )
        for portrait_id in claim.portrait_ids:
            add_edge(
                source=portrait_node_by_id.get(portrait_id, ""),
                target=node_id,
                kind="explains",
                weight=_claim_weight(claim),
                evidence_ids=claim.evidence_ids,
            )
        if claim.needs_user_calibration:
            add_edge(
                source=node_id,
                target=node_id,
                kind="asks_followup",
                weight=0.72,
                evidence_ids=claim.evidence_ids,
            )
        if claim.blocked_overclaim:
            add_edge(
                source=node_id,
                target=node_id,
                kind="blocks",
                weight=0.66,
                evidence_ids=claim.evidence_ids,
            )

    top_claim_ids = [claim.claim_id for claim in _rank_claims(claims)[:12]]
    top_path_ids = [path.path_id for path in sorted(paths, key=lambda row: (-row.score, row.path_id))[:8]]
    return DiagnosisGraph(
        graph_id=graph_id or f"{reading_id}:real-bazi-diagnosis-graph",
        reading_id=reading_id,
        nodes=nodes,
        edges=edges,
        top_claim_ids=top_claim_ids,
        top_path_ids=top_path_ids,
    )


def summarize_diagnosis_graph(graph: DiagnosisGraph) -> dict[str, Any]:
    node_counts: dict[str, int] = {}
    edge_counts: dict[str, int] = {}
    domain_counts: dict[str, int] = {}
    for node in graph.nodes:
        node_counts[node.node_kind] = node_counts.get(node.node_kind, 0) + 1
        domain_counts[node.domain] = domain_counts.get(node.domain, 0) + 1
    for edge in graph.edges:
        edge_counts[edge.edge_kind] = edge_counts.get(edge.edge_kind, 0) + 1
    return {
        "version": DIAGNOSIS_GRAPH_VERSION,
        "graph_id": graph.graph_id,
        "reading_id": graph.reading_id,
        "node_count": len(graph.nodes),
        "edge_count": len(graph.edges),
        "node_counts": dict(sorted(node_counts.items())),
        "edge_counts": dict(sorted(edge_counts.items())),
        "domain_counts": dict(sorted(domain_counts.items())),
        "top_claim_ids": graph.top_claim_ids,
        "top_path_ids": graph.top_path_ids,
        "boundary": "diagnosis_graph_summary_routes_evidence_to_claims_without_fact_generation",
    }


def _rank_claims(claims: Sequence[DiagnosisClaim]) -> list[DiagnosisClaim]:
    return sorted(
        claims,
        key=lambda row: (
            -_claim_weight(row),
            _level_rank(row.claim_level),
            row.domain,
            row.claim_id,
        ),
    )


def _claim_weight(claim: DiagnosisClaim) -> float:
    weight = _band_weight(claim.confidence_band)
    if claim.claim_level == "domain":
        weight += 0.1
    if claim.claim_level == "path":
        weight += 0.06
    if claim.needs_user_calibration:
        weight -= 0.08
    if claim.blocked_overclaim:
        weight -= 0.03
    return round(max(0.01, min(1.0, weight)), 3)


def _band_weight(value: str) -> float:
    return {"high": 0.92, "medium": 0.68, "low": 0.42}.get(value, 0.5)


def _level_rank(value: str) -> int:
    order = ["domain", "path", "portrait", "feature", "timing", "question", "fact"]
    return order.index(value) if value in order else 99


def _safe_id(value: str) -> str:
    return value.replace(":", ".").replace("/", ".")


def _dedupe(values: Sequence[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        if value and value not in out:
            out.append(value)
    return out
