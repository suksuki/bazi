from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable

from product.agent_case_store import AgentCaseStore
from product.canonical_scene import (
    CanonicalSceneOwner,
    CanonicalSceneUnavailable,
    canonical_scene_source_from_case_row,
)
from core.contracts import BirthInputCanonical
from core.engines import normalize_birth_input
from core.engines.bazi import build_bazi_material_store
from core.graph import build_mingli_graph_from_material_store, explore_mingli_paths
from core.graph.contracts import MingliGraph, MingliGraphNode, MingliPath
from core.life_case import (
    LifeCase,
    node_ref_for_graph_node,
    path_key_for_graph_path,
    relation_key_for_graph_edge,
)
from core.mingli_agent.contracts import ChartWorldInstance
from experience.canonical_scene import CanonicalScene, compile_canonical_scene
from experience.contracts import ParticipantRun, TheaterEvent
from experience.experiments import (
    MechanismEdge,
    MechanismNode,
    MechanismPath,
    MingliMechanismSnapshot,
    MechanismSandboxState,
    PillarVisual,
    SandboxResult,
    apply_single_node_ablation,
    compile_visual_spec,
    create_sandbox_state,
    issue_mechanism_snapshot,
    restore_sandbox,
)
from experience.lab import exploration_from_lab_session, update_lab_session
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
        scene_owner: CanonicalSceneOwner,
        theater_store: TheaterStore,
        runtime: TheaterRuntime,
    ) -> None:
        self.case_store = case_store
        self.scene_owner = scene_owner
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
                "lab_session": update_lab_session(current.lab_session, status="active", now=now),
                "predicted_key_node_id": node_id,
                "selected_nodes": list(dict.fromkeys([*current.selected_nodes, node_id])),
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
        exploration = exploration_from_lab_session(
            session=state.lab_session,
            topic_id=self._session_topic_id(session_id),
            selected_node_ids=state.selected_nodes,
            result_refs=[result.result_id],
            observations=[observation.strip() or default_observation],
            open_question=open_question.strip(),
            restored_original=True,
        )
        exploration = exploration.model_copy(update={
            "responses": {
                "predicted_key_node_id": state.predicted_key_node_id or "",
                "ablated_node_id": removed,
            },
            "life_case_version_observed": snapshot.life_case_version,
        })
        self.theater_store.save_exploration(exploration)
        saved_state = state.model_copy(update={
            "lab_session": update_lab_session(state.lab_session, status="saved"),
        })
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
        try:
            scene = self.scene_owner.issue_scene(
                case_id=case_id,
                participant_id=run.participant_ref,
                account_role="member",
            )
        except CanonicalSceneUnavailable as exc:
            raise MingliExperimentUnavailable("experiment_canonical_scene_required") from exc
        if envelope.source.source_hash != scene.identity.source_hash:
            raise MingliExperimentUnavailable("experiment_scene_source_changed")
        return run, _snapshot_from_case_row(case_id=case_id, row=row, scene=scene)

    def _latest_state_and_result(
        self,
        run: ParticipantRun,
    ) -> tuple[MechanismSandboxState | None, SandboxResult | None]:
        state: MechanismSandboxState | None = None
        result: SandboxResult | None = None
        for event in self._private_experiment_events(run):
            state_payload = event.payload.get("sandbox_state")
            result_payload = event.payload.get("sandbox_result")
            if isinstance(state_payload, dict):
                state = MechanismSandboxState.model_validate(state_payload)
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
        sandbox: MechanismSandboxState,
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


