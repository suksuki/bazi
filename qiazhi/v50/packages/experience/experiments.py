from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import Field, computed_field, model_validator

from experience.contracts import ExperienceModel
from experience.lab import MingliLabSession, update_lab_session


ExperimentAuthority = Literal["visual_only", "deterministic_structure", "reasoning_required"]


class PillarVisual(ExperienceModel):
    pillar_id: str = Field(min_length=1, max_length=120)
    label: Literal["年柱", "月柱", "日柱", "时柱"]
    stem: str = Field(min_length=1, max_length=4)
    branch: str = Field(min_length=1, max_length=4)
    hidden_stems: list[str] = Field(default_factory=list)
    stem_node_id: str = Field(min_length=1, max_length=260)
    branch_node_id: str = Field(min_length=1, max_length=260)
    visual_anchor_id: str = Field(min_length=1, max_length=120)


class MechanismNode(ExperienceModel):
    node_id: str = Field(min_length=1, max_length=260)
    label: str = Field(min_length=1, max_length=20)
    node_type: str = Field(min_length=1, max_length=80)
    position: str = Field(default="", max_length=120)
    element: str = Field(default="", max_length=40)
    yin_yang: str = Field(default="", max_length=40)
    ten_god: str = Field(default="", max_length=80)
    visual_anchor_id: str = Field(min_length=1, max_length=160)
    visual_group: Literal["pillar", "hidden", "path"] = "path"
    selectable: bool = True
    source_refs: list[str] = Field(default_factory=list)


class MechanismEdge(ExperienceModel):
    edge_id: str = Field(min_length=1, max_length=320)
    from_node_id: str = Field(min_length=1, max_length=260)
    to_node_id: str = Field(min_length=1, max_length=260)
    relation_type: str = Field(min_length=1, max_length=100)
    relation_label: str = Field(default="", max_length=120)
    path_eligibility: Literal["eligible", "evidence_only", "not_yet_qualified"]
    eligibility_reason_refs: list[str] = Field(min_length=1)
    source_refs: list[str] = Field(default_factory=list)


class MechanismPathEvidence(ExperienceModel):
    segment_validity: Literal["complete", "partial", "broken"]
    direction_coherence: Literal["coherent", "mixed", "invalid"]
    temporal_coherence: Literal["active", "partial", "inactive", "not_evaluated"]
    root_support: Literal["present_ungraded", "absent", "not_evaluated"]
    reveal_support: Literal["present_ungraded", "absent", "not_evaluated"]
    blocking: Literal["none_detected", "potential", "confirmed"]
    closure: Literal["closed", "open", "interrupted"]
    provenance_quality: Literal["high", "medium", "low"]
    reason_refs: list[str] = Field(min_length=1)


class MechanismPath(ExperienceModel):
    path_ref: str = Field(min_length=1, max_length=260)
    path_kind: Literal["approved", "competing"]
    display_label: str = Field(min_length=1, max_length=240)
    node_ids: list[str] = Field(min_length=2)
    edge_ids: list[str] = Field(min_length=1)
    relation_types: list[str] = Field(min_length=1)
    validation_state: Literal[
        "qualified",
        "qualified_with_conditions",
        "broken",
        "unresolved",
    ]
    evidence: MechanismPathEvidence
    claim_refs: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)


