from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Literal

from pydantic import Field, model_validator

from core.graph import (
    AssertionLifecycle,
    NodeRef,
    PathAssertion,
    ProvenanceRecord,
    RelationAssertion,
    canonical_scene_scope_ref,
)
from experience.canonical_scene import (
    CanonicalProjectionEnvelope,
    CanonicalSceneIdentity,
    CanonicalSceneSource,
)
from experience.compiler import canonical_hash
from experience.contracts import ExperienceModel, TopicExploration


LabExperimentKind = Literal[
    "mechanism_ablation",
    "temporal_hypothesis",
    "relation_inspection",
    "candidate_interpretation",
    "competing_path_comparison",
    "synthetic_case",
    "counterexample_review",
    "algorithm_change_validation",
]
LabSessionStatus = Literal["active", "modified", "restored", "saved", "discarded"]
LabComparisonStatus = Literal["open", "needs_evidence", "resolved", "rejected"]
LabPromotionStatus = Literal["blocked", "ready_for_risk_gate"]


class MingliLabSession(ExperienceModel):
    """Shared non-authoritative identity for every Mingli Lab experiment."""

    schema_version: Literal["deepbazi.mingli_lab_session.v1"] = (
        "deepbazi.mingli_lab_session.v1"
    )
    session_id: str = Field(min_length=1, max_length=180)
    participant_run_id: str = Field(default="", max_length=180)
    case_ref: str = Field(min_length=1, max_length=180)
    scene_id: str = Field(min_length=1, max_length=180)
    scene_source_hash: str = Field(min_length=64, max_length=64)
    disclosure_hash: str = Field(min_length=64, max_length=64)
    experiment_kind: LabExperimentKind
    base_snapshot_ref: str = Field(min_length=1, max_length=220)
    source_mode: Literal["canonical_projection", "synthetic_fixture", "legacy_unresolved"]
    synthetic_fixture_ref: str = Field(default="", max_length=220)
    revision: int = Field(default=0, ge=0)
    status: LabSessionStatus = "active"
    created_at: datetime
    updated_at: datetime
    writes_chart: Literal[False] = False
    writes_life_case: Literal[False] = False
    promotes_candidate: Literal[False] = False

    @model_validator(mode="after")
    def validate_source(self) -> "MingliLabSession":
        if self.source_mode == "canonical_projection" and self.scene_id.startswith("legacy-"):
            raise ValueError("canonical_lab_session_requires_canonical_scene")
        if self.source_mode == "synthetic_fixture" and not self.synthetic_fixture_ref:
            raise ValueError("synthetic_lab_session_requires_fixture_ref")
        return self


class LabEvidenceSet(ExperienceModel):
    """Evidence required before a Lab candidate may enter a separate risk gate."""

    schema_version: Literal["deepbazi.lab_evidence_set.v1"] = (
        "deepbazi.lab_evidence_set.v1"
    )
    positive_fixture_refs: list[str] = Field(default_factory=list)
    negative_fixture_refs: list[str] = Field(default_factory=list)
    boundary_fixture_refs: list[str] = Field(default_factory=list)
    synthetic_case_refs: list[str] = Field(default_factory=list)
    counterexample_refs: list[str] = Field(default_factory=list)
    resolved_counterexample_refs: list[str] = Field(default_factory=list)
    regression_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_references(self) -> "LabEvidenceSet":
        for field_name in (
            "positive_fixture_refs",
            "negative_fixture_refs",
            "boundary_fixture_refs",
            "synthetic_case_refs",
            "counterexample_refs",
            "resolved_counterexample_refs",
            "regression_refs",
        ):
            values = getattr(self, field_name)
            if any(not value.strip() for value in values):
                raise ValueError(f"lab_evidence_empty_ref:{field_name}")
            if len(values) != len(set(values)):
                raise ValueError(f"lab_evidence_duplicate_ref:{field_name}")
        if not set(self.resolved_counterexample_refs).issubset(self.counterexample_refs):
            raise ValueError("lab_resolved_counterexample_not_observed")
        return self


