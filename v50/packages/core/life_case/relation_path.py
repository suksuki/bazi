from __future__ import annotations

from typing import Any, Iterable, Literal

from core.graph.provenance import (
    AssertionLifecycle,
    MingliRelationState,
    NodeRef,
    PathAssertion,
    PathKey,
    ProvenanceRecord,
    RelationAssertion,
    RelationDirectionality,
    RelationKey,
    RelationPositionContext,
    canonical_scene_scope_ref,
    relation_directionality,
    validate_assertion_history,
)
from core.life_case.contracts import ChartVersionRef, FormalInsight, LifeCase
from core.mingli_agent.contracts import (
    ChartWorldInstance,
    CognitivePathSegment,
    MingliCognitiveRecord,
    WorldFact,
)
from core.mingli_agent.path_bridge import validate_path_candidate_fact


def build_committed_relation_path_assertions(
    *,
    insight: FormalInsight,
    world: ChartWorldInstance,
    life_case_id: str,
    chart_version: ChartVersionRef,
    case_version: str,
) -> tuple[list[RelationAssertion], list[PathAssertion]]:
    record = _projection_record(insight)
    if record is None:
        return _assertions_from_insight_refs(
            insight=insight,
            world=world,
            life_case_id=life_case_id,
            chart_version=chart_version,
            case_version=case_version,
            mode="commit",
        )
    return _assertions_from_record(
        insight=insight,
        record=record,
        world=world,
        life_case_id=life_case_id,
        chart_version=chart_version,
        case_version=case_version,
        mode="commit",
    )


def relation_path_assertions_for_case(
    *,
    life_case: LifeCase,
    world: ChartWorldInstance,
) -> tuple[list[RelationAssertion], list[PathAssertion]]:
    if life_case.relation_assertions or life_case.path_assertions:
        return list(life_case.relation_assertions), list(life_case.path_assertions)
    record = _projection_record(life_case.baseline_insight)
    if record is None:
        return _assertions_from_insight_refs(
            insight=life_case.baseline_insight,
            world=world,
            life_case_id=life_case.life_case_id,
            chart_version=life_case.chart_version,
            case_version=life_case.case_version,
            mode="legacy",
        )
    return _assertions_from_record(
        insight=life_case.baseline_insight,
        record=record,
        world=world,
        life_case_id=life_case.life_case_id,
        chart_version=life_case.chart_version,
        case_version=life_case.case_version,
        mode="legacy",
    )


def _assertions_from_insight_refs(
    *,
    insight: FormalInsight,
    world: ChartWorldInstance,
    life_case_id: str,
    chart_version: ChartVersionRef,
    case_version: str,
    mode: Literal["commit", "legacy"],
) -> tuple[list[RelationAssertion], list[PathAssertion]]:
    refs = _insight_source_refs(insight)
    path_fact, path_error = _selected_path_fact_from_refs(refs=refs, world=world)
    if path_fact is not None:
        resolved = _assertions_from_path_fact(
            insight=insight,
            record=None,
            fact=path_fact,
            world=world,
            life_case_id=life_case_id,
            chart_version=chart_version,
            case_version=case_version,
            mode=mode,
        )
        if resolved is not None:
            return resolved

    resolved = _assertions_from_relation_chain(
        insight=insight,
        record=None,
        facts=_exact_relation_facts(refs=refs, world=world),
        world=world,
        life_case_id=life_case_id,
        chart_version=chart_version,
        case_version=case_version,
        mode=mode,
    )
    if resolved is not None:
        return resolved
    return [], [_unresolved_assertion(
        insight=insight,
        record=None,
        reason=path_error or (
            "legacy_case_has_no_exact_structured_path_source"
            if mode == "legacy"
            else "committed_insight_has_no_exact_structured_path_source"
        ),
        mode=mode,
        case_version=case_version,
    )]


def node_ref_for_graph_node(
    *,
    node: Any,
    world: ChartWorldInstance,
    life_case: LifeCase,
) -> NodeRef:
    return _node_ref(
        descriptor={
            "position": node.position,
            "node_type": node.node_type.value,
            "label": node.label,
        },
        world=world,
        life_case_id=life_case.life_case_id,
        chart_version=life_case.chart_version,
    )


