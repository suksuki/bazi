from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import text

from abu_v60.game import DreamEpisodeContract, DreamGameplayDirector
from abu_v60.provenance import content_hash
from abu_v60.story import (
    EpisodeAdmissionError,
    EpisodeTransitionContract,
    validate_persisted_episode_admission,
)


class EpisodeCatalogError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ActiveEpisodeCatalog:
    """Validated, replayable view of every active Dream episode."""

    episodes: tuple[DreamEpisodeContract, ...]
    transitions: tuple[EpisodeTransitionContract, ...]
    active_episode_refs: tuple[str, ...]
    entry_episode_ref: str
    entry_episode_refs: tuple[str, ...]
    question_sequence_indexes: tuple[tuple[str, int], ...]
    graph_hash: str

    @property
    def entry(self) -> DreamEpisodeContract:
        return self.for_episode(self.entry_episode_ref)

    def for_episode(self, episode_ref: str) -> DreamEpisodeContract:
        episode = next(
            (item for item in self.episodes if item.episode_ref == episode_ref),
            None,
        )
        if episode is None:
            raise EpisodeCatalogError("dream_episode_not_found")
        return episode

    def for_question(self, question_ref: str) -> DreamEpisodeContract:
        episode = next(
            (item for item in self.episodes if item.question_ref == question_ref),
            None,
        )
        if episode is None:
            raise EpisodeCatalogError("dream_episode_not_active")
        return episode

    def tree_entry_version(self, question_ref: str) -> int:
        return self._tree_sequence_index(question_ref) * 2 + 1

    def tree_settlement_version(self, question_ref: str) -> int:
        return self._tree_sequence_index(question_ref) * 2 + 2

    def transition_after(
        self,
        question_ref: str,
    ) -> EpisodeTransitionContract | None:
        return next(
            (
                transition
                for transition in self.transitions
                if transition.runtime_status == "ACTIVE"
                and transition.from_question_ref == question_ref
            ),
            None,
        )

    def next_episode(
        self,
        question_ref: str,
    ) -> tuple[DreamEpisodeContract, str] | None:
        transition = self.transition_after(question_ref)
        if transition is None:
            return None
        return self.for_question(transition.to_question_ref), transition.label

    def _tree_sequence_index(self, question_ref: str) -> int:
        try:
            return dict(self.question_sequence_indexes)[question_ref]
        except KeyError as exc:
            raise EpisodeCatalogError("dream_episode_not_active") from exc

    def public_summary(self) -> dict[str, Any]:
        return {
            "status": "READY",
            "entry_episode_ref": self.entry_episode_ref,
            "entry_episode_refs": list(self.entry_episode_refs),
            "entry_episode_count": len(self.entry_episode_refs),
            "active_episode_count": len(self.active_episode_refs),
            "retired_episode_count": len(self.episodes) - len(self.active_episode_refs),
            "ordered_episode_refs": list(self.active_episode_refs),
            "active_transition_count": sum(
                transition.runtime_status == "ACTIVE" for transition in self.transitions
            ),
            "graph_hash": self.graph_hash,
        }


