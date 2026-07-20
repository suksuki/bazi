from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable
from uuid import uuid4

from product.agent_case_store import AgentCaseStore
from core.contracts import BirthInputCanonical
from core.engines import normalize_birth_input
from core.engines.bazi import build_bazi_material_store
from core.graph import build_mingli_graph_from_material_store, explore_mingli_paths
from core.graph.contracts import MingliGraph, MingliGraphNode, MingliPath
from core.life_case import (
    LifeCase,
    active_path_assertions,
    node_ref_for_graph_node,
    path_key_for_graph_path,
    relation_key_for_graph_edge,
    relation_path_assertions_for_case,
)
from core.mingli_agent.contracts import ChartWorldInstance, MingliCognitiveRecord
from experience.contracts import ParticipantRun, TheaterEvent, TopicExploration
from experience.experiments import (
    MechanismEdge,
    MechanismNode,
    MechanismPath,
    MingliMechanismSnapshot,
    MingliSandboxState,
    PillarVisual,
    SandboxResult,
    apply_single_node_ablation,
    compile_visual_spec,
    create_sandbox_state,
    issue_mechanism_snapshot,
    restore_sandbox,
)
from experience.runtime import TheaterRuntime
from experience.store import TheaterStore


POSITION_LABELS = {
    "year": "年柱",
    "month": "月柱",
    "day": "日柱",
    "hour": "时柱",
}


class MingliExperimentUnavailable(ValueError):
    pass


