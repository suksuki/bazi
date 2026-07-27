from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any, Literal

from pydantic import Field, model_validator

from core.contracts.base import V50Model, require_non_empty, require_refs
from core.graph.provenance import (
    MingliRelationState,
    NodeRef,
    RelationDirectionality,
    RelationKey,
)


RELATION_FACT_CONTRACT_VERSION = "deepbazi.relation-fact.rgm02.v1"
RELATION_FACT_PROFILE_VERSION = "bazi.deterministic-relation-facts.v1"
RELATION_LEGALITY_POLICY_VERSION = "bazi.relation-legality.lab-path-focus.v1"

RelationLegalityClass = Literal[
    "legal_direct",
    "legal_mediated",
    "containment",
    "positional",
    "unsupported",
    "illegal_cross_layer",
]
RelationProvenanceStatus = Literal[
    "complete",
    "incomplete",
    "quarantined",
    "illegal",
]

_ELEMENT_ACTION_FAMILIES = {
    "generates",
    "controls",
    "same_element_support",
}
_BRANCH_RELATION_FAMILIES = {
    "forms_half_combination",
    "forms_triple_combination",
    "clashes",
    "harmonizes",
    "harms",
    "breaks",
    "punishes",
}
_MEDIATED_EVIDENCE_FAMILIES = {
    "roots",
    "source_identity_evidence",
    "source_element_affinity",
}


class RelationFactState(str, Enum):
    RELATION_CANDIDATE = "RELATION_CANDIDATE"
    RELATION_STRUCTURALLY_PRESENT = "RELATION_STRUCTURALLY_PRESENT"
    TARGETS_IDENTIFIED = "TARGETS_IDENTIFIED"


class RelationActivationState(str, Enum):
    NOT_ACTIVATED = "not_activated"
    NATAL_PRESENT = "natal_present"
    TEMPORALLY_ACTIVATED = "temporally_activated"


class RelationFactLegalityAssessment(V50Model):
    policy_version: str = RELATION_LEGALITY_POLICY_VERSION
    legality_class: RelationLegalityClass
    relation_kind: str
    direct_or_mediated: Literal[
        "direct",
        "mediated",
        "not_applicable",
        "unsupported",
        "illegal",
    ]
    participant_kinds: list[str] = Field(min_length=2)
    mediator_refs: list[str] = Field(default_factory=list)
    prerequisite_refs: list[str] = Field(default_factory=list)
    exclusion_refs: list[str] = Field(default_factory=list)
    source_layer: str
    time_scope: str
    professional_stage: str
    rule_id: str
    rule_version: str
    evidence_refs: list[str] = Field(default_factory=list)
    provenance_status: RelationProvenanceStatus
    missing_requirements: list[str] = Field(default_factory=list)
    default_path_eligible: bool = False
    inventory_visible: bool = False


class RelationParticipantRole(V50Model):
    participant_ref: str
    role: Literal[
        "producer",
        "target",
        "participant",
        "carrier",
        "environment",
        "activator",
    ]

    @model_validator(mode="after")
    def validate_role(self) -> "RelationParticipantRole":
        require_non_empty(self.participant_ref, "participant_ref")
        return self


