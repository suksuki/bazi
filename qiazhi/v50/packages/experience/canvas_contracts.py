from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import Field, computed_field, model_validator

from experience.compiler import canonical_hash
from experience.contracts import ExperienceModel
from experience.lab import MingliLabSession


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
            scene_source_hash=canonical_hash({"base_snapshot_id": base_snapshot_id}),
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




def _unique_refs(rows: list[Any], field: str, error: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for row in rows:
        ref = str(getattr(row, field))
        if ref in result:
            raise ValueError(f"{error}:{ref}")
        result[ref] = row
    return result

