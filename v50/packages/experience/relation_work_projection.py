from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from core.graph import (
    RelationEffectResolution,
    RelationEffectResolutionStatus,
    RelationFactRevision,
    WorkPathCandidate,
)
from core.graph.relation_facts import (
    RELATION_FACT_CONTRACT_VERSION,
    RELATION_LEGALITY_POLICY_VERSION,
    assess_relation_fact_legality,
)
from core.graph.work_paths import WORK_PATH_CONTRACT_VERSION
from experience.compiler import canonical_hash
from experience.contracts import ExperienceModel


RELATION_WORK_PROJECTION_VERSION = "deepbazi.relation-work-projection.p0.v1"
RelationWorkAudience = Literal["dream", "lab"]
RelationWorkDisclosure = Literal[
    "dream_and_lab",
    "lab_only",
    "professional_only",
    "legacy_read_only",
]


class RelationWorkSourceBinding(ExperienceModel):
    scene_ref: str = Field(min_length=1, max_length=220)
    life_case_id: str = Field(min_length=1, max_length=180)
    chart_version_id: str = Field(min_length=1, max_length=180)
    world_lineage: str = Field(min_length=1, max_length=180)
    source_snapshot_ref: str = Field(min_length=1, max_length=220)
    source_snapshot_hash: str = Field(min_length=64, max_length=64)


class RelationFactProjectionItem(ExperienceModel):
    relation_fact_id: str = Field(min_length=1, max_length=220)
    fact_revision_ref: str = Field(min_length=1, max_length=220)
    fact_key_ref: str = Field(min_length=1, max_length=220)
    relation_family: str = Field(min_length=1, max_length=100)
    relation_kind: str = Field(min_length=1, max_length=100)
    participant_refs: list[str] = Field(min_length=2)
    participant_kinds: list[str] = Field(min_length=2)
    participant_coordinates: list[dict[str, str]] = Field(min_length=2)
    participant_roles: dict[str, str]
    directionality: Literal["directed", "symmetric"]
    direct_or_mediated: Literal[
        "direct",
        "mediated",
        "not_applicable",
        "unsupported",
        "illegal",
    ]
    mediator_refs: list[str] = Field(default_factory=list)
    prerequisite_refs: list[str] = Field(default_factory=list)
    exclusion_refs: list[str] = Field(default_factory=list)
    source_layer: str = Field(min_length=1, max_length=100)
    time_scope: str = Field(min_length=1, max_length=100)
    professional_stage: str = Field(min_length=1, max_length=100)
    rule_id: str = Field(min_length=1, max_length=180)
    rule_version: str = Field(min_length=1, max_length=180)
    provenance_status: Literal[
        "complete",
        "incomplete",
        "quarantined",
        "illegal",
    ]
    legality_class: Literal[
        "legal_direct",
        "legal_mediated",
        "containment",
        "positional",
        "unsupported",
        "illegal_cross_layer",
    ]
    legality_policy_version: str = RELATION_LEGALITY_POLICY_VERSION
    missing_requirements: list[str] = Field(default_factory=list)
    default_path_eligible: bool = False
    inventory_visible: bool = False
    fact_state: Literal[
        "RELATION_CANDIDATE",
        "RELATION_STRUCTURALLY_PRESENT",
        "TARGETS_IDENTIFIED",
    ]
    activation_state: Literal[
        "not_activated",
        "natal_present",
        "temporally_activated",
    ]
    temporal_stage: Literal["natal", "luck", "year", "month", "other"]
    valid_from_stage: str = Field(min_length=1, max_length=160)
    valid_to_stage: str = Field(default="", max_length=160)
    effect_resolution_ref: str = Field(default="", max_length=220)
    effect_status: Literal[
        "effect_unresolved",
        "professionally_resolved",
        "rejected",
    ]
    resolved_effect_atoms: list[str] = Field(default_factory=list)
    unresolved_reasons: list[str] = Field(default_factory=list)
    disclosure_state: RelationWorkDisclosure
    relation_fact_contract_version: str = RELATION_FACT_CONTRACT_VERSION
    school_profile_id: str = Field(min_length=1, max_length=180)
    school_profile_version: str = Field(min_length=1, max_length=180)
    producer_id: str = Field(min_length=1, max_length=180)
    producer_version: str = Field(min_length=1, max_length=180)
    evidence_refs: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_professional_state(self) -> "RelationFactProjectionItem":
        if self.effect_status == "professionally_resolved":
            if not self.effect_resolution_ref or not self.resolved_effect_atoms:
                raise ValueError("projected_resolved_effect_requires_receipt_and_atoms")
            if self.unresolved_reasons:
                raise ValueError("projected_resolved_effect_cannot_be_unresolved")
        elif self.resolved_effect_atoms:
            raise ValueError("projected_unresolved_effect_cannot_emit_atoms")
        if self.effect_status == "effect_unresolved" and not self.unresolved_reasons:
            raise ValueError("projected_unresolved_effect_requires_reason")
        return self


