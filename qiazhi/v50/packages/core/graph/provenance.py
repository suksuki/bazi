from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any, Literal

from pydantic import Field, model_validator

from core.contracts.base import V50Model, require_non_empty


RELATION_ONTOLOGY_VERSION = "deepbazi.relation-ontology.pre-ra1.v1"


class RelationDirectionality(str, Enum):
    DIRECTED = "directed"
    SYMMETRIC = "symmetric"


class AssertionLifecycle(str, Enum):
    CANDIDATE = "candidate"
    COMMITTED = "committed"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"
    LEGACY_UNRESOLVED = "legacy_unresolved"


class MingliRelationState(str, Enum):
    POTENTIAL = "potential"
    STRUCTURAL = "structural"
    TIME_ACTIVATED = "time_activated"
    EFFECTIVE = "effective"


NodeScope = Literal["natal", "luck", "year", "month", "other"]
NodeLevel = Literal["pillar", "stem", "branch", "hidden_stem", "other"]


class NodeRef(V50Model):
    version: str = "deepbazi.node_ref.v1"
    node_ref: str = ""
    scene_ref: str
    life_case_id: str
    chart_version_id: str
    world_id: str
    scope: NodeScope
    slot: str
    level: NodeLevel
    component: str
    temporal_snapshot_ref: str = ""

    @model_validator(mode="after")
    def validate_identity(self) -> "NodeRef":
        for value, field in (
            (self.scene_ref, "scene_ref"),
            (self.life_case_id, "life_case_id"),
            (self.chart_version_id, "chart_version_id"),
            (self.world_id, "world_id"),
            (self.slot, "slot"),
            (self.component, "component"),
        ):
            require_non_empty(value, field)
        if self.scope != "natal" and not self.temporal_snapshot_ref:
            raise ValueError("temporal_node_requires_snapshot_ref")
        expected = _stable_id("node", self.identity_payload())
        if self.node_ref and self.node_ref != expected:
            raise ValueError("node_ref_identity_mismatch")
        object.__setattr__(self, "node_ref", expected)
        return self

    def identity_payload(self) -> dict[str, Any]:
        return {
            "scene_ref": self.scene_ref,
            "life_case_id": self.life_case_id,
            "chart_version_id": self.chart_version_id,
            "world_id": self.world_id,
            "scope": self.scope,
            "slot": self.slot,
            "level": self.level,
            "component": self.component,
            "temporal_snapshot_ref": self.temporal_snapshot_ref,
        }


class RelationPositionContext(V50Model):
    """Typed location evidence; it never decides strength or effectiveness."""

    version: str = "deepbazi.relation_position_context.six02.v1"
    source_scope: NodeScope
    target_scope: NodeScope
    source_slot: str
    target_slot: str
    source_level: NodeLevel
    target_level: NodeLevel
    adjacent: bool = False
    column_span: int | None = Field(default=None, ge=0)
    intervening_node_refs: list[str] = Field(default_factory=list)
    ref_namespace: Literal["candidate_node_key", "node_ref"] = "node_ref"
    direction: Literal[
        "same_column",
        "left_to_right",
        "right_to_left",
        "symmetric",
        "temporal_to_natal",
        "natal_to_temporal",
        "cross_temporal",
        "other",
    ] = "other"
    scene_layer: Literal[
        "natal_state",
        "luck_state",
        "year_state",
        "month_state",
        "mixed_temporal",
    ] = "natal_state"

    @model_validator(mode="after")
    def validate_position_context(self) -> "RelationPositionContext":
        require_non_empty(self.source_slot, "source_slot")
        require_non_empty(self.target_slot, "target_slot")
        same_semantic_column = (
            self.source_scope == self.target_scope
            and self.source_slot == self.target_slot
        )
        if self.adjacent and self.column_span != 1:
            raise ValueError("adjacent_relation_requires_one_column_span")
        if self.column_span == 0 and not same_semantic_column:
            raise ValueError("zero_column_span_requires_same_slot")
        if same_semantic_column and self.column_span not in {0, None}:
            raise ValueError("same_slot_relation_cannot_have_positive_column_span")
        if len(self.intervening_node_refs) != len(set(self.intervening_node_refs)):
            raise ValueError("relation_position_context_duplicate_intervening_ref")
        return self


