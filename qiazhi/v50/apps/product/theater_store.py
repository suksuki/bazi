from __future__ import annotations

import os

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from experience.contracts import (
    MingliExperienceEnvelope,
    ParticipantRun,
    PerformanceCueInstance,
    TheaterEvent,
    TheaterSession,
    TopicExploration,
)
from experience.store import MemoryTheaterStore, TheaterStore
from product.database_schema import ensure_product_database_schema


class PostgresTheaterStore:
    persistent = True
    storage_name = "v50_postgresql_theater"

    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        ensure_product_database_schema(database_url)

    def _connect(self):
        import psycopg

        return psycopg.connect(self.database_url)

    def save_session(self, session: TheaterSession) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO v50_theater_sessions (session_id, session_json)
                    VALUES (%s, %s)
                    ON CONFLICT (session_id) DO UPDATE SET
                      session_json = jsonb_set(
                        EXCLUDED.session_json,
                        '{sequence}',
                        to_jsonb(
                          GREATEST(
                            COALESCE((v50_theater_sessions.session_json->>'sequence')::integer, 0),
                            COALESCE((EXCLUDED.session_json->>'sequence')::integer, 0)
                          )
                        ),
                        true
                      ),
                      updated_at = now()
                    """,
                    (session.session_id, Jsonb(session.model_dump(mode="json"))),
                )

    def get_session(self, session_id: str) -> TheaterSession | None:
        row = self._one("SELECT session_json FROM v50_theater_sessions WHERE session_id = %s", (session_id,))
        return TheaterSession.model_validate(row["session_json"]) if row else None

    def save_envelope(self, envelope: MingliExperienceEnvelope) -> None:
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("SELECT source_hash FROM v50_theater_envelopes WHERE envelope_id = %s", (envelope.envelope_id,))
                previous = cur.fetchone()
                if previous and previous["source_hash"] != envelope.source.source_hash:
                    raise ValueError("immutable_envelope_conflict")
                cur.execute(
                    """
                    INSERT INTO v50_theater_envelopes (envelope_id, source_hash, envelope_json)
                    VALUES (%s, %s, %s) ON CONFLICT (envelope_id) DO NOTHING
                    """,
                    (envelope.envelope_id, envelope.source.source_hash, Jsonb(envelope.model_dump(mode="json"))),
                )

    def get_envelope(self, envelope_id: str) -> MingliExperienceEnvelope | None:
        row = self._one("SELECT envelope_json FROM v50_theater_envelopes WHERE envelope_id = %s", (envelope_id,))
        return MingliExperienceEnvelope.model_validate(row["envelope_json"]) if row else None

    def save_participant(self, run: ParticipantRun) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO v50_theater_participants (participant_run_id, session_id, participant_json)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (participant_run_id) DO UPDATE SET participant_json = EXCLUDED.participant_json, updated_at = now()
                    """,
                    (run.participant_run_id, run.session_id, Jsonb(run.model_dump(mode="json"))),
                )

    def get_participant(self, participant_run_id: str) -> ParticipantRun | None:
        row = self._one(
            "SELECT participant_json FROM v50_theater_participants WHERE participant_run_id = %s",
            (participant_run_id,),
        )
        return ParticipantRun.model_validate(row["participant_json"]) if row else None

    def list_participants(self, session_id: str) -> list[ParticipantRun]:
        rows = self._all(
            "SELECT participant_json FROM v50_theater_participants WHERE session_id = %s ORDER BY participant_run_id",
            (session_id,),
        )
        return [ParticipantRun.model_validate(row["participant_json"]) for row in rows]

    def save_cue(self, session_id: str, cue: PerformanceCueInstance) -> None:
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("SELECT cue_hash FROM v50_theater_cues WHERE cue_instance_id = %s", (cue.cue_instance_id,))
                previous = cur.fetchone()
                if previous and previous["cue_hash"] != cue.cue_hash:
                    raise ValueError("immutable_cue_conflict")
                cur.execute(
                    """
                    INSERT INTO v50_theater_cues (cue_instance_id, session_id, cue_hash, cue_json)
                    VALUES (%s, %s, %s, %s) ON CONFLICT (cue_instance_id) DO NOTHING
                    """,
                    (cue.cue_instance_id, session_id, cue.cue_hash, Jsonb(cue.model_dump(mode="json"))),
                )

    def get_cue(self, cue_instance_id: str) -> PerformanceCueInstance | None:
        row = self._one("SELECT cue_json FROM v50_theater_cues WHERE cue_instance_id = %s", (cue_instance_id,))
        return PerformanceCueInstance.model_validate(row["cue_json"]) if row else None

    def list_cues(self, session_id: str) -> list[PerformanceCueInstance]:
        rows = self._all("SELECT cue_json FROM v50_theater_cues WHERE session_id = %s ORDER BY created_at", (session_id,))
        return [PerformanceCueInstance.model_validate(row["cue_json"]) for row in rows]

    def append_event(self, event: TheaterEvent) -> None:
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    "SELECT session_json FROM v50_theater_sessions WHERE session_id = %s FOR UPDATE",
                    (event.session_id,),
                )
                row = cur.fetchone()
                if not row:
                    raise ValueError("theater_session_not_found")
                session = TheaterSession.model_validate(row["session_json"])
                expected = session.sequence + 1
                if event.sequence != expected:
                    raise ValueError(f"event_sequence_conflict:expected_{expected}:got_{event.sequence}")
                cur.execute(
                    """
                    INSERT INTO v50_theater_events
                      (event_id, session_id, sequence, scope, participant_run_id, event_json, occurred_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        event.event_id,
                        event.session_id,
                        event.sequence,
                        event.scope,
                        event.participant_run_id,
                        Jsonb(event.model_dump(mode="json")),
                        event.occurred_at,
                    ),
                )
                session = session.model_copy(update={"sequence": event.sequence})
                cur.execute(
                    "UPDATE v50_theater_sessions SET session_json = %s, updated_at = now() WHERE session_id = %s",
                    (Jsonb(session.model_dump(mode="json")), event.session_id),
                )

    def list_events(self, session_id: str, *, after_sequence: int = 0) -> list[TheaterEvent]:
        rows = self._all(
            "SELECT event_json FROM v50_theater_events WHERE session_id = %s AND sequence > %s ORDER BY sequence",
            (session_id, after_sequence),
        )
        return [TheaterEvent.model_validate(row["event_json"]) for row in rows]

    def save_exploration(self, exploration: TopicExploration) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO v50_topic_explorations (exploration_id, participant_run_id, exploration_json)
                    VALUES (%s, %s, %s) ON CONFLICT (exploration_id) DO NOTHING
                    """,
                    (
                        exploration.exploration_id,
                        exploration.participant_run_id,
                        Jsonb(exploration.model_dump(mode="json")),
                    ),
                )

    def get_exploration(self, exploration_id: str) -> TopicExploration | None:
        row = self._one(
            "SELECT exploration_json FROM v50_topic_explorations WHERE exploration_id = %s",
            (exploration_id,),
        )
        return TopicExploration.model_validate(row["exploration_json"]) if row else None

    def list_explorations(self, participant_run_id: str) -> list[TopicExploration]:
        rows = self._all(
            "SELECT exploration_json FROM v50_topic_explorations WHERE participant_run_id = %s ORDER BY created_at",
            (participant_run_id,),
        )
        return [TopicExploration.model_validate(row["exploration_json"]) for row in rows]

    def _one(self, sql: str, params: tuple[object, ...]):
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, params)
                return cur.fetchone()

    def _all(self, sql: str, params: tuple[object, ...]):
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, params)
                return cur.fetchall()


def build_theater_store() -> TheaterStore:
    database_url = os.getenv("V50_DATABASE_URL", "").strip()
    return PostgresTheaterStore(database_url) if database_url else MemoryTheaterStore()