class MingliMechanismSnapshot(ExperienceModel):
    schema_version: Literal["deepbazi.mingli_mechanism_snapshot.v1"] = (
        "deepbazi.mingli_mechanism_snapshot.v1"
    )
    snapshot_id: str = Field(min_length=1, max_length=220)
    snapshot_hash: str = Field(min_length=64, max_length=64)
    case_id: str = Field(min_length=1, max_length=180)
    chart_version: str = Field(min_length=1, max_length=180)
    life_case_version: str = Field(min_length=1, max_length=180)
    cognitive_record_id: str = Field(min_length=1, max_length=180)
    scene_id: str = Field(default="scene-unbound-fixture", min_length=1, max_length=180)
    scene_source_hash: str = Field(default="0" * 64, min_length=64, max_length=64)
    disclosure_hash: str = Field(default="0" * 64, min_length=64, max_length=64)
    pillars: list[PillarVisual] = Field(min_length=4, max_length=4)
    nodes: list[MechanismNode] = Field(min_length=2)
    edges: list[MechanismEdge] = Field(min_length=1)
    approved_paths: list[MechanismPath] = Field(min_length=1)
    competing_paths: list[MechanismPath] = Field(default_factory=list)
    approved_key_nodes: list[str] = Field(default_factory=list)
    unresolved_conditions: list[str] = Field(default_factory=list)
    claim_refs: list[str] = Field(default_factory=list)
    visual_anchors: dict[str, str] = Field(default_factory=dict)
    issued_at: datetime
    boundaries: list[str] = Field(
        default_factory=lambda: [
            "实验分支",
            "原命盘没有改变",
            "当前探索不会自动写入正式认知",
        ]
    )

    @model_validator(mode="after")
    def validate_graph_references(self) -> "MingliMechanismSnapshot":
        node_ids = {item.node_id for item in self.nodes}
        edge_ids = {item.edge_id for item in self.edges}
        if len(node_ids) != len(self.nodes):
            raise ValueError("mechanism_snapshot_duplicate_node")
        if len(edge_ids) != len(self.edges):
            raise ValueError("mechanism_snapshot_duplicate_edge")
        for edge in self.edges:
            if edge.from_node_id not in node_ids or edge.to_node_id not in node_ids:
                raise ValueError(f"mechanism_snapshot_edge_missing_node:{edge.edge_id}")
        for path in [*self.approved_paths, *self.competing_paths]:
            if not set(path.node_ids).issubset(node_ids):
                raise ValueError(f"mechanism_snapshot_path_missing_node:{path.path_ref}")
            if not set(path.edge_ids).issubset(edge_ids):
                raise ValueError(f"mechanism_snapshot_path_missing_edge:{path.path_ref}")
        return self


class VisualInteractionCapability(ExperienceModel):
    action: str = Field(min_length=1, max_length=100)
    authority: ExperimentAuthority
    available: bool = True


class MingliVisualSpec(ExperienceModel):
    schema_version: Literal["deepbazi.mingli_visual_spec.v1"] = "deepbazi.mingli_visual_spec.v1"
    snapshot_hash: str = Field(min_length=64, max_length=64)
    pillars: list[PillarVisual] = Field(min_length=4, max_length=4)
    nodes: list[MechanismNode] = Field(min_length=2)
    edges: list[MechanismEdge] = Field(min_length=1)
    paths: list[MechanismPath] = Field(min_length=1)
    layers: list[str] = Field(default_factory=lambda: ["pillars", "approved_path", "competing_path"])
    visual_states: list[str] = Field(
        default_factory=lambda: [
            "normal",
            "focus",
            "active",
            "supporting",
            "competing",
            "uncertain",
            "ablated",
        ]
    )
    interaction_capabilities: list[VisualInteractionCapability] = Field(default_factory=list)
    stable_layout: bool = True


class MingliVisualCue(ExperienceModel):
    at_ms: int = Field(ge=0)
    action: Literal["reveal", "focus", "pulse", "flow", "split", "dim", "sever", "ghost", "restore", "compare"]
    target: str = Field(min_length=1, max_length=320)


class NodeAblationOperation(ExperienceModel):
    operation_id: str = Field(min_length=1, max_length=180)
    operation_type: Literal["remove_node"] = "remove_node"
    node_id: str = Field(min_length=1, max_length=260)
    authority: Literal["deterministic_structure"] = "deterministic_structure"
    applied_at: datetime