class LabCandidateRevision(ExperienceModel):
    """An isolated candidate revision; it is never a formal LifeCase assertion."""

    schema_version: Literal["deepbazi.lab_candidate_revision.v1"] = (
        "deepbazi.lab_candidate_revision.v1"
    )
    revision_id: str = Field(min_length=1, max_length=180)
    revision: int = Field(ge=1)
    relation_assertions: list[RelationAssertion] = Field(default_factory=list)
    path_assertions: list[PathAssertion] = Field(default_factory=list)
    interpretation: str = Field(default="", max_length=2000)
    conditions: list[str] = Field(default_factory=list)
    counter_signals: list[str] = Field(default_factory=list)
    supersedes_revision_id: str = Field(default="", max_length=180)
    created_at: datetime
    writes_chart: Literal[False] = False
    writes_life_case: Literal[False] = False
    commits_assertion: Literal[False] = False

    @model_validator(mode="after")
    def validate_candidate_only(self) -> "LabCandidateRevision":
        assertions = [*self.relation_assertions, *self.path_assertions]
        if not assertions:
            raise ValueError("lab_candidate_revision_requires_assertion")
        if any(item.status != AssertionLifecycle.CANDIDATE for item in assertions):
            raise ValueError("lab_candidate_revision_requires_candidate_status")
        if self.revision == 1 and self.supersedes_revision_id:
            raise ValueError("first_lab_candidate_revision_cannot_supersede")
        return self


class LabPathComparison(ExperienceModel):
    schema_version: Literal["deepbazi.lab_path_comparison.v1"] = (
        "deepbazi.lab_path_comparison.v1"
    )
    comparison_id: str = Field(min_length=1, max_length=180)
    path_assertion_refs: list[str] = Field(min_length=2)
    selected_path_assertion_ref: str = Field(default="", max_length=180)
    status: LabComparisonStatus = "open"
    reason_refs: list[str] = Field(default_factory=list)
    created_at: datetime

    @model_validator(mode="after")
    def validate_comparison(self) -> "LabPathComparison":
        if len(self.path_assertion_refs) != len(set(self.path_assertion_refs)):
            raise ValueError("lab_path_comparison_duplicate_ref")
        if (
            self.selected_path_assertion_ref
            and self.selected_path_assertion_ref not in self.path_assertion_refs
        ):
            raise ValueError("lab_path_comparison_selection_not_compared")
        return self