class DreamEpisodeCatalog:
    """Single runtime reader and graph validator for persisted Dream content."""

    def __init__(self, director: DreamGameplayDirector | None = None) -> None:
        self._director = director or DreamGameplayDirector()

    def load(self, connection: Any) -> ActiveEpisodeCatalog:
        rows = (
            connection.execute(
                text(
                    """
                SELECT question.question_ref, question.actor_ref,
                       question.life_case_revision_ref, question.world_event_ref,
                       question.cutoff_tick, question.due_tick,
                       question.resolution_rule_json,
                       question.episode_ref, question.episode_version,
                       question.episode_contract_json,
                       question.episode_contract_hash, question.question_hash,
                       question.organ_set_hash, question.evidence_refs_json,
                       question.admission_manifest_json,
                       question.admission_manifest_hash,
                       life_case.revision_hash AS life_case_revision_hash,
                       event.outcome_hash
                FROM story.question_instances AS question
                JOIN mingli.life_case_revisions AS life_case
                  ON life_case.life_case_revision_ref =
                     question.life_case_revision_ref
                JOIN world.events AS event
                  ON event.world_event_ref = question.world_event_ref
                ORDER BY question.episode_ref
                """
                )
            )
            .mappings()
            .all()
        )
        transition_rows = (
            connection.execute(
                text(
                    """
                    SELECT transition_ref, transition_version,
                           from_question_ref, to_question_ref, label,
                           runtime_status, transition_json, transition_hash
                    FROM story.episode_transitions
                    ORDER BY transition_ref
                    """
                )
            )
            .mappings()
            .all()
        )
        return self.from_rows(
            [dict(row) for row in rows],
            transition_rows=[dict(row) for row in transition_rows],
        )

    def from_rows(
        self,
        rows: list[dict[str, Any]],
        *,
        transition_rows: list[dict[str, Any]],
    ) -> ActiveEpisodeCatalog:
        if not rows:
            raise EpisodeCatalogError("dream_episode_catalog_empty")

        episodes = tuple(
            sorted(
                (self._validated_episode(row) for row in rows),
                key=lambda item: item.episode_ref,
            )
        )
        self._validate_unique_identity(episodes)
        active = tuple(episode for episode in episodes if episode.runtime_status == "ACTIVE")
        if not active:
            raise EpisodeCatalogError("dream_active_episode_catalog_empty")

        entrypoints = tuple(episode for episode in active if episode.entrypoint)
        if not entrypoints:
            raise EpisodeCatalogError("dream_entry_episode_missing")

        transitions = tuple(self._validated_transition(row) for row in transition_rows)
        by_question = {episode.question_ref: episode for episode in active}
        ordered_active, ordered_entries, sequence_indexes = self._validate_graph(
            entries=entrypoints,
            by_question=by_question,
            transitions=transitions,
        )
        graph_payload = [
            {
                "episode_ref": episode.episode_ref,
                "episode_version": episode.episode_version,
                "question_ref": episode.question_ref,
                "contract": episode.model_dump(mode="json"),
            }
            for episode in ordered_active
        ]
        graph_payload.extend(
            {
                "transition": transition.model_dump(mode="json"),
            }
            for transition in sorted(
                transitions,
                key=lambda item: item.transition_ref,
            )
            if transition.runtime_status == "ACTIVE"
        )
        return ActiveEpisodeCatalog(
            episodes=episodes,
            transitions=transitions,
            active_episode_refs=tuple(item.episode_ref for item in ordered_active),
            entry_episode_ref=ordered_entries[0].episode_ref,
            entry_episode_refs=tuple(item.episode_ref for item in ordered_entries),
            question_sequence_indexes=sequence_indexes,
            graph_hash=content_hash(graph_payload),
        )

    def _validated_episode(self, row: dict[str, Any]) -> DreamEpisodeContract:
        try:
            episode = self._director.load_episode(
                payload=row["episode_contract_json"],
                expected_hash=row["episode_contract_hash"],
                question_ref=row["question_ref"],
            )
        except (KeyError, ValueError) as exc:
            raise EpisodeCatalogError(str(exc)) from exc

        persisted_identity = {
            "episode_ref": row.get("episode_ref"),
            "episode_version": row.get("episode_version"),
            "actor_ref": row.get("actor_ref"),
            "tree_ref": row.get("tree_ref"),
            "world_event_ref": row.get("world_event_ref"),
            "cutoff_tick": row.get("cutoff_tick"),
            "due_tick": row.get("due_tick"),
        }
        for field_name, persisted_value in persisted_identity.items():
            if persisted_value is not None and persisted_value != getattr(episode, field_name):
                raise EpisodeCatalogError(f"episode_{field_name}_column_mismatch")

        resolution_rule = row.get("resolution_rule_json")
        if resolution_rule is None or content_hash(resolution_rule) != episode.resolution_rule_hash:
            raise EpisodeCatalogError("episode_resolution_rule_hash_mismatch")
        try:
            validate_persisted_episode_admission(
                manifest_payload=row["admission_manifest_json"],
                manifest_hash=row["admission_manifest_hash"],
                episode=episode,
                persisted=row,
            )
        except (KeyError, EpisodeAdmissionError) as exc:
            raise EpisodeCatalogError(str(exc)) from exc
        return episode

    @staticmethod
    def _validated_transition(
        row: dict[str, Any],
    ) -> EpisodeTransitionContract:
        try:
            transition = EpisodeTransitionContract.model_validate(row["transition_json"])
        except (KeyError, ValueError) as exc:
            raise EpisodeCatalogError(str(exc)) from exc
        if content_hash(transition.model_dump(mode="json")) != row.get("transition_hash"):
            raise EpisodeCatalogError("episode_transition_hash_mismatch")
        for field_name in (
            "transition_ref",
            "transition_version",
            "from_question_ref",
            "to_question_ref",
            "label",
            "runtime_status",
        ):
            if row.get(field_name) != getattr(transition, field_name):
                raise EpisodeCatalogError(f"episode_transition_{field_name}_column_mismatch")
        return transition

    @staticmethod
    def _validate_unique_identity(
        episodes: tuple[DreamEpisodeContract, ...],
    ) -> None:
        for field_name in ("episode_ref", "question_ref", "content_key"):
            values = [getattr(episode, field_name) for episode in episodes]
            if len(values) != len(set(values)):
                raise EpisodeCatalogError(f"dream_active_episode_{field_name}_not_unique")

    @staticmethod
    def _validate_graph(
        *,
        entries: tuple[DreamEpisodeContract, ...],
        by_question: dict[str, DreamEpisodeContract],
        transitions: tuple[EpisodeTransitionContract, ...],
    ) -> tuple[
        tuple[DreamEpisodeContract, ...],
        tuple[DreamEpisodeContract, ...],
        tuple[tuple[str, int], ...],
    ]:
        active_transitions = tuple(
            transition for transition in transitions if transition.runtime_status == "ACTIVE"
        )
        from_refs = [transition.from_question_ref for transition in active_transitions]
        to_refs = [transition.to_question_ref for transition in active_transitions]
        if len(from_refs) != len(set(from_refs)):
            raise EpisodeCatalogError("dream_episode_transition_branching")
        if len(to_refs) != len(set(to_refs)):
            raise EpisodeCatalogError("dream_episode_transition_multiple_parents")
        if any(
            transition.from_question_ref not in by_question
            or transition.to_question_ref not in by_question
            for transition in active_transitions
        ):
            raise EpisodeCatalogError("dream_episode_transition_endpoint_inactive")
        incoming_refs = set(to_refs)
        entry_refs = {episode.question_ref for episode in entries}
        if entry_refs & incoming_refs:
            raise EpisodeCatalogError("dream_entry_episode_cannot_have_parent")
        non_entry_refs = set(by_question) - entry_refs
        if non_entry_refs != incoming_refs:
            raise EpisodeCatalogError("dream_non_entry_episode_parent_mismatch")

        by_source = {transition.from_question_ref: transition for transition in active_transitions}
        visited: set[str] = set()
        chains: list[tuple[DreamEpisodeContract, ...]] = []
        for entry in sorted(entries, key=lambda item: item.episode_ref):
            chain: list[DreamEpisodeContract] = []
            current = entry
            while True:
                if current.question_ref in visited:
                    raise EpisodeCatalogError("dream_episode_continuation_cycle")
                visited.add(current.question_ref)
                chain.append(current)
                transition = by_source.get(current.question_ref)
                if transition is None:
                    break
                next_episode = by_question.get(transition.to_question_ref)
                if next_episode is None:
                    raise EpisodeCatalogError("dream_episode_continuation_missing")
                if next_episode.entrypoint:
                    raise EpisodeCatalogError("dream_continuation_cannot_be_entrypoint")
                if (
                    next_episode.actor_ref != current.actor_ref
                    or next_episode.tree_ref != current.tree_ref
                ):
                    raise EpisodeCatalogError("dream_continuation_identity_mismatch")
                if next_episode.cutoff_tick < current.due_tick:
                    raise EpisodeCatalogError("dream_continuation_time_overlap")
                current = next_episode
            chains.append(tuple(chain))

        if visited != set(by_question):
            raise EpisodeCatalogError("dream_active_episode_unreachable")
        if len(active_transitions) != len(by_question) - len(entries):
            raise EpisodeCatalogError("dream_episode_transition_count_mismatch")
        ordered_chains = tuple(
            sorted(
                chains,
                key=lambda chain: (-len(chain), chain[0].episode_ref),
            )
        )
        ordered = tuple(episode for chain in ordered_chains for episode in chain)
        ordered_entries = tuple(chain[0] for chain in ordered_chains)
        sequence_indexes = tuple(
            (episode.question_ref, index)
            for chain in ordered_chains
            for index, episode in enumerate(chain)
        )
        return ordered, ordered_entries, sequence_indexes