class WorkPathProjectionItem(ExperienceModel):
    work_path_candidate_ref: str = Field(min_length=1, max_length=220)
    label: str = Field(min_length=1, max_length=100)
    actor_ref: str = Field(min_length=1, max_length=220)
    actor_role: str = Field(min_length=1, max_length=80)
    action: str = Field(min_length=1, max_length=120)
    receiver_ref: str = Field(min_length=1, max_length=220)
    receiver_role: str = Field(min_length=1, max_length=80)
    ordered_fact_revision_refs: list[str] = Field(min_length=1)
    participant_coordinates: list[dict[str, str]] = Field(min_length=2)
    intermediate_participant_refs: list[str] = Field(default_factory=list)
    structural_carrier_refs: list[str] = Field(default_factory=list)
    effect_resolution_refs: list[str] = Field(default_factory=list)
    blocker_refs: list[str] = Field(default_factory=list)
    blocker_types: list[str] = Field(default_factory=list)
    shared_resource_refs: list[str] = Field(default_factory=list)
    competing_path_group_ref: str = Field(default="", max_length=220)
    cycle_node_refs: list[str] = Field(default_factory=list)
    bottleneck_node_refs: list[str] = Field(default_factory=list)
    counterfactual_refs: list[str] = Field(default_factory=list)
    temporal_delta_refs: list[str] = Field(default_factory=list)
    valid_from_stage: str = Field(min_length=1, max_length=160)
    valid_to_stage: str = Field(default="", max_length=160)
    axes: dict[str, str]
    unresolved_reasons: list[str] = Field(min_length=1)
    disclosure_state: RelationWorkDisclosure
    work_path_contract_version: str = WORK_PATH_CONTRACT_VERSION
    school_profile_id: str = Field(min_length=1, max_length=180)
    school_profile_version: str = Field(min_length=1, max_length=180)
    provenance_refs: list[str] = Field(min_length=1)
    professional_rank: Literal[None] = None
    main_work_declared: Literal[False] = False


class ProfessionalResolutionProjectionItem(ExperienceModel):
    effect_resolution_ref: str = Field(min_length=1, max_length=220)
    relation_fact_revision_refs: list[str] = Field(min_length=1)
    relation_fact_key_refs: list[str] = Field(min_length=1)
    resolved_effect_atoms: list[str] = Field(min_length=1)
    profile_id: str = Field(min_length=1, max_length=180)
    profile_version: str = Field(min_length=1, max_length=180)
    evidence_refs: list[str] = Field(min_length=1)
    disclosure_state: RelationWorkDisclosure


