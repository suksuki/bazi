from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field, model_validator

from core.graph.provenance import (
    AssertionLifecycle,
    PathAssertion,
    RelationAssertion,
    validate_assertion_history,
)
from experience.compiler import canonical_hash
from experience.contracts import (
    AllowedChartFact,
    ApprovedClaim,
    ApprovedReasoningStep,
    CompetingHypothesis,
    EnvelopeUncertainty,
    ExperienceModel,
)


CanonicalSceneRole = Literal["guest", "member", "practitioner", "research", "admin"]
CanonicalProjectionKind = Literal["onecanvas", "abu", "theater", "xiangfa", "workspace"]
CANONICAL_PROJECTION_KINDS: tuple[CanonicalProjectionKind, ...] = (
    "onecanvas",
    "abu",
    "theater",
    "xiangfa",
    "workspace",
)


class CanonicalTemporalState(ExperienceModel):
    temporal_snapshot_refs: list[str] = Field(default_factory=list)
    selected_period: str = Field(default="", max_length=40)
    luck_pillar: str = Field(default="", max_length=4)
    luck_year_range: list[int] = Field(default_factory=list, max_length=2)
    annual_pillar: str = Field(default="", max_length=4)
    analysis_year: int | None = Field(default=None, ge=1800, le=2200)
    validation_status: str = Field(default="unavailable", max_length=80)
    publicly_supported: bool = False
    source_refs: list[str] = Field(default_factory=list)


class CanonicalRelationAssertionView(ExperienceModel):
    assertion_ref: str = Field(min_length=1, max_length=180)
    relation_ref: str = Field(min_length=1, max_length=180)
    relation_type: str = Field(min_length=1, max_length=100)
    participant_node_refs: list[str] = Field(min_length=2)
    status: Literal["committed", "superseded", "rejected", "legacy_unresolved"]
    supersedes: str = Field(default="", max_length=180)
    statement: str = Field(default="", max_length=500)
    source_refs: list[str] = Field(default_factory=list)


class CanonicalPathAssertionView(ExperienceModel):
    assertion_ref: str = Field(min_length=1, max_length=180)
    path_ref: str = Field(min_length=1, max_length=180)
    node_refs: list[str] = Field(default_factory=list)
    relation_refs: list[str] = Field(default_factory=list)
    status: Literal["committed", "superseded", "rejected", "legacy_unresolved"]
    supersedes: str = Field(default="", max_length=180)
    statement: str = Field(default="", max_length=500)
    unresolved_reason: str = Field(default="", max_length=180)
    source_refs: list[str] = Field(default_factory=list)


class CanonicalSceneSource(ExperienceModel):
    schema_version: Literal["deepbazi.canonical_scene_source.v1"] = (
        "deepbazi.canonical_scene_source.v1"
    )
    case_ref: str = Field(min_length=1, max_length=180)
    chart_version_id: str = Field(min_length=1, max_length=180)
    chart_hash: str = Field(min_length=1, max_length=128)
    world_id: str = Field(min_length=1, max_length=180)
    life_case_id: str = Field(min_length=1, max_length=180)
    life_case_version: str = Field(min_length=1, max_length=120)
    source_updated_at: datetime
    chart_facts: list[AllowedChartFact] = Field(min_length=4, max_length=4)
    approved_claims: list[ApprovedClaim] = Field(min_length=1)
    approved_reasoning_steps: list[ApprovedReasoningStep] = Field(default_factory=list)
    competing_hypotheses: list[CompetingHypothesis] = Field(default_factory=list)
    relation_assertions: list[RelationAssertion] = Field(default_factory=list)
    path_assertions: list[PathAssertion] = Field(default_factory=list)
    temporal_state: CanonicalTemporalState = Field(default_factory=CanonicalTemporalState)
    uncertainty: EnvelopeUncertainty = Field(default_factory=EnvelopeUncertainty)
    must_not_say: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(min_length=3)

    @model_validator(mode="after")
    def validate_source_identity(self) -> "CanonicalSceneSource":
        _unique(self.chart_facts, "fact_ref", "canonical_scene_duplicate_fact")
        _unique(self.approved_claims, "claim_ref", "canonical_scene_duplicate_claim")
        _unique(
            self.approved_reasoning_steps,
            "step_ref",
            "canonical_scene_duplicate_reasoning_step",
        )
        _unique(
            self.competing_hypotheses,
            "hypothesis_ref",
            "canonical_scene_duplicate_hypothesis",
        )
        _unique(
            self.relation_assertions,
            "assertion_id",
            "canonical_scene_duplicate_relation_assertion",
        )
        _unique(
            self.path_assertions,
            "assertion_id",
            "canonical_scene_duplicate_path_assertion",
        )
        if any(item.status == AssertionLifecycle.CANDIDATE for item in self.relation_assertions):
            raise ValueError("canonical_scene_source_cannot_accept_candidate_relation")
        if any(item.status == AssertionLifecycle.CANDIDATE for item in self.path_assertions):
            raise ValueError("canonical_scene_source_cannot_accept_candidate_path")
        validate_assertion_history(self.relation_assertions)
        validate_assertion_history(self.path_assertions)
        slots = [item.pillar_slot for item in self.chart_facts]
        if slots != ["year", "month", "day", "hour"]:
            raise ValueError("canonical_scene_requires_ordered_four_pillars")
        return self


