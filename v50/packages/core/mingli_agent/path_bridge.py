from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.mingli_agent.contracts import (
    ChartWorldInstance,
    CognitivePathCandidate,
    CognitivePathSegment,
    WorkPathReasoning,
    WorldFact,
)


_RELATION_LABELS = {
    "generates": "生",
    "controls": "克",
    "same_element_support": "同气",
    "forms_triple_combination": "三合",
}


@dataclass(frozen=True)
class PathBridgeReceipt:
    selected_path_ref: str
    accepted_segment_count: int
    rejected_segment_count: int
    rejected_refs: tuple[str, ...]
    reason_codes: tuple[str, ...]


def bind_structured_path_candidate(
    *,
    work_path: WorkPathReasoning,
    world: ChartWorldInstance,
) -> tuple[WorkPathReasoning, PathBridgeReceipt]:
    """Bind one cognitive choice to system-owned path and relation identities."""

    facts_by_id = {
        fact.fact_id: fact
        for fact in world.facts
        if fact.category == "candidate_path"
    }
    relation_facts_by_key = _relation_facts_by_key(world)
    rejected_refs: list[str] = []
    reason_codes: list[str] = []
    selected: CognitivePathCandidate | None = None
    selected_fact: WorldFact | None = None

    for ref in dict.fromkeys(work_path.candidate_path_refs):
        fact = facts_by_id.get(ref)
        if fact is None:
            rejected_refs.append(ref)
            reason_codes.append(f"path_bridge.unknown_candidate_ref:{ref}")
            continue
        candidate = _materialize_candidate(
            fact=fact,
            relation_facts_by_key=relation_facts_by_key,
        )
        if any(segment.validation_status == "validated" for segment in candidate.segments):
            selected = candidate
            selected_fact = fact
            break
        rejected_refs.append(ref)
        reason_codes.extend(candidate.rejection_reasons)

    competing = [
        ref
        for ref in dict.fromkeys(work_path.competing_path_refs)
        if ref in facts_by_id and ref != (selected_fact.fact_id if selected_fact else "")
    ]
    if selected is None or selected_fact is None:
        return work_path.model_copy(update={
            "candidate_path_refs": [],
            "competing_path_refs": competing,
            "structured_candidate": None,
        }), PathBridgeReceipt(
            selected_path_ref="",
            accepted_segment_count=0,
            rejected_segment_count=0,
            rejected_refs=tuple(rejected_refs),
            reason_codes=tuple(dict.fromkeys(reason_codes or ["path_bridge.no_structured_selection"])),
        )

    accepted = [item for item in selected.segments if item.validation_status == "validated"]
    rejected = [item for item in selected.segments if item.validation_status == "rejected"]
    node_descriptors = selected_fact.payload.get("node_descriptors") or []
    statement, source, transformations, target = _validated_narration(
        candidate=selected,
        node_descriptors=node_descriptors,
    )
    evidence_refs = list(dict.fromkeys([
        *work_path.evidence_refs,
        selected_fact.fact_id,
        *[item.relation_ref for item in accepted],
    ]))
    return work_path.model_copy(update={
        "path_statement": statement,
        "source": source,
        "transformations": transformations,
        "target": target,
        "closure": "closed" if not rejected else "broken",
        "evidence_refs": evidence_refs,
        "origin": "system_enumerated",
        "candidate_path_refs": [selected_fact.fact_id],
        "competing_path_refs": competing,
        "structured_candidate": selected,
    }), PathBridgeReceipt(
        selected_path_ref=selected_fact.fact_id,
        accepted_segment_count=len(accepted),
        rejected_segment_count=len(rejected),
        rejected_refs=tuple(rejected_refs),
        reason_codes=tuple(dict.fromkeys([
            *reason_codes,
            *selected.rejection_reasons,
        ])),
    )


def validate_path_candidate_fact(
    *,
    fact: WorldFact,
    world: ChartWorldInstance,
) -> CognitivePathCandidate:
    return _materialize_candidate(
        fact=fact,
        relation_facts_by_key=_relation_facts_by_key(world),
    )


def _relation_facts_by_key(world: ChartWorldInstance) -> dict[str, WorldFact | None]:
    output: dict[str, WorldFact | None] = {}
    for fact in world.facts:
        if fact.category != "graph_relation":
            continue
        key = str(fact.payload.get("candidate_relation_key") or "")
        if not key:
            continue
        output[key] = None if key in output else fact
    return output


def _materialize_candidate(
    *,
    fact: WorldFact,
    relation_facts_by_key: dict[str, WorldFact | None],
) -> CognitivePathCandidate:
    payload = fact.payload
    nodes = payload.get("node_descriptors")
    relations = payload.get("relation_descriptors")
    path_key = str(payload.get("candidate_path_key") or "")
    top_reasons: list[str] = []
    if not isinstance(nodes, list) or len(nodes) < 2:
        top_reasons.append("path_bridge.node_chain_missing")
        nodes = []
    if not isinstance(relations, list):
        top_reasons.append("path_bridge.relation_chain_missing")
        relations = []
    if len(relations) != max(0, len(nodes) - 1):
        top_reasons.append("path_bridge.segment_count_mismatch")
    if payload.get("validation_status") not in {"qualified", "qualified_with_conditions"}:
        top_reasons.append("path_bridge.candidate_not_qualified")
    if not path_key:
        top_reasons.append("path_bridge.path_key_missing")

    segments: list[CognitivePathSegment] = []
    segment_count = max(len(relations), max(0, len(nodes) - 1))
    for index in range(segment_count):
        source = nodes[index] if index < len(nodes) else {}
        target = nodes[index + 1] if index + 1 < len(nodes) else {}
        relation = relations[index] if index < len(relations) else {}
        segments.append(_validate_segment(
            index=index,
            source=source,
            target=target,
            relation=relation,
            relation_facts_by_key=relation_facts_by_key,
        ))
    rejected = [item for item in segments if item.validation_status == "rejected"]
    validated = [item for item in segments if item.validation_status == "validated"]
    status = (
        "validated"
        if segments and not rejected and not top_reasons
        else "partial"
        if validated
        else "rejected"
    )
    return CognitivePathCandidate(
        candidate_path_ref=fact.fact_id,
        candidate_path_key=path_key,
        segments=segments,
        validation_status=status,
        rejection_reasons=list(dict.fromkeys([
            *top_reasons,
            *[reason for item in rejected for reason in item.rejection_reasons],
        ])),
    )