class SharedRelationWorkProjection(ExperienceModel):
    schema_version: Literal[
        "deepbazi.relation-work-projection.p0.v1"
    ] = RELATION_WORK_PROJECTION_VERSION
    foundation_ref: str = Field(min_length=1, max_length=220)
    source: RelationWorkSourceBinding
    factual_view: list[RelationFactProjectionItem] = Field(default_factory=list)
    candidate_path_view: list[WorkPathProjectionItem] = Field(default_factory=list)
    professionally_resolved_view: list[
        ProfessionalResolutionProjectionItem
    ] = Field(default_factory=list)
    source_profile_versions: list[str] = Field(default_factory=list)
    content_hash: str = Field(min_length=64, max_length=64)
    read_only: Literal[True] = True
    writes_life_case: Literal[False] = False
    declares_main_work: Literal[False] = False

    @model_validator(mode="after")
    def validate_foundation(self) -> "SharedRelationWorkProjection":
        known_facts = {item.fact_revision_ref for item in self.factual_view}
        for item in self.candidate_path_view:
            if not set(item.ordered_fact_revision_refs).issubset(known_facts):
                raise ValueError("projection_path_references_unknown_relation_fact")
        for item in self.professionally_resolved_view:
            if not set(item.relation_fact_revision_refs).issubset(known_facts):
                raise ValueError("projection_effect_references_unknown_relation_fact")
        payload = self.model_dump(
            mode="json",
            exclude={"foundation_ref", "content_hash"},
        )
        expected_hash = canonical_hash(payload)
        if self.content_hash != expected_hash:
            raise ValueError("relation_work_projection_content_hash_mismatch")
        expected_ref = f"relation-work-projection:{expected_hash}"
        if self.foundation_ref != expected_ref:
            raise ValueError("relation_work_projection_foundation_ref_mismatch")
        return self


class RelationWorkProjectionView(ExperienceModel):
    schema_version: Literal[
        "deepbazi.relation-work-projection-view.p0.v1"
    ] = "deepbazi.relation-work-projection-view.p0.v1"
    audience: RelationWorkAudience
    foundation_ref: str = Field(min_length=1, max_length=220)
    foundation_content_hash: str = Field(min_length=64, max_length=64)
    source: RelationWorkSourceBinding
    factual_view: list[RelationFactProjectionItem] = Field(default_factory=list)
    candidate_path_view: list[WorkPathProjectionItem] = Field(default_factory=list)
    professionally_resolved_view: list[
        ProfessionalResolutionProjectionItem
    ] = Field(default_factory=list)
    withheld_counts: dict[str, int] = Field(default_factory=dict)
    read_only: Literal[True] = True
    consumer_inference_allowed: Literal[False] = False
    content_hash: str = Field(min_length=64, max_length=64)

    @model_validator(mode="after")
    def validate_view_hash(self) -> "RelationWorkProjectionView":
        payload = self.model_dump(mode="json", exclude={"content_hash"})
        if self.content_hash != canonical_hash(payload):
            raise ValueError("relation_work_projection_view_hash_mismatch")
        return self


def compile_shared_relation_work_projection(
    *,
    relation_facts: list[RelationFactRevision],
    work_path_candidates: list[WorkPathCandidate],
    effect_resolutions: list[RelationEffectResolution],
) -> SharedRelationWorkProjection:
    if not relation_facts:
        raise ValueError("relation_work_projection_requires_relation_fact")
    ordered_facts = sorted(relation_facts, key=lambda item: item.revision_ref)
    source = _source_binding(ordered_facts)
    fact_by_ref = {item.revision_ref: item for item in ordered_facts}
    effect_by_fact: dict[str, RelationEffectResolution] = {}
    for resolution in effect_resolutions:
        for fact_ref in resolution.relation_fact_revision_refs:
            if fact_ref not in fact_by_ref:
                raise ValueError("effect_resolution_references_unknown_relation_fact")
            if fact_ref in effect_by_fact:
                raise ValueError("multiple_effect_resolutions_for_same_fact_revision")
            effect_by_fact[fact_ref] = resolution
    factual_items = [
        _project_fact(fact, effect_by_fact.get(fact.revision_ref))
        for fact in ordered_facts
    ]
    coordinates = {
        fact.revision_ref: [
            _coordinate(item)
            for item in fact.fact_key.participant_refs
        ]
        for fact in ordered_facts
    }
    disclosures = {
        fact.revision_ref: _fact_disclosure(fact)
        for fact in ordered_facts
    }
    path_items = [
        _project_path(candidate, coordinates, disclosures)
        for candidate in sorted(
            work_path_candidates,
            key=lambda item: item.candidate_ref,
        )
    ]
    professional_items = [
        _project_professional(resolution, ordered_facts)
        for resolution in sorted(
            effect_resolutions,
            key=lambda item: item.resolution_ref,
        )
        if resolution.status
        == RelationEffectResolutionStatus.PROFESSIONALLY_RESOLVED
        and all(
            _fact_disclosure(
                fact_by_ref[fact_ref]
            )
            != "legacy_read_only"
            for fact_ref in resolution.relation_fact_revision_refs
        )
    ]
    source_profiles = sorted({
        *(
            f"{item.fact_key.school_profile_id}@"
            f"{item.fact_key.school_profile_version}"
            for item in ordered_facts
        ),
        *(
            f"{item.profile_id}@{item.profile_version}"
            for item in effect_resolutions
        ),
    })
    payload = {
        "schema_version": RELATION_WORK_PROJECTION_VERSION,
        "source": source.model_dump(mode="json"),
        "factual_view": [item.model_dump(mode="json") for item in factual_items],
        "candidate_path_view": [item.model_dump(mode="json") for item in path_items],
        "professionally_resolved_view": [
            item.model_dump(mode="json") for item in professional_items
        ],
        "source_profile_versions": source_profiles,
        "read_only": True,
        "writes_life_case": False,
        "declares_main_work": False,
    }
    content_hash = canonical_hash(payload)
    return SharedRelationWorkProjection(
        foundation_ref=f"relation-work-projection:{content_hash}",
        source=source,
        factual_view=factual_items,
        candidate_path_view=path_items,
        professionally_resolved_view=professional_items,
        source_profile_versions=source_profiles,
        content_hash=content_hash,
    )


