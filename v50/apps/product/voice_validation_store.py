from __future__ import annotations

import os
import threading
from typing import Protocol

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from experience.voice_validation import (
    VoiceComprehensionAnalystReview,
    VoiceComprehensionSubmission,
    VoiceValidationInteractionEvent,
    VoiceValidationSession,
)
from product.database_schema import check_product_database_schema


class VoiceValidationStore(Protocol):
    persistent: bool
    storage_name: str

    def create(self, session: VoiceValidationSession) -> None: ...
    def get(self, session_id: str) -> VoiceValidationSession | None: ...
    def append_event(
        self, session_id: str, event: VoiceValidationInteractionEvent
    ) -> VoiceValidationSession: ...
    def submit(
        self, session_id: str, submission: VoiceComprehensionSubmission
    ) -> VoiceValidationSession: ...
    def save_review(
        self, session_id: str, review: VoiceComprehensionAnalystReview
    ) -> VoiceValidationSession: ...
    def list_sessions(self) -> list[VoiceValidationSession]: ...


class MemoryVoiceValidationStore:
    persistent = False
    storage_name = "memory_voice_validation"

    def __init__(self) -> None:
        self._sessions: dict[str, VoiceValidationSession] = {}
        self._lock = threading.RLock()

    def create(self, session: VoiceValidationSession) -> None:
        with self._lock:
            previous = self._sessions.get(session.session_id)
            if previous and previous != session:
                raise ValueError("voice_validation_session_conflict")
            self._sessions[session.session_id] = session

    def get(self, session_id: str) -> VoiceValidationSession | None:
        with self._lock:
            return self._sessions.get(session_id)

    def append_event(
        self, session_id: str, event: VoiceValidationInteractionEvent
    ) -> VoiceValidationSession:
        with self._lock:
            session = self._required(session_id)
            if any(item.client_event_id == event.client_event_id for item in session.interactions):
                return session
            updated = session.model_copy(
                update={"interactions": [*session.interactions, event]}
            )
            self._sessions[session_id] = updated
            return updated

    def submit(
        self, session_id: str, submission: VoiceComprehensionSubmission
    ) -> VoiceValidationSession:
        with self._lock:
            session = self._required(session_id)
            if session.comprehension and session.comprehension != submission:
                raise ValueError("voice_validation_submission_already_locked")
            updated = session.model_copy(
                update={"status": "submitted", "comprehension": submission}
            )
            self._sessions[session_id] = updated
            return updated

    def save_review(
        self, session_id: str, review: VoiceComprehensionAnalystReview
    ) -> VoiceValidationSession:
        with self._lock:
            session = self._required(session_id)
            if session.analyst_review and session.analyst_review != review:
                raise ValueError("voice_validation_review_already_locked")
            updated = session.model_copy(update={"analyst_review": review})
            self._sessions[session_id] = updated
            return updated

    def list_sessions(self) -> list[VoiceValidationSession]:
        with self._lock:
            return sorted(self._sessions.values(), key=lambda item: item.started_at)

    def _required(self, session_id: str) -> VoiceValidationSession:
        session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(session_id)
        return session


class PostgresVoiceValidationStore:
    persistent = True
    storage_name = "v50_postgresql_voice_validation"

    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        check_product_database_schema(database_url)

    def _connect(self):
        import psycopg

        return psycopg.connect(self.database_url)

    def create(self, session: VoiceValidationSession) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO v50_voice_validation_sessions
                      (session_id, participant_ref, case_id, arm, session_json)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (session_id) DO NOTHING
                    """,
                    (
                        session.session_id,
                        session.participant_ref,
                        session.case_id,
                        session.arm,
                        Jsonb(session.model_dump(mode="json")),
                    ),
                )

    def get(self, session_id: str) -> VoiceValidationSession | None:
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    "SELECT session_json FROM v50_voice_validation_sessions WHERE session_id = %s",
                    (session_id,),
                )
                row = cur.fetchone()
        return VoiceValidationSession.model_validate(row["session_json"]) if row else None

    def append_event(
        self, session_id: str, event: VoiceValidationInteractionEvent
    ) -> VoiceValidationSession:
        return self._mutate(
            session_id,
            lambda session: session
            if any(item.client_event_id == event.client_event_id for item in session.interactions)
            else session.model_copy(update={"interactions": [*session.interactions, event]}),
        )

    def submit(
        self, session_id: str, submission: VoiceComprehensionSubmission
    ) -> VoiceValidationSession:
        def update(session: VoiceValidationSession) -> VoiceValidationSession:
            if session.comprehension and session.comprehension != submission:
                raise ValueError("voice_validation_submission_already_locked")
            return session.model_copy(
                update={"status": "submitted", "comprehension": submission}
            )

        return self._mutate(session_id, update)

    def save_review(
        self, session_id: str, review: VoiceComprehensionAnalystReview
    ) -> VoiceValidationSession:
        def update(session: VoiceValidationSession) -> VoiceValidationSession:
            if session.analyst_review and session.analyst_review != review:
                raise ValueError("voice_validation_review_already_locked")
            return session.model_copy(update={"analyst_review": review})

        return self._mutate(session_id, update)

    def list_sessions(self) -> list[VoiceValidationSession]:
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    "SELECT session_json FROM v50_voice_validation_sessions ORDER BY created_at"
                )
                rows = cur.fetchall()
        return [VoiceValidationSession.model_validate(row["session_json"]) for row in rows]

    def _mutate(self, session_id: str, operation) -> VoiceValidationSession:
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    "SELECT session_json FROM v50_voice_validation_sessions "
                    "WHERE session_id = %s FOR UPDATE",
                    (session_id,),
                )
                row = cur.fetchone()
                if row is None:
                    raise KeyError(session_id)
                updated = operation(VoiceValidationSession.model_validate(row["session_json"]))
                cur.execute(
                    "UPDATE v50_voice_validation_sessions SET session_json = %s, updated_at = now() "
                    "WHERE session_id = %s",
                    (Jsonb(updated.model_dump(mode="json")), session_id),
                )
        return updated


def build_voice_validation_store() -> VoiceValidationStore:
    database_url = os.getenv("V50_DATABASE_URL", "").strip()
    return (
        PostgresVoiceValidationStore(database_url)
        if database_url
        else MemoryVoiceValidationStore()
    )