class CanonicalSceneIdentity(ExperienceModel):
    scene_id: str = Field(min_length=1, max_length=180)
    compiler_version: str = Field(min_length=1, max_length=100)
    case_ref: str = Field(min_length=1, max_length=180)
    chart_version_id: str = Field(min_length=1, max_length=180)
    world_id: str = Field(min_length=1, max_length=180)
    life_case_id: str = Field(min_length=1, max_length=180)
    life_case_version: str = Field(min_length=1, max_length=120)
    source_updated_at: datetime
    source_hash: str = Field(min_length=64, max_length=64)


class CanonicalRoleDisclosure(ExperienceModel):
    policy_version: Literal["canonical-scene-disclosure.v1"] = "canonical-scene-disclosure.v1"
    role: CanonicalSceneRole
    disclosure_level: Literal["chart_facts", "approved_insights", "professional", "research"]
    visible_fact_refs: list[str]
    visible_claim_refs: list[str]
    visible_reasoning_step_refs: list[str]
    visible_hypothesis_refs: list[str]
    visible_temporal_refs: list[str]
    visible_relation_assertion_refs: list[str] = Field(default_factory=list)
    visible_path_assertion_refs: list[str] = Field(default_factory=list)
    prohibited_fields: list[str]
    prohibited_capabilities: list[str]
    disclosure_hash: str = Field(min_length=64, max_length=64)


class CanonicalScene(ExperienceModel):
    schema_version: Literal["deepbazi.canonical_scene.v1"] = "deepbazi.canonical_scene.v1"
    identity: CanonicalSceneIdentity
    role_disclosure: CanonicalRoleDisclosure
    chart_facts: list[AllowedChartFact]
    approved_claims: list[ApprovedClaim]
    approved_reasoning_steps: list[ApprovedReasoningStep]
    competing_hypotheses: list[CompetingHypothesis]
    relation_assertions: list[CanonicalRelationAssertionView]
    path_assertions: list[CanonicalPathAssertionView]
    temporal_state: CanonicalTemporalState
    uncertainty: EnvelopeUncertainty
    must_not_say: list[str]
    semantic_refs: list[str]
    content_hash: str = Field(min_length=64, max_length=64)

    @model_validator(mode="after")
    def validate_disclosed_content(self) -> "CanonicalScene":
        disclosure = self.role_disclosure
        actual = {
            "facts": [item.fact_ref for item in self.chart_facts],
            "claims": [item.claim_ref for item in self.approved_claims],
            "reasoning": [item.step_ref for item in self.approved_reasoning_steps],
            "hypotheses": [item.hypothesis_ref for item in self.competing_hypotheses],
            "relations": [item.assertion_ref for item in self.relation_assertions],
            "paths": [item.assertion_ref for item in self.path_assertions],
        }
        expected = {
            "facts": disclosure.visible_fact_refs,
            "claims": disclosure.visible_claim_refs,
            "reasoning": disclosure.visible_reasoning_step_refs,
            "hypotheses": disclosure.visible_hypothesis_refs,
            "relations": disclosure.visible_relation_assertion_refs,
            "paths": disclosure.visible_path_assertion_refs,
        }
        if actual != expected:
            raise ValueError("canonical_scene_disclosure_content_mismatch")
        if set(self.semantic_refs) != {
            *actual["facts"],
            *actual["claims"],
            *actual["reasoning"],
            *actual["hypotheses"],
            *actual["relations"],
            *actual["paths"],
            *disclosure.visible_temporal_refs,
        }:
            raise ValueError("canonical_scene_semantic_ref_mismatch")
        return self


