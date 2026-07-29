from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import text

from abu_v60.provenance import canonical_json, content_hash
from abu_v60.world.contracts import WorldEventStatus


class WorldEventAdmissionError(ValueError):
    pass


class WorldEventEvidenceDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    evidence_ref: str = Field(min_length=1)
    committed_at_tick: int = Field(ge=0)
    payload: dict[str, Any]

    @model_validator(mode="after")
    def payload_identity_matches(self) -> WorldEventEvidenceDefinition:
        if self.payload.get("evidence_ref") != self.evidence_ref:
            raise ValueError("world_event_evidence_identity_mismatch")
        observed_at_tick = self.payload.get("observed_at_tick")
        if observed_at_tick is not None and int(observed_at_tick) > self.committed_at_tick:
            raise ValueError("world_event_evidence_observed_after_commit")
        return self


class WorldEventDefinition(BaseModel):
    """Immutable authoring input for a committed or scheduled WorldEvent."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    world_event_ref: str = Field(min_length=1)
    world_ref: str = Field(min_length=1)
    actor_ref: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    due_tick: int = Field(ge=0)
    initial_status: Literal[
        WorldEventStatus.SCHEDULED,
        WorldEventStatus.SETTLED,
    ]
    event_payload: dict[str, Any]
    sealed_outcome: dict[str, Any]
    initial_evidence: tuple[WorldEventEvidenceDefinition, ...] = ()
    settled_at_tick: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def event_contract_is_complete(self) -> WorldEventDefinition:
        if not str(self.event_payload.get("summary", "")).strip():
            raise ValueError("world_event_summary_required")
        evidence_refs = [item.evidence_ref for item in self.initial_evidence]
        if len(evidence_refs) != len(set(evidence_refs)):
            raise ValueError("world_event_initial_evidence_refs_must_be_unique")

        if self.initial_status is WorldEventStatus.SCHEDULED:
            if self.settled_at_tick is not None or self.initial_evidence:
                raise ValueError("scheduled_world_event_cannot_start_settled")
            if (
                self.event_payload.get("resolution_owner") != "V60_WORLD_ENGINE"
                or self.event_payload.get("answer_can_affect_outcome") is not False
            ):
                raise ValueError("scheduled_world_event_requires_system_outcome_owner")
            outcome_evidence = self.sealed_outcome.get("evidence")
            if (
                not str(self.sealed_outcome.get("actual_event", "")).strip()
                or not isinstance(outcome_evidence, list)
                or not outcome_evidence
            ):
                raise ValueError("scheduled_world_event_requires_sealed_outcome")
        else:
            if self.settled_at_tick != self.due_tick:
                raise ValueError("historical_world_event_tick_mismatch")
            if self.sealed_outcome:
                raise ValueError("historical_world_event_cannot_claim_future_outcome")
        return self


class WorldEventAuthoritySnapshot(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    actor_case_ref: str = Field(min_length=1)
    actor_kind: str = Field(min_length=1)
    actor_branch: str = Field(min_length=1)


class WorldEventEvidenceBinding(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    evidence_ref: str = Field(min_length=1)
    committed_at_tick: int = Field(ge=0)
    evidence_hash: str = Field(min_length=64, max_length=64)


class WorldEventAdmissionManifest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    admission_version: Literal["v60.world-event-admission.001"]
    world_event_ref: str = Field(min_length=1)
    world_ref: str = Field(min_length=1)
    actor_ref: str = Field(min_length=1)
    actor_case_ref: str = Field(min_length=1)
    actor_kind: str = Field(min_length=1)
    actor_branch: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    due_tick: int = Field(ge=0)
    initial_status: Literal[
        WorldEventStatus.SCHEDULED,
        WorldEventStatus.SETTLED,
    ]
    event_payload_hash: str = Field(min_length=64, max_length=64)
    outcome_hash: str = Field(min_length=64, max_length=64)
    initial_evidence: tuple[WorldEventEvidenceBinding, ...]
    definition_hash: str = Field(min_length=64, max_length=64)

    @model_validator(mode="after")
    def initial_evidence_is_unique(self) -> WorldEventAdmissionManifest:
        refs = [item.evidence_ref for item in self.initial_evidence]
        if refs != sorted(refs) or len(refs) != len(set(refs)):
            raise ValueError("world_event_manifest_evidence_must_be_sorted_unique")
        return self


class CompiledWorldEventAdmission(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    definition: WorldEventDefinition
    authority: WorldEventAuthoritySnapshot
    event_payload_hash: str = Field(min_length=64, max_length=64)
    outcome_hash: str = Field(min_length=64, max_length=64)
    definition_hash: str = Field(min_length=64, max_length=64)
    admission_manifest: WorldEventAdmissionManifest
    admission_manifest_hash: str = Field(min_length=64, max_length=64)

    @model_validator(mode="after")
    def hashes_match_payloads(self) -> CompiledWorldEventAdmission:
        if content_hash(self.definition.event_payload) != self.event_payload_hash:
            raise ValueError("world_event_payload_hash_mismatch")
        if content_hash(self.definition.sealed_outcome) != self.outcome_hash:
            raise ValueError("world_event_outcome_hash_mismatch")
        if content_hash(self.admission_manifest.model_dump(mode="json")) != (
            self.admission_manifest_hash
        ):
            raise ValueError("world_event_admission_manifest_hash_mismatch")
        return self


def _definition_payload(
    *,
    definition: WorldEventDefinition,
    authority: WorldEventAuthoritySnapshot,
) -> dict[str, Any]:
    return {
        "world_event_ref": definition.world_event_ref,
        "world_ref": definition.world_ref,
        "actor_ref": definition.actor_ref,
        "actor_case_ref": authority.actor_case_ref,
        "event_type": definition.event_type,
        "due_tick": definition.due_tick,
        "initial_status": definition.initial_status,
        "event_payload": definition.event_payload,
        "sealed_outcome": definition.sealed_outcome,
        "initial_evidence": [
            {
                "evidence_ref": item.evidence_ref,
                "committed_at_tick": item.committed_at_tick,
                "evidence_hash": content_hash(item.payload),
            }
            for item in sorted(
                definition.initial_evidence,
                key=lambda candidate: candidate.evidence_ref,
            )
        ],
    }


class WorldEventAdmissionCompiler:
    def compile(
        self,
        *,
        definition: WorldEventDefinition,
        authority: WorldEventAuthoritySnapshot,
    ) -> CompiledWorldEventAdmission:
        definition = WorldEventDefinition.model_validate(definition.model_dump(mode="json"))
        event_payload_hash = content_hash(definition.event_payload)
        outcome_hash = content_hash(definition.sealed_outcome)
        definition_hash = content_hash(
            _definition_payload(definition=definition, authority=authority)
        )
        initial_evidence = tuple(
            WorldEventEvidenceBinding(
                evidence_ref=item.evidence_ref,
                committed_at_tick=item.committed_at_tick,
                evidence_hash=content_hash(item.payload),
            )
            for item in sorted(
                definition.initial_evidence,
                key=lambda candidate: candidate.evidence_ref,
            )
        )
        manifest = WorldEventAdmissionManifest(
            admission_version="v60.world-event-admission.001",
            world_event_ref=definition.world_event_ref,
            world_ref=definition.world_ref,
            actor_ref=definition.actor_ref,
            actor_case_ref=authority.actor_case_ref,
            actor_kind=authority.actor_kind,
            actor_branch=authority.actor_branch,
            event_type=definition.event_type,
            due_tick=definition.due_tick,
            initial_status=definition.initial_status,
            event_payload_hash=event_payload_hash,
            outcome_hash=outcome_hash,
            initial_evidence=initial_evidence,
            definition_hash=definition_hash,
        )
        return CompiledWorldEventAdmission(
            definition=definition,
            authority=authority,
            event_payload_hash=event_payload_hash,
            outcome_hash=outcome_hash,
            definition_hash=definition_hash,
            admission_manifest=manifest,
            admission_manifest_hash=content_hash(manifest.model_dump(mode="json")),
        )


def validate_persisted_world_event_admission(
    persisted: dict[str, Any],
) -> WorldEventAdmissionManifest:
    try:
        manifest = WorldEventAdmissionManifest.model_validate(persisted["admission_manifest_json"])
    except (KeyError, ValueError) as exc:
        raise WorldEventAdmissionError("world_event_admission_manifest_invalid") from exc
    if content_hash(manifest.model_dump(mode="json")) != persisted.get("admission_manifest_hash"):
        raise WorldEventAdmissionError("world_event_admission_manifest_hash_mismatch")
    expected = {
        "world_event_ref": persisted["world_event_ref"],
        "world_ref": persisted["world_ref"],
        "actor_ref": persisted["actor_ref"],
        "actor_case_ref": persisted["actor_case_ref"],
        "actor_kind": persisted["actor_kind"],
        "actor_branch": persisted["actor_branch"],
        "event_type": persisted["event_type"],
        "due_tick": int(persisted["due_tick"]),
        "event_payload_hash": content_hash(persisted["event_json"]),
        "outcome_hash": persisted["outcome_hash"],
        "definition_hash": persisted["definition_hash"],
    }
    for field_name, expected_value in expected.items():
        if getattr(manifest, field_name) != expected_value:
            raise WorldEventAdmissionError(f"world_event_admission_{field_name}_binding_mismatch")
    if content_hash(persisted["sealed_outcome_json"]) != manifest.outcome_hash:
        raise WorldEventAdmissionError("world_event_admission_outcome_hash_mismatch")
    definition_payload = {
        "world_event_ref": persisted["world_event_ref"],
        "world_ref": persisted["world_ref"],
        "actor_ref": persisted["actor_ref"],
        "actor_case_ref": persisted["actor_case_ref"],
        "event_type": persisted["event_type"],
        "due_tick": int(persisted["due_tick"]),
        "initial_status": manifest.initial_status,
        "event_payload": persisted["event_json"],
        "sealed_outcome": persisted["sealed_outcome_json"],
        "initial_evidence": [item.model_dump(mode="json") for item in manifest.initial_evidence],
    }
    if content_hash(definition_payload) != manifest.definition_hash:
        raise WorldEventAdmissionError("world_event_admission_definition_hash_mismatch")
    return manifest


def validate_persisted_world_event_evidence(
    connection: Any,
    *,
    manifest: WorldEventAdmissionManifest,
) -> None:
    for expected in manifest.initial_evidence:
        row = (
            connection.execute(
                text(
                    """
                    SELECT world_event_ref, committed_at_tick, evidence_hash
                    FROM world.event_evidence
                    WHERE evidence_ref = :evidence_ref
                    """
                ),
                {"evidence_ref": expected.evidence_ref},
            )
            .mappings()
            .one_or_none()
        )
        if (
            row is None
            or row["world_event_ref"] != manifest.world_event_ref
            or int(row["committed_at_tick"]) != expected.committed_at_tick
            or row["evidence_hash"] != expected.evidence_hash
        ):
            raise WorldEventAdmissionError("world_event_initial_evidence_binding_mismatch")


class WorldEventAdmissionService:
    """The World schema's idempotent admission path for authored events."""

    def __init__(self, compiler: WorldEventAdmissionCompiler | None = None) -> None:
        self._compiler = compiler or WorldEventAdmissionCompiler()

    def admit(
        self,
        connection: Any,
        *,
        definition: WorldEventDefinition,
    ) -> CompiledWorldEventAdmission:
        authority = self._authority_snapshot(connection, definition=definition)
        admission = self._compiler.compile(
            definition=definition,
            authority=authority,
        )
        parameters = self._sql_parameters(admission)
        connection.execute(
            text(
                """
                INSERT INTO world.events
                    (world_event_ref, world_ref, actor_ref, event_type, due_tick,
                     status, event_json, sealed_outcome_json, outcome_hash,
                     settled_at_tick, settlement_hash, definition_hash,
                     admission_manifest_json, admission_manifest_hash)
                VALUES
                    (:event_ref, :world_ref, :actor_ref, :event_type, :due_tick,
                     :status, CAST(:event_json AS jsonb),
                     CAST(:outcome_json AS jsonb), :outcome_hash,
                     :settled_at_tick, :settlement_hash, :definition_hash,
                     CAST(:manifest_json AS jsonb), :manifest_hash)
                ON CONFLICT (world_event_ref) DO NOTHING
                """
            ),
            parameters,
        )
        for evidence in definition.initial_evidence:
            connection.execute(
                text(
                    """
                    INSERT INTO world.event_evidence
                        (evidence_ref, world_event_ref, committed_at_tick,
                         evidence_json, evidence_hash)
                    VALUES
                        (:evidence_ref, :event_ref, :tick,
                         CAST(:evidence_json AS jsonb), :evidence_hash)
                    ON CONFLICT (evidence_ref) DO NOTHING
                    """
                ),
                {
                    "evidence_ref": evidence.evidence_ref,
                    "event_ref": definition.world_event_ref,
                    "tick": evidence.committed_at_tick,
                    "evidence_json": canonical_json(evidence.payload),
                    "evidence_hash": content_hash(evidence.payload),
                },
            )
        self._verify_persisted(connection, admission=admission)
        return admission

    @staticmethod
    def _authority_snapshot(
        connection: Any,
        *,
        definition: WorldEventDefinition,
    ) -> WorldEventAuthoritySnapshot:
        row = (
            connection.execute(
                text(
                    """
                    SELECT actor.case_ref, actor.actor_kind, actor.branch
                    FROM world.actors AS actor
                    JOIN world.worlds AS world
                      ON world.world_ref = actor.world_ref
                    WHERE actor.actor_ref = :actor_ref
                      AND actor.world_ref = :world_ref
                    """
                ),
                {
                    "actor_ref": definition.actor_ref,
                    "world_ref": definition.world_ref,
                },
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise WorldEventAdmissionError("world_event_admission_authority_missing")
        return WorldEventAuthoritySnapshot(
            actor_case_ref=row["case_ref"],
            actor_kind=row["actor_kind"],
            actor_branch=row["branch"],
        )

    @staticmethod
    def _sql_parameters(
        admission: CompiledWorldEventAdmission,
    ) -> dict[str, Any]:
        definition = admission.definition
        settlement_hash = None
        if definition.initial_status is WorldEventStatus.SETTLED:
            settlement_hash = content_hash(
                {
                    "world_event_ref": definition.world_event_ref,
                    "settled_at_tick": definition.settled_at_tick,
                }
            )
        return {
            "event_ref": definition.world_event_ref,
            "world_ref": definition.world_ref,
            "actor_ref": definition.actor_ref,
            "event_type": definition.event_type,
            "due_tick": definition.due_tick,
            "status": definition.initial_status,
            "event_json": canonical_json(definition.event_payload),
            "outcome_json": canonical_json(definition.sealed_outcome),
            "outcome_hash": admission.outcome_hash,
            "settled_at_tick": definition.settled_at_tick,
            "settlement_hash": settlement_hash,
            "definition_hash": admission.definition_hash,
            "manifest_json": canonical_json(admission.admission_manifest.model_dump(mode="json")),
            "manifest_hash": admission.admission_manifest_hash,
        }

    @staticmethod
    def _verify_persisted(
        connection: Any,
        *,
        admission: CompiledWorldEventAdmission,
    ) -> None:
        row = (
            connection.execute(
                text(
                    """
                    SELECT event.*, actor.case_ref AS actor_case_ref,
                           actor.actor_kind, actor.branch AS actor_branch
                    FROM world.events AS event
                    JOIN world.actors AS actor
                      ON actor.actor_ref = event.actor_ref
                    WHERE event.world_event_ref = :event_ref
                    """
                ),
                {"event_ref": admission.definition.world_event_ref},
            )
            .mappings()
            .one()
        )
        try:
            manifest = validate_persisted_world_event_admission(dict(row))
            validate_persisted_world_event_evidence(
                connection,
                manifest=manifest,
            )
        except WorldEventAdmissionError as exc:
            raise WorldEventAdmissionError("world_event_admission_conflict") from exc
        if (
            manifest.definition_hash != admission.definition_hash
            or row["admission_manifest_hash"] != admission.admission_manifest_hash
        ):
            raise WorldEventAdmissionError("world_event_admission_conflict")