class MechanismSandboxState(ExperienceModel):
    schema_version: Literal[
        "deepbazi.mingli_sandbox_state.v1",
        "deepbazi.mechanism_sandbox_state.v2",
    ] = "deepbazi.mechanism_sandbox_state.v2"
    lab_session: MingliLabSession
    predicted_key_node_id: str | None = Field(default=None, max_length=260)
    selected_nodes: list[str] = Field(default_factory=list)
    ablation_operations: list[NodeAblationOperation] = Field(default_factory=list)
    temporal_overlay: str | None = Field(default=None, max_length=160)
    active_hypothesis: str | None = Field(default=None, max_length=260)
    comparison_mode: Literal["baseline", "baseline_modified"] = "baseline"

    @model_validator(mode="before")
    @classmethod
    def upgrade_legacy_state(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        payload = dict(value)
        if "lab_session" in payload:
            for field in (
                "sandbox_id",
                "participant_run_id",
                "base_snapshot_hash",
                "status",
                "created_at",
                "updated_at",
                "writes_life_case",
            ):
                payload.pop(field, None)
            return payload
        created_at = payload.pop("created_at", datetime(1970, 1, 1, tzinfo=timezone.utc))
        updated_at = payload.pop("updated_at", created_at)
        base_snapshot_hash = str(payload.pop("base_snapshot_hash"))
        payload["lab_session"] = MingliLabSession(
            session_id=str(payload.pop("sandbox_id")),
            participant_run_id=str(payload.pop("participant_run_id")),
            case_ref="legacy-unresolved",
            scene_id="legacy-unresolved",
            scene_source_hash=base_snapshot_hash,
            disclosure_hash="0" * 64,
            experiment_kind="mechanism_ablation",
            base_snapshot_ref=base_snapshot_hash,
            source_mode="legacy_unresolved",
            status=payload.pop("status", "active"),
            created_at=created_at,
            updated_at=updated_at,
        ).model_dump(mode="json")
        payload.pop("writes_life_case", None)
        return payload

    @computed_field
    @property
    def sandbox_id(self) -> str:
        return self.lab_session.session_id

    @computed_field
    @property
    def participant_run_id(self) -> str:
        return self.lab_session.participant_run_id

    @computed_field
    @property
    def base_snapshot_hash(self) -> str:
        return self.lab_session.base_snapshot_ref

    @computed_field
    @property
    def status(self) -> str:
        return self.lab_session.status

    @computed_field
    @property
    def created_at(self) -> datetime:
        return self.lab_session.created_at

    @computed_field
    @property
    def updated_at(self) -> datetime:
        return self.lab_session.updated_at

    @computed_field
    @property
    def writes_life_case(self) -> Literal[False]:
        return False


class DeterministicChangeSet(ExperienceModel):
    removed_node_id: str = Field(min_length=1, max_length=260)
    invalidated_edges: list[str] = Field(default_factory=list)
    remaining_edges: list[str] = Field(default_factory=list)
    affected_paths: list[str] = Field(default_factory=list)
    unaffected_paths: list[str] = Field(default_factory=list)
    invalidated_claim_refs: list[str] = Field(default_factory=list)


class SandboxResult(ExperienceModel):
    schema_version: Literal["deepbazi.sandbox_result.v1"] = "deepbazi.sandbox_result.v1"
    result_id: str = Field(min_length=1, max_length=180)
    sandbox_id: str = Field(min_length=1, max_length=180)
    base_snapshot_hash: str = Field(min_length=64, max_length=64)
    modified_snapshot_hash: str = Field(min_length=64, max_length=64)
    authority: Literal["deterministic_structure"] = "deterministic_structure"
    deterministic_changes: DeterministicChangeSet
    reasoning_required: bool = True
    uncertainty: list[str] = Field(default_factory=list)
    boundaries: list[str] = Field(
        default_factory=lambda: [
            "实验分支",
            "原命盘没有改变",
            "结构变化可以确定，现实命理含义仍需专业推理",
        ]
    )
    created_at: datetime
    writes_life_case: Literal[False] = False


def issue_mechanism_snapshot(**values: Any) -> MingliMechanismSnapshot:
    payload = {
        "schema_version": "deepbazi.mingli_mechanism_snapshot.v1",
        **values,
        "snapshot_hash": "0" * 64,
    }
    provisional = MingliMechanismSnapshot.model_validate(payload)
    signature = canonical_payload_hash(provisional.model_dump(mode="json", exclude={"snapshot_hash"}))
    return provisional.model_copy(update={"snapshot_hash": signature})


def compile_visual_spec(snapshot: MingliMechanismSnapshot) -> MingliVisualSpec:
    return MingliVisualSpec(
        snapshot_hash=snapshot.snapshot_hash,
        pillars=snapshot.pillars,
        nodes=snapshot.nodes,
        edges=snapshot.edges,
        paths=[*snapshot.approved_paths, *snapshot.competing_paths],
        interaction_capabilities=[
            VisualInteractionCapability(action="focus_node", authority="visual_only"),
            VisualInteractionCapability(action="toggle_path", authority="visual_only"),
            VisualInteractionCapability(action="ablate_node", authority="deterministic_structure"),
            VisualInteractionCapability(action="interpret_real_world_meaning", authority="reasoning_required"),
        ],
    )


def create_sandbox_state(
    *,
    participant_run_id: str,
    snapshot: MingliMechanismSnapshot,
    predicted_key_node_id: str | None = None,
) -> MechanismSandboxState:
    now = datetime.now(timezone.utc)
    if predicted_key_node_id is not None:
        _require_selectable_node(snapshot, predicted_key_node_id)
    return MechanismSandboxState(
        lab_session=MingliLabSession(
            session_id=f"lab-{uuid4().hex[:20]}",
            participant_run_id=participant_run_id,
            case_ref=snapshot.case_id,
            scene_id=snapshot.scene_id,
            scene_source_hash=snapshot.scene_source_hash,
            disclosure_hash=snapshot.disclosure_hash,
            experiment_kind="mechanism_ablation",
            base_snapshot_ref=snapshot.snapshot_hash,
            source_mode=(
                "canonical_projection"
                if not snapshot.scene_id.startswith("scene-unbound")
                else "synthetic_fixture"
            ),
            created_at=now,
            updated_at=now,
        ),
        predicted_key_node_id=predicted_key_node_id,
        selected_nodes=[predicted_key_node_id] if predicted_key_node_id else [],
    )


def apply_single_node_ablation(
    *,
    snapshot: MingliMechanismSnapshot,
    sandbox: MechanismSandboxState,
    node_id: str,
) -> tuple[MechanismSandboxState, SandboxResult]:
    if sandbox.base_snapshot_hash != snapshot.snapshot_hash:
        raise ValueError("sandbox_snapshot_hash_mismatch")
    if sandbox.ablation_operations:
        raise ValueError("single_node_ablation_already_completed")
    if sandbox.status != "active":
        raise ValueError("single_node_ablation_requires_active_sandbox")
    _require_selectable_node(snapshot, node_id)
    invalidated_edges = sorted(
        edge.edge_id
        for edge in snapshot.edges
        if edge.from_node_id == node_id or edge.to_node_id == node_id
    )
    invalidated_edge_set = set(invalidated_edges)
    paths = [*snapshot.approved_paths, *snapshot.competing_paths]
    affected = sorted(
        path.path_ref
        for path in paths
        if node_id in path.node_ids or invalidated_edge_set.intersection(path.edge_ids)
    )
    affected_set = set(affected)
    unaffected = sorted(path.path_ref for path in paths if path.path_ref not in affected_set)
    invalidated_claim_refs = sorted({
        claim_ref
        for path in paths
        if path.path_ref in affected_set
        for claim_ref in path.claim_refs
    })
    now = datetime.now(timezone.utc)
    operation = NodeAblationOperation(
        operation_id=f"ablation-{uuid4().hex[:20]}",
        node_id=node_id,
        applied_at=now,
    )
    remaining_edges = sorted(
        edge.edge_id for edge in snapshot.edges if edge.edge_id not in invalidated_edge_set
    )
    modified_hash = canonical_payload_hash({
        "base_snapshot_hash": snapshot.snapshot_hash,
        "operation": operation.model_dump(mode="json"),
        "remaining_edges": remaining_edges,
    })
    result = SandboxResult(
        result_id=f"sandbox-result-{uuid4().hex[:20]}",
        sandbox_id=sandbox.sandbox_id,
        base_snapshot_hash=snapshot.snapshot_hash,
        modified_snapshot_hash=modified_hash,
        deterministic_changes=DeterministicChangeSet(
            removed_node_id=node_id,
            invalidated_edges=invalidated_edges,
            remaining_edges=remaining_edges,
            affected_paths=affected,
            unaffected_paths=unaffected,
            invalidated_claim_refs=invalidated_claim_refs,
        ),
        uncertainty=[
            "本结果只说明已批准结构快照中的关系与路径完整性变化。",
            "它在现实生活中的表现，仍需专业 Reasoner 结合整盘重新解释。",
        ],
        created_at=now,
    )
    updated = sandbox.model_copy(update={
        "lab_session": update_lab_session(sandbox.lab_session, status="modified", now=now),
        "selected_nodes": list(dict.fromkeys([*sandbox.selected_nodes, node_id])),
        "ablation_operations": [*sandbox.ablation_operations, operation],
        "comparison_mode": "baseline_modified",
    })
    return updated, result


def restore_sandbox(sandbox: MechanismSandboxState) -> MechanismSandboxState:
    if not sandbox.ablation_operations:
        raise ValueError("experiment_ablation_required_before_restore")
    if sandbox.status == "saved":
        raise ValueError("saved_experiment_cannot_be_restored")
    now = datetime.now(timezone.utc)
    return sandbox.model_copy(update={
        "lab_session": update_lab_session(sandbox.lab_session, status="restored", now=now),
        "comparison_mode": "baseline",
    })


def canonical_payload_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _require_selectable_node(snapshot: MingliMechanismSnapshot, node_id: str) -> MechanismNode:
    node = next((item for item in snapshot.nodes if item.node_id == node_id), None)
    if node is None:
        raise ValueError("experiment_node_not_in_snapshot")
    if not node.selectable:
        raise ValueError("experiment_node_not_selectable")
    return node