class CanonicalProjectionEnvelope(ExperienceModel):
    schema_version: Literal["deepbazi.canonical_projection_envelope.v1"] = (
        "deepbazi.canonical_projection_envelope.v1"
    )
    projection_id: str = Field(min_length=1, max_length=200)
    projection_kind: CanonicalProjectionKind
    scene_identity: CanonicalSceneIdentity
    role_disclosure: CanonicalRoleDisclosure
    adapter_id: str = Field(min_length=1, max_length=120)
    payload: dict[str, Any]
    semantic_refs: list[str]
    projection_hash: str = Field(min_length=64, max_length=64)
    creates_mingli_facts: Literal[False] = False
    creates_mingli_claims: Literal[False] = False
    writes_chart: Literal[False] = False
    writes_life_case: Literal[False] = False

    @model_validator(mode="after")
    def validate_projection_refs(self) -> "CanonicalProjectionEnvelope":
        disclosed = {
            *self.role_disclosure.visible_fact_refs,
            *self.role_disclosure.visible_claim_refs,
            *self.role_disclosure.visible_reasoning_step_refs,
            *self.role_disclosure.visible_hypothesis_refs,
            *self.role_disclosure.visible_temporal_refs,
            *self.role_disclosure.visible_relation_assertion_refs,
            *self.role_disclosure.visible_path_assertion_refs,
        }
        if not set(self.semantic_refs).issubset(disclosed):
            raise ValueError("canonical_projection_uses_undisclosed_ref")
        return self


class CanonicalSceneBundle(ExperienceModel):
    schema_version: Literal["deepbazi.canonical_scene_bundle.v1"] = (
        "deepbazi.canonical_scene_bundle.v1"
    )
    scene: CanonicalScene
    projections: dict[CanonicalProjectionKind, CanonicalProjectionEnvelope]
    owner: Literal["CanonicalSceneCompiler"] = "CanonicalSceneCompiler"
    source_chain: list[str]
    compatibility_policy: dict[str, Any]

    @model_validator(mode="after")
    def validate_projection_identity(self) -> "CanonicalSceneBundle":
        if set(self.projections) != set(CANONICAL_PROJECTION_KINDS):
            raise ValueError("canonical_scene_requires_all_projection_kinds")
        for kind, projection in self.projections.items():
            if projection.projection_kind != kind:
                raise ValueError("canonical_projection_kind_key_mismatch")
            if projection.scene_identity != self.scene.identity:
                raise ValueError("canonical_projection_scene_identity_mismatch")
            if projection.role_disclosure != self.scene.role_disclosure:
                raise ValueError("canonical_projection_disclosure_mismatch")
        return self


