from __future__ import annotations

from core.graph import (
    NodeRef,
    RelationFactRevision,
    WorkPathCandidate,
    WorkRoleAssignment,
    discover_role_based_work_path_candidates,
)
from core.graph.contracts import MingliGraph
from core.graph.relation_facts import assess_relation_fact_legality


def compile_relation_work_candidates(
    *,
    graph: MingliGraph,
    node_refs: dict[str, NodeRef],
    relation_facts: list[RelationFactRevision],
) -> list[WorkPathCandidate]:
    assignments = [
        WorkRoleAssignment(
            participant_ref=node_refs[node.node_id].node_ref,
            role=_work_role(node.ten_god),
            evidence_refs=list(
                dict.fromkeys(
                    [
                        node.node_id,
                        node.node_key,
                        *node.material_refs,
                        *node.evidence_refs,
                    ]
                )
            ),
        )
        for node in graph.nodes
        if node.node_id in node_refs
    ]
    preferred_fact_refs = {
        fact.revision_ref
        for fact in relation_facts
        if assess_relation_fact_legality(fact).default_path_eligible
    }
    discovered = discover_role_based_work_path_candidates(
        relation_facts=relation_facts,
        role_assignments=assignments,
        valid_from_stage="natal",
    )
    return _representative_structural_candidates(
        discovered,
        preferred_fact_refs=preferred_fact_refs,
    )


def _work_role(ten_god: str) -> str:
    if ten_god == "day_master":
        return "day_master"
    if ten_god in {"shi_shen", "shang_guan"}:
        return "shi_shang"
    if ten_god in {"zheng_cai", "pian_cai"}:
        return "wealth"
    if ten_god in {"zheng_guan", "qi_sha"}:
        return "officer_killing"
    if ten_god in {"zheng_yin", "pian_yin"}:
        return "resource"
    if ten_god in {"bi_jian", "jie_cai"}:
        return "peer"
    return "other"


def _representative_structural_candidates(
    candidates: list[WorkPathCandidate],
    *,
    preferred_fact_refs: set[str],
) -> list[WorkPathCandidate]:
    """Keep one coordinate-specific candidate per mechanism without ranking effects."""

    grouped: dict[str, list[WorkPathCandidate]] = {}
    for candidate in sorted(
        candidates,
        key=lambda item: _candidate_preference(item, preferred_fact_refs),
    ):
        grouped.setdefault(candidate.label, []).append(candidate)

    wealth_paths = grouped.get("食伤生财", [])
    killing_paths = grouped.get("食伤制杀", [])
    linked_pairs = [
        (wealth, killing)
        for wealth in wealth_paths
        for killing in killing_paths
        if wealth.actor_ref == killing.actor_ref
    ]
    if linked_pairs:
        wealth, killing = min(
            linked_pairs,
            key=lambda pair: (
                _candidate_preference(pair[0], preferred_fact_refs)[0]
                + _candidate_preference(pair[1], preferred_fact_refs)[0],
                pair[0].candidate_ref,
                pair[1].candidate_ref,
            ),
        )
    else:
        wealth = wealth_paths[0] if wealth_paths else None
        killing = killing_paths[0] if killing_paths else None

    wealth_to_killing = grouped.get("财生杀", [])
    linked_wealth_to_killing = [
        candidate
        for candidate in wealth_to_killing
        if (
            wealth is not None
            and candidate.actor_ref == wealth.receiver_ref
            and (
                killing is None
                or candidate.receiver_ref == killing.receiver_ref
            )
        )
    ]
    if not linked_wealth_to_killing and wealth is not None:
        linked_wealth_to_killing = [
            candidate
            for candidate in wealth_to_killing
            if candidate.actor_ref == wealth.receiver_ref
        ]
    wealth_to_killing_choice = (
        min(
            linked_wealth_to_killing,
            key=lambda item: _candidate_preference(
                item,
                preferred_fact_refs,
            ),
        )
        if linked_wealth_to_killing
        else wealth_to_killing[0]
        if wealth_to_killing
        else None
    )

    selected = [
        item
        for item in (wealth, killing, wealth_to_killing_choice)
        if item is not None
    ]
    return sorted(selected, key=lambda item: item.label)


def _candidate_preference(
    candidate: WorkPathCandidate,
    preferred_fact_refs: set[str],
) -> tuple[int, str]:
    return (
        0
        if all(
            segment.relation_fact_revision_ref in preferred_fact_refs
            for segment in candidate.segments
        )
        else 1,
        candidate.candidate_ref,
    )


__all__ = ["compile_relation_work_candidates"]