class ProductMingliExperimentPort:
    """Read approved cognition and run isolated structural experiments.

    This adapter may rebuild deterministic chart structure and append private
    theater events.  It has no LifeCase write method and never invokes a
    Reasoner or LLM.
    """

    def __init__(
        self,
        *,
        case_store: AgentCaseStore,
        theater_store: TheaterStore,
        runtime: TheaterRuntime,
    ) -> None:
        self.case_store = case_store
        self.theater_store = theater_store
        self.runtime = runtime

    def load(self, *, session_id: str, participant_run_id: str) -> dict[str, Any]:
        run, snapshot = self._authorized_snapshot(
            session_id=session_id,
            participant_run_id=participant_run_id,
        )
        state, result = self._latest_state_and_result(run)
        if state is None or state.base_snapshot_hash != snapshot.snapshot_hash:
            state = create_sandbox_state(participant_run_id=participant_run_id, snapshot=snapshot)
        if not self._has_event(run, "mingli_experiment_snapshot_issued", snapshot.snapshot_hash):
            self._record(
                run=run,
                event_type="mingli_experiment_snapshot_issued",
                payload={
                    "snapshot_hash": snapshot.snapshot_hash,
                    "chart_version": snapshot.chart_version,
                    "life_case_version": snapshot.life_case_version,
                    "authority": "approved_cognition_read_only",
                },
            )
        return self._payload(snapshot=snapshot, sandbox=state, result=result)

    def predict(
        self,
        *,
        session_id: str,
        participant_run_id: str,
        node_id: str,
    ) -> dict[str, Any]:
        run, snapshot = self._authorized_snapshot(
            session_id=session_id,
            participant_run_id=participant_run_id,
        )
        current, _ = self._latest_state_and_result(run)
        validated = create_sandbox_state(
            participant_run_id=participant_run_id,
            snapshot=snapshot,
            predicted_key_node_id=node_id,
        )
        if current and current.base_snapshot_hash == snapshot.snapshot_hash:
            if current.ablation_operations or current.status != "active":
                raise MingliExperimentUnavailable("prediction_locked_after_ablation")
            now = datetime.now(timezone.utc)
            state = current.model_copy(update={
                "predicted_key_node_id": node_id,
                "selected_nodes": list(dict.fromkeys([*current.selected_nodes, node_id])),
                "updated_at": now,
            })
        else:
            state = validated
        self._record(
            run=run,
            event_type="mingli_experiment_prediction_recorded",
            payload={
                "sandbox_state": state.model_dump(mode="json"),
                "authority": "visual_only",
            },
        )
        return self._payload(snapshot=snapshot, sandbox=state, result=None)

    def ablate(
        self,
        *,
        session_id: str,
        participant_run_id: str,
        node_id: str,
    ) -> dict[str, Any]:
        run, snapshot = self._authorized_snapshot(
            session_id=session_id,
            participant_run_id=participant_run_id,
        )
        state, _ = self._latest_state_and_result(run)
        if state is None or state.base_snapshot_hash != snapshot.snapshot_hash:
            state = create_sandbox_state(participant_run_id=participant_run_id, snapshot=snapshot)
        elif state.status == "saved":
            raise MingliExperimentUnavailable("experiment_already_saved")
        state, result = apply_single_node_ablation(snapshot=snapshot, sandbox=state, node_id=node_id)
        self._record(
            run=run,
            event_type="mingli_experiment_ablation_applied",
            payload={
                "sandbox_state": state.model_dump(mode="json"),
                "sandbox_result": result.model_dump(mode="json"),
                "authority": "deterministic_structure",
                "reasoner_used": False,
                "llm_used": False,
            },
        )
        return self._payload(snapshot=snapshot, sandbox=state, result=result)

    def restore(
        self,
        *,
        session_id: str,
        participant_run_id: str,
    ) -> dict[str, Any]:
        run, snapshot = self._authorized_snapshot(
            session_id=session_id,
            participant_run_id=participant_run_id,
        )
        state, result = self._latest_state_and_result(run)
        if state is None or state.base_snapshot_hash != snapshot.snapshot_hash:
            state = create_sandbox_state(participant_run_id=participant_run_id, snapshot=snapshot)
        state = restore_sandbox(state)
        self._record(
            run=run,
            event_type="mingli_experiment_original_restored",
            payload={
                "sandbox_state": state.model_dump(mode="json"),
                "base_snapshot_hash": snapshot.snapshot_hash,
                "authority": "visual_only",
            },
        )
        return self._payload(snapshot=snapshot, sandbox=state, result=result)

    def save(
        self,
        *,
        session_id: str,
        participant_run_id: str,
        observation: str = "",
        open_question: str = "",
    ) -> dict[str, Any]:
        run, snapshot = self._authorized_snapshot(
            session_id=session_id,
            participant_run_id=participant_run_id,
        )
        state, result = self._latest_state_and_result(run)
        if state is None or result is None:
            raise MingliExperimentUnavailable("experiment_result_required_before_save")
        if state.status != "restored":
            raise MingliExperimentUnavailable("restore_original_before_save")
        removed = result.deterministic_changes.removed_node_id
        node = next(item for item in snapshot.nodes if item.node_id == removed)
        default_observation = (
            f"暂时拿开{node.label}后，{len(result.deterministic_changes.invalidated_edges)}条关系消失，"
            f"{len(result.deterministic_changes.affected_paths)}条路径受到影响。"
        )
        exploration = TopicExploration(
            exploration_id=f"exploration-{uuid4().hex[:20]}",
            participant_run_id=participant_run_id,
            topic_id=self._session_topic_id(session_id),
            responses={
                "predicted_key_node_id": state.predicted_key_node_id or "",
                "ablated_node_id": removed,
            },
            experiment_kind="single_node_structural_ablation",
            base_snapshot_hash=snapshot.snapshot_hash,
            selected_node_ids=state.selected_nodes,
            sandbox_result_refs=[result.result_id],
            observations=[observation.strip() or default_observation],
            open_question=open_question.strip(),
            restored_original=True,
            capability_trace=["visual_only", "deterministic_structure", "reasoning_required"],
            life_case_version_observed=snapshot.life_case_version,
            created_at=datetime.now(timezone.utc),
        )
        self.theater_store.save_exploration(exploration)
        saved_state = state.model_copy(update={"status": "saved", "updated_at": datetime.now(timezone.utc)})
        self._record(
            run=run,
            event_type="mingli_experiment_exploration_saved",
            payload={
                "exploration_id": exploration.exploration_id,
                "sandbox_state": saved_state.model_dump(mode="json"),
                "writes_life_case": False,
            },
        )
        return {
            **self._payload(snapshot=snapshot, sandbox=saved_state, result=result),
            "topic_exploration": exploration.model_dump(mode="json"),
        }

    def _authorized_snapshot(
        self,
        *,
        session_id: str,
        participant_run_id: str,
    ) -> tuple[ParticipantRun, MingliMechanismSnapshot]:
        run = self.theater_store.get_participant(participant_run_id)
        if run is None or run.session_id != session_id:
            raise MingliExperimentUnavailable("participant_run_not_found")
        envelope = self.theater_store.get_envelope(run.envelope_id)
        if envelope is None or envelope.mode != "personal_ready":
            raise MingliExperimentUnavailable("approved_personal_cognition_required")
        if "single_node_ablation" not in envelope.topic_scope.permitted_capabilities:
            raise MingliExperimentUnavailable("topic_does_not_permit_structural_ablation")
        if "modify_life_case" not in envelope.topic_scope.prohibited_capabilities:
            raise MingliExperimentUnavailable("experiment_life_case_boundary_missing")
        case_id = envelope.source.case_ref
        if not case_id:
            raise MingliExperimentUnavailable("experiment_case_reference_missing")
        row = self.case_store.get(case_id=case_id, user_id=run.participant_ref)
        if row is None:
            raise MingliExperimentUnavailable("experience_case_not_found")
        return run, _snapshot_from_case_row(case_id=case_id, row=row)

    def _latest_state_and_result(
        self,
        run: ParticipantRun,
    ) -> tuple[MingliSandboxState | None, SandboxResult | None]:
        state: MingliSandboxState | None = None
        result: SandboxResult | None = None
        for event in self._private_experiment_events(run):
            state_payload = event.payload.get("sandbox_state")
            result_payload = event.payload.get("sandbox_result")
            if isinstance(state_payload, dict):
                state = MingliSandboxState.model_validate(state_payload)
            if isinstance(result_payload, dict):
                result = SandboxResult.model_validate(result_payload)
        return state, result

    def _private_experiment_events(self, run: ParticipantRun) -> list[TheaterEvent]:
        return [
            event
            for event in self.theater_store.list_events(run.session_id)
            if event.scope == "participant_private"
            and event.participant_run_id == run.participant_run_id
            and event.event_type.startswith("mingli_experiment_")
        ]

    def _has_event(self, run: ParticipantRun, event_type: str, snapshot_hash: str) -> bool:
        return any(
            event.event_type == event_type and event.payload.get("snapshot_hash") == snapshot_hash
            for event in self._private_experiment_events(run)
        )

    def _record(self, *, run: ParticipantRun, event_type: str, payload: dict[str, Any]) -> None:
        self.runtime.record_private_event(
            session_id=run.session_id,
            participant_run_id=run.participant_run_id,
            event_type=event_type,
            node_id=run.current_node_id,
            payload=payload,
        )

    def _session_topic_id(self, session_id: str) -> str:
        session = self.theater_store.get_session(session_id)
        if session is None:
            raise MingliExperimentUnavailable("theater_session_not_found")
        return session.topic_id

    @staticmethod
    def _payload(
        *,
        snapshot: MingliMechanismSnapshot,
        sandbox: MingliSandboxState,
        result: SandboxResult | None,
    ) -> dict[str, Any]:
        return {
            "status": "experiment_ready",
            "snapshot": snapshot.model_dump(mode="json"),
            "visual_spec": compile_visual_spec(snapshot).model_dump(mode="json"),
            "sandbox_state": sandbox.model_dump(mode="json"),
            "sandbox_result": result.model_dump(mode="json") if result else None,
            "boundaries": snapshot.boundaries,
            "life_case_modified": False,
            "llm_used": False,
            "reasoner_used": False,
        }