class RelationKey(V50Model):
    version: str = "deepbazi.relation_key.v1"
    relation_key: str = ""
    scene_ref: str
    ontology_version: str = RELATION_ONTOLOGY_VERSION
    relation_type: str
    participant_refs: list[NodeRef] = Field(min_length=2)
    directionality: RelationDirectionality
    arity: int = Field(default=0, ge=2)
    scope: NodeScope = "natal"

    @model_validator(mode="before")
    @classmethod
    def normalize_symmetric_participants(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        payload = dict(value)
        raw_directionality = payload.get("directionality")
        directionality = (
            raw_directionality.value
            if isinstance(raw_directionality, RelationDirectionality)
            else str(raw_directionality or "")
        )
        participants = payload.get("participant_refs")
        if directionality == RelationDirectionality.SYMMETRIC.value and isinstance(participants, list):
            payload["participant_refs"] = sorted(
                participants,
                key=lambda item: _node_ref_value(item),
            )
        return payload

    @model_validator(mode="after")
    def validate_identity(self) -> "RelationKey":
        require_non_empty(self.scene_ref, "scene_ref")
        require_non_empty(self.ontology_version, "ontology_version")
        require_non_empty(self.relation_type, "relation_type")
        if len({item.node_ref for item in self.participant_refs}) != len(self.participant_refs):
            raise ValueError("relation_key_duplicate_participant")
        if any(item.scene_ref != self.scene_ref for item in self.participant_refs):
            raise ValueError("relation_key_scene_mismatch")
        if self.arity not in {0, len(self.participant_refs)}:
            raise ValueError("relation_key_arity_mismatch")
        object.__setattr__(self, "arity", len(self.participant_refs))
        expected = _stable_id("relation", self.identity_payload())
        if self.relation_key and self.relation_key != expected:
            raise ValueError("relation_key_identity_mismatch")
        object.__setattr__(self, "relation_key", expected)
        return self

    def identity_payload(self) -> dict[str, Any]:
        return {
            "scene_ref": self.scene_ref,
            "ontology_version": self.ontology_version,
            "relation_type": self.relation_type,
            "participant_refs": [item.node_ref for item in self.participant_refs],
            "directionality": self.directionality.value,
            "arity": len(self.participant_refs),
            "scope": self.scope,
        }


class PathKey(V50Model):
    version: str = "deepbazi.path_key.v1"
    path_key: str = ""
    scene_ref: str
    ontology_version: str = RELATION_ONTOLOGY_VERSION
    node_refs: list[NodeRef] = Field(min_length=2)
    relation_keys: list[RelationKey] = Field(min_length=1)
    scope: NodeScope = "natal"
    directed: Literal[True] = True

    @model_validator(mode="after")
    def validate_identity(self) -> "PathKey":
        require_non_empty(self.scene_ref, "scene_ref")
        require_non_empty(self.ontology_version, "ontology_version")
        if any(item.scene_ref != self.scene_ref for item in self.node_refs):
            raise ValueError("path_key_node_scene_mismatch")
        if any(item.scene_ref != self.scene_ref for item in self.relation_keys):
            raise ValueError("path_key_relation_scene_mismatch")
        expected = _stable_id("path", self.identity_payload())
        if self.path_key and self.path_key != expected:
            raise ValueError("path_key_identity_mismatch")
        object.__setattr__(self, "path_key", expected)
        return self

    def identity_payload(self) -> dict[str, Any]:
        return {
            "scene_ref": self.scene_ref,
            "ontology_version": self.ontology_version,
            "node_refs": [item.node_ref for item in self.node_refs],
            "relation_keys": [item.relation_key for item in self.relation_keys],
            "scope": self.scope,
            "directed": True,
        }


class ProvenanceRecord(V50Model):
    version: str = "deepbazi.relation_path_provenance.v1"
    provenance_id: str = ""
    source: Literal[
        "graph_candidate",
        "reasoner_commit",
        "legacy_exact_import",
        "legacy_unresolved",
    ]
    producer_id: str
    producer_version: str
    evidence_refs: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    created_at: str

    @model_validator(mode="after")
    def validate_identity(self) -> "ProvenanceRecord":
        require_non_empty(self.producer_id, "producer_id")
        require_non_empty(self.producer_version, "producer_version")
        require_non_empty(self.created_at, "created_at")
        expected = _stable_id("provenance", {
            "source": self.source,
            "producer_id": self.producer_id,
            "producer_version": self.producer_version,
            "evidence_refs": list(dict.fromkeys(self.evidence_refs)),
            "source_refs": list(dict.fromkeys(self.source_refs)),
            "created_at": self.created_at,
        })
        if self.provenance_id and self.provenance_id != expected:
            raise ValueError("provenance_identity_mismatch")
        object.__setattr__(self, "provenance_id", expected)
        return self


class RelationAssertion(V50Model):
    version: str = "deepbazi.relation_assertion.v1"
    assertion_id: str = ""
    relation_key: RelationKey
    assertion_version: str
    status: AssertionLifecycle
    provenance: ProvenanceRecord
    relation_state: MingliRelationState = MingliRelationState.EFFECTIVE
    mechanism_ref: str = "legacy_exact_relation"
    position_context: RelationPositionContext | None = None
    verification_refs: list[str] = Field(default_factory=list)
    supersedes: str = ""
    statement: str = ""

    @model_validator(mode="before")
    @classmethod
    def infer_legacy_relation_state(cls, value: Any) -> Any:
        if not isinstance(value, dict) or value.get("relation_state"):
            return value
        payload = dict(value)
        status = payload.get("status")
        status_value = status.value if isinstance(status, AssertionLifecycle) else str(status or "")
        payload["relation_state"] = (
            MingliRelationState.STRUCTURAL.value
            if status_value == AssertionLifecycle.CANDIDATE.value
            else MingliRelationState.EFFECTIVE.value
        )
        return payload

    @model_validator(mode="after")
    def validate_identity(self) -> "RelationAssertion":
        require_non_empty(self.assertion_version, "assertion_version")
        _validate_lifecycle_source(status=self.status, source=self.provenance.source)
        require_non_empty(self.mechanism_ref, "mechanism_ref")
        if (
            self.status == AssertionLifecycle.COMMITTED
            and self.relation_state != MingliRelationState.EFFECTIVE
        ):
            raise ValueError("committed_relation_assertion_requires_effective_state")
        if (
            self.status == AssertionLifecycle.CANDIDATE
            and self.relation_state == MingliRelationState.EFFECTIVE
        ):
            raise ValueError("candidate_relation_assertion_cannot_be_effective")
        if self.status == AssertionLifecycle.SUPERSEDED and not self.supersedes:
            raise ValueError("superseded_assertion_requires_predecessor")
        expected = _stable_id("relation-assertion", {
            "relation_key": self.relation_key.relation_key,
            "assertion_version": self.assertion_version,
            "status": self.status.value,
            "provenance": self.provenance.provenance_id,
            "supersedes": self.supersedes,
        })
        if self.assertion_id and self.assertion_id != expected:
            raise ValueError("relation_assertion_identity_mismatch")
        object.__setattr__(self, "assertion_id", expected)
        return self


class PathAssertion(V50Model):
    version: str = "deepbazi.path_assertion.v1"
    assertion_id: str = ""
    path_key: PathKey | None = None
    assertion_version: str
    status: AssertionLifecycle
    provenance: ProvenanceRecord
    source_candidate_ref: str = ""
    segment_validation_refs: list[str] = Field(default_factory=list)
    rejected_segment_refs: list[str] = Field(default_factory=list)
    supersedes: str = ""
    statement: str = ""
    legacy_ref: str = ""
    unresolved_reason: str = ""

    @model_validator(mode="after")
    def validate_identity(self) -> "PathAssertion":
        require_non_empty(self.assertion_version, "assertion_version")
        _validate_lifecycle_source(status=self.status, source=self.provenance.source)
        if self.status == AssertionLifecycle.LEGACY_UNRESOLVED:
            if self.path_key is not None or not self.legacy_ref or not self.unresolved_reason:
                raise ValueError("legacy_unresolved_path_contract_invalid")
        elif self.path_key is None:
            raise ValueError("resolved_path_assertion_requires_path_key")
        if self.status == AssertionLifecycle.SUPERSEDED and not self.supersedes:
            raise ValueError("superseded_assertion_requires_predecessor")
        expected = _stable_id("path-assertion", {
            "path_key": self.path_key.path_key if self.path_key else "",
            "legacy_ref": self.legacy_ref,
            "assertion_version": self.assertion_version,
            "status": self.status.value,
            "provenance": self.provenance.provenance_id,
            "supersedes": self.supersedes,
        })
        if self.assertion_id and self.assertion_id != expected:
            raise ValueError("path_assertion_identity_mismatch")
        object.__setattr__(self, "assertion_id", expected)
        return self


def validate_assertion_history(
    assertions: list[RelationAssertion] | list[PathAssertion],
) -> None:
    """Require persisted supersession links to point backward within one history."""

    positions: dict[str, int] = {}
    for index, assertion in enumerate(assertions):
        if assertion.assertion_id in positions:
            raise ValueError("assertion_history_duplicate_id")
        positions[assertion.assertion_id] = index
    for index, assertion in enumerate(assertions):
        predecessor = assertion.supersedes
        if not predecessor:
            continue
        predecessor_index = positions.get(predecessor)
        if predecessor_index is None:
            raise ValueError("assertion_supersedes_unknown_history")
        if predecessor_index >= index:
            raise ValueError("assertion_supersedes_non_prior_history")


def _validate_lifecycle_source(
    *,
    status: AssertionLifecycle,
    source: str,
) -> None:
    if source == "graph_candidate" and status != AssertionLifecycle.CANDIDATE:
        raise ValueError("graph_candidate_provenance_requires_candidate_status")
    if status == AssertionLifecycle.CANDIDATE and source != "graph_candidate":
        raise ValueError("candidate_assertion_requires_graph_candidate_provenance")
    if source == "legacy_unresolved" and status != AssertionLifecycle.LEGACY_UNRESOLVED:
        raise ValueError("legacy_unresolved_provenance_requires_unresolved_status")
    if status == AssertionLifecycle.LEGACY_UNRESOLVED and source != "legacy_unresolved":
        raise ValueError("legacy_unresolved_assertion_requires_unresolved_provenance")


def canonical_scene_scope_ref(*, life_case_id: str, chart_version_id: str) -> str:
    return _stable_id("scene-scope", {
        "life_case_id": life_case_id,
        "chart_version_id": chart_version_id,
    })


def relation_directionality(relation_type: str) -> RelationDirectionality:
    if relation_type in {
        "same_element_support",
        "forms_half_combination",
        "forms_triple_combination",
        "clashes",
        "harmonizes",
        "harms",
        "breaks",
        "punishes",
        "position_link",
    }:
        return RelationDirectionality.SYMMETRIC
    return RelationDirectionality.DIRECTED


def stable_candidate_node_key(
    *,
    reading_id: str,
    position: str,
    node_type: str,
    label: str,
) -> str:
    return _stable_candidate_id(
        "candidate-node",
        [reading_id, position, node_type, label],
    )


def stable_candidate_relation_key(
    *,
    reading_id: str,
    relation_type: str,
    participant_node_keys: list[str],
    directionality: RelationDirectionality,
    scope: str = "natal",
) -> str:
    participants = list(participant_node_keys)
    if directionality == RelationDirectionality.SYMMETRIC:
        participants.sort()
    return _stable_candidate_id(
        "candidate-relation",
        [
            reading_id,
            RELATION_ONTOLOGY_VERSION,
            relation_type,
            directionality.value,
            str(len(participants)),
            scope,
            "participants",
            *participants,
        ],
    )


def stable_candidate_path_key(
    *,
    reading_id: str,
    state_layer: str,
    node_keys: list[str],
    relation_keys: list[str],
) -> str:
    return _stable_candidate_id(
        "candidate-path",
        [
            reading_id,
            RELATION_ONTOLOGY_VERSION,
            state_layer,
            "nodes",
            str(len(node_keys)),
            *node_keys,
            "relations",
            str(len(relation_keys)),
            *relation_keys,
        ],
    )


def _stable_candidate_id(prefix: str, parts: list[str]) -> str:
    """Hash hot-path candidate identities without general JSON serialization."""

    payload = "\x00".join([prefix, *parts]).encode("utf-8")
    return f"{prefix}-{hashlib.sha256(payload).hexdigest()[:32]}"


def _node_ref_value(value: Any) -> str:
    if isinstance(value, NodeRef):
        return value.node_ref
    if isinstance(value, dict):
        if value.get("node_ref"):
            return str(value["node_ref"])
        payload = {key: value.get(key, "") for key in (
            "scene_ref",
            "life_case_id",
            "chart_version_id",
            "world_id",
            "scope",
            "slot",
            "level",
            "component",
            "temporal_snapshot_ref",
        )}
        return _stable_id("node", payload)
    return str(value)


def _stable_id(prefix: str, payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return f"{prefix}:{hashlib.sha256(encoded.encode('utf-8')).hexdigest()}"