def compile_canonical_scene(
    *,
    source: CanonicalSceneSource,
    role: CanonicalSceneRole,
) -> CanonicalScene:
    """Compile one role-filtered scene from an immutable formal source."""

    source_hash = canonical_hash(source)
    identity = CanonicalSceneIdentity(
        scene_id=f"scene-{source_hash[:24]}",
        compiler_version="canonical-scene-compiler.cag03.v1",
        case_ref=source.case_ref,
        chart_version_id=source.chart_version_id,
        world_id=source.world_id,
        life_case_id=source.life_case_id,
        life_case_version=source.life_case_version,
        source_updated_at=source.source_updated_at,
        source_hash=source_hash,
    )
    facts = list(source.chart_facts)
    professional = role in {"practitioner", "research", "admin"}
    claims = (
        list(source.approved_claims)
        if professional
        else [
            item.model_copy(update={"evidence_refs": [], "visual_anchors": []})
            for item in source.approved_claims
        ]
        if role == "member"
        else []
    )
    reasoning = (
        list(source.approved_reasoning_steps)
        if professional
        else [
            item.model_copy(update={
                "premise": "当前角色不披露专业推理前提。",
                "source_refs": [],
            })
            for item in source.approved_reasoning_steps
        ]
        if role == "member"
        else []
    )
    hypotheses = list(source.competing_hypotheses) if professional else []
    active_relation_ids = _active_committed_assertion_ids(source.relation_assertions)
    active_path_ids = _active_committed_assertion_ids(source.path_assertions)
    relation_assertions = [
        _relation_assertion_view(item, disclose_sources=professional)
        for item in source.relation_assertions
        if professional
        or (role == "member" and item.assertion_id in active_relation_ids)
    ]
    path_assertions = [
        _path_assertion_view(item, disclose_sources=professional)
        for item in source.path_assertions
        if professional
        or (role == "member" and item.assertion_id in active_path_ids)
    ]
    temporal_refs = list(source.temporal_state.temporal_snapshot_refs)
    temporal_state = (
        source.temporal_state
        if professional
        else source.temporal_state.model_copy(update={"source_refs": []})
    )
    disclosure_level = (
        "research"
        if role in {"research", "admin"}
        else "professional"
        if role == "practitioner"
        else "approved_insights"
        if role == "member"
        else "chart_facts"
    )
    disclosure_payload = {
        "role": role,
        "disclosure_level": disclosure_level,
        "facts": [item.fact_ref for item in facts],
        "claims": [item.claim_ref for item in claims],
        "reasoning": [item.step_ref for item in reasoning],
        "hypotheses": [item.hypothesis_ref for item in hypotheses],
        "relations": [item.assertion_ref for item in relation_assertions],
        "paths": [item.assertion_ref for item in path_assertions],
        "temporal": temporal_refs,
        "prohibited_fields": [
            "reality_evidence",
            "draft_insights",
            "research_context",
            "legacy_record",
            "raw_world_facts",
            "undisclosed_relation_assertions",
            "undisclosed_path_assertions",
        ],
        "prohibited_capabilities": [
            "modify_chart",
            "modify_life_case",
            "promote_candidate",
            "infer_missing_relation",
            "promote_relation_assertion",
            "promote_path_assertion",
            "override_scene_source",
        ],
    }
    disclosure = CanonicalRoleDisclosure(
        policy_version="canonical-scene-disclosure.v1",
        role=role,
        disclosure_level=disclosure_level,
        visible_fact_refs=disclosure_payload["facts"],
        visible_claim_refs=disclosure_payload["claims"],
        visible_reasoning_step_refs=disclosure_payload["reasoning"],
        visible_hypothesis_refs=disclosure_payload["hypotheses"],
        visible_temporal_refs=temporal_refs,
        visible_relation_assertion_refs=disclosure_payload["relations"],
        visible_path_assertion_refs=disclosure_payload["paths"],
        prohibited_fields=disclosure_payload["prohibited_fields"],
        prohibited_capabilities=disclosure_payload["prohibited_capabilities"],
        disclosure_hash=canonical_hash(disclosure_payload),
    )
    semantic_refs = list(dict.fromkeys([
        *disclosure.visible_fact_refs,
        *disclosure.visible_claim_refs,
        *disclosure.visible_reasoning_step_refs,
        *disclosure.visible_hypothesis_refs,
        *disclosure.visible_relation_assertion_refs,
        *disclosure.visible_path_assertion_refs,
        *disclosure.visible_temporal_refs,
    ]))
    view_payload = {
        "identity": identity.model_dump(mode="json"),
        "role_disclosure": disclosure.model_dump(mode="json"),
        "chart_facts": [item.model_dump(mode="json") for item in facts],
        "approved_claims": [item.model_dump(mode="json") for item in claims],
        "approved_reasoning_steps": [item.model_dump(mode="json") for item in reasoning],
        "competing_hypotheses": [item.model_dump(mode="json") for item in hypotheses],
        "relation_assertions": [item.model_dump(mode="json") for item in relation_assertions],
        "path_assertions": [item.model_dump(mode="json") for item in path_assertions],
        "temporal_state": temporal_state.model_dump(mode="json"),
        "uncertainty": source.uncertainty.model_dump(mode="json"),
        "must_not_say": source.must_not_say,
        "semantic_refs": semantic_refs,
    }
    return CanonicalScene(
        **view_payload,
        content_hash=canonical_hash(view_payload),
    )


