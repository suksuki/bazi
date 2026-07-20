from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from threading import RLock
from typing import Any
from uuid import uuid4

from experience.contracts import (
    CompiledTopic,
    MingliExperienceEnvelope,
    ParticipantRun,
    PerformanceCueInstance,
    SceneNode,
    TheaterEvent,
    TheaterSession,
    TopicExploration,
)
from experience.cues import CueRenderError, freeze_performance_cue
from experience.store import TheaterStore


PUBLIC_SENSITIVE_KEYS = {
    "envelope",
    "envelope_id",
    "envelope_hash",
    "life_case",
    "life_case_version",
    "birth",
    "birth_input",
    "birth_location",
    "chart",
    "chart_facts",
    "pillars",
    "approved_claim",
    "approved_claims",
    "competing_hypotheses",
    "private_answer",
    "participant_ref",
}


class TheaterRuntimeError(ValueError):
    pass


class TheaterRuntime:
    """Generic, deterministic runtime for every compiled Abu topic."""

    def __init__(self, *, store: TheaterStore, topics: list[CompiledTopic]) -> None:
        self.store = store
        self.topics = {(item.topic.topic_id, item.topic.version): item for item in topics}
        self._locks: dict[str, RLock] = {}

    def list_topics(self) -> list[dict[str, Any]]:
        return [
            {
                "topic_id": topic.topic.topic_id,
                "version": topic.topic.version,
                "title": topic.topic.title,
                "purpose": topic.topic.purpose,
                "supported_modes": topic.topic.supported_modes,
                "content_hash": topic.content_hash,
            }
            for topic in self.topics.values()
        ]

    def required_capabilities(self, *, topic_id: str, topic_version: str) -> list[str]:
        return list(self._topic(topic_id, topic_version).topic.required_experience_capabilities)

    def create_session(self, *, topic_id: str, topic_version: str, mode: str) -> TheaterSession:
        topic = self._topic(topic_id, topic_version)
        if mode not in topic.topic.supported_modes:
            raise TheaterRuntimeError(f"unsupported_mode:{mode}")
        if mode == "replay":
            raise TheaterRuntimeError("replay_requires_existing_session")
        now = _now()
        session = TheaterSession(
            session_id=f"theater-{uuid4().hex[:20]}",
            topic_id=topic_id,
            topic_version=topic_version,
            topic_hash=topic.content_hash,
            mode=mode,
            status="running",
            current_public_node_id=topic.entry_node,
            created_at=now,
            updated_at=now,
        )
        self.store.save_session(session)
        self._append_event(session, event_type="session_started", scope="public", node_id=topic.entry_node, payload={
            "topic_id": topic_id,
            "topic_version": topic_version,
            "mode": mode,
        })
        self._activate_public_node(session_id=session.session_id, node_id=topic.entry_node)
        return self._require_session(session.session_id)

    def join(
        self,
        *,
        session_id: str,
        envelope: MingliExperienceEnvelope,
        access_token_hash: str = "",
    ) -> ParticipantRun:
        with self._lock(session_id):
            session = self._require_session(session_id)
            topic = self._topic(session.topic_id, session.topic_version)
            if envelope.topic_scope.topic_id != session.topic_id or envelope.topic_scope.topic_version != session.topic_version:
                raise TheaterRuntimeError("envelope_topic_mismatch")
            if envelope.source.expires_at <= _now():
                raise TheaterRuntimeError("envelope_expired")
            self.store.save_envelope(envelope)
            now = _now()
            run = ParticipantRun(
                participant_run_id=f"run-{uuid4().hex[:20]}",
                session_id=session_id,
                participant_ref=envelope.participant_scope.participant_ref,
                access_token_hash=access_token_hash,
                envelope_id=envelope.envelope_id,
                envelope_mode=envelope.mode,
                current_node_id=session.active_private_node_id or session.current_public_node_id,
                status="private_scene" if session.active_private_node_id else "joined",
                joined_at=now,
                updated_at=now,
            )
            self.store.save_participant(run)
            participants = self.store.list_participants(session_id)
            session = session.model_copy(update={"participant_count": len(participants), "updated_at": now})
            self.store.save_session(session)
            self._append_event(session, event_type="participant_joined", scope="public", payload={
                "participant_count": len(participants),
            })
            if session.active_private_node_id:
                self._enter_private_node(run=run, node_id=session.active_private_node_id)
            return self._require_participant(run.participant_run_id)

    def advance(self, *, session_id: str, event: str = "next") -> TheaterSession:
        with self._lock(session_id):
            session = self._require_session(session_id)
            if session.status == "paused":
                raise TheaterRuntimeError("session_paused")
            if session.active_private_node_id:
                raise TheaterRuntimeError("private_window_requires_rejoin")
            topic = self._topic(session.topic_id, session.topic_version)
            node = topic.scene_nodes[session.current_public_node_id]
            target = _transition_target(node, event)
            if target is None:
                if not node.transitions:
                    session = session.model_copy(update={"status": "completed", "updated_at": _now()})
                    self.store.save_session(session)
                    self._append_event(session, event_type="session_completed", scope="public", node_id=node.node_id)
                    return self._require_session(session_id)
                raise TheaterRuntimeError(f"transition_not_found:{node.node_id}:{event}")
            target_node = topic.scene_nodes[target]
            if target_node.visibility == "public":
                self._activate_public_node(session_id=session_id, node_id=target)
            else:
                now = _now()
                session = session.model_copy(update={
                    "active_private_node_id": target,
                    "last_private_node_id": target,
                    "updated_at": now,
                })
                self.store.save_session(session)
                self._append_event(session, event_type="private_window_opened", scope="public", node_id=target, payload={
                    "participant_count": session.participant_count,
                })
                for run in self.store.list_participants(session_id):
                    self._enter_private_node(run=run, node_id=target)
            return self._require_session(session_id)

    def complete_private(
        self,
        *,
        session_id: str,
        participant_run_id: str,
        response: str = "",
    ) -> ParticipantRun:
        with self._lock(session_id):
            session = self._require_session(session_id)
            node_id = session.active_private_node_id
            if not node_id:
                raise TheaterRuntimeError("no_active_private_window")
            run = self._require_participant(participant_run_id)
            if run.session_id != session_id or run.current_node_id != node_id:
                raise TheaterRuntimeError("participant_not_in_active_private_node")
            topic = self._topic(session.topic_id, session.topic_version)
            node = topic.scene_nodes[node_id]
            value = response.strip()
            if node.interaction.required and not value:
                raise TheaterRuntimeError("private_response_required")
            if node.interaction.options and value not in node.interaction.options:
                raise TheaterRuntimeError("private_response_not_allowed")
            answers = dict(run.private_answers)
            if value:
                answers[node_id] = value
            now = _now()
            run = run.model_copy(update={
                "private_answers": answers,
                "status": "at_barrier",
                "updated_at": now,
            })
            self.store.save_participant(run)
            self._append_event(
                session,
                event_type="private_interaction_completed",
                scope="participant_private",
                participant_run_id=participant_run_id,
                node_id=node_id,
                payload={"response": value, "recorded": bool(value)},
            )
            participants = self.store.list_participants(session_id)
            ready_count = sum(item.status == "at_barrier" for item in participants)
            self._append_event(session, event_type="participant_ready", scope="public", node_id=node_id, payload={
                "ready_count": ready_count,
                "participant_count": len(participants),
            })
            if ready_count == len(participants) and participants:
                self._append_event(session, event_type="private_window_ready", scope="public", node_id=node_id, payload={
                    "ready_count": ready_count,
                })
            if node.interaction.kind == "capsule" and value:
                self.store.save_exploration(TopicExploration(
                    exploration_id=f"exploration-{uuid4().hex[:20]}",
                    participant_run_id=participant_run_id,
                    topic_id=session.topic_id,
                    responses=answers,
                    capsule_message=value,
                    created_at=now,
                ))
            if session.mode in {"solo", "time_shift"}:
                self.rejoin(session_id=session_id)
            return self._require_participant(participant_run_id)

    def rejoin(self, *, session_id: str) -> TheaterSession:
        with self._lock(session_id):
            session = self._require_session(session_id)
            node_id = session.active_private_node_id
            if not node_id:
                raise TheaterRuntimeError("no_private_window_to_rejoin")
            topic = self._topic(session.topic_id, session.topic_version)
            node = topic.scene_nodes[node_id]
            target = node.rejoin_node
            if not target:
                raise TheaterRuntimeError("private_node_has_no_rejoin")
            self._append_event(session, event_type="private_window_closed", scope="public", node_id=node_id)
            session = self._require_session(session_id).model_copy(
                update={"active_private_node_id": None, "updated_at": _now()}
            )
            self.store.save_session(session)
            self._activate_public_node(session_id=session_id, node_id=target)
            return self._require_session(session_id)

    def reveal_group_trace(self, *, session_id: str) -> TheaterEvent:
        with self._lock(session_id):
            session = self._require_session(session_id)
            source_node = session.last_private_node_id or ""
            participants = self.store.list_participants(session_id)
            answers = [item.private_answers.get(source_node, "") for item in participants]
            answers = [item for item in answers if item]
            topic = self._topic(session.topic_id, session.topic_version)
            if len(participants) < topic.policies.aggregation_minimum:
                return self._append_event(session, event_type="group_trace_suppressed", scope="public", payload={
                    "reason": "aggregation_minimum_not_met",
                    "participant_count": len(participants),
                    "minimum": topic.policies.aggregation_minimum,
                })
            return self._append_event(session, event_type="group_trace_revealed", scope="public", payload={
                "choice_counts": dict(Counter(answers)),
                "participant_count": len(participants),
            })

    def set_paused(self, *, session_id: str, paused: bool) -> TheaterSession:
        with self._lock(session_id):
            session = self._require_session(session_id)
            session = session.model_copy(update={"status": "paused" if paused else "running", "updated_at": _now()})
            self.store.save_session(session)
            self._append_event(session, event_type="session_paused" if paused else "session_resumed", scope="public")
            return self._require_session(session_id)

    def snapshot(
        self,
        *,
        session_id: str,
        participant_run_id: str | None = None,
        operator: bool = False,
        after_sequence: int = 0,
    ) -> dict[str, Any]:
        session = self._require_session(session_id)
        run = self._require_participant(participant_run_id) if participant_run_id else None
        if run and run.session_id != session_id:
            raise TheaterRuntimeError("participant_session_mismatch")
        events = [
            event
            for event in self.store.list_events(session_id, after_sequence=after_sequence)
            if _event_visible(event=event, participant_run_id=participant_run_id, operator=operator)
        ]
        cue_ids = {event.cue_instance_id for event in events if event.cue_instance_id}
        cues = [cue for cue in self.store.list_cues(session_id) if cue.cue_instance_id in cue_ids]
        topic = self._topic(session.topic_id, session.topic_version)
        node_id = run.current_node_id if run else session.current_public_node_id
        node = topic.scene_nodes[node_id]
        participant_payload = run.model_dump(mode="json") if run else None
        if participant_payload is not None:
            participant_payload.pop("access_token_hash", None)
        return {
            "session": session.model_dump(mode="json"),
            "topic": topic.topic.model_dump(mode="json"),
            "participant": participant_payload,
            "scene": node.model_dump(mode="json"),
            "events": [item.model_dump(mode="json") for item in events],
            "cues": [item.model_dump(mode="json") for item in cues],
            "assets": {key: item.model_dump(mode="json") for key, item in topic.assets.items()},
            "recovered": after_sequence > 0,
        }

    def replay(self, *, session_id: str, participant_run_id: str | None = None) -> dict[str, Any]:
        snapshot = self.snapshot(session_id=session_id, participant_run_id=participant_run_id)
        return {
            "replay_of": session_id,
            "topic_hash": snapshot["session"]["topic_hash"],
            "events": snapshot["events"],
            "cues": snapshot["cues"],
            "regeneration_performed": False,
            "llm_used": False,
            "reasoner_used": False,
            "tts_regenerated": False,
        }

    def record_private_event(
        self,
        *,
        session_id: str,
        participant_run_id: str,
        event_type: str,
        node_id: str,
        payload: dict[str, Any],
    ) -> TheaterEvent:
        """Append an application-owned private event through the session clock."""

        if not event_type.startswith("mingli_experiment_"):
            raise TheaterRuntimeError("private_extension_event_not_allowed")
        with self._lock(session_id):
            session = self._require_session(session_id)
            run = self._require_participant(participant_run_id)
            if run.session_id != session_id:
                raise TheaterRuntimeError("participant_session_mismatch")
            return self._append_event(
                session,
                event_type=event_type,
                scope="participant_private",
                participant_run_id=participant_run_id,
                node_id=node_id,
                payload=payload,
            )

    def _activate_public_node(self, *, session_id: str, node_id: str) -> None:
        session = self._require_session(session_id)
        topic = self._topic(session.topic_id, session.topic_version)
        node = topic.scene_nodes[node_id]
        if node.visibility != "public":
            raise TheaterRuntimeError(f"cannot_activate_private_as_public:{node_id}")
        status = "completed" if not node.transitions else "running"
        now = _now()
        session = session.model_copy(update={
            "current_public_node_id": node_id,
            "active_private_node_id": None,
            "status": status,
            "updated_at": now,
        })
        self.store.save_session(session)
        self._append_event(session, event_type="public_scene_entered", scope="public", node_id=node_id, payload={
            "act": node.act,
            "dramatic_purpose": node.dramatic_purpose,
        })
        for cue_id in node.cue_template_ids:
            cue = freeze_performance_cue(
                template=topic.cue_templates[cue_id],
                participant_run_id=None,
                public_bindings={},
            )
            self.store.save_cue(session_id, cue)
            self._append_cue_event(session=session, node=node, cue=cue)
        for run in self.store.list_participants(session_id):
            self.store.save_participant(run.model_copy(update={
                "current_node_id": node_id,
                "status": "completed" if status == "completed" else "joined",
                "updated_at": now,
            }))

    def _enter_private_node(self, *, run: ParticipantRun, node_id: str) -> None:
        session = self._require_session(run.session_id)
        topic = self._topic(session.topic_id, session.topic_version)
        node = topic.scene_nodes[node_id]
        if node.visibility != "participant_private":
            raise TheaterRuntimeError(f"cannot_enter_public_as_private:{node_id}")
        envelope = self.store.get_envelope(run.envelope_id)
        if not envelope:
            raise TheaterRuntimeError("participant_envelope_missing")
        frozen_ids = list(run.frozen_cue_ids)
        self._append_event(
            session,
            event_type="private_scene_entered",
            scope="participant_private",
            participant_run_id=run.participant_run_id,
            node_id=node_id,
            payload={"interaction": node.interaction.model_dump(mode="json")},
        )
        for cue_id in node.cue_template_ids:
            template = topic.cue_templates[cue_id]
            try:
                cue = freeze_performance_cue(
                    template=template,
                    participant_run_id=run.participant_run_id,
                    envelope=envelope,
                )
            except CueRenderError:
                if not template.fallback_template_id:
                    raise
                cue = freeze_performance_cue(
                    template=topic.cue_templates[template.fallback_template_id],
                    participant_run_id=run.participant_run_id,
                    envelope=envelope,
                )
            self.store.save_cue(session.session_id, cue)
            frozen_ids.append(cue.cue_instance_id)
            self._append_cue_event(session=session, node=node, cue=cue, participant_run_id=run.participant_run_id)
        self.store.save_participant(run.model_copy(update={
            "current_node_id": node_id,
            "status": "private_scene",
            "frozen_cue_ids": frozen_ids,
            "updated_at": _now(),
        }))

    def _append_cue_event(
        self,
        *,
        session: TheaterSession,
        node: SceneNode,
        cue: PerformanceCueInstance,
        participant_run_id: str | None = None,
    ) -> TheaterEvent:
        return self._append_event(
            session,
            event_type="cue_frozen",
            scope=node.visibility,
            participant_run_id=participant_run_id,
            node_id=node.node_id,
            cue_instance_id=cue.cue_instance_id,
            cue_hash=cue.cue_hash,
            payload={
                "dialogue": cue.final_dialogue,
                "subtitle": cue.final_subtitle,
                "actor_commands": [item.model_dump(mode="json") for item in cue.final_actor_commands],
                "stage_commands": [item.model_dump(mode="json") for item in cue.final_stage_commands],
                "audio_asset": cue.final_audio_asset,
            },
        )

    def _append_event(
        self,
        session: TheaterSession,
        *,
        event_type: str,
        scope: str,
        participant_run_id: str | None = None,
        node_id: str = "",
        cue_instance_id: str | None = None,
        cue_hash: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> TheaterEvent:
        current = self._require_session(session.session_id)
        body = payload or {}
        if scope == "public":
            _validate_public_payload(body)
        event = TheaterEvent(
            event_id=f"event-{uuid4().hex[:20]}",
            session_id=session.session_id,
            sequence=current.sequence + 1,
            event_type=event_type,
            scope=scope,
            participant_run_id=participant_run_id,
            node_id=node_id,
            cue_instance_id=cue_instance_id,
            cue_hash=cue_hash,
            payload=body,
            occurred_at=_now(),
        )
        self.store.append_event(event)
        return event

    def _topic(self, topic_id: str, topic_version: str) -> CompiledTopic:
        topic = self.topics.get((topic_id, topic_version))
        if not topic:
            raise TheaterRuntimeError(f"compiled_topic_not_found:{topic_id}:{topic_version}")
        return topic

    def _require_session(self, session_id: str) -> TheaterSession:
        session = self.store.get_session(session_id)
        if not session:
            raise TheaterRuntimeError("theater_session_not_found")
        return session

    def _require_participant(self, participant_run_id: str | None) -> ParticipantRun:
        if not participant_run_id:
            raise TheaterRuntimeError("participant_run_required")
        run = self.store.get_participant(participant_run_id)
        if not run:
            raise TheaterRuntimeError("participant_run_not_found")
        return run

    def _lock(self, session_id: str) -> RLock:
        return self._locks.setdefault(session_id, RLock())


def _transition_target(node: SceneNode, event: str) -> str | None:
    return next((item.target for item in node.transitions if item.event == event), None)


def _event_visible(*, event: TheaterEvent, participant_run_id: str | None, operator: bool) -> bool:
    if event.scope == "public":
        return True
    if event.scope == "operator":
        return operator
    return bool(participant_run_id and event.participant_run_id == participant_run_id)


def _validate_public_payload(payload: Any, path: str = "payload") -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            normalized = str(key).lower()
            if normalized in PUBLIC_SENSITIVE_KEYS:
                raise TheaterRuntimeError(f"public_event_sensitive_key:{path}.{key}")
            _validate_public_payload(value, f"{path}.{key}")
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            _validate_public_payload(value, f"{path}[{index}]")


def _now() -> datetime:
    return datetime.now(timezone.utc)
