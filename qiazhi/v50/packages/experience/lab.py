from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Literal

from pydantic import Field, model_validator

from experience.canonical_scene import CanonicalProjectionEnvelope
from experience.contracts import ExperienceModel, TopicExploration


LabExperimentKind = Literal["mechanism_ablation", "temporal_hypothesis"]
LabSessionStatus = Literal["active", "modified", "restored", "saved", "discarded"]


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
        return self


def issue_lab_session(
    *,
    projection: CanonicalProjectionEnvelope,
    session_id: str,
    participant_run_id: str,
    experiment_kind: LabExperimentKind,
    base_snapshot_ref: str,
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
        source_mode="canonical_projection",
        created_at=issued_at,
        updated_at=issued_at,
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