def relation_key_for_graph_edge(
    *,
    edge: Any,
    nodes_by_id: dict[str, Any],
    world: ChartWorldInstance,
    life_case: LifeCase,
    node_refs_by_id: dict[str, NodeRef] | None = None,
) -> RelationKey:
    participants = (
        [node_refs_by_id[node_id] for node_id in edge.participant_node_ids]
        if node_refs_by_id is not None
        else [
            node_ref_for_graph_node(
                node=nodes_by_id[node_id],
                world=world,
                life_case=life_case,
            )
            for node_id in edge.participant_node_ids
        ]
    )
    return RelationKey(
        scene_ref=canonical_scene_scope_ref(
            life_case_id=life_case.life_case_id,
            chart_version_id=life_case.chart_version.version_id,
        ),
        relation_type=edge.edge_type.value,
        participant_refs=participants,
        directionality=edge.directionality,
        scope="natal",
    )


def path_key_for_graph_path(
    *,
    path: Any,
    nodes_by_id: dict[str, Any],
    edges_by_id: dict[str, Any],
    world: ChartWorldInstance,
    life_case: LifeCase,
    node_refs_by_id: dict[str, NodeRef] | None = None,
    relation_keys_by_id: dict[str, RelationKey] | None = None,
) -> PathKey:
    node_refs = (
        [node_refs_by_id[node_id] for node_id in path.node_ids]
        if node_refs_by_id is not None
        else [
            node_ref_for_graph_node(node=nodes_by_id[node_id], world=world, life_case=life_case)
            for node_id in path.node_ids
        ]
    )
    relation_keys = (
        [relation_keys_by_id[edge_id] for edge_id in path.edge_ids]
        if relation_keys_by_id is not None
        else [
            relation_key_for_graph_edge(
                edge=edges_by_id[edge_id],
                nodes_by_id=nodes_by_id,
                world=world,
                life_case=life_case,
                node_refs_by_id=node_refs_by_id,
            )
            for edge_id in path.edge_ids
        ]
    )
    return PathKey(
        scene_ref=canonical_scene_scope_ref(
            life_case_id=life_case.life_case_id,
            chart_version_id=life_case.chart_version.version_id,
        ),
        node_refs=node_refs,
        relation_keys=relation_keys,
        scope="natal",
    )


def active_relation_assertions(
    assertions: Iterable[RelationAssertion],
) -> list[RelationAssertion]:
    superseded = {item.supersedes for item in assertions if item.supersedes}
    return [
        item for item in assertions
        if item.status == AssertionLifecycle.COMMITTED
        and item.assertion_id not in superseded
    ]


def active_path_assertions(assertions: Iterable[PathAssertion]) -> list[PathAssertion]:
    superseded = {item.supersedes for item in assertions if item.supersedes}
    return [
        item for item in assertions
        if item.status == AssertionLifecycle.COMMITTED
        and item.assertion_id not in superseded
    ]


def append_relation_assertion(
    history: Iterable[RelationAssertion],
    assertion: RelationAssertion,
) -> list[RelationAssertion]:
    return _append_assertion(list(history), assertion)


def append_path_assertion(
    history: Iterable[PathAssertion],
    assertion: PathAssertion,
) -> list[PathAssertion]:
    return _append_assertion(list(history), assertion)


def _append_assertion(history: list[Any], assertion: Any) -> list[Any]:
    existing = {item.assertion_id: item for item in history}
    if assertion.assertion_id in existing:
        if existing[assertion.assertion_id] != assertion:
            raise ValueError("assertion_id_collision")
        return history
    if assertion.supersedes and assertion.supersedes not in existing:
        raise ValueError("assertion_supersedes_unknown_history")
    updated = [*history, assertion]
    validate_assertion_history(updated)
    return updated