def _snapshot_from_case_row(*, case_id: str, row: dict[str, Any]) -> MingliMechanismSnapshot:
    birth_payload = row.get("birth_input")
    world_payload = row.get("world")
    life_case_payload = row.get("life_case")
    record_payload = row.get("record")
    if not isinstance(birth_payload, dict):
        raise MingliExperimentUnavailable("experiment_birth_input_missing")
    if (
        not isinstance(world_payload, dict)
        or not isinstance(life_case_payload, dict)
        or not isinstance(record_payload, dict)
    ):
        raise MingliExperimentUnavailable("approved_cognitive_record_required")
    birth_input = BirthInputCanonical.model_validate(birth_payload)
    world = ChartWorldInstance.model_validate(world_payload)
    life_case = LifeCase.model_validate(life_case_payload)
    record = MingliCognitiveRecord.model_validate(record_payload)
    baseline = life_case.baseline_insight
    if (
        life_case.status != "active"
        or not life_case.chart_version.active
        or baseline.status != "committed"
        or baseline.epistemic_state not in {"reliable", "competing"}
        or record.reliability_disposition not in {"reliable", "competing"}
        or record.review.disposition not in {"reliable", "competing"}
    ):
        raise MingliExperimentUnavailable("approved_active_cognition_required")
    source_record_id = baseline.provenance.source_record_id or baseline.baseline_record_id
    if source_record_id and source_record_id != record.record_id:
        raise MingliExperimentUnavailable("baseline_record_mismatch")

    graph, explored_paths = _rebuild_graph(case_id=case_id, birth_input=birth_input)
    nodes_by_id = {node.node_id: node for node in graph.nodes}
    edges_by_id = {edge.edge_id: edge for edge in graph.edges}
    node_ref_models = {
        node_id: node_ref_for_graph_node(node=node, world=world, life_case=life_case)
        for node_id, node in nodes_by_id.items()
    }
    node_refs = {node_id: item.node_ref for node_id, item in node_ref_models.items()}
    relation_key_models = {
        edge_id: relation_key_for_graph_edge(
            edge=edge,
            nodes_by_id=nodes_by_id,
            world=world,
            life_case=life_case,
            node_refs_by_id=node_ref_models,
        )
        for edge_id, edge in edges_by_id.items()
    }
    relation_refs = {
        edge_id: item.relation_key
        for edge_id, item in relation_key_models.items()
    }
    path_refs = {
        path.path_id: path_key_for_graph_path(
            path=path,
            nodes_by_id=nodes_by_id,
            edges_by_id=edges_by_id,
            world=world,
            life_case=life_case,
            node_refs_by_id=node_ref_models,
            relation_keys_by_id=relation_key_models,
        ).path_key
        for path in explored_paths.paths
    }
    _, stored_path_assertions = relation_path_assertions_for_case(
        life_case=life_case,
        world=world,
    )
    approved = _match_asserted_paths(
        assertions=active_path_assertions(stored_path_assertions),
        paths=explored_paths.paths,
        path_refs=path_refs,
    )
    competing_refs = record.cognition.work_path.competing_path_refs
    if not approved:
        raise MingliExperimentUnavailable("committed_path_not_exactly_available")
    competing = _match_referenced_paths(
        refs=competing_refs,
        paths=explored_paths.paths,
        path_refs=path_refs,
    )[:1]
    selected_paths = [approved[0], *[
        item for item in competing if item[2] != approved[0][2]
    ]]
    selected_node_ids = {
        node_id for _, path, _ in selected_paths for node_id in path.node_ids
    }
    selected_edge_ids = {
        edge_id for _, path, _ in selected_paths for edge_id in path.edge_ids
    }
    for node in graph.nodes:
        if node.node_type.value in {"stem", "branch"}:
            selected_node_ids.add(node.node_id)
    graph_nodes = [node for node in graph.nodes if node.node_id in selected_node_ids]
    graph_edges = [edge for edge in graph.edges if edge.edge_id in selected_edge_ids]
    path_models = [
        _mechanism_path(
            ref=source_ref,
            path=path,
            path_ref=path_ref,
            nodes_by_id=nodes_by_id,
            node_refs=node_refs,
            relation_refs=relation_refs,
            path_kind="approved" if index == 0 else "competing",
            display_label=(
                record.cognition.work_path.path_statement
                if index == 0
                else f"竞争路径：{' → '.join(nodes_by_id[node_id].label for node_id in path.node_ids)}"
            ),
            claim_refs=[baseline.insight_id] if index == 0 else [],
        )
        for index, (source_ref, path, path_ref) in enumerate(selected_paths)
    ]
    approved_key_nodes = list(dict.fromkeys(
        node_ref
        for reasoning in record.cognition.useful_god_reasoning
        for node_ref in reasoning.node_refs
        if node_ref in selected_node_ids
    ))
    approved_key_nodes = [node_refs[item] for item in approved_key_nodes]
    issued_at = _parse_datetime(record.created_at) or _parse_datetime(life_case.updated_at) or datetime.now(timezone.utc)
    return issue_mechanism_snapshot(
        snapshot_id=f"mechanism-snapshot:{case_id}:{life_case.case_version}:{record.record_id}",
        case_id=case_id,
        chart_version=life_case.chart_version.version_id,
        life_case_version=life_case.case_version,
        cognitive_record_id=record.record_id,
        pillars=_pillar_visuals(birth_input=birth_input, graph=graph, node_refs=node_refs),
        nodes=[_mechanism_node(node, node_ref=node_refs[node.node_id]) for node in graph_nodes],
        edges=[
            MechanismEdge(
                edge_id=relation_refs[edge.edge_id],
                from_node_id=node_refs[edge.from_node_id],
                to_node_id=node_refs[edge.to_node_id],
                relation_type=edge.edge_type.value,
                relation_label=edge.relation_label,
                strength=edge.strength,
                source_refs=[*edge.material_refs, *edge.evidence_refs],
            )
            for edge in graph_edges
        ],
        approved_paths=[path_models[0]],
        competing_paths=path_models[1:],
        approved_key_nodes=approved_key_nodes,
        unresolved_conditions=list(dict.fromkeys([
            *baseline.conditions,
            *baseline.uncertainty.reasons,
            *record.cognition.unresolved_questions,
        ]))[:8],
        claim_refs=[baseline.insight_id],
        visual_anchors={node_refs[node.node_id]: _visual_anchor(node) for node in graph_nodes},
        issued_at=issued_at,
    )


