from __future__ import annotations

import threading
from typing import Any, Protocol

from experience.contracts import (
    MingliExperienceEnvelope,
    ParticipantRun,
    PerformanceCueInstance,
    TheaterEvent,
    TheaterSession,
    TopicExploration,
)


class TheaterStore(Protocol):
    persistent: bool
    storage_name: str

    def save_session(self, session: TheaterSession) -> None: ...
    def get_session(self, session_id: str) -> TheaterSession | None: ...
    def save_envelope(self, envelope: MingliExperienceEnvelope) -> None: ...
    def get_envelope(self, envelope_id: str) -> MingliExperienceEnvelope | None: ...
    def save_participant(self, run: ParticipantRun) -> None: ...
    def get_participant(self, participant_run_id: str) -> ParticipantRun | None: ...
    def list_participants(self, session_id: str) -> list[ParticipantRun]: ...
    def save_cue(self, session_id: str, cue: PerformanceCueInstance) -> None: ...
    def get_cue(self, cue_instance_id: str) -> PerformanceCueInstance | None: ...
    def list_cues(self, session_id: str) -> list[PerformanceCueInstance]: ...
    def append_event(self, event: TheaterEvent) -> None: ...
    def list_events(self, session_id: str, *, after_sequence: int = 0) -> list[TheaterEvent]: ...
    def save_exploration(self, exploration: TopicExploration) -> None: ...
    def get_exploration(self, exploration_id: str) -> TopicExploration | None: ...
    def list_explorations(self, participant_run_id: str) -> list[TopicExploration]: ...


class MemoryTheaterStore:
    persistent = False
    storage_name = "memory_theater"

    def __init__(self) -> None:
        self._sessions: dict[str, TheaterSession] = {}
        self._envelopes: dict[str, MingliExperienceEnvelope] = {}
        self._participants: dict[str, ParticipantRun] = {}
        self._cues: dict[str, tuple[str, PerformanceCueInstance]] = {}
        self._events: dict[str, list[TheaterEvent]] = {}
        self._explorations: dict[str, TopicExploration] = {}
        self._lock = threading.RLock()

    def save_session(self, session: TheaterSession) -> None:
        with self._lock:
            previous = self._sessions.get(session.session_id)
            if previous and previous.sequence > session.sequence:
                session = session.model_copy(update={"sequence": previous.sequence})
            self._sessions[session.session_id] = session

    def get_session(self, session_id: str) -> TheaterSession | None:
        with self._lock:
            return self._sessions.get(session_id)

    def save_envelope(self, envelope: MingliExperienceEnvelope) -> None:
        with self._lock:
            previous = self._envelopes.get(envelope.envelope_id)
            if previous and previous != envelope:
                raise ValueError("immutable_envelope_conflict")
            self._envelopes[envelope.envelope_id] = envelope

    def get_envelope(self, envelope_id: str) -> MingliExperienceEnvelope | None:
        with self._lock:
            return self._envelopes.get(envelope_id)

    def save_participant(self, run: ParticipantRun) -> None:
        with self._lock:
            self._participants[run.participant_run_id] = run

    def get_participant(self, participant_run_id: str) -> ParticipantRun | None:
        with self._lock:
            return self._participants.get(participant_run_id)

    def list_participants(self, session_id: str) -> list[ParticipantRun]:
        with self._lock:
            return [item for item in self._participants.values() if item.session_id == session_id]

    def save_cue(self, session_id: str, cue: PerformanceCueInstance) -> None:
        with self._lock:
            previous = self._cues.get(cue.cue_instance_id)
            if previous and previous != (session_id, cue):
                raise ValueError("immutable_cue_conflict")
            self._cues[cue.cue_instance_id] = (session_id, cue)

    def get_cue(self, cue_instance_id: str) -> PerformanceCueInstance | None:
        with self._lock:
            row = self._cues.get(cue_instance_id)
            return row[1] if row else None

    def list_cues(self, session_id: str) -> list[PerformanceCueInstance]:
        with self._lock:
            return [cue for stored_session, cue in self._cues.values() if stored_session == session_id]

    def append_event(self, event: TheaterEvent) -> None:
        with self._lock:
            rows = self._events.setdefault(event.session_id, [])
            if any(item.sequence == event.sequence for item in rows):
                raise ValueError("duplicate_event_sequence")
            rows.append(event)
            rows.sort(key=lambda item: item.sequence)
            session = self._sessions.get(event.session_id)
            if session:
                self._sessions[event.session_id] = session.model_copy(
                    update={"sequence": max(session.sequence, event.sequence)}
                )

    def list_events(self, session_id: str, *, after_sequence: int = 0) -> list[TheaterEvent]:
        with self._lock:
            return [item for item in self._events.get(session_id, []) if item.sequence > after_sequence]

    def save_exploration(self, exploration: TopicExploration) -> None:
        with self._lock:
            self._explorations[exploration.exploration_id] = exploration

    def get_exploration(self, exploration_id: str) -> TopicExploration | None:
        with self._lock:
            return self._explorations.get(exploration_id)

    def list_explorations(self, participant_run_id: str) -> list[TopicExploration]:
        with self._lock:
            return [
                item
                for item in self._explorations.values()
                if item.participant_run_id == participant_run_id
            ]

    def dump_counts(self) -> dict[str, Any]:
        with self._lock:
            return {
                "sessions": len(self._sessions),
                "participants": len(self._participants),
                "events": sum(len(rows) for rows in self._events.values()),
                "cues": len(self._cues),
                "explorations": len(self._explorations),
            }