class MingliLabStudy(ExperienceModel):
    """Research projection over one canonical scene, with isolated candidates."""

    schema_version: Literal["deepbazi.mingli_lab_study.v1"] = (
        "deepbazi.mingli_lab_study.v1"
    )
    study_id: str = Field(min_length=1, max_length=180)
    session: MingliLabSession
    scene_identity: CanonicalSceneIdentity
    disclosure_hash: str = Field(min_length=64, max_length=64)
    relation_scene_ref: str = Field(min_length=1, max_length=180)
    disclosed_relation_assertion_refs: list[str] = Field(default_factory=list)
    disclosed_path_assertion_refs: list[str] = Field(default_factory=list)
    node_refs: list[NodeRef] = Field(default_factory=list)
    formal_relation_assertions: list[RelationAssertion] = Field(default_factory=list)
    formal_path_assertions: list[PathAssertion] = Field(default_factory=list)
    provenance_records: list[ProvenanceRecord] = Field(default_factory=list)
    candidate_revisions: list[LabCandidateRevision] = Field(default_factory=list)
    path_comparisons: list[LabPathComparison] = Field(default_factory=list)
    evidence: LabEvidenceSet = Field(default_factory=LabEvidenceSet)
    created_at: datetime
    updated_at: datetime
    writes_chart: Literal[False] = False
    writes_life_case: Literal[False] = False
    promotes_candidate: Literal[False] = False

    @model_validator(mode="after")
    def validate_authority_boundary(self) -> "MingliLabStudy":
        if (
            self.session.scene_id != self.scene_identity.scene_id
            or self.session.scene_source_hash != self.scene_identity.source_hash
            or self.session.disclosure_hash != self.disclosure_hash
            or self.session.case_ref != self.scene_identity.case_ref
        ):
            raise ValueError("lab_study_scene_identity_mismatch")
        relation_ids = [item.assertion_id for item in self.formal_relation_assertions]
        path_ids = [item.assertion_id for item in self.formal_path_assertions]
        if relation_ids != self.disclosed_relation_assertion_refs:
            raise ValueError("lab_study_relation_disclosure_mismatch")
        if path_ids != self.disclosed_path_assertion_refs:
            raise ValueError("lab_study_path_disclosure_mismatch")
        if any(
            item.status == AssertionLifecycle.CANDIDATE
            for item in [*self.formal_relation_assertions, *self.formal_path_assertions]
        ):
            raise ValueError("lab_study_formal_view_cannot_contain_candidate")
        expected_nodes = _nodes_from_assertions(
            relation_assertions=self.formal_relation_assertions,
            path_assertions=self.formal_path_assertions,
        )
        if {item.node_ref for item in self.node_refs} != {
            item.node_ref for item in expected_nodes
        }:
            raise ValueError("lab_study_node_projection_mismatch")
        expected_provenance = _provenance_from_assertions(
            relation_assertions=self.formal_relation_assertions,
            path_assertions=self.formal_path_assertions,
        )
        if {item.provenance_id for item in self.provenance_records} != {
            item.provenance_id for item in expected_provenance
        }:
            raise ValueError("lab_study_provenance_projection_mismatch")
        if any(
            scene_ref != self.relation_scene_ref
            for scene_ref in _assertion_scene_refs(
                relation_assertions=self.formal_relation_assertions,
                path_assertions=self.formal_path_assertions,
            )
        ):
            raise ValueError("lab_study_formal_assertion_scene_mismatch")
        revision_ids = [item.revision_id for item in self.candidate_revisions]
        if len(revision_ids) != len(set(revision_ids)):
            raise ValueError("lab_study_duplicate_candidate_revision")
        candidate_assertion_ids: list[str] = []
        for index, revision in enumerate(self.candidate_revisions, start=1):
            if revision.revision != index:
                raise ValueError("lab_study_candidate_revision_sequence_mismatch")
            if any(
                scene_ref != self.relation_scene_ref
                for scene_ref in _assertion_scene_refs(
                    relation_assertions=revision.relation_assertions,
                    path_assertions=revision.path_assertions,
                )
            ):
                raise ValueError("lab_study_candidate_assertion_scene_mismatch")
            candidate_assertion_ids.extend(
                item.assertion_id
                for item in [*revision.relation_assertions, *revision.path_assertions]
            )
        if len(candidate_assertion_ids) != len(set(candidate_assertion_ids)):
            raise ValueError("lab_study_duplicate_candidate_assertion")
        if set(candidate_assertion_ids).intersection({*relation_ids, *path_ids}):
            raise ValueError("lab_study_candidate_overwrites_formal_assertion")
        known_path_refs = {
            *path_ids,
            *(
                item.assertion_id
                for revision in self.candidate_revisions
                for item in revision.path_assertions
            ),
        }
        if any(
            not set(comparison.path_assertion_refs).issubset(known_path_refs)
            for comparison in self.path_comparisons
        ):
            raise ValueError("lab_path_comparison_uses_unknown_assertion")
        return self


class LabPromotionProposal(ExperienceModel):
    """A hand-off to a separate risk gate; this object cannot promote anything."""

    schema_version: Literal["deepbazi.lab_promotion_proposal.v1"] = (
        "deepbazi.lab_promotion_proposal.v1"
    )
    proposal_id: str = Field(min_length=1, max_length=180)
    study_id: str = Field(min_length=1, max_length=180)
    candidate_revision_id: str = Field(min_length=1, max_length=180)
    status: LabPromotionStatus
    evidence_refs: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    requires_risk_gate: Literal[True] = True
    writes_chart: Literal[False] = False
    writes_life_case: Literal[False] = False
    performs_promotion: Literal[False] = False