def _rebuild_graph(*, case_id: str, birth_input: BirthInputCanonical):
    calendar = normalize_birth_input(birth_input)
    material_store = build_bazi_material_store(
        reading_id=case_id,
        birth_input=birth_input,
        calendar=calendar,
    )
    graph = build_mingli_graph_from_material_store(material_store)
    return graph, explore_mingli_paths(graph)


def _match_asserted_paths(
    *,
    assertions: Iterable[Any],
    paths: list[MingliPath],
    path_refs: dict[str, str],
) -> list[tuple[str, MingliPath, str]]:
    paths_by_ref = {
        path_refs[path.path_id]: path
        for path in paths
    }
    output: list[tuple[str, MingliPath, str]] = []
    for assertion in assertions:
        path_key = assertion.path_key
        if path_key is None:
            continue
        path = paths_by_ref.get(path_key.path_key)
        if path is not None:
            output.append((assertion.assertion_id, path, path_key.path_key))
    return output


def _match_referenced_paths(
    *,
    refs: Iterable[str],
    paths: list[MingliPath],
    path_refs: dict[str, str],
) -> list[tuple[str, MingliPath, str]]:
    paths_by_id = {
        ref: path
        for path in paths
        for ref in (path.path_id, path.path_key)
    }
    matched: list[tuple[str, MingliPath, str]] = []
    used: set[str] = set()
    for raw_ref in refs:
        ref = str(raw_ref).strip()
        if not ref:
            continue
        path = paths_by_id.get(ref)
        if path is not None and path.path_id not in used:
            matched.append((ref, path, path_refs[path.path_id]))
            used.add(path.path_id)
    return matched