def _assertions_from_record(
    *,
    insight: FormalInsight,
    record: MingliCognitiveRecord,
    world: ChartWorldInstance,
    life_case_id: str,
    chart_version: ChartVersionRef,
    case_version: str,
    mode: Literal["commit", "legacy"],
) -> tuple[list[RelationAssertion], list[PathAssertion]]:
    path_fact, path_error = _selected_path_fact(
        record=record,
        world=world,
        mode=mode,
    )
    if path_fact is not None:
        resolved = _assertions_from_path_fact(
            insight=insight,
            record=record,
            fact=path_fact,
            world=world,
            life_case_id=life_case_id,
            chart_version=chart_version,
            case_version=case_version,
            mode=mode,
        )
        if resolved is not None:
            return resolved

    relation_facts = _exact_relation_facts(
        refs=record.cognition.work_path.evidence_refs,
        world=world,
    )
    resolved = _assertions_from_relation_chain(
        insight=insight,
        record=record,
        facts=relation_facts,
        world=world,
        life_case_id=life_case_id,
        chart_version=chart_version,
        case_version=case_version,
        mode=mode,
    )
    if resolved is not None:
        return resolved
    reason = path_error or (
        "legacy_relation_chain_is_not_exactly_resolvable"
        if mode == "legacy"
        else "committed_path_lacks_ordered_structured_relation_evidence"
    )
    return [], [_unresolved_assertion(
        insight=insight,
        record=record,
        reason=reason,
        mode=mode,
        case_version=case_version,
    )]


def _selected_path_fact(
    *,
    record: MingliCognitiveRecord,
    world: ChartWorldInstance,
    mode: Literal["commit", "legacy"],
) -> tuple[WorldFact | None, str]:
    if mode == "commit":
        structured = record.cognition.work_path.structured_candidate
        if structured is None:
            return None, "committed_cognition_has_no_structured_path_candidate"
        if structured.validation_status not in {"validated", "partial"}:
            return None, "committed_cognition_path_candidate_not_validated"
        matches = [
            fact
            for fact in world.facts
            if fact.category == "candidate_path"
            and fact.fact_id == structured.candidate_path_ref
        ]
        if len(matches) != 1:
            return None, "structured_path_candidate_ref_not_unique"
        rebuilt = validate_path_candidate_fact(fact=matches[0], world=world)
        if rebuilt != structured:
            return None, "structured_path_candidate_integrity_mismatch"
        selected_refs = list(dict.fromkeys(record.cognition.work_path.candidate_path_refs))
        if selected_refs != [structured.candidate_path_ref]:
            return None, "structured_path_candidate_selection_mismatch"
        return matches[0], ""

    path_refs = list(dict.fromkeys([
        *record.cognition.work_path.candidate_path_refs,
        *record.cognition.work_path.evidence_refs,
    ]))
    return _selected_path_fact_from_refs(refs=path_refs, world=world)


def _selected_path_fact_from_refs(
    *,
    refs: Iterable[str],
    world: ChartWorldInstance,
) -> tuple[WorldFact | None, str]:
    for ref in refs:
        matches = [
            fact for fact in world.facts
            if fact.category == "candidate_path"
            and (fact.fact_id == ref or ref in fact.source_refs)
        ]
        if len(matches) == 1:
            return matches[0], ""
        if len(matches) > 1:
            return None, "candidate_path_ref_is_ambiguous"
    return None, "candidate_path_ref_not_found"


