from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, computed_field, model_validator

from experience.contracts import ExperienceModel
from experience.lab import MingliLabSession, update_lab_session


CanvasRole = Literal["guest", "member", "practitioner", "research", "admin"]
CanvasStage = Literal["natal", "luck", "year"]
CanvasSourceMode = Literal["canonical", "committed", "derived", "hypothetical", "presentation"]
CanvasEpistemicStatus = Literal[
    "fact",
    "derived",
    "candidate",
    "committed",
    "blocked",
    "hypothetical",
    "presentation_only",
]
CanvasDisclosure = Literal["public", "member", "practitioner", "research"]
CanvasSemanticState = Literal["latent", "active", "reinforced", "weakened", "blocked"]
CanvasRelationState = Literal["potential", "structural", "time_activated", "effective"]
CanvasChangeType = Literal[
    "introduced",
    "removed",
    "activated",
    "reinforced",
    "weakened",
    "blocked",
    "reopened",
    "unchanged",
]


class CanvasCompileError(ValueError):
    pass


class CanvasTrace(ExperienceModel):
    source_mode: CanvasSourceMode
    epistemic_status: CanvasEpistemicStatus
    source_refs: list[str] = Field(min_length=1)
    commitment_refs: list[str] = Field(default_factory=list)
    uncertainty: list[str] = Field(default_factory=list)
    rejection_or_block_reasons: list[str] = Field(default_factory=list)
    disclosure: CanvasDisclosure = "member"

    @model_validator(mode="after")
    def validate_authority(self) -> "CanvasTrace":
        if self.source_mode == "committed" and self.epistemic_status != "committed":
            raise ValueError("committed_source_requires_committed_status")
        if self.epistemic_status == "committed" and not self.commitment_refs:
            raise ValueError("committed_status_requires_commitment_ref")
        if self.source_mode == "hypothetical" and self.epistemic_status != "hypothetical":
            raise ValueError("hypothetical_source_requires_hypothetical_status")
        if self.source_mode == "presentation" and self.epistemic_status != "presentation_only":
            raise ValueError("presentation_source_requires_presentation_status")
        if self.epistemic_status == "blocked" and not self.rejection_or_block_reasons:
            raise ValueError("blocked_status_requires_reason")
        return self


class CanvasSemanticSlot(ExperienceModel):
    slot_ref: str = Field(min_length=1, max_length=180)
    slot_type: Literal["natal_year", "natal_month", "natal_day", "natal_hour", "luck", "year"]
    label: str = Field(min_length=1, max_length=40)
    stem: str = Field(min_length=1, max_length=4)
    branch: str = Field(min_length=1, max_length=4)
    hidden_stems: list[str] = Field(default_factory=list)
    immutable: bool
    trace: CanvasTrace


class CanvasNode(ExperienceModel):
    node_ref: str = Field(min_length=1, max_length=220)
    label: str = Field(min_length=1, max_length=80)
    node_type: str = Field(min_length=1, max_length=80)
    semantic_slot_ref: str = Field(default="", max_length=180)
    element: str = Field(default="", max_length=40)
    polarity: str = Field(default="", max_length=40)
    ten_god: str = Field(default="", max_length=80)
    trace: CanvasTrace


class CanvasRelation(ExperienceModel):
    relation_ref: str = Field(min_length=1, max_length=260)
    from_node_ref: str = Field(min_length=1, max_length=220)
    to_node_ref: str = Field(min_length=1, max_length=220)
    participant_node_refs: list[str] = Field(default_factory=list, min_length=0)
    relation_type: str = Field(min_length=1, max_length=100)
    label: str = Field(min_length=1, max_length=140)
    relation_state: CanvasRelationState = "structural"
    semantic_state: CanvasSemanticState = "active"
    trace: CanvasTrace
    state_trace: CanvasTrace
    change_reason_refs: list[str] = Field(default_factory=list)


class CanvasCluster(ExperienceModel):
    cluster_ref: str = Field(min_length=1, max_length=220)
    label: str = Field(min_length=1, max_length=160)
    node_refs: list[str] = Field(min_length=2)
    relation_refs: list[str] = Field(default_factory=list)
    trace: CanvasTrace


class CanvasPath(ExperienceModel):
    path_ref: str = Field(min_length=1, max_length=240)
    label: str = Field(min_length=1, max_length=240)
    node_refs: list[str] = Field(min_length=2)
    relation_refs: list[str] = Field(min_length=1)
    required_refs: list[str] = Field(default_factory=list)
    semantic_state: CanvasSemanticState
    trace: CanvasTrace
    state_trace: CanvasTrace
    change_reason_refs: list[str] = Field(default_factory=list)


class CanvasPathStateUpdate(ExperienceModel):
    path_ref: str = Field(min_length=1, max_length=240)
    semantic_state: CanvasSemanticState
    state_trace: CanvasTrace
    change_reason_refs: list[str] = Field(min_length=1)


class CanvasRemoval(ExperienceModel):
    object_type: Literal["node", "relation", "cluster", "path"]
    target_ref: str = Field(min_length=1, max_length=260)
    reason_refs: list[str] = Field(min_length=1)
    source_refs: list[str] = Field(min_length=1)
    source_mode: Literal["derived", "hypothetical"]


class CanvasChartSource(ExperienceModel):
    chart_version_id: str = Field(min_length=1, max_length=180)
    world_id: str = Field(min_length=1, max_length=180)
    slots: list[CanvasSemanticSlot] = Field(min_length=4, max_length=4)
    nodes: list[CanvasNode] = Field(min_length=2)
    relations: list[CanvasRelation] = Field(default_factory=list)
    clusters: list[CanvasCluster] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_natal_source(self) -> "CanvasChartSource":
        expected = ["natal_year", "natal_month", "natal_day", "natal_hour"]
        if [item.slot_type for item in self.slots] != expected:
            raise ValueError("chart_source_requires_ordered_four_natal_slots")
        if any(not item.immutable for item in self.slots):
            raise ValueError("natal_slots_must_be_immutable")
        if any(item.trace.source_mode != "canonical" for item in self.slots):
            raise ValueError("natal_slots_must_be_canonical")
        return self