def project_relation_work_for_consumer(
    projection: SharedRelationWorkProjection,
    *,
    audience: RelationWorkAudience,
) -> RelationWorkProjectionView:
    allowed = (
        {"dream_and_lab"}
        if audience == "dream"
        else {"dream_and_lab", "lab_only", "professional_only", "legacy_read_only"}
    )
    factual = [
        item for item in projection.factual_view
        if item.disclosure_state in allowed
    ]
    paths = [
        item for item in projection.candidate_path_view
        if item.disclosure_state in allowed
    ]
    professional = [
        item for item in projection.professionally_resolved_view
        if item.disclosure_state in allowed
    ]
    payload = {
        "schema_version": "deepbazi.relation-work-projection-view.p0.v1",
        "audience": audience,
        "foundation_ref": projection.foundation_ref,
        "foundation_content_hash": projection.content_hash,
        "source": projection.source.model_dump(mode="json"),
        "factual_view": [item.model_dump(mode="json") for item in factual],
        "candidate_path_view": [item.model_dump(mode="json") for item in paths],
        "professionally_resolved_view": [
            item.model_dump(mode="json") for item in professional
        ],
        "withheld_counts": {
            "facts": len(projection.factual_view) - len(factual),
            "paths": len(projection.candidate_path_view) - len(paths),
            "professional": (
                len(projection.professionally_resolved_view) - len(professional)
            ),
        },
        "read_only": True,
        "consumer_inference_allowed": False,
    }
    return RelationWorkProjectionView(
        **payload,
        content_hash=canonical_hash(payload),
    )


def _source_binding(
    relation_facts: list[RelationFactRevision],
) -> RelationWorkSourceBinding:
    first = relation_facts[0]
    identity = first.fact_key
    expected = (
        identity.scene_ref,
        identity.life_case_id,
        identity.chart_version_id,
        identity.world_lineage,
        first.source_snapshot_ref,
        first.source_snapshot_hash,
    )
    for item in relation_facts[1:]:
        current = (
            item.fact_key.scene_ref,
            item.fact_key.life_case_id,
            item.fact_key.chart_version_id,
            item.fact_key.world_lineage,
            item.source_snapshot_ref,
            item.source_snapshot_hash,
        )
        if current != expected:
            raise ValueError("relation_work_projection_mixed_source_snapshot")
    return RelationWorkSourceBinding(
        scene_ref=identity.scene_ref,
        life_case_id=identity.life_case_id,
        chart_version_id=identity.chart_version_id,
        world_lineage=identity.world_lineage,
        source_snapshot_ref=first.source_snapshot_ref,
        source_snapshot_hash=first.source_snapshot_hash,
    )