def _validate_segment(
    *,
    index: int,
    source: Any,
    target: Any,
    relation: Any,
    relation_facts_by_key: dict[str, WorldFact | None],
) -> CognitivePathSegment:
    source = source if isinstance(source, dict) else {}
    target = target if isinstance(target, dict) else {}
    relation = relation if isinstance(relation, dict) else {}
    source_ref = str(source.get("candidate_node_key") or "")
    target_ref = str(target.get("candidate_node_key") or "")
    relation_key = str(relation.get("candidate_relation_key") or "")
    relation_fact = relation_facts_by_key.get(relation_key)
    relation_ref = relation_fact.fact_id if relation_fact is not None else ""
    relation_state = str(relation.get("relation_state") or "")
    mechanism_ref = str(relation.get("mechanism_ref") or "")
    directionality = str(relation.get("directionality") or "")
    participant_refs = [
        str(item.get("candidate_node_key") or "")
        for item in relation.get("participants") or []
        if isinstance(item, dict)
    ]
    reasons: list[str] = []
    if not source_ref or not target_ref:
        reasons.append("path_bridge.segment_node_ref_missing")
    if not relation_key:
        reasons.append("path_bridge.segment_relation_key_missing")
    if relation_fact is None:
        reasons.append("path_bridge.segment_relation_ref_not_unique")
    if relation_state not in {"structural", "time_activated", "effective"}:
        reasons.append("path_bridge.segment_relation_not_structural")
    if relation.get("path_eligibility") != "eligible":
        reasons.append("path_bridge.segment_relation_not_path_eligible")
    if not mechanism_ref:
        reasons.append("path_bridge.segment_mechanism_missing")
    if directionality == "directed":
        if participant_refs[:2] != [source_ref, target_ref]:
            reasons.append("path_bridge.segment_direction_mismatch")
    elif source_ref not in participant_refs or target_ref not in participant_refs:
        reasons.append("path_bridge.segment_participant_mismatch")
    if relation_fact is not None:
        fact_payload = relation_fact.payload
        if str(fact_payload.get("candidate_relation_key") or "") != relation_key:
            reasons.append("path_bridge.segment_relation_fact_mismatch")
        if str(fact_payload.get("relation_state") or "") != relation_state:
            reasons.append("path_bridge.segment_state_mismatch")
        if str(fact_payload.get("mechanism_ref") or "") != mechanism_ref:
            reasons.append("path_bridge.segment_mechanism_mismatch")
    return CognitivePathSegment(
        segment_index=index,
        source_node_ref=source_ref or "missing-source",
        relation_ref=relation_ref or "missing-relation",
        relation_key=relation_key or "missing-relation-key",
        target_node_ref=target_ref or "missing-target",
        relation_type=str(relation.get("relation_type") or "unknown"),
        relation_state=(
            relation_state
            if relation_state in {"structural", "time_activated", "effective"}
            else "structural"
        ),
        mechanism_ref=mechanism_ref or "missing-mechanism",
        validation_status="rejected" if reasons else "validated",
        rejection_reasons=list(dict.fromkeys(reasons)),
    )


def _validated_narration(
    *,
    candidate: CognitivePathCandidate,
    node_descriptors: list[Any],
) -> tuple[str, list[str], list[str], list[str]]:
    labels = [
        _node_label(item)
        for item in node_descriptors
        if isinstance(item, dict)
    ]
    runs: list[list[CognitivePathSegment]] = []
    current: list[CognitivePathSegment] = []
    for segment in candidate.segments:
        if segment.validation_status == "validated":
            current.append(segment)
            continue
        if current:
            runs.append(current)
            current = []
    if current:
        runs.append(current)
    phrases: list[str] = []
    for run in runs:
        first_index = run[0].segment_index
        phrase = labels[first_index] if first_index < len(labels) else run[0].source_node_ref
        for segment in run:
            target_index = segment.segment_index + 1
            target = labels[target_index] if target_index < len(labels) else segment.target_node_ref
            relation = _RELATION_LABELS.get(segment.relation_type, segment.relation_type)
            phrase += f" —{relation}→ {target}"
        phrases.append(phrase)
    statement = "已验证路径：" + "；独立片段：".join(phrases)
    if not phrases:
        statement = "当前没有通过分段验证的结构路径。"
    first_run = runs[0] if runs else []
    if not first_run:
        return statement, [], [], []
    start_index = first_run[0].segment_index
    end_index = first_run[-1].segment_index + 1
    selected_labels = labels[start_index:end_index + 1]
    return (
        statement,
        selected_labels[:1],
        selected_labels[1:-1],
        selected_labels[-1:],
    )


def _node_label(descriptor: dict[str, Any]) -> str:
    label = str(descriptor.get("label") or "?")
    position = str(descriptor.get("position") or "")
    return f"{label}（{position}）" if position else label