def _assertions_from_path_fact(
    *,
    insight: FormalInsight,
    record: MingliCognitiveRecord | None,
    fact: WorldFact,
    world: ChartWorldInstance,
    life_case_id: str,
    chart_version: ChartVersionRef,
    case_version: str,
    mode: Literal["commit", "legacy"],
) -> tuple[list[RelationAssertion], list[PathAssertion]] | None:
    node_descriptors = fact.payload.get("node_descriptors")
    relation_descriptors = fact.payload.get("relation_descriptors")
    if not isinstance(node_descriptors, list) or not isinstance(relation_descriptors, list):
        return None
    candidate = validate_path_candidate_fact(fact=fact, world=world)
    runs = _validated_segment_runs(candidate.segments)
    if not runs:
        return None
    source = "reasoner_commit" if mode == "commit" else "legacy_exact_import"
    relation_assertions: list[RelationAssertion] = []
    path_assertions: list[PathAssertion] = []
    rejected_refs = [
        f"{fact.fact_id}:segment:{item.segment_index}"
        for item in candidate.segments
        if item.validation_status == "rejected"
    ]
    for run_index, run in enumerate(runs):
        start = run[0].segment_index
        end = run[-1].segment_index + 1
        run_node_descriptors = node_descriptors[start:end + 1]
        run_relation_descriptors = relation_descriptors[start:end]
        try:
            node_refs = [
                _node_ref(
                    descriptor=item,
                    world=world,
                    life_case_id=life_case_id,
                    chart_version=chart_version,
                )
                for item in run_node_descriptors
            ]
            relation_keys = [
                _relation_key(
                    descriptor=item,
                    world=world,
                    life_case_id=life_case_id,
                    chart_version=chart_version,
                )
                for item in run_relation_descriptors
            ]
        except (KeyError, TypeError, ValueError):
            continue
        if len(node_refs) < 2 or len(relation_keys) != len(node_refs) - 1:
            continue
        run_statement = _validated_run_statement(
            node_descriptors=run_node_descriptors,
            relation_descriptors=run_relation_descriptors,
        )
        run_relation_assertions: list[RelationAssertion] = []
        for key, descriptor, segment in zip(
            relation_keys,
            run_relation_descriptors,
            run,
            strict=True,
        ):
            mechanism_ref = str(descriptor.get("mechanism_ref") or "")
            if not mechanism_ref:
                continue
            run_relation_assertions.append(RelationAssertion(
                relation_key=key,
                assertion_version=f"{case_version}:baseline",
                status=AssertionLifecycle.COMMITTED,
                provenance=_provenance(
                    insight=insight,
                    source=source,
                    evidence_refs=[fact.fact_id, segment.relation_ref],
                    source_refs=[key.relation_key, *fact.source_refs],
                ),
                relation_state=MingliRelationState.EFFECTIVE,
                mechanism_ref=mechanism_ref,
                position_context=_formal_position_context(
                    descriptor=descriptor,
                    world=world,
                    life_case_id=life_case_id,
                    chart_version=chart_version,
                ),
                verification_refs=[
                    "path_bridge.segment.validated",
                    segment.relation_ref,
                    segment.relation_key,
                ],
                statement=run_statement,
            ))
        if len(run_relation_assertions) != len(relation_keys):
            continue
        relation_assertions.extend(run_relation_assertions)
        path_key = PathKey(
            scene_ref=canonical_scene_scope_ref(
                life_case_id=life_case_id,
                chart_version_id=chart_version.version_id,
            ),
            node_refs=node_refs,
            relation_keys=relation_keys,
            scope="natal",
        )
        path_assertions.append(PathAssertion(
            path_key=path_key,
            assertion_version=f"{case_version}:baseline:{run_index}",
            status=AssertionLifecycle.COMMITTED,
            provenance=_provenance(
                insight=insight,
                source=source,
                evidence_refs=[fact.fact_id, *[item.relation_ref for item in run]],
                source_refs=[
                    *fact.source_refs,
                    str(fact.payload.get("candidate_path_key") or ""),
                ],
            ),
            source_candidate_ref=fact.fact_id,
            segment_validation_refs=[
                f"{fact.fact_id}:segment:{item.segment_index}:validated"
                for item in run
            ],
            rejected_segment_refs=rejected_refs,
            statement=run_statement,
        ))
    if not path_assertions:
        return None
    return _dedupe_assertions_by_id(relation_assertions), path_assertions


def _validated_segment_runs(
    segments: list[CognitivePathSegment],
) -> list[list[CognitivePathSegment]]:
    runs: list[list[CognitivePathSegment]] = []
    current: list[CognitivePathSegment] = []
    previous_index: int | None = None
    for segment in segments:
        contiguous = previous_index is None or segment.segment_index == previous_index + 1
        if segment.validation_status == "validated" and contiguous:
            current.append(segment)
        elif segment.validation_status == "validated":
            if current:
                runs.append(current)
            current = [segment]
        elif current:
            runs.append(current)
            current = []
        previous_index = segment.segment_index
    if current:
        runs.append(current)
    return runs