def _pillar_visuals(
    *,
    birth_input: BirthInputCanonical,
    graph: MingliGraph,
    node_refs: dict[str, str],
) -> list[PillarVisual]:
    nodes_by_position = {node.position: node for node in graph.nodes}
    pillars = {
        "year": birth_input.year_pillar,
        "month": birth_input.month_pillar,
        "day": birth_input.day_pillar,
        "hour": birth_input.hour_pillar,
    }
    output: list[PillarVisual] = []
    for slot, value in pillars.items():
        stem_node = nodes_by_position[f"{slot}_stem"]
        branch_node = nodes_by_position[f"{slot}_branch"]
        output.append(PillarVisual(
            pillar_id=f"pillar-{slot}",
            label=POSITION_LABELS[slot],
            stem=value[0],
            branch=value[1],
            hidden_stems=[str(item) for item in branch_node.attributes.get("hidden_stems", [])],
            stem_node_id=node_refs[stem_node.node_id],
            branch_node_id=node_refs[branch_node.node_id],
            visual_anchor_id=f"pillar-{slot}",
        ))
    return output


def _mechanism_node(node: MingliGraphNode, *, node_ref: str) -> MechanismNode:
    return MechanismNode(
        node_id=node_ref,
        label=node.label,
        node_type=node.node_type.value,
        position=node.position,
        element=node.element,
        yin_yang=node.yin_yang,
        ten_god=node.ten_god,
        visual_anchor_id=_visual_anchor(node),
        visual_group=(
            "pillar"
            if node.node_type.value in {"stem", "branch"}
            else "hidden"
            if node.node_type.value == "hidden_stem"
            else "path"
        ),
        source_refs=[*node.material_refs, *node.evidence_refs],
    )


def _mechanism_path(
    *,
    ref: str,
    path: MingliPath,
    path_ref: str,
    nodes_by_id: dict[str, MingliGraphNode],
    node_refs: dict[str, str],
    relation_refs: dict[str, str],
    path_kind: str,
    display_label: str,
    claim_refs: list[str],
) -> MechanismPath:
    return MechanismPath(
        path_ref=path_ref,
        path_kind=path_kind,
        display_label=display_label,
        node_ids=[node_refs[item] for item in path.node_ids],
        edge_ids=[relation_refs[item] for item in path.edge_ids],
        relation_types=path.relation_types,
        tool_score=path.path_score,
        claim_refs=claim_refs,
        source_refs=[ref, path_ref, path.path_id, *path.graph_refs, *path.evidence_refs],
    )


def _visual_anchor(node: MingliGraphNode) -> str:
    return f"node-{node.position}-{node.node_type.value}-{node.label}"


def _parse_datetime(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None