class CanvasLifeCaseSource(ExperienceModel):
    life_case_id: str = Field(min_length=1, max_length=180)
    life_case_version: str = Field(min_length=1, max_length=120)
    paths: list[CanvasPath] = Field(default_factory=list)
    uncertainty: list[str] = Field(default_factory=list)
    must_not_say: list[str] = Field(default_factory=list)


class CanvasTemporalLayer(ExperienceModel):
    layer_id: str = Field(min_length=1, max_length=180)
    layer_type: Literal["luck", "year"]
    layer_mode: Literal["official", "hypothetical"]
    temporal_snapshot_id: str = Field(default="", max_length=180)
    slot: CanvasSemanticSlot
    nodes: list[CanvasNode] = Field(default_factory=list)
    relations: list[CanvasRelation] = Field(default_factory=list)
    clusters: list[CanvasCluster] = Field(default_factory=list)
    paths: list[CanvasPath] = Field(default_factory=list)
    path_updates: list[CanvasPathStateUpdate] = Field(default_factory=list)
    removals: list[CanvasRemoval] = Field(default_factory=list)
    source_refs: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_layer_authority(self) -> "CanvasTemporalLayer":
        if self.slot.slot_type != self.layer_type:
            raise ValueError("temporal_layer_slot_type_mismatch")
        if self.slot.immutable:
            raise ValueError("temporal_layer_slot_cannot_be_immutable")
        traces = [
            self.slot.trace,
            *(item.trace for item in self.nodes),
            *(item.trace for item in self.relations),
            *(item.state_trace for item in self.relations),
            *(item.trace for item in self.clusters),
            *(item.trace for item in self.paths),
            *(item.state_trace for item in self.paths),
            *(item.state_trace for item in self.path_updates),
        ]
        if self.layer_mode == "hypothetical":
            if any(item.source_mode != "hypothetical" for item in traces):
                raise ValueError("hypothetical_layer_requires_hypothetical_traces")
            if any(item.source_mode != "hypothetical" for item in self.removals):
                raise ValueError("hypothetical_layer_requires_hypothetical_removals")
        elif any(item.source_mode == "hypothetical" for item in traces):
            raise ValueError("official_layer_cannot_contain_hypothetical_trace")
        return self


class MingliCanvasCompileInput(ExperienceModel):
    schema_version: Literal["deepbazi.mingli_canvas_compile_input.v1"] = (
        "deepbazi.mingli_canvas_compile_input.v1"
    )
    compiler_version: str = Field(min_length=1, max_length=100)
    compiled_at: datetime
    chart: CanvasChartSource
    life_case: CanvasLifeCaseSource
    temporal_layers: list[CanvasTemporalLayer] = Field(default_factory=list)


class CanvasSandboxMutation(ExperienceModel):
    mutation_id: str = Field(min_length=1, max_length=180)
    action_type: Literal["set_luck", "set_year", "replace_year", "clear_year"]
    field_path: Literal["temporal.luck", "temporal.year"]
    before_layer_id: str = Field(default="", max_length=180)
    after_layer_id: str = Field(default="", max_length=180)
    base_snapshot_id: str = Field(min_length=1, max_length=180)
    source_mode: Literal["derived", "hypothetical"]
    source_refs: list[str] = Field(min_length=1)


class CanvasAction(ExperienceModel):
    action_id: str = Field(min_length=1, max_length=180)
    action_type: Literal["set_luck", "set_year", "replace_year", "clear_year", "restore"]
    target_layer_id: str = Field(default="", max_length=180)
    source_ref: str = Field(min_length=1, max_length=220)