def _validated_run_statement(
    *,
    node_descriptors: list[Any],
    relation_descriptors: list[Any],
) -> str:
    relation_labels = {
        "generates": "生",
        "controls": "克",
        "same_element_support": "同气",
        "forms_triple_combination": "三合",
    }
    if not node_descriptors:
        return "已验证结构路径"
    first = node_descriptors[0] if isinstance(node_descriptors[0], dict) else {}
    statement = _descriptor_label(first)
    for relation, target in zip(
        relation_descriptors,
        node_descriptors[1:],
        strict=True,
    ):
        relation = relation if isinstance(relation, dict) else {}
        target = target if isinstance(target, dict) else {}
        relation_type = str(relation.get("relation_type") or "关系")
        statement += (
            f" —{relation_labels.get(relation_type, relation_type)}→ "
            f"{_descriptor_label(target)}"
        )
    return f"已验证路径：{statement}"


def _descriptor_label(descriptor: dict[str, Any]) -> str:
    label = str(descriptor.get("label") or "?")
    position = str(descriptor.get("position") or "")
    return f"{label}（{position}）" if position else label


def _formal_position_context(
    *,
    descriptor: dict[str, Any],
    world: ChartWorldInstance,
    life_case_id: str,
    chart_version: ChartVersionRef,
) -> RelationPositionContext | None:
    raw = descriptor.get("position_context")
    if not isinstance(raw, dict):
        return None
    intervening = raw.get("intervening_nodes")
    intervening = intervening if isinstance(intervening, list) else []
    try:
        intervening_refs = [
            _node_ref(
                descriptor=item,
                world=world,
                life_case_id=life_case_id,
                chart_version=chart_version,
            ).node_ref
            for item in intervening
        ]
        return RelationPositionContext(
            source_scope=str(raw.get("source_scope") or "natal"),
            target_scope=str(raw.get("target_scope") or "natal"),
            source_slot=str(raw.get("source_slot") or ""),
            target_slot=str(raw.get("target_slot") or ""),
            source_level=str(raw.get("source_level") or "other"),
            target_level=str(raw.get("target_level") or "other"),
            adjacent=bool(raw.get("adjacent")),
            column_span=raw.get("column_span"),
            intervening_node_refs=intervening_refs,
            ref_namespace="node_ref",
            direction=str(raw.get("direction") or "other"),
            scene_layer=str(raw.get("scene_layer") or "natal_state"),
        )
    except (KeyError, TypeError, ValueError):
        return None


def _exact_relation_facts(
    *,
    refs: Iterable[str],
    world: ChartWorldInstance,
) -> list[WorldFact]:
    facts_by_id = {item.fact_id: item for item in world.facts}
    output: list[WorldFact] = []
    for ref in refs:
        fact = facts_by_id.get(str(ref))
        if fact is not None and fact.category == "graph_relation":
            output.append(fact)
    return output