class RelationFactKey(V50Model):
    version: str = RELATION_FACT_CONTRACT_VERSION
    fact_key: str = ""
    scene_ref: str
    life_case_id: str
    chart_version_id: str
    world_lineage: str
    ontology_version: str
    relation_family: str
    participant_refs: list[NodeRef] = Field(min_length=2)
    participant_roles: list[RelationParticipantRole] = Field(min_length=2)
    directionality: RelationDirectionality
    scope: Literal["natal", "luck", "year", "month", "other"] = "natal"
    school_profile_id: str = "bazi.selected-profile"
    school_profile_version: str = RELATION_FACT_PROFILE_VERSION

    @model_validator(mode="before")
    @classmethod
    def normalize_symmetric_identity(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        payload = dict(value)
        directionality = payload.get("directionality")
        directionality_value = (
            directionality.value
            if isinstance(directionality, RelationDirectionality)
            else str(directionality or "")
        )
        if directionality_value != RelationDirectionality.SYMMETRIC.value:
            return payload
        participants = payload.get("participant_refs")
        if isinstance(participants, list):
            payload["participant_refs"] = sorted(
                participants,
                key=_node_ref_value,
            )
        roles = payload.get("participant_roles")
        if isinstance(roles, list):
            payload["participant_roles"] = sorted(
                roles,
                key=_participant_role_ref,
            )
        return payload

    @model_validator(mode="after")
    def validate_identity(self) -> "RelationFactKey":
        for value, field in (
            (self.scene_ref, "scene_ref"),
            (self.life_case_id, "life_case_id"),
            (self.chart_version_id, "chart_version_id"),
            (self.world_lineage, "world_lineage"),
            (self.ontology_version, "ontology_version"),
            (self.relation_family, "relation_family"),
            (self.school_profile_id, "school_profile_id"),
            (self.school_profile_version, "school_profile_version"),
        ):
            require_non_empty(value, field)
        participant_ids = [item.node_ref for item in self.participant_refs]
        if len(participant_ids) != len(set(participant_ids)):
            raise ValueError("relation_fact_duplicate_participant")
        if any(item.scene_ref != self.scene_ref for item in self.participant_refs):
            raise ValueError("relation_fact_participant_scene_mismatch")
        if any(
            item.life_case_id != self.life_case_id
            for item in self.participant_refs
        ):
            raise ValueError("relation_fact_participant_life_case_mismatch")
        if any(
            item.chart_version_id != self.chart_version_id
            for item in self.participant_refs
        ):
            raise ValueError("relation_fact_participant_chart_version_mismatch")
        role_ids = [item.participant_ref for item in self.participant_roles]
        if sorted(role_ids) != sorted(participant_ids):
            raise ValueError("relation_fact_participant_role_mismatch")
        expected = _stable_id("relation-fact", self.identity_payload())
        if self.fact_key and self.fact_key != expected:
            raise ValueError("relation_fact_key_identity_mismatch")
        object.__setattr__(self, "fact_key", expected)
        return self

    def identity_payload(self) -> dict[str, Any]:
        return {
            "scene_ref": self.scene_ref,
            "life_case_id": self.life_case_id,
            "chart_version_id": self.chart_version_id,
            "world_lineage": self.world_lineage,
            "ontology_version": self.ontology_version,
            "relation_family": self.relation_family,
            "participant_refs": [item.node_ref for item in self.participant_refs],
            "participant_roles": [
                item.model_dump(mode="json") for item in self.participant_roles
            ],
            "directionality": self.directionality.value,
            "scope": self.scope,
            "school_profile_id": self.school_profile_id,
            "school_profile_version": self.school_profile_version,
        }


class RelationFactRevision(V50Model):
    version: str = RELATION_FACT_CONTRACT_VERSION
    revision_ref: str = ""
    revision_number: int = Field(default=1, ge=1)
    fact_key: RelationFactKey
    fact_state: RelationFactState
    activation_state: RelationActivationState
    source_snapshot_ref: str
    source_snapshot_hash: str = Field(min_length=64, max_length=64)
    producer_id: str
    producer_version: str
    evidence_refs: list[str] = Field(min_length=1)
    mechanism_ref: str
    temporal_stage: Literal["natal", "luck", "year", "month", "other"] = "natal"
    valid_from_stage: str
    valid_to_stage: str = ""
    supersedes_ref: str = ""
    withdrawn_by_ref: str = ""
    effect_resolution_ref: str = ""
    disclosure_manifest: dict[str, str] = Field(default_factory=dict)
    replay_hash: str = ""

    @model_validator(mode="after")
    def validate_revision(self) -> "RelationFactRevision":
        for value, field in (
            (self.source_snapshot_ref, "source_snapshot_ref"),
            (self.producer_id, "producer_id"),
            (self.producer_version, "producer_version"),
            (self.mechanism_ref, "mechanism_ref"),
            (self.valid_from_stage, "valid_from_stage"),
        ):
            require_non_empty(value, field)
        require_refs(self.evidence_refs, "evidence_refs")
        if self.withdrawn_by_ref and not self.valid_to_stage:
            raise ValueError("withdrawn_relation_fact_requires_valid_to_stage")
        if self.revision_number > 1 and not self.supersedes_ref:
            raise ValueError("relation_fact_revision_requires_predecessor")
        payload = self.replay_payload()
        expected_replay = _stable_hash(payload)
        if self.replay_hash and self.replay_hash != expected_replay:
            raise ValueError("relation_fact_replay_hash_mismatch")
        object.__setattr__(self, "replay_hash", expected_replay)
        expected_ref = _stable_id(
            "relation-fact-revision",
            {
                "fact_key": self.fact_key.fact_key,
                "revision_number": self.revision_number,
                "replay_hash": expected_replay,
            },
        )
        if self.revision_ref and self.revision_ref != expected_ref:
            raise ValueError("relation_fact_revision_identity_mismatch")
        object.__setattr__(self, "revision_ref", expected_ref)
        return self

    def replay_payload(self) -> dict[str, Any]:
        return {
            "fact_key": self.fact_key.identity_payload(),
            "revision_number": self.revision_number,
            "fact_state": self.fact_state.value,
            "activation_state": self.activation_state.value,
            "source_snapshot_ref": self.source_snapshot_ref,
            "source_snapshot_hash": self.source_snapshot_hash,
            "producer_id": self.producer_id,
            "producer_version": self.producer_version,
            "evidence_refs": list(dict.fromkeys(self.evidence_refs)),
            "mechanism_ref": self.mechanism_ref,
            "temporal_stage": self.temporal_stage,
            "valid_from_stage": self.valid_from_stage,
            "valid_to_stage": self.valid_to_stage,
            "supersedes_ref": self.supersedes_ref,
            "withdrawn_by_ref": self.withdrawn_by_ref,
            "effect_resolution_ref": self.effect_resolution_ref,
            "disclosure_manifest": dict(sorted(self.disclosure_manifest.items())),
        }


def relation_fact_from_key(
    *,
    relation_key: RelationKey,
    relation_state: MingliRelationState,
    world_lineage: str,
    source_snapshot_ref: str,
    source_snapshot_hash: str,
    producer_id: str,
    producer_version: str,
    evidence_refs: list[str],
    mechanism_ref: str,
    temporal_stage: Literal["natal", "luck", "year", "month", "other"],
    valid_from_stage: str,
    school_profile_id: str = "bazi.selected-profile",
    school_profile_version: str = RELATION_FACT_PROFILE_VERSION,
    disclosure_manifest: dict[str, str] | None = None,
) -> RelationFactRevision:
    participants = list(relation_key.participant_refs)
    roles = _participant_roles(
        participants=participants,
        directionality=relation_key.directionality,
    )
    fact_state = (
        RelationFactState.RELATION_CANDIDATE
        if relation_state == MingliRelationState.POTENTIAL
        else RelationFactState.TARGETS_IDENTIFIED
        if relation_key.directionality == RelationDirectionality.DIRECTED
        else RelationFactState.RELATION_STRUCTURALLY_PRESENT
    )
    activation_state = (
        RelationActivationState.TEMPORALLY_ACTIVATED
        if relation_state == MingliRelationState.TIME_ACTIVATED
        else RelationActivationState.NATAL_PRESENT
        if temporal_stage == "natal"
        else RelationActivationState.NOT_ACTIVATED
    )
    first = participants[0]
    key = RelationFactKey(
        scene_ref=relation_key.scene_ref,
        life_case_id=first.life_case_id,
        chart_version_id=first.chart_version_id,
        world_lineage=world_lineage,
        ontology_version=relation_key.ontology_version,
        relation_family=relation_key.relation_type,
        participant_refs=participants,
        participant_roles=roles,
        directionality=relation_key.directionality,
        scope=relation_key.scope,
        school_profile_id=school_profile_id,
        school_profile_version=school_profile_version,
    )
    return RelationFactRevision(
        fact_key=key,
        fact_state=fact_state,
        activation_state=activation_state,
        source_snapshot_ref=source_snapshot_ref,
        source_snapshot_hash=source_snapshot_hash,
        producer_id=producer_id,
        producer_version=producer_version,
        evidence_refs=list(dict.fromkeys(evidence_refs)),
        mechanism_ref=mechanism_ref,
        temporal_stage=temporal_stage,
        valid_from_stage=valid_from_stage,
        disclosure_manifest=disclosure_manifest
        or {
            "fact": "practitioner",
            "candidate": "research",
            "effect": "not_available",
        },
    )


def withdraw_relation_fact(
    previous: RelationFactRevision,
    *,
    withdrawn_by_ref: str,
    valid_to_stage: str,
) -> RelationFactRevision:
    require_non_empty(withdrawn_by_ref, "withdrawn_by_ref")
    require_non_empty(valid_to_stage, "valid_to_stage")
    payload = previous.model_dump(mode="json")
    payload.update({
        "revision_ref": "",
        "revision_number": previous.revision_number + 1,
        "supersedes_ref": previous.revision_ref,
        "withdrawn_by_ref": withdrawn_by_ref,
        "valid_to_stage": valid_to_stage,
        "replay_hash": "",
    })
    return RelationFactRevision.model_validate(payload)


def restore_relation_fact(
    previous: RelationFactRevision,
    *,
    source_snapshot_ref: str,
    source_snapshot_hash: str,
    evidence_refs: list[str],
    valid_from_stage: str,
) -> RelationFactRevision:
    if not previous.withdrawn_by_ref:
        raise ValueError("relation_fact_restore_requires_withdrawn_revision")
    payload = previous.model_dump(mode="json")
    payload.update({
        "revision_ref": "",
        "revision_number": previous.revision_number + 1,
        "source_snapshot_ref": source_snapshot_ref,
        "source_snapshot_hash": source_snapshot_hash,
        "evidence_refs": list(dict.fromkeys(evidence_refs)),
        "valid_from_stage": valid_from_stage,
        "valid_to_stage": "",
        "supersedes_ref": previous.revision_ref,
        "withdrawn_by_ref": "",
        "activation_state": RelationActivationState.NATAL_PRESENT.value,
        "replay_hash": "",
    })
    return RelationFactRevision.model_validate(payload)


def assess_relation_fact_legality(
    fact: RelationFactRevision,
) -> RelationFactLegalityAssessment:
    """Classify a committed relation without inferring professional effect."""

    participants = fact.fact_key.participant_refs
    levels = [item.level for item in participants]
    scopes = [item.scope for item in participants]
    family = fact.fact_key.relation_family
    mechanism = fact.mechanism_ref
    missing: list[str] = []
    exclusions: list[str] = []
    mediators: list[str] = []
    prerequisites = list(dict.fromkeys([
        fact.source_snapshot_ref,
        *fact.evidence_refs,
    ]))

    temporal = fact.temporal_stage != "natal" or any(
        scope != "natal" for scope in scopes
    )
    if temporal:
        if fact.activation_state != RelationActivationState.TEMPORALLY_ACTIVATED:
            missing.append("temporal_activation_rule")
        if any(
            item.scope != "natal" and not item.temporal_snapshot_ref
            for item in participants
        ):
            missing.append("temporal_snapshot_ref")

    legality: RelationLegalityClass
    directness: Literal[
        "direct",
        "mediated",
        "not_applicable",
        "unsupported",
        "illegal",
    ]
    professional_stage = "relation_fact_only"

    if family == "stores":
        if levels[:2] == ["branch", "hidden_stem"]:
            legality = "containment"
            directness = "not_applicable"
            professional_stage = "containment_evidence"
        else:
            legality = "illegal_cross_layer"
            directness = "illegal"
            missing.append("branch_to_hidden_stem_containment_shape")
    elif family == "position_link":
        if (
            len(participants) == 2
            and {levels[0], levels[1]} == {"stem", "branch"}
            and participants[0].slot == participants[1].slot
        ):
            legality = "positional"
            directness = "not_applicable"
            professional_stage = "positional_evidence"
        else:
            legality = "illegal_cross_layer"
            directness = "illegal"
            missing.append("same_column_stem_branch_position_shape")
    elif family in _MEDIATED_EVIDENCE_FAMILIES:
        legality = "legal_mediated"
        directness = "mediated"
        professional_stage = "supporting_evidence_only"
        mediators = [
            item.node_ref
            for item in participants
            if item.level in {"branch", "hidden_stem"}
        ]
    elif family in _ELEMENT_ACTION_FAMILIES:
        if all(level == "stem" for level in levels):
            legality = "legal_direct"
            directness = "direct"
            professional_stage = "structural_candidate"
        elif "branch" in levels and "stem" in levels:
            legality = "illegal_cross_layer"
            directness = "illegal"
            missing.append("registered_cross_layer_mediator")
        else:
            legality = "unsupported"
            directness = "unsupported"
            missing.append("manifestation_or_mediation_evidence")
            exclusions.append("five_element_potential_is_not_direct_action")
    elif family in _BRANCH_RELATION_FAMILIES:
        if all(level == "branch" for level in levels):
            legality = "legal_direct"
            directness = "direct"
            professional_stage = "structural_relation"
        else:
            legality = "illegal_cross_layer"
            directness = "illegal"
            missing.append("branch_relation_requires_branch_participants")
    else:
        legality = "unsupported"
        directness = "unsupported"
        missing.append("registered_relation_family")

    if fact.fact_state == RelationFactState.RELATION_CANDIDATE:
        if legality == "legal_direct":
            legality = "unsupported"
            directness = "unsupported"
        missing.append("structurally_present_relation")
    if fact.withdrawn_by_ref or fact.valid_to_stage:
        if legality in {"legal_direct", "legal_mediated"}:
            legality = "unsupported"
            directness = "unsupported"
        missing.append("currently_valid_relation_revision")
    if temporal and missing:
        if legality in {"legal_direct", "legal_mediated"}:
            legality = "unsupported"
            directness = "unsupported"

    if not mechanism:
        missing.append("rule_id")
    if not fact.producer_version:
        missing.append("rule_version")
    if not fact.evidence_refs:
        missing.append("evidence_refs")
    missing = list(dict.fromkeys(missing))

    if legality == "illegal_cross_layer":
        provenance_status: RelationProvenanceStatus = "illegal"
    elif legality == "unsupported":
        provenance_status = "quarantined"
    elif missing:
        provenance_status = "incomplete"
    else:
        provenance_status = "complete"

    default_path_eligible = (
        legality == "legal_direct"
        and family in _ELEMENT_ACTION_FAMILIES
        and directness == "direct"
        and provenance_status == "complete"
        and professional_stage == "structural_candidate"
    )
    inventory_visible = (
        legality in {"legal_direct", "legal_mediated", "containment", "positional"}
        and provenance_status == "complete"
    )
    source_layer = (
        scopes[0]
        if len(set(scopes)) == 1
        else "mixed_temporal"
    )
    return RelationFactLegalityAssessment(
        legality_class=legality,
        relation_kind=family,
        direct_or_mediated=directness,
        participant_kinds=levels,
        mediator_refs=list(dict.fromkeys(mediators)),
        prerequisite_refs=prerequisites,
        exclusion_refs=list(dict.fromkeys(exclusions)),
        source_layer=source_layer,
        time_scope=fact.temporal_stage,
        professional_stage=professional_stage,
        rule_id=mechanism or "missing",
        rule_version=fact.producer_version or "missing",
        evidence_refs=list(dict.fromkeys([
            fact.revision_ref,
            *fact.evidence_refs,
        ])),
        provenance_status=provenance_status,
        missing_requirements=missing,
        default_path_eligible=default_path_eligible,
        inventory_visible=inventory_visible,
    )


def _participant_roles(
    *,
    participants: list[NodeRef],
    directionality: RelationDirectionality,
) -> list[RelationParticipantRole]:
    if directionality == RelationDirectionality.SYMMETRIC:
        return [
            RelationParticipantRole(participant_ref=item.node_ref, role="participant")
            for item in participants
        ]
    return [
        RelationParticipantRole(
            participant_ref=item.node_ref,
            role="producer" if index == 0 else "target" if index == 1 else "participant",
        )
        for index, item in enumerate(participants)
    ]


def _node_ref_value(value: Any) -> str:
    if isinstance(value, NodeRef):
        return value.node_ref
    if isinstance(value, dict):
        return str(value.get("node_ref") or "")
    return str(value)


def _participant_role_ref(value: Any) -> str:
    if isinstance(value, RelationParticipantRole):
        return value.participant_ref
    if isinstance(value, dict):
        return str(value.get("participant_ref") or "")
    return str(value)


def _stable_hash(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _stable_id(prefix: str, payload: Any) -> str:
    return f"{prefix}:{_stable_hash(payload)}"