def issue_lab_session(
    *,
    projection: CanonicalProjectionEnvelope,
    session_id: str,
    participant_run_id: str,
    experiment_kind: LabExperimentKind,
    base_snapshot_ref: str,
    source_mode: Literal["canonical_projection", "synthetic_fixture"] = (
        "canonical_projection"
    ),
    synthetic_fixture_ref: str = "",
    now: datetime | None = None,
) -> MingliLabSession:
    if projection.projection_kind not in {"onecanvas", "workspace", "theater"}:
        raise ValueError("lab_session_requires_structural_projection")
    issued_at = now or datetime.now(timezone.utc)
    return MingliLabSession(
        session_id=session_id,
        participant_run_id=participant_run_id,
        case_ref=projection.scene_identity.case_ref,
        scene_id=projection.scene_identity.scene_id,
        scene_source_hash=projection.scene_identity.source_hash,
        disclosure_hash=projection.role_disclosure.disclosure_hash,
        experiment_kind=experiment_kind,
        base_snapshot_ref=base_snapshot_ref,
        source_mode=source_mode,
        synthetic_fixture_ref=synthetic_fixture_ref,
        created_at=issued_at,
        updated_at=issued_at,
    )


def open_lab_study(
    *,
    session: MingliLabSession,
    projection: CanonicalProjectionEnvelope,
    source: CanonicalSceneSource,
    study_id: str,
    now: datetime | None = None,
) -> MingliLabStudy:
    """Open a research-only view without copying or owning formal cognition."""

    if projection.projection_kind not in {"workspace", "onecanvas"}:
        raise ValueError("lab_study_requires_workspace_or_onecanvas_projection")
    if projection.role_disclosure.disclosure_level != "research":
        raise ValueError("lab_study_requires_research_disclosure")
    if (
        session.scene_id != projection.scene_identity.scene_id
        or session.scene_source_hash != projection.scene_identity.source_hash
        or session.disclosure_hash != projection.role_disclosure.disclosure_hash
    ):
        raise ValueError("lab_session_projection_identity_mismatch")
    if canonical_hash(source) != projection.scene_identity.source_hash:
        raise ValueError("lab_study_source_hash_mismatch")
    identity = projection.scene_identity
    if (
        source.case_ref != identity.case_ref
        or source.chart_version_id != identity.chart_version_id
        or source.world_id != identity.world_id
        or source.life_case_id != identity.life_case_id
        or source.life_case_version != identity.life_case_version
    ):
        raise ValueError("lab_study_source_identity_mismatch")

    relation_by_id = {item.assertion_id: item for item in source.relation_assertions}
    path_by_id = {item.assertion_id: item for item in source.path_assertions}
    relation_refs = projection.role_disclosure.visible_relation_assertion_refs
    path_refs = projection.role_disclosure.visible_path_assertion_refs
    if not set(relation_refs).issubset(relation_by_id):
        raise ValueError("lab_study_disclosed_relation_missing_from_source")
    if not set(path_refs).issubset(path_by_id):
        raise ValueError("lab_study_disclosed_path_missing_from_source")
    relation_assertions = [relation_by_id[item] for item in relation_refs]
    path_assertions = [path_by_id[item] for item in path_refs]
    issued_at = now or datetime.now(timezone.utc)
    return MingliLabStudy(
        study_id=study_id,
        session=session,
        scene_identity=identity,
        disclosure_hash=projection.role_disclosure.disclosure_hash,
        relation_scene_ref=canonical_scene_scope_ref(
            life_case_id=source.life_case_id,
            chart_version_id=source.chart_version_id,
        ),
        disclosed_relation_assertion_refs=list(relation_refs),
        disclosed_path_assertion_refs=list(path_refs),
        node_refs=_nodes_from_assertions(
            relation_assertions=relation_assertions,
            path_assertions=path_assertions,
        ),
        formal_relation_assertions=relation_assertions,
        formal_path_assertions=path_assertions,
        provenance_records=_provenance_from_assertions(
            relation_assertions=relation_assertions,
            path_assertions=path_assertions,
        ),
        created_at=issued_at,
        updated_at=issued_at,
    )