def _assertions_from_relation_chain(
    *,
    insight: FormalInsight,
    record: MingliCognitiveRecord | None,
    facts: list[WorldFact],
    world: ChartWorldInstance,
    life_case_id: str,
    chart_version: ChartVersionRef,
    case_version: str,
    mode: Literal["commit", "legacy"],
) -> tuple[list[RelationAssertion], list[PathAssertion]] | None:
    if not facts:
        return None
    relation_keys: list[RelationKey] = []
    ordered_nodes: list[NodeRef] = []
    for fact in facts:
        if not _relation_fact_is_path_eligible(fact):
            return None
        descriptor = _relation_descriptor_from_fact(fact)
        try:
            key = _relation_key(
                descriptor=descriptor,
                world=world,
                life_case_id=life_case_id,
                chart_version=chart_version,
            )
        except (KeyError, TypeError, ValueError):
            return None
        if len(key.participant_refs) != 2:
            return None
        source, target = key.participant_refs
        if key.directionality == RelationDirectionality.SYMMETRIC:
            return None
        if not ordered_nodes:
            ordered_nodes.extend([source, target])
        elif ordered_nodes[-1].node_ref == source.node_ref:
            ordered_nodes.append(target)
        else:
            return None
        relation_keys.append(key)
    source = "reasoner_commit" if mode == "commit" else "legacy_exact_import"
    assertions = [
        RelationAssertion(
            relation_key=key,
            assertion_version=f"{case_version}:baseline",
            status=AssertionLifecycle.COMMITTED,
            provenance=_provenance(
                insight=insight,
                source=source,
                evidence_refs=[fact.fact_id],
                source_refs=[*fact.source_refs, key.relation_key],
            ),
            relation_state=MingliRelationState.EFFECTIVE,
            mechanism_ref=str(fact.payload.get("mechanism_ref") or "legacy_exact_relation"),
            position_context=_formal_position_context(
                descriptor=_relation_descriptor_from_fact(fact),
                world=world,
                life_case_id=life_case_id,
                chart_version=chart_version,
            ),
            verification_refs=["path_bridge.segment.validated", fact.fact_id],
            statement=fact.statement,
        )
        for key, fact in zip(relation_keys, facts, strict=True)
    ]
    path_key = PathKey(
        scene_ref=canonical_scene_scope_ref(
            life_case_id=life_case_id,
            chart_version_id=chart_version.version_id,
        ),
        node_refs=ordered_nodes,
        relation_keys=relation_keys,
        scope="natal",
    )
    return _dedupe_assertions_by_id(assertions), [PathAssertion(
        path_key=path_key,
        assertion_version=f"{case_version}:baseline",
        status=AssertionLifecycle.COMMITTED,
        provenance=_provenance(
            insight=insight,
            source=source,
            evidence_refs=[item.fact_id for item in facts],
            source_refs=[ref for item in facts for ref in item.source_refs],
        ),
        statement=_path_statement(insight=insight, record=record),
    )]


def _dedupe_assertions_by_id(
    assertions: list[RelationAssertion],
) -> list[RelationAssertion]:
    output: dict[str, RelationAssertion] = {}
    for assertion in assertions:
        existing = output.get(assertion.assertion_id)
        if existing is not None and existing != assertion:
            raise ValueError("relation_assertion_identity_collision")
        output[assertion.assertion_id] = assertion
    return list(output.values())


def _insight_source_refs(insight: FormalInsight) -> list[str]:
    return list(dict.fromkeys([
        *insight.basis.chart_fact_refs,
        *(ref for step in insight.reasoning_path for ref in step.source_refs),
    ]))


def _path_statement(
    *,
    insight: FormalInsight,
    record: MingliCognitiveRecord | None,
) -> str:
    if record is not None and record.cognition.work_path.path_statement:
        return record.cognition.work_path.path_statement
    if insight.reasoning_path and insight.reasoning_path[-1].conclusion:
        return insight.reasoning_path[-1].conclusion
    return insight.claim


def _relation_descriptor_from_fact(fact: WorldFact) -> dict[str, Any]:
    participants = fact.payload.get("participants")
    if not isinstance(participants, list):
        participants = [
            {
                "position": fact.payload.get("from_position"),
                "node_type": _level_from_position(str(fact.payload.get("from_position") or "")),
                "label": fact.payload.get("from"),
            },
            {
                "position": fact.payload.get("to_position"),
                "node_type": _level_from_position(str(fact.payload.get("to_position") or "")),
                "label": fact.payload.get("to"),
            },
        ]
    return {
        "relation_type": fact.payload.get("relation"),
        "directionality": fact.payload.get("directionality"),
        "participants": participants,
        "relation_state": fact.payload.get("relation_state"),
        "path_eligibility": fact.payload.get("path_eligibility"),
        "mechanism_ref": fact.payload.get("mechanism_ref"),
        "position_context": fact.payload.get("position_context"),
    }


def _relation_fact_is_path_eligible(fact: WorldFact) -> bool:
    return (
        fact.category == "graph_relation"
        and fact.payload.get("relation_state")
        in {"structural", "time_activated", "effective"}
        and fact.payload.get("path_eligibility") == "eligible"
        and bool(fact.payload.get("mechanism_ref"))
    )