def compile_canonical_scene_bundle(scene: CanonicalScene) -> CanonicalSceneBundle:
    projections = {
        kind: compile_canonical_projection(scene=scene, kind=kind)
        for kind in CANONICAL_PROJECTION_KINDS
    }
    return CanonicalSceneBundle(
        scene=scene,
        projections=projections,
        source_chain=[
            "ChartWorldInstance",
            "LifeCase",
            "CanonicalSceneCompiler",
            "CanonicalProjectionEnvelope",
        ],
        compatibility_policy={
            "legacy_routes_remain_read_only_adapters": True,
            "legacy_routes_may_not_override_scene_identity": True,
            "client_formal_fact_input": False,
            "graph_and_path_semantics_changed": False,
            "relation_path_identity_owner": "LifeCase",
            "client_relation_path_input": False,
        },
    )


def compile_canonical_projection(
    *,
    scene: CanonicalScene,
    kind: CanonicalProjectionKind,
) -> CanonicalProjectionEnvelope:
    payload, refs = _projection_payload(scene=scene, kind=kind)
    projection_basis = {
        "scene_id": scene.identity.scene_id,
        "source_hash": scene.identity.source_hash,
        "disclosure_hash": scene.role_disclosure.disclosure_hash,
        "projection_kind": kind,
        "payload": payload,
        "semantic_refs": refs,
    }
    projection_hash = canonical_hash(projection_basis)
    return CanonicalProjectionEnvelope(
        projection_id=f"projection-{kind}-{projection_hash[:20]}",
        projection_kind=kind,
        scene_identity=scene.identity,
        role_disclosure=scene.role_disclosure,
        adapter_id=f"canonical-scene-{kind}.cag03.v1",
        payload=payload,
        semantic_refs=refs,
        projection_hash=projection_hash,
    )


def _projection_payload(
    *,
    scene: CanonicalScene,
    kind: CanonicalProjectionKind,
) -> tuple[dict[str, Any], list[str]]:
    fact_refs = [item.fact_ref for item in scene.chart_facts]
    claim_refs = [item.claim_ref for item in scene.approved_claims]
    reasoning_refs = [item.step_ref for item in scene.approved_reasoning_steps]
    hypothesis_refs = [item.hypothesis_ref for item in scene.competing_hypotheses]
    relation_assertion_refs = [item.assertion_ref for item in scene.relation_assertions]
    path_assertion_refs = [item.assertion_ref for item in scene.path_assertions]
    temporal_refs = list(scene.role_disclosure.visible_temporal_refs)

    if kind == "onecanvas":
        refs = [
            *fact_refs,
            *claim_refs,
            *reasoning_refs,
            *relation_assertion_refs,
            *path_assertion_refs,
            *temporal_refs,
        ]
        payload = {
            "semantic_slots": [item.model_dump(mode="json") for item in scene.chart_facts],
            "temporal_state": scene.temporal_state.model_dump(mode="json"),
            "committed_claim_refs": claim_refs,
            "reasoning_step_refs": reasoning_refs,
            "relation_assertions": [
                item.model_dump(mode="json") for item in scene.relation_assertions
            ],
            "path_assertions": [
                item.model_dump(mode="json") for item in scene.path_assertions
            ],
            "renderer_policy": {
                "infer_relations": False,
                "infer_paths": False,
                "mutate_formal_state": False,
            },
        }
    elif kind == "abu":
        refs = [
            *claim_refs,
            *reasoning_refs,
            *hypothesis_refs,
            *relation_assertion_refs,
            *path_assertion_refs,
            *temporal_refs,
        ]
        payload = {
            "approved_claims": [item.model_dump(mode="json") for item in scene.approved_claims],
            "approved_reasoning_steps": [
                item.model_dump(mode="json") for item in scene.approved_reasoning_steps
            ],
            "competing_hypotheses": [
                item.model_dump(mode="json") for item in scene.competing_hypotheses
            ],
            "relation_assertion_refs": relation_assertion_refs,
            "path_assertions": [
                item.model_dump(mode="json") for item in scene.path_assertions
            ],
            "uncertainty": scene.uncertainty.model_dump(mode="json"),
            "must_not_say": scene.must_not_say,
            "abu_policy": "explain_navigate_and_request_approved_actions_only",
        }
    elif kind == "theater":
        refs = [
            *fact_refs,
            *claim_refs,
            *reasoning_refs,
            *relation_assertion_refs,
            *path_assertion_refs,
            *temporal_refs,
        ]
        payload = {
            "chart_facts": [item.model_dump(mode="json") for item in scene.chart_facts],
            "approved_claims": [item.model_dump(mode="json") for item in scene.approved_claims],
            "reasoning_steps": [
                item.model_dump(mode="json") for item in scene.approved_reasoning_steps
            ],
            "relation_assertion_refs": relation_assertion_refs,
            "path_assertion_refs": path_assertion_refs,
            "cue_binding_refs": refs,
            "runtime_policy": "frozen_cues_may_only_consume_disclosed_refs",
        }
    elif kind == "xiangfa":
        refs = [
            *fact_refs,
            *claim_refs,
            *relation_assertion_refs,
            *path_assertion_refs,
            *temporal_refs,
        ]
        payload = {
            "semantic_bindings": [
                *({"semantic_ref": ref, "kind": "chart_fact"} for ref in fact_refs),
                *({"semantic_ref": ref, "kind": "approved_claim"} for ref in claim_refs),
                *({"semantic_ref": ref, "kind": "temporal_state"} for ref in temporal_refs),
                *({"semantic_ref": ref, "kind": "relation_assertion"} for ref in relation_assertion_refs),
                *({"semantic_ref": ref, "kind": "path_assertion"} for ref in path_assertion_refs),
            ],
            "render_policy": {
                "visual_metaphor_may_add_mingli_fact": False,
                "unbound_visuals_are_decoration_only": True,
            },
        }
    else:
        refs = [
            *fact_refs,
            *claim_refs,
            *relation_assertion_refs,
            *path_assertion_refs,
            *temporal_refs,
        ]
        payload = {
            "case_ref": scene.identity.case_ref,
            "baseline_claim": (
                scene.approved_claims[0].model_dump(mode="json")
                if scene.approved_claims
                else None
            ),
            "available_claim_refs": claim_refs,
            "relation_assertion_refs": relation_assertion_refs,
            "path_assertion_refs": path_assertion_refs,
            "temporal_state": scene.temporal_state.model_dump(mode="json"),
            "mode_catalog": ["overview", "onecanvas", "xiangfa", "theater", "mingli_lab"],
            "workspace_policy": "ui_state_never_becomes_formal_cognition",
        }
    return payload, list(dict.fromkeys(refs))