def append_lab_candidate_revision(
    study: MingliLabStudy,
    *,
    revision: LabCandidateRevision,
) -> MingliLabStudy:
    expected_revision = len(study.candidate_revisions) + 1
    if revision.revision != expected_revision:
        raise ValueError("lab_candidate_revision_sequence_mismatch")
    if study.candidate_revisions:
        if revision.supersedes_revision_id != study.candidate_revisions[-1].revision_id:
            raise ValueError("lab_candidate_revision_predecessor_mismatch")
    if any(
        scene_ref != study.relation_scene_ref
        for scene_ref in _assertion_scene_refs(
            relation_assertions=revision.relation_assertions,
            path_assertions=revision.path_assertions,
        )
    ):
        raise ValueError("lab_candidate_revision_scene_mismatch")
    existing_ids = {
        *(item.assertion_id for item in study.formal_relation_assertions),
        *(item.assertion_id for item in study.formal_path_assertions),
        *(
            item.assertion_id
            for existing in study.candidate_revisions
            for item in [*existing.relation_assertions, *existing.path_assertions]
        ),
    }
    if any(
        item.assertion_id in existing_ids
        for item in [*revision.relation_assertions, *revision.path_assertions]
    ):
        raise ValueError("lab_candidate_assertion_already_present")
    return _replace_study(study, {
        "candidate_revisions": [*study.candidate_revisions, revision],
        "updated_at": revision.created_at,
    })


def record_lab_path_comparison(
    study: MingliLabStudy,
    *,
    comparison: LabPathComparison,
) -> MingliLabStudy:
    if any(
        item.comparison_id == comparison.comparison_id
        for item in study.path_comparisons
    ):
        raise ValueError("lab_path_comparison_already_present")
    return _replace_study(study, {
        "path_comparisons": [*study.path_comparisons, comparison],
        "updated_at": comparison.created_at,
    })


def update_lab_evidence(
    study: MingliLabStudy,
    *,
    evidence: LabEvidenceSet,
    now: datetime | None = None,
) -> MingliLabStudy:
    return _replace_study(study, {
        "evidence": evidence,
        "updated_at": now or datetime.now(timezone.utc),
    })


def build_lab_promotion_proposal(
    study: MingliLabStudy,
    *,
    candidate_revision_id: str,
) -> LabPromotionProposal:
    if not any(
        item.revision_id == candidate_revision_id
        for item in study.candidate_revisions
    ):
        raise ValueError("lab_promotion_candidate_revision_not_found")
    evidence = study.evidence
    requirements = {
        "positive_fixture": bool(evidence.positive_fixture_refs),
        "negative_fixture": bool(evidence.negative_fixture_refs),
        "boundary_fixture": bool(evidence.boundary_fixture_refs),
        "synthetic_case": bool(evidence.synthetic_case_refs),
        "counterexample": bool(evidence.counterexample_refs),
        "counterexamples_resolved": (
            bool(evidence.counterexample_refs)
            and set(evidence.counterexample_refs)
            == set(evidence.resolved_counterexample_refs)
        ),
        "regression": bool(evidence.regression_refs),
    }
    missing = [name for name, present in requirements.items() if not present]
    evidence_refs = list(dict.fromkeys([
        *evidence.positive_fixture_refs,
        *evidence.negative_fixture_refs,
        *evidence.boundary_fixture_refs,
        *evidence.synthetic_case_refs,
        *evidence.counterexample_refs,
        *evidence.resolved_counterexample_refs,
        *evidence.regression_refs,
    ]))
    proposal_basis = {
        "study_id": study.study_id,
        "candidate_revision_id": candidate_revision_id,
        "evidence_refs": evidence_refs,
        "missing_requirements": missing,
    }
    return LabPromotionProposal(
        proposal_id=f"lab-proposal-{canonical_hash(proposal_basis)[:24]}",
        study_id=study.study_id,
        candidate_revision_id=candidate_revision_id,
        status="blocked" if missing else "ready_for_risk_gate",
        evidence_refs=evidence_refs,
        missing_requirements=missing,
    )