def _project_fact(
    fact: RelationFactRevision,
    resolution: RelationEffectResolution | None,
) -> RelationFactProjectionItem:
    legality = assess_relation_fact_legality(fact)
    disclosure = _fact_disclosure(fact)
    if (
        disclosure == "legacy_read_only"
        and resolution is not None
        and resolution.status
        == RelationEffectResolutionStatus.PROFESSIONALLY_RESOLVED
    ):
        effect_status = "effect_unresolved"
        effect_ref = resolution.resolution_ref
        atoms = []
        reasons = ["legacy_read_only_not_professional_authority"]
    elif resolution is None:
        effect_status = "effect_unresolved"
        effect_ref = ""
        atoms: list[str] = []
        reasons = ["effect_resolution_missing"]
    elif resolution.status == RelationEffectResolutionStatus.PROFESSIONALLY_RESOLVED:
        effect_status = "professionally_resolved"
        effect_ref = resolution.resolution_ref
        atoms = list(resolution.resolved_effect_atoms)
        reasons = []
    elif resolution.status == RelationEffectResolutionStatus.REJECTED:
        effect_status = "rejected"
        effect_ref = resolution.resolution_ref
        atoms = []
        reasons = list(resolution.rejection_reasons)
    else:
        effect_status = "effect_unresolved"
        effect_ref = resolution.resolution_ref
        atoms = []
        reasons = list(resolution.unresolved_reasons)
    return RelationFactProjectionItem(
        relation_fact_id=fact.revision_ref,
        fact_revision_ref=fact.revision_ref,
        fact_key_ref=fact.fact_key.fact_key,
        relation_family=fact.fact_key.relation_family,
        relation_kind=legality.relation_kind,
        participant_refs=[
            item.node_ref for item in fact.fact_key.participant_refs
        ],
        participant_kinds=legality.participant_kinds,
        participant_coordinates=[
            _coordinate(item) for item in fact.fact_key.participant_refs
        ],
        participant_roles={
            item.participant_ref: item.role
            for item in fact.fact_key.participant_roles
        },
        directionality=fact.fact_key.directionality.value,
        direct_or_mediated=legality.direct_or_mediated,
        mediator_refs=legality.mediator_refs,
        prerequisite_refs=legality.prerequisite_refs,
        exclusion_refs=legality.exclusion_refs,
        source_layer=legality.source_layer,
        time_scope=legality.time_scope,
        professional_stage=legality.professional_stage,
        rule_id=legality.rule_id,
        rule_version=legality.rule_version,
        provenance_status=legality.provenance_status,
        legality_class=legality.legality_class,
        missing_requirements=legality.missing_requirements,
        default_path_eligible=legality.default_path_eligible,
        inventory_visible=legality.inventory_visible,
        fact_state=fact.fact_state.value,
        activation_state=fact.activation_state.value,
        temporal_stage=fact.temporal_stage,
        valid_from_stage=fact.valid_from_stage,
        valid_to_stage=fact.valid_to_stage,
        effect_resolution_ref=effect_ref,
        effect_status=effect_status,
        resolved_effect_atoms=atoms,
        unresolved_reasons=reasons,
        disclosure_state=disclosure,
        school_profile_id=fact.fact_key.school_profile_id,
        school_profile_version=fact.fact_key.school_profile_version,
        producer_id=fact.producer_id,
        producer_version=fact.producer_version,
        evidence_refs=[fact.revision_ref, *fact.evidence_refs],
    )