class TemporalSandboxState(ExperienceModel):
    schema_version: Literal[
        "deepbazi.temporal_sandbox_state.v1",
        "deepbazi.temporal_sandbox_state.v2",
    ] = "deepbazi.temporal_sandbox_state.v2"
    lab_session: MingliLabSession
    base_luck_layer_id: str = Field(default="", max_length=180)
    base_year_layer_id: str = Field(default="", max_length=180)
    selected_luck_layer_id: str = Field(default="", max_length=180)
    selected_year_layer_id: str = Field(default="", max_length=180)
    mutations: list[CanvasSandboxMutation] = Field(default_factory=list)
    current_canvas_spec_id: str = Field(default="", max_length=180)
    current_diff_spec_id: str = Field(default="", max_length=180)

    @model_validator(mode="before")
    @classmethod
    def upgrade_legacy_state(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        payload = dict(value)
        if "lab_session" in payload:
            for field in (
                "sandbox_session_id",
                "base_snapshot_id",
                "revision",
                "status",
                "writes_chart",
                "writes_life_case",
            ):
                payload.pop(field, None)
            return payload
        base_snapshot_id = str(payload.pop("base_snapshot_id"))
        session_id = str(payload.pop("sandbox_session_id"))
        status = str(payload.pop("status", "active"))
        if status == "saved_as_exploration":
            status = "saved"
        epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
        payload["lab_session"] = MingliLabSession(
            session_id=session_id,
            case_ref="legacy-unresolved",
            scene_id="legacy-unresolved",
            scene_source_hash=_canonical_hash({"base_snapshot_id": base_snapshot_id}),
            disclosure_hash="0" * 64,
            experiment_kind="temporal_hypothesis",
            base_snapshot_ref=base_snapshot_id,
            source_mode="legacy_unresolved",
            revision=int(payload.pop("revision", 0)),
            status=status,
            created_at=epoch,
            updated_at=epoch,
        ).model_dump(mode="json")
        payload.pop("writes_chart", None)
        payload.pop("writes_life_case", None)
        return payload

    @computed_field
    @property
    def sandbox_session_id(self) -> str:
        return self.lab_session.session_id

    @computed_field
    @property
    def base_snapshot_id(self) -> str:
        return self.lab_session.base_snapshot_ref

    @computed_field
    @property
    def revision(self) -> int:
        return self.lab_session.revision

    @computed_field
    @property
    def status(self) -> str:
        return self.lab_session.status

    @computed_field
    @property
    def writes_chart(self) -> Literal[False]:
        return False

    @computed_field
    @property
    def writes_life_case(self) -> Literal[False]:
        return False


class CanvasCompileRequest(ExperienceModel):
    source: MingliCanvasCompileInput
    stage: CanvasStage
    luck_layer_id: str = Field(default="", max_length=180)
    year_layer_id: str = Field(default="", max_length=180)
    sandbox: TemporalSandboxState | None = None


class CanvasIdentity(ExperienceModel):
    canvas_spec_id: str = Field(min_length=1, max_length=180)
    chart_version_id: str = Field(min_length=1, max_length=180)
    temporal_snapshot_id: str = Field(default="", max_length=180)
    life_case_id: str = Field(min_length=1, max_length=180)
    sandbox_session_id: str = Field(default="", max_length=180)
    compiler_version: str = Field(min_length=1, max_length=100)
    compiled_at: datetime
    audience_role: CanvasRole | None = None
    content_hash: str = Field(min_length=64, max_length=64)


class CanvasEpistemology(ExperienceModel):
    epistemic_statuses: list[CanvasEpistemicStatus]
    source_refs: list[str]
    commitment_refs: list[str]
    uncertainty: list[str]
    rejection_or_block_reasons: list[str]
    must_not_say: list[str]


class CanvasInteractionPolicy(ExperienceModel):
    allowed_interactions: list[str]
    immutable_slots: list[str]
    sandbox_mutations: list[str]


class CanvasVisualAnchor(ExperienceModel):
    anchor_ref: str = Field(min_length=1, max_length=220)
    object_ref: str = Field(min_length=1, max_length=260)
    group: str = Field(min_length=1, max_length=80)
    trace: CanvasTrace


class CanvasPresentation(ExperienceModel):
    visual_anchors: list[CanvasVisualAnchor]
    layers: list[str]
    emphasis: list[str]
    narration_targets: list[str]


class MingliCanvasSpec(ExperienceModel):
    schema_version: Literal["deepbazi.mingli_canvas_spec.v1"] = "deepbazi.mingli_canvas_spec.v1"
    identity: CanvasIdentity
    stage: CanvasStage
    semantic_slots: list[CanvasSemanticSlot]
    nodes: list[CanvasNode]
    relations: list[CanvasRelation]
    clusters: list[CanvasCluster]
    paths: list[CanvasPath]
    epistemology: CanvasEpistemology
    interaction: CanvasInteractionPolicy
    presentation: CanvasPresentation

    @model_validator(mode="after")
    def validate_references(self) -> "MingliCanvasSpec":
        slots = _unique_refs(self.semantic_slots, "slot_ref", "canvas_duplicate_slot")
        nodes = _unique_refs(self.nodes, "node_ref", "canvas_duplicate_node")
        relations = _unique_refs(self.relations, "relation_ref", "canvas_duplicate_relation")
        _unique_refs(self.clusters, "cluster_ref", "canvas_duplicate_cluster")
        _unique_refs(self.paths, "path_ref", "canvas_duplicate_path")
        natal_types = [item.slot_type for item in self.semantic_slots if item.slot_type.startswith("natal_")]
        if natal_types != ["natal_year", "natal_month", "natal_day", "natal_hour"]:
            raise ValueError("canvas_requires_ordered_four_natal_slots")
        if any(not slots[ref].immutable for ref in slots if ref.startswith("slot-natal-")):
            raise ValueError("canvas_natal_slot_mutability_violation")
        for node in self.nodes:
            if node.semantic_slot_ref and node.semantic_slot_ref not in slots:
                raise ValueError(f"canvas_node_missing_slot:{node.node_ref}")
        for relation in self.relations:
            if relation.from_node_ref not in nodes or relation.to_node_ref not in nodes:
                raise ValueError(f"canvas_relation_missing_node:{relation.relation_ref}")
            participants = relation.participant_node_refs or [
                relation.from_node_ref,
                relation.to_node_ref,
            ]
            if len(participants) < 2 or not set(participants).issubset(nodes):
                raise ValueError(f"canvas_relation_missing_participant:{relation.relation_ref}")
        for cluster in self.clusters:
            if not set(cluster.node_refs).issubset(nodes):
                raise ValueError(f"canvas_cluster_missing_node:{cluster.cluster_ref}")
            if not set(cluster.relation_refs).issubset(relations):
                raise ValueError(f"canvas_cluster_missing_relation:{cluster.cluster_ref}")
        for path in self.paths:
            if not set(path.node_refs).issubset(nodes):
                raise ValueError(f"canvas_path_missing_node:{path.path_ref}")
            if not set(path.relation_refs).issubset(relations):
                raise ValueError(f"canvas_path_missing_relation:{path.path_ref}")
        return self


class CanvasObjectDelta(ExperienceModel):
    object_type: Literal["node", "relation", "cluster", "path"]
    target_ref: str = Field(min_length=1, max_length=260)
    change_type: CanvasChangeType
    before_state: str = Field(default="", max_length=80)
    after_state: str = Field(default="", max_length=80)
    reason_refs: list[str] = Field(min_length=1)
    source_refs: list[str] = Field(min_length=1)


class CanvasEpistemicDelta(ExperienceModel):
    object_type: Literal["node", "relation", "cluster", "path"]
    target_ref: str = Field(min_length=1, max_length=260)
    status_scope: Literal["object", "state"]
    before_status: CanvasEpistemicStatus
    after_status: CanvasEpistemicStatus
    reason_refs: list[str] = Field(min_length=1)
    source_refs: list[str] = Field(min_length=1)


class CanvasDiffSpec(ExperienceModel):
    schema_version: Literal["deepbazi.canvas_diff_spec.v1"] = "deepbazi.canvas_diff_spec.v1"
    diff_id: str = Field(min_length=1, max_length=180)
    from_spec_id: str = Field(min_length=1, max_length=180)
    to_spec_id: str = Field(min_length=1, max_length=180)
    source_action_ref: str = Field(min_length=1, max_length=220)
    added_nodes: list[CanvasObjectDelta]
    removed_nodes: list[CanvasObjectDelta]
    added_relations: list[CanvasObjectDelta]
    removed_relations: list[CanvasObjectDelta]
    changed_relations: list[CanvasObjectDelta]
    added_clusters: list[CanvasObjectDelta]
    removed_clusters: list[CanvasObjectDelta]
    introduced_paths: list[CanvasObjectDelta]
    removed_paths: list[CanvasObjectDelta]
    activated_paths: list[CanvasObjectDelta]
    blocked_paths: list[CanvasObjectDelta]
    reopened_paths: list[CanvasObjectDelta]
    reinforced_paths: list[CanvasObjectDelta]
    weakened_paths: list[CanvasObjectDelta]
    unchanged_paths: list[CanvasObjectDelta]
    changed_epistemic_status: list[CanvasEpistemicDelta]
    explanation_refs: list[str]
    uncertainty: list[str]
    content_hash: str = Field(min_length=64, max_length=64)


class CanvasContextPack(ExperienceModel):
    schema_version: Literal["deepbazi.canvas_context_pack.v1"] = "deepbazi.canvas_context_pack.v1"
    context_pack_id: str = Field(min_length=1, max_length=180)
    canvas_spec_id: str = Field(min_length=1, max_length=180)
    diff_spec_id: str = Field(default="", max_length=180)
    role: CanvasRole
    current_stage: CanvasStage
    selected_object_refs: list[str]
    visible_layers: list[str]
    committed_path_refs: list[str]
    candidate_path_refs: list[str]
    blocked_path_refs: list[str]
    hypothetical_mutations: list[CanvasSandboxMutation]
    diff_reason_refs: list[str]
    uncertainty: list[str]
    must_not_say: list[str]
    disclosed_object_refs: list[str]
    content_hash: str = Field(min_length=64, max_length=64)


def load_canvas_compile_input(path: str | Path) -> MingliCanvasCompileInput:
    return MingliCanvasCompileInput.model_validate_json(Path(path).read_text(encoding="utf-8"))


def create_temporal_sandbox(
    *,
    sandbox_session_id: str,
    base_snapshot_id: str,
    luck_layer_id: str = "",
    year_layer_id: str = "",
    lab_session: MingliLabSession | None = None,
) -> TemporalSandboxState:
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    return TemporalSandboxState(
        lab_session=lab_session or MingliLabSession(
            session_id=sandbox_session_id,
            case_ref="synthetic-fixture",
            scene_id=f"scene-fixture-{_canonical_hash({'base': base_snapshot_id})[:20]}",
            scene_source_hash=_canonical_hash({"base_snapshot_id": base_snapshot_id}),
            disclosure_hash="0" * 64,
            experiment_kind="temporal_hypothesis",
            base_snapshot_ref=base_snapshot_id,
            source_mode="synthetic_fixture",
            synthetic_fixture_ref=base_snapshot_id,
            created_at=epoch,
            updated_at=epoch,
        ),
        base_luck_layer_id=luck_layer_id,
        base_year_layer_id=year_layer_id,
        selected_luck_layer_id=luck_layer_id,
        selected_year_layer_id=year_layer_id,
    )


def apply_canvas_action(
    *,
    source: MingliCanvasCompileInput,
    sandbox: TemporalSandboxState,
    action: CanvasAction,
) -> TemporalSandboxState:
    if action.action_type == "restore":
        return restore_temporal_sandbox(sandbox)
    if sandbox.status not in {"active", "modified"}:
        raise CanvasCompileError("sandbox_action_requires_active_state")
    layers = {item.layer_id: item for item in source.temporal_layers}
    target = layers.get(action.target_layer_id) if action.target_layer_id else None
    if action.action_type != "clear_year" and target is None:
        raise CanvasCompileError(f"sandbox_action_missing_layer:{action.target_layer_id}")
    if action.action_type == "set_luck" and target and target.layer_type != "luck":
        raise CanvasCompileError("sandbox_action_luck_requires_luck_layer")
    if action.action_type in {"set_year", "replace_year"} and target and target.layer_type != "year":
        raise CanvasCompileError("sandbox_action_year_requires_year_layer")

    before = sandbox.selected_luck_layer_id if action.action_type == "set_luck" else sandbox.selected_year_layer_id
    after = "" if action.action_type == "clear_year" else action.target_layer_id
    field_path = "temporal.luck" if action.action_type == "set_luck" else "temporal.year"
    source_mode: Literal["derived", "hypothetical"] = (
        "hypothetical" if target and target.layer_mode == "hypothetical" else "derived"
    )
    mutation = CanvasSandboxMutation(
        mutation_id=f"mutation-{_canonical_hash({'session': sandbox.sandbox_session_id, 'revision': sandbox.revision + 1, 'action': action.model_dump(mode='json')})[:24]}",
        action_type=action.action_type,
        field_path=field_path,
        before_layer_id=before,
        after_layer_id=after,
        base_snapshot_id=sandbox.base_snapshot_id,
        source_mode=source_mode,
        source_refs=[action.source_ref, *(target.source_refs if target else [])],
    )
    updates: dict[str, Any] = {
        "lab_session": update_lab_session(
            sandbox.lab_session,
            status="modified",
            now=sandbox.lab_session.updated_at,
        ),
        "mutations": [*sandbox.mutations, mutation],
        "current_canvas_spec_id": "",
        "current_diff_spec_id": "",
    }
    if action.action_type == "set_luck":
        updates["selected_luck_layer_id"] = after
    else:
        updates["selected_year_layer_id"] = after
    return sandbox.model_copy(update=updates)


def restore_temporal_sandbox(sandbox: TemporalSandboxState) -> TemporalSandboxState:
    if sandbox.status not in {"active", "modified"}:
        raise CanvasCompileError("sandbox_restore_requires_active_state")
    return sandbox.model_copy(update={
        "lab_session": update_lab_session(
            sandbox.lab_session,
            status="restored",
            now=sandbox.lab_session.updated_at,
        ),
        "selected_luck_layer_id": sandbox.base_luck_layer_id,
        "selected_year_layer_id": sandbox.base_year_layer_id,
        "current_canvas_spec_id": "",
        "current_diff_spec_id": "",
    })


def compile_canvas_spec(request: CanvasCompileRequest) -> MingliCanvasSpec:
    source = request.source
    layers = {item.layer_id: item for item in source.temporal_layers}
    sandbox_active = request.sandbox is not None and request.sandbox.status in {"active", "modified"}
    luck_id = request.sandbox.selected_luck_layer_id if sandbox_active else request.luck_layer_id
    year_id = request.sandbox.selected_year_layer_id if sandbox_active else request.year_layer_id
    selected = _selected_layers(stage=request.stage, luck_id=luck_id, year_id=year_id, layers=layers)

    slots = list(source.chart.slots)
    nodes = {item.node_ref: item for item in source.chart.nodes}
    relations = {item.relation_ref: item for item in source.chart.relations}
    clusters = {item.cluster_ref: item for item in source.chart.clusters}
    paths = {item.path_ref: item for item in source.life_case.paths}

    for layer in selected:
        slots.append(layer.slot)
        nodes.update({item.node_ref: item for item in layer.nodes})
        relations.update({item.relation_ref: item for item in layer.relations})
        clusters.update({item.cluster_ref: item for item in layer.clusters})
        paths.update({item.path_ref: item for item in layer.paths})
        for removal in layer.removals:
            target = {"node": nodes, "relation": relations, "cluster": clusters, "path": paths}[removal.object_type]
            target.pop(removal.target_ref, None)
        for update in layer.path_updates:
            current = paths.get(update.path_ref)
            if current is None:
                raise CanvasCompileError(f"canvas_path_update_missing_path:{update.path_ref}")
            paths[update.path_ref] = current.model_copy(update={
                "semantic_state": update.semantic_state,
                "state_trace": update.state_trace,
                "change_reason_refs": update.change_reason_refs,
            })

    sandbox_id = request.sandbox.sandbox_session_id if sandbox_active else ""
    temporal_snapshot_id = selected[-1].temporal_snapshot_id if selected else ""
    return _issue_canvas_spec(
        chart_version_id=source.chart.chart_version_id,
        life_case_id=source.life_case.life_case_id,
        compiler_version=source.compiler_version,
        compiled_at=source.compiled_at,
        base_uncertainty=source.life_case.uncertainty,
        must_not_say=source.life_case.must_not_say,
        stage=request.stage,
        temporal_snapshot_id=temporal_snapshot_id,
        sandbox_session_id=sandbox_id,
        audience_role=None,
        slots=slots,
        nodes=list(nodes.values()),
        relations=list(relations.values()),
        clusters=list(clusters.values()),
        paths=list(paths.values()),
    )


def compile_canvas_diff(
    from_spec: MingliCanvasSpec,
    to_spec: MingliCanvasSpec,
    *,
    source_action_ref: str,
) -> CanvasDiffSpec:
    from_nodes = {item.node_ref: item for item in from_spec.nodes}
    to_nodes = {item.node_ref: item for item in to_spec.nodes}
    from_relations = {item.relation_ref: item for item in from_spec.relations}
    to_relations = {item.relation_ref: item for item in to_spec.relations}
    from_clusters = {item.cluster_ref: item for item in from_spec.clusters}
    to_clusters = {item.cluster_ref: item for item in to_spec.clusters}
    from_paths = {item.path_ref: item for item in from_spec.paths}
    to_paths = {item.path_ref: item for item in to_spec.paths}

    added_nodes = _added_deltas("node", from_nodes, to_nodes)
    removed_nodes = _removed_deltas("node", from_nodes, to_nodes)
    added_relations = _added_deltas("relation", from_relations, to_relations)
    removed_relations = _removed_deltas("relation", from_relations, to_relations)
    changed_relations = _state_deltas("relation", from_relations, to_relations)
    added_clusters = _added_deltas("cluster", from_clusters, to_clusters)
    removed_clusters = _removed_deltas("cluster", from_clusters, to_clusters)
    path_deltas = _path_deltas(from_paths, to_paths)
    epistemic = _epistemic_deltas(
        ("node", from_nodes, to_nodes),
        ("relation", from_relations, to_relations),
        ("cluster", from_clusters, to_clusters),
        ("path", from_paths, to_paths),
    )

    grouped = {kind: [item for item in path_deltas if item.change_type == kind] for kind in (
        "introduced", "removed", "activated", "blocked", "reopened", "reinforced", "weakened", "unchanged"
    )}
    explanation_refs = sorted({
        ref
        for collection in [
            added_nodes, removed_nodes, added_relations, removed_relations, changed_relations,
            added_clusters, removed_clusters, path_deltas,
        ]
        for item in collection
        for ref in item.reason_refs
    })
    payload = {
        "from_spec_id": from_spec.identity.canvas_spec_id,
        "to_spec_id": to_spec.identity.canvas_spec_id,
        "source_action_ref": source_action_ref,
        "added_nodes": added_nodes,
        "removed_nodes": removed_nodes,
        "added_relations": added_relations,
        "removed_relations": removed_relations,
        "changed_relations": changed_relations,
        "added_clusters": added_clusters,
        "removed_clusters": removed_clusters,
        "introduced_paths": grouped["introduced"],
        "removed_paths": grouped["removed"],
        "activated_paths": grouped["activated"],
        "blocked_paths": grouped["blocked"],
        "reopened_paths": grouped["reopened"],
        "reinforced_paths": grouped["reinforced"],
        "weakened_paths": grouped["weakened"],
        "unchanged_paths": grouped["unchanged"],
        "changed_epistemic_status": epistemic,
        "explanation_refs": explanation_refs,
        "uncertainty": sorted(set(to_spec.epistemology.uncertainty)),
    }
    digest = _canonical_hash(payload)
    return CanvasDiffSpec(
        diff_id=f"canvas-diff-{digest[:24]}",
        content_hash=digest,
        **payload,
    )


def project_canvas_spec_for_role(spec: MingliCanvasSpec, role: CanvasRole) -> MingliCanvasSpec:
    slots = [item for item in spec.semantic_slots if _trace_visible(item.trace, role)]
    if role in {"guest", "member"}:
        slots = [item.model_copy(update={"hidden_stems": []}) for item in slots]
    nodes = [item for item in spec.nodes if _trace_visible(item.trace, role)]
    node_refs = {item.node_ref for item in nodes}
    relations = [
        item for item in spec.relations
        if item.from_node_ref in node_refs
        and item.to_node_ref in node_refs
        and _trace_visible(item.trace, role)
        and _trace_visible(item.state_trace, role)
    ]
    relation_refs = {item.relation_ref for item in relations}
    clusters = [
        item for item in spec.clusters
        if set(item.node_refs).issubset(node_refs)
        and set(item.relation_refs).issubset(relation_refs)
        and _trace_visible(item.trace, role)
    ]
    paths = [
        item for item in spec.paths
        if set(item.node_refs).issubset(node_refs)
        and set(item.relation_refs).issubset(relation_refs)
        and _trace_visible(item.trace, role)
        and _trace_visible(item.state_trace, role)
    ]
    visible_refs = {
        *(item.slot_ref for item in slots),
        *node_refs,
        *relation_refs,
        *(item.cluster_ref for item in clusters),
        *(item.path_ref for item in paths),
    }
    presentation = spec.presentation.model_copy(update={
        "visual_anchors": [item for item in spec.presentation.visual_anchors if item.object_ref in visible_refs],
        "emphasis": [item for item in spec.presentation.emphasis if item in visible_refs],
        "narration_targets": [item for item in spec.presentation.narration_targets if item in visible_refs],
    })
    return _issue_canvas_spec(
        chart_version_id=spec.identity.chart_version_id,
        life_case_id=spec.identity.life_case_id,
        compiler_version=spec.identity.compiler_version,
        compiled_at=spec.identity.compiled_at,
        base_uncertainty=spec.epistemology.uncertainty,
        must_not_say=spec.epistemology.must_not_say,
        stage=spec.stage,
        temporal_snapshot_id=spec.identity.temporal_snapshot_id,
        sandbox_session_id=spec.identity.sandbox_session_id,
        audience_role=role,
        slots=slots,
        nodes=nodes,
        relations=relations,
        clusters=clusters,
        paths=paths,
        presentation=presentation,
    )


def compile_canvas_context(
    *,
    spec: MingliCanvasSpec,
    diff: CanvasDiffSpec | None,
    role: CanvasRole,
    selected_object_refs: list[str],
    visible_layers: list[str],
    sandbox: TemporalSandboxState | None = None,
) -> CanvasContextPack:
    projected = project_canvas_spec_for_role(spec, role)
    disclosed = sorted({
        *(item.slot_ref for item in projected.semantic_slots),
        *(item.node_ref for item in projected.nodes),
        *(item.relation_ref for item in projected.relations),
        *(item.cluster_ref for item in projected.clusters),
        *(item.path_ref for item in projected.paths),
    })
    disclosed_set = set(disclosed)
    selected = sorted(set(selected_object_refs).intersection(disclosed_set))
    committed = sorted(item.path_ref for item in projected.paths if item.trace.epistemic_status == "committed")
    candidate = sorted(item.path_ref for item in projected.paths if item.trace.epistemic_status == "candidate")
    blocked = sorted(item.path_ref for item in projected.paths if item.trace.epistemic_status == "blocked")
    mutations = []
    if sandbox and sandbox.status == "modified":
        mutations = [item for item in sandbox.mutations if item.source_mode == "hypothetical"]
    diff_reasons: list[str] = []
    if diff:
        delta_collections = [
            diff.added_nodes,
            diff.removed_nodes,
            diff.added_relations,
            diff.removed_relations,
            diff.changed_relations,
            diff.added_clusters,
            diff.removed_clusters,
            diff.introduced_paths,
            diff.removed_paths,
            diff.activated_paths,
            diff.blocked_paths,
            diff.reopened_paths,
            diff.reinforced_paths,
            diff.weakened_paths,
            diff.unchanged_paths,
        ]
        diff_reasons = sorted({
            ref
            for collection in delta_collections
            for item in collection
            if item.target_ref in disclosed_set
            for ref in item.reason_refs
        })
    payload = {
        "canvas_spec_id": projected.identity.canvas_spec_id,
        "diff_spec_id": diff.diff_id if diff else "",
        "role": role,
        "current_stage": projected.stage,
        "selected_object_refs": selected,
        "visible_layers": sorted(set(visible_layers).intersection(projected.presentation.layers)),
        "committed_path_refs": committed,
        "candidate_path_refs": candidate,
        "blocked_path_refs": blocked,
        "hypothetical_mutations": mutations,
        "diff_reason_refs": diff_reasons,
        "uncertainty": projected.epistemology.uncertainty,
        "must_not_say": projected.epistemology.must_not_say,
        "disclosed_object_refs": disclosed,
    }
    digest = _canonical_hash(payload)
    return CanvasContextPack(
        context_pack_id=f"canvas-context-{digest[:24]}",
        content_hash=digest,
        **payload,
    )


def _selected_layers(
    *,
    stage: CanvasStage,
    luck_id: str,
    year_id: str,
    layers: dict[str, CanvasTemporalLayer],
) -> list[CanvasTemporalLayer]:
    if stage == "natal":
        if luck_id or year_id:
            raise CanvasCompileError("natal_stage_cannot_select_temporal_layer")
        return []
    if not luck_id or luck_id not in layers or layers[luck_id].layer_type != "luck":
        raise CanvasCompileError("luck_stage_requires_valid_luck_layer")
    selected = [layers[luck_id]]
    if stage == "luck":
        if year_id:
            raise CanvasCompileError("luck_stage_cannot_select_year_layer")
        return selected
    if not year_id or year_id not in layers or layers[year_id].layer_type != "year":
        raise CanvasCompileError("year_stage_requires_valid_year_layer")
    return [*selected, layers[year_id]]


def _issue_canvas_spec(
    *,
    chart_version_id: str,
    life_case_id: str,
    compiler_version: str,
    compiled_at: datetime,
    base_uncertainty: list[str],
    must_not_say: list[str],
    stage: CanvasStage,
    temporal_snapshot_id: str,
    sandbox_session_id: str,
    audience_role: CanvasRole | None,
    slots: list[CanvasSemanticSlot],
    nodes: list[CanvasNode],
    relations: list[CanvasRelation],
    clusters: list[CanvasCluster],
    paths: list[CanvasPath],
    presentation: CanvasPresentation | None = None,
) -> MingliCanvasSpec:
    slots = sorted(slots, key=lambda item: _slot_order(item.slot_type))
    nodes = sorted(nodes, key=lambda item: item.node_ref)
    relations = sorted(relations, key=lambda item: item.relation_ref)
    clusters = sorted(clusters, key=lambda item: item.cluster_ref)
    paths = sorted(paths, key=lambda item: item.path_ref)
    traces = [
        *(item.trace for item in slots),
        *(item.trace for item in nodes),
        *(item.trace for item in relations),
        *(item.state_trace for item in relations),
        *(item.trace for item in clusters),
        *(item.trace for item in paths),
        *(item.state_trace for item in paths),
    ]
    epistemology = CanvasEpistemology(
        epistemic_statuses=sorted(set(item.epistemic_status for item in traces)),
        source_refs=sorted({ref for item in traces for ref in item.source_refs}),
        commitment_refs=sorted({ref for item in traces for ref in item.commitment_refs}),
        uncertainty=sorted({*base_uncertainty, *(reason for item in traces for reason in item.uncertainty)}),
        rejection_or_block_reasons=sorted({reason for item in traces for reason in item.rejection_or_block_reasons}),
        must_not_say=must_not_say,
    )
    interaction = CanvasInteractionPolicy(
        allowed_interactions=["select_object", "toggle_layer", "set_luck", "set_year", "replace_year", "restore"],
        immutable_slots=[item.slot_ref for item in slots if item.immutable],
        sandbox_mutations=["temporal.luck", "temporal.year"],
    )
    if presentation is None:
        object_refs = [
            *(item.slot_ref for item in slots),
            *(item.node_ref for item in nodes),
            *(item.relation_ref for item in relations),
            *(item.cluster_ref for item in clusters),
            *(item.path_ref for item in paths),
        ]
        presentation_trace = CanvasTrace(
            source_mode="presentation",
            epistemic_status="presentation_only",
            source_refs=["presentation:canvas-default-v1"],
            disclosure="public",
        )
        presentation = CanvasPresentation(
            visual_anchors=[
                CanvasVisualAnchor(
                    anchor_ref=f"anchor-{ref}",
                    object_ref=ref,
                    group=_anchor_group(ref),
                    trace=presentation_trace,
                )
                for ref in object_refs
            ],
            layers=["generation_control", "combination", "conflict", "work_path"],
            emphasis=[item.path_ref for item in paths if item.trace.epistemic_status == "committed"],
            narration_targets=[item.path_ref for item in paths if item.trace.epistemic_status in {"committed", "candidate"}],
        )
    identity_seed = {
        "chart_version_id": chart_version_id,
        "temporal_snapshot_id": temporal_snapshot_id,
        "life_case_id": life_case_id,
        "sandbox_session_id": sandbox_session_id,
        "compiler_version": compiler_version,
        "compiled_at": compiled_at,
        "audience_role": audience_role,
    }
    body = {
        "stage": stage,
        "semantic_slots": slots,
        "nodes": nodes,
        "relations": relations,
        "clusters": clusters,
        "paths": paths,
        "epistemology": epistemology,
        "interaction": interaction,
        "presentation": presentation,
    }
    digest = _canonical_hash({"identity": identity_seed, **body})
    identity = CanvasIdentity(
        canvas_spec_id=f"canvas-spec-{digest[:24]}",
        content_hash=digest,
        **identity_seed,
    )
    return MingliCanvasSpec(identity=identity, **body)


def _added_deltas(object_type: str, before: dict[str, Any], after: dict[str, Any]) -> list[CanvasObjectDelta]:
    return [
        _object_delta(object_type, after[ref], "introduced", before_state="", after_state=_object_state(after[ref]))
        for ref in sorted(set(after) - set(before))
    ]


def _removed_deltas(object_type: str, before: dict[str, Any], after: dict[str, Any]) -> list[CanvasObjectDelta]:
    return [
        _object_delta(object_type, before[ref], "removed", before_state=_object_state(before[ref]), after_state="")
        for ref in sorted(set(before) - set(after))
    ]


def _state_deltas(object_type: str, before: dict[str, Any], after: dict[str, Any]) -> list[CanvasObjectDelta]:
    result: list[CanvasObjectDelta] = []
    for ref in sorted(set(before).intersection(after)):
        old = _object_state(before[ref])
        new = _object_state(after[ref])
        if old != new:
            result.append(_object_delta(object_type, after[ref], _semantic_change(old, new), old, new))
    return result


def _path_deltas(before: dict[str, CanvasPath], after: dict[str, CanvasPath]) -> list[CanvasObjectDelta]:
    result = _added_deltas("path", before, after)
    result.extend(_removed_deltas("path", before, after))
    for ref in sorted(set(before).intersection(after)):
        old = before[ref].semantic_state
        new = after[ref].semantic_state
        result.append(_object_delta("path", after[ref], _semantic_change(old, new), old, new))
    return sorted(result, key=lambda item: (item.target_ref, item.change_type))


def _epistemic_deltas(*collections: tuple[str, dict[str, Any], dict[str, Any]]) -> list[CanvasEpistemicDelta]:
    result: list[CanvasEpistemicDelta] = []
    for object_type, before, after in collections:
        for ref in sorted(set(before).intersection(after)):
            pairs = [("object", before[ref].trace, after[ref].trace)]
            if hasattr(before[ref], "state_trace"):
                pairs.append(("state", before[ref].state_trace, after[ref].state_trace))
            for scope, old, new in pairs:
                if old.epistemic_status == new.epistemic_status:
                    continue
                result.append(CanvasEpistemicDelta(
                    object_type=object_type,
                    target_ref=ref,
                    status_scope=scope,
                    before_status=old.epistemic_status,
                    after_status=new.epistemic_status,
                    reason_refs=_reasons(after[ref]),
                    source_refs=sorted(set(old.source_refs + new.source_refs)),
                ))
    return result


def _object_delta(
    object_type: str,
    item: Any,
    change_type: CanvasChangeType,
    before_state: str,
    after_state: str,
) -> CanvasObjectDelta:
    return CanvasObjectDelta(
        object_type=object_type,
        target_ref=_object_ref(item),
        change_type=change_type,
        before_state=before_state,
        after_state=after_state,
        reason_refs=_reasons(item),
        source_refs=_sources(item),
    )


def _semantic_change(before: str, after: str) -> CanvasChangeType:
    if before == after:
        return "unchanged"
    if before == "blocked" and after != "blocked":
        return "reopened"
    if after == "blocked":
        return "blocked"
    if after == "reinforced":
        return "reinforced"
    if after == "weakened" or (before == "active" and after == "latent"):
        return "weakened"
    if before == "latent" and after == "active":
        return "activated"
    return "activated"


def _object_ref(item: Any) -> str:
    for field in ("node_ref", "relation_ref", "cluster_ref", "path_ref"):
        value = getattr(item, field, "")
        if value:
            return value
    raise CanvasCompileError("canvas_object_missing_ref")


def _object_state(item: Any) -> str:
    return str(getattr(item, "semantic_state", item.trace.epistemic_status))


def _sources(item: Any) -> list[str]:
    refs = list(item.trace.source_refs)
    if hasattr(item, "state_trace"):
        refs.extend(item.state_trace.source_refs)
    return sorted(set(refs))


def _reasons(item: Any) -> list[str]:
    reasons = list(getattr(item, "change_reason_refs", []))
    reasons.extend(item.trace.rejection_or_block_reasons)
    if hasattr(item, "state_trace"):
        reasons.extend(item.state_trace.rejection_or_block_reasons)
    return sorted(set(reasons or _sources(item)))


def _trace_visible(trace: CanvasTrace, role: CanvasRole) -> bool:
    if role == "admin":
        return True
    rank = {"public": 0, "member": 1, "practitioner": 2, "research": 3}
    role_rank = {"guest": 0, "member": 1, "practitioner": 2, "research": 3}[role]
    return role_rank >= rank[trace.disclosure]


def _slot_order(slot_type: str) -> int:
    return {"natal_year": 0, "natal_month": 1, "natal_day": 2, "natal_hour": 3, "luck": 4, "year": 5}[slot_type]


def _anchor_group(ref: str) -> str:
    return ref.split("-", 1)[0]


def _unique_refs(rows: list[Any], field: str, error: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for row in rows:
        ref = str(getattr(row, field))
        if ref in result:
            raise ValueError(f"{error}:{ref}")
        result[ref] = row
    return result


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(
        _canonical_value(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _canonical_value(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return _canonical_value(value.model_dump(mode="json"))
    if isinstance(value, dict):
        return {str(key): _canonical_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical_value(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    return value