def update_lab_session(
    session: MingliLabSession,
    *,
    status: LabSessionStatus,
    now: datetime | None = None,
) -> MingliLabSession:
    return session.model_copy(update={
        "revision": session.revision + 1,
        "status": status,
        "updated_at": now or datetime.now(timezone.utc),
    })


def exploration_from_lab_session(
    *,
    session: MingliLabSession,
    topic_id: str,
    selected_node_ids: list[str],
    result_refs: list[str],
    observations: list[str],
    open_question: str = "",
    restored_original: bool,
) -> TopicExploration:
    if session.status not in {"restored", "saved"} or not restored_original:
        raise ValueError("lab_exploration_requires_restored_formal_scene")
    return TopicExploration(
        exploration_id=f"exploration:{session.session_id}:{session.revision}",
        participant_run_id=session.participant_run_id,
        topic_id=topic_id,
        experiment_kind=session.experiment_kind,
        lab_session_id=session.session_id,
        scene_id=session.scene_id,
        scene_source_hash=session.scene_source_hash,
        disclosure_hash=session.disclosure_hash,
        base_snapshot_ref=session.base_snapshot_ref,
        base_snapshot_hash=_snapshot_hash(session.base_snapshot_ref),
        selected_node_ids=selected_node_ids,
        sandbox_result_refs=result_refs,
        observations=observations,
        open_question=open_question,
        restored_original=True,
        capability_trace=["visual_only", "deterministic_structure", "reasoning_required"],
        case_local_only=True,
        created_at=session.updated_at,
    )


def _snapshot_hash(value: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) == 64 and all(character in "0123456789abcdef" for character in normalized):
        return normalized
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _nodes_from_assertions(
    *,
    relation_assertions: list[RelationAssertion],
    path_assertions: list[PathAssertion],
) -> list[NodeRef]:
    nodes: dict[str, NodeRef] = {}
    for assertion in relation_assertions:
        for node in assertion.relation_key.participant_refs:
            nodes[node.node_ref] = node
    for assertion in path_assertions:
        if assertion.path_key is None:
            continue
        for node in assertion.path_key.node_refs:
            nodes[node.node_ref] = node
        for relation in assertion.path_key.relation_keys:
            for node in relation.participant_refs:
                nodes[node.node_ref] = node
    return [nodes[key] for key in sorted(nodes)]


def _provenance_from_assertions(
    *,
    relation_assertions: list[RelationAssertion],
    path_assertions: list[PathAssertion],
) -> list[ProvenanceRecord]:
    records = {
        item.provenance.provenance_id: item.provenance
        for item in [*relation_assertions, *path_assertions]
    }
    return [records[key] for key in sorted(records)]


def _assertion_scene_refs(
    *,
    relation_assertions: list[RelationAssertion],
    path_assertions: list[PathAssertion],
) -> list[str]:
    refs = [item.relation_key.scene_ref for item in relation_assertions]
    refs.extend(
        item.path_key.scene_ref
        for item in path_assertions
        if item.path_key is not None
    )
    return refs


def _replace_study(
    study: MingliLabStudy,
    updates: dict[str, object],
) -> MingliLabStudy:
    payload = study.model_dump(mode="python")
    payload.update(updates)
    return MingliLabStudy.model_validate(payload)