def _relation_key(
    *,
    descriptor: Any,
    world: ChartWorldInstance,
    life_case_id: str,
    chart_version: ChartVersionRef,
) -> RelationKey:
    if not isinstance(descriptor, dict):
        raise TypeError("relation_descriptor_required")
    relation_type = str(descriptor["relation_type"])
    raw_participants = descriptor["participants"]
    if not isinstance(raw_participants, list):
        raise TypeError("relation_participants_required")
    participants = [
        _node_ref(
            descriptor=item,
            world=world,
            life_case_id=life_case_id,
            chart_version=chart_version,
        )
        for item in raw_participants
    ]
    raw_directionality = str(descriptor.get("directionality") or "")
    directionality = (
        RelationDirectionality(raw_directionality)
        if raw_directionality
        else relation_directionality(relation_type)
    )
    return RelationKey(
        scene_ref=canonical_scene_scope_ref(
            life_case_id=life_case_id,
            chart_version_id=chart_version.version_id,
        ),
        relation_type=relation_type,
        participant_refs=participants,
        directionality=directionality,
        scope="natal",
    )


def _node_ref(
    *,
    descriptor: Any,
    world: ChartWorldInstance,
    life_case_id: str,
    chart_version: ChartVersionRef,
) -> NodeRef:
    if not isinstance(descriptor, dict):
        raise TypeError("node_descriptor_required")
    position = str(descriptor["position"])
    label = str(descriptor["label"])
    slot = position.split("_", 1)[0]
    level = str(descriptor.get("node_type") or _level_from_position(position))
    if level not in {"pillar", "stem", "branch", "hidden_stem", "other"}:
        level = _level_from_position(position)
    return NodeRef(
        scene_ref=canonical_scene_scope_ref(
            life_case_id=life_case_id,
            chart_version_id=chart_version.version_id,
        ),
        life_case_id=life_case_id,
        chart_version_id=chart_version.version_id,
        world_id=world.world_id,
        scope="natal",
        slot=slot,
        level=level,
        component=label,
    )


def _level_from_position(position: str) -> str:
    if position.endswith("_hidden_stem"):
        return "hidden_stem"
    if position.endswith("_stem"):
        return "stem"
    if position.endswith("_branch"):
        return "branch"
    return "other"


def _projection_record(insight: FormalInsight) -> MingliCognitiveRecord | None:
    payload = insight.projection_payload.get("record_projection")
    if not isinstance(payload, dict):
        return None
    try:
        return MingliCognitiveRecord.model_validate(payload)
    except Exception:  # noqa: BLE001 - malformed legacy projection remains unresolved.
        return None


def _provenance(
    *,
    insight: FormalInsight,
    source: Literal["reasoner_commit", "legacy_exact_import"],
    evidence_refs: list[str],
    source_refs: list[str],
) -> ProvenanceRecord:
    return ProvenanceRecord(
        source=source,
        producer_id=insight.provenance.reasoner_id,
        producer_version=insight.provenance.reasoner_version,
        evidence_refs=list(dict.fromkeys(ref for ref in evidence_refs if ref)),
        source_refs=list(dict.fromkeys([
            insight.insight_id,
            insight.provenance.source_record_id,
            *(ref for ref in source_refs if ref),
        ])),
        created_at=insight.provenance.generated_at,
    )


def _unresolved_assertion(
    *,
    insight: FormalInsight,
    record: MingliCognitiveRecord | None,
    reason: str,
    mode: Literal["commit", "legacy"],
    case_version: str,
) -> PathAssertion:
    statement = (
        record.cognition.work_path.path_statement
        if record is not None
        else insight.reasoning_path[-1].conclusion
        if insight.reasoning_path
        else insight.claim
    )
    legacy_ref = (
        record.record_id
        if record is not None
        else insight.provenance.source_record_id or insight.insight_id
    )
    return PathAssertion(
        assertion_version=f"{case_version}:baseline",
        status=AssertionLifecycle.LEGACY_UNRESOLVED,
        provenance=ProvenanceRecord(
            source="legacy_unresolved",
            producer_id=insight.provenance.reasoner_id or "legacy",
            producer_version=insight.provenance.reasoner_version or "legacy",
            evidence_refs=list(insight.basis.chart_fact_refs),
            source_refs=list(dict.fromkeys([
                insight.insight_id,
                legacy_ref,
                f"resolution-mode:{mode}",
            ])),
            created_at=insight.provenance.generated_at,
        ),
        statement=statement,
        legacy_ref=legacy_ref,
        unresolved_reason=reason,
    )