def _relation_assertion_view(
    assertion: RelationAssertion,
    *,
    disclose_sources: bool,
) -> CanonicalRelationAssertionView:
    return CanonicalRelationAssertionView(
        assertion_ref=assertion.assertion_id,
        relation_ref=assertion.relation_key.relation_key,
        relation_type=assertion.relation_key.relation_type,
        participant_node_refs=[
            item.node_ref for item in assertion.relation_key.participant_refs
        ],
        status=assertion.status.value,  # type: ignore[arg-type]
        supersedes=assertion.supersedes,
        statement=assertion.statement,
        source_refs=(
            list(dict.fromkeys([
                assertion.provenance.provenance_id,
                *assertion.provenance.evidence_refs,
                *assertion.provenance.source_refs,
            ]))
            if disclose_sources
            else []
        ),
    )


def _path_assertion_view(
    assertion: PathAssertion,
    *,
    disclose_sources: bool,
) -> CanonicalPathAssertionView:
    path_key = assertion.path_key
    return CanonicalPathAssertionView(
        assertion_ref=assertion.assertion_id,
        path_ref=path_key.path_key if path_key else assertion.legacy_ref,
        node_refs=[item.node_ref for item in path_key.node_refs] if path_key else [],
        relation_refs=[
            item.relation_key for item in path_key.relation_keys
        ] if path_key else [],
        status=assertion.status.value,  # type: ignore[arg-type]
        supersedes=assertion.supersedes,
        statement=assertion.statement,
        unresolved_reason=assertion.unresolved_reason,
        source_refs=(
            list(dict.fromkeys([
                assertion.provenance.provenance_id,
                *assertion.provenance.evidence_refs,
                *assertion.provenance.source_refs,
            ]))
            if disclose_sources
            else []
        ),
    )


def _active_committed_assertion_ids(assertions: list[Any]) -> set[str]:
    superseded = {item.supersedes for item in assertions if item.supersedes}
    return {
        item.assertion_id
        for item in assertions
        if item.status == AssertionLifecycle.COMMITTED
        and item.assertion_id not in superseded
    }


def _unique(rows: list[Any], field: str, error: str) -> None:
    values = [str(getattr(item, field)) for item in rows]
    if len(values) != len(set(values)):
        raise ValueError(error)
