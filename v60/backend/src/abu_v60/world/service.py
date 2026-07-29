from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import text

from abu_v60.decision import (
    CognitiveDecisionLedger,
    DecisionAuthority,
    DecisionKind,
    DecisionRequest,
    DecisionRouteStatus,
)
from abu_v60.provenance import canonical_json, content_hash, stable_ref
from abu_v60.system_manifest import PRIMARY_WORLD_ID
from abu_v60.world.admission import (
    WorldEventAdmissionError,
    WorldEventAdmissionService,
    WorldEventDefinition,
    WorldEventEvidenceDefinition,
    validate_persisted_world_event_admission,
    validate_persisted_world_event_evidence,
)
from abu_v60.world.contracts import WorldClock, WorldClockEpoch, WorldEventStatus


class WorldContinuityError(ValueError):
    pass


@dataclass(frozen=True)
class WorldSettlement:
    world_event_ref: str
    settled_at_tick: int
    settlement_hash: str
    already_settled: bool
    decision_id: str | None = None


@dataclass(frozen=True)
class WorldPulse:
    world_ref: str
    previous_tick: int
    current_tick: int
    epoch: int
    settled_event_refs: tuple[str, ...]


class WorldContinuityEngine:
    """Single write owner for clock, world event settlement and actor continuity."""

    def __init__(self, decisions: CognitiveDecisionLedger | None = None) -> None:
        self._decisions = decisions or CognitiveDecisionLedger()

    def current_tick(self, connection: Any, *, world_ref: str = PRIMARY_WORLD_ID) -> int:
        return int(
            connection.execute(
                text("SELECT current_tick FROM world.worlds WHERE world_ref = :world_ref"),
                {"world_ref": world_ref},
            ).scalar_one()
        )

    def pulse(
        self,
        *,
        connection: Any,
        world_ref: str = PRIMARY_WORLD_ID,
        observed_at: datetime | None = None,
    ) -> WorldPulse:
        previous_tick = self.current_tick(connection, world_ref=world_ref)
        clock = self.advance_clock(
            connection=connection,
            world_ref=world_ref,
            observed_at=observed_at,
        )
        settlements = self.settle_due_events(
            connection=connection,
            world_ref=world_ref,
        )
        return WorldPulse(
            world_ref=world_ref,
            previous_tick=previous_tick,
            current_tick=clock.tick,
            epoch=clock.epoch,
            settled_event_refs=tuple(item.world_event_ref for item in settlements),
        )

    def advance_clock(
        self,
        *,
        connection: Any,
        world_ref: str = PRIMARY_WORLD_ID,
        observed_at: datetime | None = None,
    ) -> WorldClock:
        authoritative_observed_at = (
            observed_at or connection.execute(text("SELECT clock_timestamp()")).scalar_one()
        )
        row = (
            connection.execute(
                text(
                    """
                SELECT w.current_epoch, w.current_tick,
                       e.start_tick, e.rate_numerator, e.rate_denominator,
                       e.created_at AS anchored_at
                FROM world.worlds AS w
                JOIN world.clock_epochs AS e
                  ON e.world_ref = w.world_ref
                 AND e.epoch = w.current_epoch
                WHERE w.world_ref = :world_ref
                FOR UPDATE OF w
                """
                ),
                {
                    "world_ref": world_ref,
                },
            )
            .mappings()
            .one()
        )
        epoch = WorldClockEpoch(
            world_ref=world_ref,
            epoch=int(row["current_epoch"]),
            start_tick=int(row["start_tick"]),
            rate_numerator=int(row["rate_numerator"]),
            rate_denominator=int(row["rate_denominator"]),
            anchored_at=row["anchored_at"],
        )
        projected_tick = epoch.project_tick(authoritative_observed_at)
        current_tick = max(int(row["current_tick"]), projected_tick)
        if current_tick != int(row["current_tick"]):
            connection.execute(
                text(
                    """
                    UPDATE world.worlds
                    SET current_tick = :current_tick,
                        updated_at = now()
                    WHERE world_ref = :world_ref
                    """
                ),
                {
                    "world_ref": world_ref,
                    "current_tick": current_tick,
                },
            )
        return WorldClock(
            world_ref=world_ref,
            epoch=epoch.epoch,
            tick=current_tick,
            rate_numerator=epoch.rate_numerator,
            rate_denominator=epoch.rate_denominator,
        )

    def settle_due_events(
        self,
        *,
        connection: Any,
        world_ref: str = PRIMARY_WORLD_ID,
        limit: int = 64,
    ) -> tuple[WorldSettlement, ...]:
        if limit < 1:
            raise WorldContinuityError("world_settlement_limit_must_be_positive")
        current_tick = self.current_tick(connection, world_ref=world_ref)
        event_refs = (
            connection.execute(
                text(
                    """
                SELECT world_event_ref
                FROM world.events
                WHERE world_ref = :world_ref
                  AND status = 'SCHEDULED'
                  AND due_tick <= :current_tick
                ORDER BY due_tick, world_event_ref
                LIMIT :limit
                FOR UPDATE SKIP LOCKED
                """
                ),
                {
                    "world_ref": world_ref,
                    "current_tick": current_tick,
                    "limit": limit,
                },
            )
            .scalars()
            .all()
        )
        settlements: list[WorldSettlement] = []
        for event_ref in event_refs:
            event = self._locked_event(connection=connection, event_ref=str(event_ref))
            settlements.append(
                self._settle_locked_event(
                    connection=connection,
                    event=event,
                    current_tick=current_tick,
                )
            )
        return tuple(settlements)

    def advance_and_settle(
        self,
        *,
        connection: Any,
        event_ref: str,
        world_ref: str = PRIMARY_WORLD_ID,
    ) -> WorldSettlement:
        event = self._locked_event(connection=connection, event_ref=event_ref)
        if event["status"] == "SETTLED":
            return WorldSettlement(
                world_event_ref=event_ref,
                settled_at_tick=int(event["settled_at_tick"]),
                settlement_hash=str(event["settlement_hash"]),
                already_settled=True,
            )
        if event["status"] != "SCHEDULED":
            raise WorldContinuityError("world_event_not_settleable")

        world = (
            connection.execute(
                text(
                    """
                SELECT w.current_epoch, w.current_tick,
                       e.rate_numerator, e.rate_denominator
                FROM world.worlds AS w
                JOIN world.clock_epochs AS e
                  ON e.world_ref = w.world_ref
                 AND e.epoch = w.current_epoch
                WHERE w.world_ref = :world_ref
                FOR UPDATE
                """
                ),
                {"world_ref": world_ref},
            )
            .mappings()
            .one()
        )
        due_tick = int(event["due_tick"])
        if int(world["current_tick"]) < due_tick:
            next_epoch = int(world["current_epoch"]) + 1
            connection.execute(
                text(
                    """
                    INSERT INTO world.clock_epochs
                        (world_ref, epoch, start_tick, rate_numerator, rate_denominator)
                    VALUES
                        (:world_ref, :epoch, :start_tick,
                         :rate_numerator, :rate_denominator)
                    """
                ),
                {
                    "world_ref": world_ref,
                    "epoch": next_epoch,
                    "start_tick": due_tick,
                    "rate_numerator": world["rate_numerator"],
                    "rate_denominator": world["rate_denominator"],
                },
            )
            connection.execute(
                text(
                    """
                    UPDATE world.worlds
                    SET current_epoch = :epoch,
                        current_tick = :tick,
                        updated_at = now()
                    WHERE world_ref = :world_ref
                    """
                ),
                {
                    "epoch": next_epoch,
                    "tick": due_tick,
                    "world_ref": world_ref,
                },
            )
        return self._settle_locked_event(
            connection=connection,
            event=event,
            current_tick=due_tick,
        )

    @staticmethod
    def _locked_event(*, connection: Any, event_ref: str) -> dict[str, Any]:
        event = dict(
            connection.execute(
                text(
                    """
                    SELECT event.*, actor.case_ref AS actor_case_ref,
                           actor.actor_kind, actor.branch AS actor_branch
                    FROM world.events AS event
                    JOIN world.actors AS actor
                      ON actor.actor_ref = event.actor_ref
                    WHERE event.world_event_ref = :event_ref
                    FOR UPDATE OF event
                    """
                ),
                {"event_ref": event_ref},
            )
            .mappings()
            .one()
        )
        try:
            manifest = validate_persisted_world_event_admission(event)
            validate_persisted_world_event_evidence(
                connection,
                manifest=manifest,
            )
        except WorldEventAdmissionError as exc:
            raise WorldContinuityError("world_event_admission_invalid") from exc
        return event

    def _settle_locked_event(
        self,
        *,
        connection: Any,
        event: Mapping[str, Any],
        current_tick: int,
    ) -> WorldSettlement:
        event_ref = str(event["world_event_ref"])
        if event["status"] == "SETTLED":
            return WorldSettlement(
                world_event_ref=event_ref,
                settled_at_tick=int(event["settled_at_tick"]),
                settlement_hash=str(event["settlement_hash"]),
                already_settled=True,
            )
        if event["status"] != "SCHEDULED":
            raise WorldContinuityError("world_event_not_settleable")
        due_tick = int(event["due_tick"])
        if current_tick < due_tick:
            raise WorldContinuityError("world_event_not_due")

        outcome = dict(event["sealed_outcome_json"])
        decision = self._decisions.route_and_record(
            connection=connection,
            request=DecisionRequest(
                request_id=stable_ref(
                    "v60-decision-request",
                    {
                        "kind": DecisionKind.WORLD_OUTCOME.value,
                        "event_ref": event_ref,
                        "outcome_hash": event["outcome_hash"],
                    },
                ),
                decision_kind=DecisionKind.WORLD_OUTCOME,
                subject_ref=event_ref,
                evidence_refs=tuple(str(item["evidence_ref"]) for item in outcome["evidence"]),
                deterministic_result={
                    "world_event_ref": event_ref,
                    "outcome_hash": event["outcome_hash"],
                },
                llm_allowed=False,
                correlation_id=event_ref,
                causation_id=str(event["event_json"].get("caused_by_event_ref", event_ref)),
            ),
        )
        if (
            decision.route.status is not DecisionRouteStatus.RESOLVED
            or decision.route.authority is not DecisionAuthority.SYSTEM
        ):
            raise WorldContinuityError("world_outcome_not_system_resolved")

        settlement_hash = self._settle_event(connection=connection, event=event)
        return WorldSettlement(
            world_event_ref=event_ref,
            settled_at_tick=due_tick,
            settlement_hash=settlement_hash,
            already_settled=False,
            decision_id=decision.decision_id,
        )

    def commit_historical_event(
        self,
        *,
        connection: Any,
        event_ref: str,
        actor_ref: str,
        event_type: str,
        summary: str,
        caused_by_event_ref: str,
        evidence: Sequence[Mapping[str, Any]],
        actor_state_delta: Mapping[str, Any],
        world_ref: str = PRIMARY_WORLD_ID,
    ) -> None:
        existing_tick = connection.execute(
            text(
                """
                SELECT due_tick
                FROM world.events
                WHERE world_event_ref = :event_ref
                """
            ),
            {"event_ref": event_ref},
        ).scalar_one_or_none()
        current_tick = (
            int(existing_tick)
            if existing_tick is not None
            else self.current_tick(connection, world_ref=world_ref)
        )
        event_payload = {
            "summary": summary,
            "visibility": "PUBLIC_AFTER_COMMIT",
            "caused_by_event_ref": caused_by_event_ref,
        }
        WorldEventAdmissionService().admit(
            connection,
            definition=WorldEventDefinition(
                world_event_ref=event_ref,
                world_ref=world_ref,
                actor_ref=actor_ref,
                event_type=event_type,
                due_tick=current_tick,
                initial_status=WorldEventStatus.SETTLED,
                event_payload=event_payload,
                sealed_outcome={},
                initial_evidence=tuple(
                    WorldEventEvidenceDefinition(
                        evidence_ref=str(item["evidence_ref"]),
                        committed_at_tick=current_tick,
                        payload=dict(item),
                    )
                    for item in evidence
                ),
                settled_at_tick=current_tick,
            ),
        )
        self._append_actor_event(
            connection=connection,
            actor_ref=actor_ref,
            event_ref=event_ref,
            summary=summary,
            world_tick=current_tick,
            state_delta=actor_state_delta,
        )

    def _settle_event(self, *, connection: Any, event: Mapping[str, Any]) -> str:
        outcome = dict(event["sealed_outcome_json"])
        settlement_payload = {
            "world_event_ref": event["world_event_ref"],
            "settled_at_tick": event["due_tick"],
            "outcome_hash": event["outcome_hash"],
        }
        settlement_hash = content_hash(settlement_payload)
        connection.execute(
            text(
                """
                UPDATE world.events
                SET status = 'SETTLED',
                    settled_at_tick = due_tick,
                    settlement_hash = :settlement_hash
                WHERE world_event_ref = :event_ref
                  AND status = 'SCHEDULED'
                """
            ),
            {
                "event_ref": event["world_event_ref"],
                "settlement_hash": settlement_hash,
            },
        )
        for evidence in outcome["evidence"]:
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
                    "evidence_ref": evidence["evidence_ref"],
                    "event_ref": event["world_event_ref"],
                    "tick": event["due_tick"],
                    "evidence_json": canonical_json(evidence),
                    "evidence_hash": content_hash(evidence),
                },
            )
        outbox_payload = {
            "world_event_ref": event["world_event_ref"],
            "settlement_hash": settlement_hash,
            "evidence_refs": [item["evidence_ref"] for item in outcome["evidence"]],
        }
        connection.execute(
            text(
                """
                INSERT INTO world.outbox
                    (outbox_ref, aggregate_ref, event_type, payload_json, payload_hash)
                VALUES
                    (:outbox_ref, :aggregate_ref, 'WORLD_EVENT_SETTLED',
                     CAST(:payload_json AS jsonb), :payload_hash)
                ON CONFLICT (payload_hash) DO NOTHING
                """
            ),
            {
                "outbox_ref": stable_ref("v60-outbox", outbox_payload),
                "aggregate_ref": event["world_event_ref"],
                "payload_json": canonical_json(outbox_payload),
                "payload_hash": content_hash(outbox_payload),
            },
        )
        state_delta = dict(
            event["event_json"].get(
                "actor_state_delta",
                {
                    "activity": "measuring-intermittent-channel-flow",
                    "last_settled_event_ref": event["world_event_ref"],
                },
            )
        )
        self._append_actor_event(
            connection=connection,
            actor_ref=str(event["actor_ref"]),
            event_ref=str(event["world_event_ref"]),
            summary=str(outcome["actual_event"]),
            world_tick=int(event["due_tick"]),
            state_delta=state_delta,
        )
        return settlement_hash

    @staticmethod
    def _append_actor_event(
        *,
        connection: Any,
        actor_ref: str,
        event_ref: str,
        summary: str,
        world_tick: int,
        state_delta: Mapping[str, Any],
    ) -> None:
        actor = (
            connection.execute(
                text(
                    """
                SELECT actor_version, timeline_json, state_json
                FROM world.actors
                WHERE actor_ref = :actor_ref
                FOR UPDATE
                """
                ),
                {"actor_ref": actor_ref},
            )
            .mappings()
            .one()
        )
        timeline = dict(actor["timeline_json"])
        timeline_events = list(timeline.get("events", []))
        existing_event = next(
            (item for item in timeline_events if item.get("world_event_ref") == event_ref),
            None,
        )
        if existing_event is not None:
            if (
                existing_event.get("summary") != summary
                or int(existing_event.get("world_tick", -1)) != world_tick
            ):
                raise WorldContinuityError("actor_timeline_event_conflict")
            return
        timeline_events.append(
            {
                "world_event_ref": event_ref,
                "summary": summary,
                "world_tick": world_tick,
            }
        )
        timeline["events"] = timeline_events
        next_state = {**dict(actor["state_json"]), **dict(state_delta)}
        next_version = int(actor["actor_version"]) + 1
        connection.execute(
            text(
                """
                UPDATE world.actors
                SET actor_version = :actor_version,
                    timeline_json = CAST(:timeline_json AS jsonb),
                    state_json = CAST(:state_json AS jsonb),
                    state_hash = :state_hash
                WHERE actor_ref = :actor_ref
                """
            ),
            {
                "actor_ref": actor_ref,
                "actor_version": next_version,
                "timeline_json": canonical_json(timeline),
                "state_json": canonical_json(next_state),
                "state_hash": content_hash(
                    {
                        "actor_ref": actor_ref,
                        "event_ref": event_ref,
                        "actor_version": next_version,
                        "timeline": timeline,
                        "state": next_state,
                    }
                ),
            },
        )