def _snapshot_from_case_row(
    *,
    case_id: str,
    row: dict[str, Any],
    scene: CanonicalScene | None = None,
) -> MingliMechanismSnapshot:
    birth_payload = row.get("birth_input")
    world_payload = row.get("world")
    life_case_payload = row.get("life_case")
    if not isinstance(birth_payload, dict):
        raise MingliExperimentUnavailable("experiment_birth_input_missing")
    if not isinstance(world_payload, dict) or not isinstance(life_case_payload, dict):
        raise MingliExperimentUnavailable("approved_life_case_required")
    birth_input = BirthInputCanonical.model_validate(birth_payload)
    world = ChartWorldInstance.model_validate(world_payload)
    life_case = LifeCase.model_validate(life_case_payload)
    baseline = life_case.baseline_insight
    if (
        life_case.status != "active"
        or not life_case.chart_version.active
        or baseline.status != "committed"
        or baseline.epistemic_state not in {"reliable", "competing"}
    ):
        raise MingliExperimentUnavailable("approved_active_cognition_required")
    scene = scene or compile_canonical_scene(
        source=canonical_scene_source_from_case_row(case_id=case_id, row=row),
        role="member",
    )
    if (
        scene.identity.case_ref != case_id
        or scene.identity.chart_version_id != life_case.chart_version.version_id
        or scene.identity.life_case_version != life_case.case_version
    ):
        raise MingliExperimentUnavailable("experiment_scene_identity_mismatch")

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
    approved = _match_scene_paths(
        assertions=scene.path_assertions,
        paths=explored_paths.paths,
        path_refs=path_refs,
    )
    if not approved:
        raise MingliExperimentUnavailable("committed_path_not_exactly_available")
    selected_paths = [approved[0]]
    selected_node_ids = {
        node_id for _, path, _, _ in selected_paths for node_id in path.node_ids
    }
    selected_edge_ids = {
        edge_id for _, path, _, _ in selected_paths for edge_id in path.edge_ids
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
            path_kind="approved",
            display_label=statement or baseline.claim,
            claim_refs=[item.claim_ref for item in scene.approved_claims[:1]],
        )
        for source_ref, path, path_ref, statement in selected_paths
    ]
    source_record_id = (
        baseline.provenance.source_record_id
        or baseline.baseline_record_id
        or baseline.insight_id
    )
    return issue_mechanism_snapshot(
        snapshot_id=f"mechanism-snapshot:{scene.identity.scene_id}",
        case_id=case_id,
        chart_version=life_case.chart_version.version_id,
        life_case_version=life_case.case_version,
        cognitive_record_id=source_record_id,
        scene_id=scene.identity.scene_id,
        scene_source_hash=scene.identity.source_hash,
        disclosure_hash=scene.role_disclosure.disclosure_hash,
        pillars=_pillar_visuals(birth_input=birth_input, graph=graph, node_refs=node_refs),
        nodes=[_mechanism_node(node, node_ref=node_refs[node.node_id]) for node in graph_nodes],
        edges=[
            MechanismEdge(
                edge_id=relation_refs[edge.edge_id],
                from_node_id=node_refs[edge.from_node_id],
                to_node_id=node_refs[edge.to_node_id],
                relation_type=edge.edge_type.value,
                relation_label=edge.relation_label,
                path_eligibility=edge.path_eligibility.value,
                eligibility_reason_refs=list(edge.eligibility_reason_refs),
                source_refs=[*edge.material_refs, *edge.evidence_refs],
            )
            for edge in graph_edges
        ],
        approved_paths=[path_models[0]],
        competing_paths=[],
        approved_key_nodes=[],
        unresolved_conditions=list(dict.fromkeys([
            *(condition for claim in scene.approved_claims for condition in claim.conditions),
            *scene.uncertainty.reasons,
        ]))[:8],
        claim_refs=[item.claim_ref for item in scene.approved_claims],
        visual_anchors={node_refs[node.node_id]: _visual_anchor(node) for node in graph_nodes},
        issued_at=scene.identity.source_updated_at,
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


def _match_scene_paths(
    *,
    assertions: Iterable[Any],
    paths: list[MingliPath],
    path_refs: dict[str, str],
) -> list[tuple[str, MingliPath, str, str]]:
    paths_by_ref = {
        path_refs[path.path_id]: path
        for path in paths
    }
    output: list[tuple[str, MingliPath, str, str]] = []
    for assertion in assertions:
        if assertion.status != "committed":
            continue
        path = paths_by_ref.get(assertion.path_ref)
        if path is not None:
            output.append((assertion.assertion_ref, path, assertion.path_ref, assertion.statement))
    return output


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
        validation_state=path.validation_state.value,
        evidence={
            "segment_validity": path.evidence_vector.segment_validity.value,
            "direction_coherence": path.evidence_vector.direction_coherence.value,
            "temporal_coherence": path.evidence_vector.temporal_coherence.value,
            "root_support": path.evidence_vector.root_support.value,
            "reveal_support": path.evidence_vector.reveal_support.value,
            "blocking": path.evidence_vector.blocking.value,
            "closure": path.evidence_vector.closure.value,
            "provenance_quality": path.evidence_vector.provenance_quality.value,
            "reason_refs": list(path.evidence_vector.reason_refs),
        },
        claim_refs=claim_refs,
        source_refs=[ref, path_ref, path.path_id, *path.graph_refs, *path.evidence_refs],
    )


def _visual_anchor(node: MingliGraphNode) -> str:
    return f"node-{node.position}-{node.node_type.value}-{node.label}"