def _project_path(
    candidate: WorkPathCandidate,
    coordinates: dict[str, list[dict[str, str]]],
    disclosures: dict[str, RelationWorkDisclosure],
) -> WorkPathProjectionItem:
    ordered_fact_refs = [
        item.relation_fact_revision_ref for item in candidate.segments
    ]
    unknown = set(ordered_fact_refs).difference(coordinates)
    if unknown:
        raise ValueError("work_path_projection_unknown_fact_revision")
    unique_coordinates: dict[str, dict[str, str]] = {}
    for fact_ref in ordered_fact_refs:
        for coordinate in coordinates[fact_ref]:
            unique_coordinates[coordinate["node_ref"]] = coordinate
    unresolved_reasons = sorted({
        *(
            f"axis:{axis}:{value}"
            for axis, value in candidate.axes.model_dump(mode="json").items()
            if value
            not in {"continuous", "natal_present", "temporarily_present"}
        ),
        *(f"blocker:{item.blocker_type}" for item in candidate.blockers),
        "professional_effect_not_admitted",
    })
    disclosure = "lab_only"
    if all(
        disclosures[item] == "dream_and_lab"
        for item in ordered_fact_refs
    ):
        disclosure = "dream_and_lab"
    return WorkPathProjectionItem(
        work_path_candidate_ref=candidate.candidate_ref,
        label=candidate.label,
        actor_ref=candidate.actor_ref,
        actor_role=candidate.actor_role,
        action=candidate.action,
        receiver_ref=candidate.receiver_ref,
        receiver_role=candidate.receiver_role,
        ordered_fact_revision_refs=ordered_fact_refs,
        participant_coordinates=list(unique_coordinates.values()),
        intermediate_participant_refs=candidate.intermediate_participant_refs,
        structural_carrier_refs=candidate.structural_carrier_refs,
        effect_resolution_refs=candidate.effect_resolution_refs,
        blocker_refs=[item.blocker_ref for item in candidate.blockers],
        blocker_types=[item.blocker_type for item in candidate.blockers],
        shared_resource_refs=[
            item.participant_ref for item in candidate.shared_resource_claims
        ],
        competing_path_group_ref=candidate.competing_path_group_ref,
        cycle_node_refs=candidate.cycle_node_refs,
        bottleneck_node_refs=candidate.bottleneck_node_refs,
        counterfactual_refs=candidate.counterfactual_refs,
        temporal_delta_refs=candidate.temporal_delta_refs,
        valid_from_stage=candidate.valid_from_stage,
        valid_to_stage=candidate.valid_to_stage,
        axes=candidate.axes.model_dump(mode="json"),
        unresolved_reasons=unresolved_reasons,
        disclosure_state=disclosure,
        school_profile_id=candidate.school_profile_id,
        school_profile_version=candidate.school_profile_version,
        provenance_refs=candidate.provenance_refs,
    )


def _project_professional(
    resolution: RelationEffectResolution,
    relation_facts: list[RelationFactRevision],
) -> ProfessionalResolutionProjectionItem:
    fact_by_ref = {item.revision_ref: item for item in relation_facts}
    if not set(resolution.relation_fact_revision_refs).issubset(fact_by_ref):
        raise ValueError("professional_projection_unknown_relation_fact")
    disclosure = (
        "dream_and_lab"
        if all(
            _fact_disclosure(fact_by_ref[item]) == "dream_and_lab"
            for item in resolution.relation_fact_revision_refs
        )
        else "professional_only"
    )
    return ProfessionalResolutionProjectionItem(
        effect_resolution_ref=resolution.resolution_ref,
        relation_fact_revision_refs=resolution.relation_fact_revision_refs,
        relation_fact_key_refs=resolution.relation_fact_key_refs,
        resolved_effect_atoms=resolution.resolved_effect_atoms,
        profile_id=resolution.profile_id,
        profile_version=resolution.profile_version,
        evidence_refs=resolution.evidence_refs,
        disclosure_state=disclosure,
    )


def _coordinate(node: object) -> dict[str, str]:
    return {
        "node_ref": str(getattr(node, "node_ref")),
        "scope": str(getattr(node, "scope")),
        "slot": str(getattr(node, "slot")),
        "level": str(getattr(node, "level")),
        "component": str(getattr(node, "component")),
        "temporal_snapshot_ref": str(getattr(node, "temporal_snapshot_ref")),
    }


def _fact_disclosure(fact: RelationFactRevision) -> RelationWorkDisclosure:
    manifest = fact.disclosure_manifest
    if (
        manifest.get("legacy_authority") == "read_only"
        or manifest.get("authority") == "legacy_read_only"
    ):
        return "legacy_read_only"
    if manifest.get("dream") in {"visible", "member", "allowed"}:
        return "dream_and_lab"
    if manifest.get("fact") in {"research", "lab"}:
        return "lab_only"
    return "professional_only"


__all__ = [
    "ProfessionalResolutionProjectionItem",
    "RELATION_WORK_PROJECTION_VERSION",
    "RelationFactProjectionItem",
    "RelationWorkProjectionView",
    "RelationWorkSourceBinding",
    "SharedRelationWorkProjection",
    "WorkPathProjectionItem",
    "compile_shared_relation_work_projection",
    "project_relation_work_for_consumer",
]
