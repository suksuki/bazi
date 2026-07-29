from __future__ import annotations

import pytest
from abu_v60.db.engine import engine
from abu_v60.dream.return_slice import return_episode_contract
from abu_v60.dream.seed import first_slice_world_event_definitions
from abu_v60.provenance import content_hash
from abu_v60.world import (
    WorldContinuityEngine,
    WorldContinuityError,
    WorldEventAdmissionCompiler,
    WorldEventAdmissionError,
    WorldEventAdmissionService,
    WorldEventAuthoritySnapshot,
    WorldEventDefinition,
    validate_persisted_world_event_admission,
)
from pydantic import ValidationError
from sqlalchemy import text


def _authority() -> WorldEventAuthoritySnapshot:
    return WorldEventAuthoritySnapshot(
        actor_case_ref="case:test",
        actor_kind="CANONICAL_SYNTHETIC",
        actor_branch="canonical_world",
    )


def test_world_event_admission_is_deterministic_and_binds_authority() -> None:
    definition = first_slice_world_event_definitions()[1]
    compiler = WorldEventAdmissionCompiler()

    first = compiler.compile(definition=definition, authority=_authority())
    replay = compiler.compile(definition=definition, authority=_authority())

    assert first == replay
    assert first.admission_manifest.actor_case_ref == "case:test"
    assert first.admission_manifest.event_payload_hash == content_hash(definition.event_payload)
    assert first.admission_manifest.outcome_hash == content_hash(definition.sealed_outcome)
    assert tuple(
        item.evidence_ref for item in first.admission_manifest.initial_evidence
    ) == tuple(
        sorted(item.evidence_ref for item in definition.initial_evidence)
    )


def test_scheduled_event_rejects_answer_owned_outcome() -> None:
    definition = first_slice_world_event_definitions()[1]
    payload = definition.model_dump(mode="json")
    payload["event_payload"]["answer_can_affect_outcome"] = True

    with pytest.raises(
        ValidationError,
        match="scheduled_world_event_requires_system_outcome_owner",
    ):
        WorldEventDefinition.model_validate(payload)


def test_world_event_admission_replay_is_idempotent_and_conflict_is_rejected() -> None:
    definition = first_slice_world_event_definitions()[1]
    service = WorldEventAdmissionService()

    with engine.begin() as connection:
        admitted = service.admit(connection, definition=definition)
        assert admitted.definition.world_event_ref == definition.world_event_ref

        changed = definition.model_copy(
            update={
                "event_payload": {
                    **definition.event_payload,
                    "summary": f"{definition.event_payload['summary']}（漂移）",
                }
            }
        )
        with pytest.raises(WorldEventAdmissionError, match="admission_conflict"):
            service.admit(connection, definition=changed)


def test_persisted_world_event_manifest_rejects_payload_drift() -> None:
    definition = first_slice_world_event_definitions()[1]
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(
                text(
                    """
                    UPDATE world.events
                    SET event_json = jsonb_set(
                        event_json,
                        '{summary}',
                        '"被篡改的世界事件"'::jsonb
                    )
                    WHERE world_event_ref = :event_ref
                    """
                ),
                {"event_ref": definition.world_event_ref},
            )
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
                    {"event_ref": definition.world_event_ref},
                )
                .mappings()
                .one()
            )
            with pytest.raises(
                WorldEventAdmissionError,
                match="event_payload_hash_binding_mismatch",
            ):
                validate_persisted_world_event_admission(dict(row))
            with pytest.raises(WorldContinuityError, match="admission_invalid"):
                WorldContinuityEngine().advance_and_settle(
                    connection=connection,
                    event_ref=definition.world_event_ref,
                )
        finally:
            transaction.rollback()


def test_world_event_admission_rejects_initial_evidence_drift() -> None:
    definition = first_slice_world_event_definitions()[0]
    assert definition.initial_evidence

    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(
                text(
                    """
                    UPDATE world.event_evidence
                    SET evidence_hash = :tampered_hash
                    WHERE evidence_ref = :evidence_ref
                    """
                ),
                {
                    "evidence_ref": definition.initial_evidence[0].evidence_ref,
                    "tampered_hash": "0" * 64,
                },
            )
            with pytest.raises(
                WorldEventAdmissionError,
                match="admission_conflict",
            ):
                WorldEventAdmissionService().admit(
                    connection,
                    definition=definition,
                )
            with pytest.raises(WorldContinuityError, match="admission_invalid"):
                WorldContinuityEngine().advance_and_settle(
                    connection=connection,
                    event_ref=definition.world_event_ref,
                )
        finally:
            transaction.rollback()


def test_historical_event_replay_does_not_advance_actor_version() -> None:
    episode = return_episode_contract()
    entry = episode.entry_world_event
    assert entry is not None

    with engine.begin() as connection:
        before = int(
            connection.execute(
                text(
                    """
                    SELECT actor_version
                    FROM world.actors
                    WHERE actor_ref = :actor_ref
                    """
                ),
                {"actor_ref": episode.actor_ref},
            ).scalar_one()
        )
        service = WorldContinuityEngine()
        for _ in range(2):
            service.commit_historical_event(
                connection=connection,
                event_ref=entry.event_ref,
                actor_ref=episode.actor_ref,
                event_type=entry.event_type,
                summary=entry.summary,
                caused_by_event_ref=entry.caused_by_event_ref,
                evidence=entry.evidence,
                actor_state_delta=entry.actor_state_delta,
            )
        after = int(
            connection.execute(
                text(
                    """
                    SELECT actor_version
                    FROM world.actors
                    WHERE actor_ref = :actor_ref
                    """
                ),
                {"actor_ref": episode.actor_ref},
            ).scalar_one()
        )
        assert after == before
