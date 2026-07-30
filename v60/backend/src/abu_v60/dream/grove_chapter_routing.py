from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import text

from abu_v60.dream.catalog import ActiveEpisodeCatalog
from abu_v60.dream.errors import DreamStateError
from abu_v60.dream.grove import GroveCandidateDefinition
from abu_v60.dream.grove_candidate_lineage import (
    candidate_source_lineage_is_valid,
)
from abu_v60.game import DreamEpisodeContract, DreamPhase
from abu_v60.provenance import content_hash
from abu_v60.story import EpisodeTransitionContract

DREAM_GROVE_CHAPTER_ROUTE_VERSION = "v60.dream-grove-chapter-route.001"


class DreamGroveChapterRoute(BaseModel):
    """Public, read-only proof of one candidate's canonical chapter frontier."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_version: Literal["v60.dream-grove-chapter-route.001"] = (
        DREAM_GROVE_CHAPTER_ROUTE_VERSION
    )
    route_hash: str = Field(min_length=64, max_length=64)
    status: Literal["AVAILABLE", "STORY_CURRENTLY_COMPLETE"]
    basis: Literal[
        "ENTRYPOINT",
        "CANONICAL_TRANSITION",
        "TERMINAL_CHAPTER",
    ]
    candidate_ref: str = Field(min_length=1)
    candidate_hash: str = Field(min_length=64, max_length=64)
    tree_ref: str = Field(min_length=1)
    previous_source_question_ref: str | None
    previous_source_episode_ref: str | None
    target_source_question_ref: str = Field(min_length=1)
    target_source_episode_ref: str = Field(min_length=1)
    target_source_episode_version: int = Field(ge=1)
    target_chapter: Literal["FIRST_VISIT", "RETURN_VISIT"]
    transition_ref: str | None
    transition_hash: str | None = Field(
        default=None,
        min_length=64,
        max_length=64,
    )
    title: str = Field(min_length=1)
    premise: str = Field(min_length=1)
    chapter_label: str = Field(min_length=1)
    routing_authority: Literal["CANONICAL_EPISODE_GRAPH"]
    attention_routing_allowed: Literal[False]
    attention_ref_used: Literal[False]
    tree_candidate_set_or_order_changed: Literal[False]
    question_changed: Literal[False]
    answer_changed: Literal[False]
    npc_choice_changed: Literal[False]
    outcome_changed: Literal[False]
    read_only: Literal[True]

    @model_validator(mode="after")
    def route_identity_is_valid(self) -> DreamGroveChapterRoute:
        identity = self.model_dump(mode="json", exclude={"route_hash"})
        if content_hash(identity) != self.route_hash:
            raise ValueError("dream_grove_chapter_route_hash_mismatch")
        if (self.transition_ref is None) != (self.transition_hash is None):
            raise ValueError(
                "dream_grove_chapter_route_transition_identity_incomplete"
            )
        if self.basis == "ENTRYPOINT" and (
            self.previous_source_question_ref is not None
            or self.previous_source_episode_ref is not None
            or self.transition_ref is not None
        ):
            raise ValueError(
                "dream_grove_chapter_route_entrypoint_lineage_invalid"
            )
        if self.basis == "CANONICAL_TRANSITION" and (
            self.previous_source_question_ref is None
            or self.previous_source_episode_ref is None
            or self.transition_ref is None
        ):
            raise ValueError(
                "dream_grove_chapter_route_transition_lineage_invalid"
            )
        if (
            self.status == "STORY_CURRENTLY_COMPLETE"
            and self.basis != "TERMINAL_CHAPTER"
        ):
            raise ValueError(
                "dream_grove_chapter_route_terminal_status_invalid"
            )
        if self.status == "AVAILABLE" and self.basis == "TERMINAL_CHAPTER":
            raise ValueError(
                "dream_grove_chapter_route_available_basis_invalid"
            )
        if self.basis == "TERMINAL_CHAPTER" and (
            self.previous_source_question_ref
            != self.target_source_question_ref
            or self.previous_source_episode_ref
            != self.target_source_episode_ref
            or self.transition_ref is not None
        ):
            raise ValueError(
                "dream_grove_chapter_route_terminal_lineage_invalid"
            )
        return self

    @classmethod
    def issue(
        cls,
        *,
        status: Literal["AVAILABLE", "STORY_CURRENTLY_COMPLETE"],
        basis: Literal[
            "ENTRYPOINT",
            "CANONICAL_TRANSITION",
            "TERMINAL_CHAPTER",
        ],
        candidate: GroveCandidateDefinition,
        previous: DreamEpisodeContract | None,
        target: DreamEpisodeContract,
        transition: EpisodeTransitionContract | None,
        chapter_label: str,
    ) -> DreamGroveChapterRoute:
        identity = {
            "contract_version": DREAM_GROVE_CHAPTER_ROUTE_VERSION,
            "status": status,
            "basis": basis,
            "candidate_ref": candidate.candidate_ref,
            "candidate_hash": candidate.candidate_hash,
            "tree_ref": candidate.tree_ref,
            "previous_source_question_ref": (
                previous.question_ref if previous is not None else None
            ),
            "previous_source_episode_ref": (
                previous.episode_ref if previous is not None else None
            ),
            "target_source_question_ref": target.question_ref,
            "target_source_episode_ref": target.episode_ref,
            "target_source_episode_version": target.episode_version,
            "target_chapter": target.chapter.value,
            "transition_ref": (
                transition.transition_ref if transition is not None else None
            ),
            "transition_hash": (
                content_hash(transition.model_dump(mode="json"))
                if transition is not None
                else None
            ),
            "title": target.narrative.for_phase(DreamPhase.OBSERVING).title,
            "premise": target.narrative.for_phase(
                DreamPhase.OBSERVING
            ).theater_beat,
            "chapter_label": chapter_label,
            "routing_authority": "CANONICAL_EPISODE_GRAPH",
            "attention_routing_allowed": False,
            "attention_ref_used": False,
            "tree_candidate_set_or_order_changed": False,
            "question_changed": False,
            "answer_changed": False,
            "npc_choice_changed": False,
            "outcome_changed": False,
            "read_only": True,
        }
        return cls(
            route_hash=content_hash(identity),
            **identity,
        )


@dataclass(frozen=True, slots=True)
class DreamGroveChapterResolution:
    route: DreamGroveChapterRoute
    target_episode: DreamEpisodeContract
    preceding_world_event_ref: str | None


@dataclass(frozen=True, slots=True)
class _CompletedChapter:
    source_question_ref: str
    outcome_world_event_ref: str


class DreamGroveChapterRouter:
    """Resolve a Grove root through canonical graph and account-owned history."""

    @staticmethod
    def lock_account(connection: Any, *, account_ref: str) -> None:
        locked = connection.execute(
            text(
                """
                SELECT account_ref
                FROM identity.accounts
                WHERE account_ref = :account_ref
                FOR UPDATE
                """
            ),
            {"account_ref": account_ref},
        ).scalar_one_or_none()
        if locked is None:
            raise DreamStateError("dream_grove_account_not_found")

    def resolve(
        self,
        connection: Any,
        *,
        account_ref: str,
        candidate: GroveCandidateDefinition,
        catalog: ActiveEpisodeCatalog,
    ) -> DreamGroveChapterResolution:
        chain = catalog.chain_from_entry(candidate.question_ref)
        root = chain[0]
        if (
            root.actor_ref != candidate.actor_ref
            or root.tree_ref != candidate.tree_ref
        ):
            raise DreamStateError("dream_grove_candidate_lineage_mismatch")
        completed = self._completed_chapters(
            connection,
            account_ref=account_ref,
            candidate=candidate,
            catalog=catalog,
        )
        completed_by_source = {
            item.source_question_ref: item for item in completed
        }
        chain_refs = tuple(episode.question_ref for episode in chain)
        completed_refs = set(completed_by_source)
        if not completed_refs.issubset(chain_refs):
            raise DreamStateError("dream_grove_chapter_history_outside_chain")

        first_missing_index = next(
            (
                index
                for index, question_ref in enumerate(chain_refs)
                if question_ref not in completed_refs
            ),
            None,
        )
        if first_missing_index is not None and any(
            question_ref in completed_refs
            for question_ref in chain_refs[first_missing_index + 1 :]
        ):
            raise DreamStateError("dream_grove_chapter_history_not_prefix")

        if first_missing_index is None:
            target_index = len(chain) - 1
            status: Literal[
                "AVAILABLE",
                "STORY_CURRENTLY_COMPLETE",
            ] = "STORY_CURRENTLY_COMPLETE"
            basis: Literal[
                "ENTRYPOINT",
                "CANONICAL_TRANSITION",
                "TERMINAL_CHAPTER",
            ] = "TERMINAL_CHAPTER"
        else:
            target_index = first_missing_index
            status = "AVAILABLE"
            basis = (
                "ENTRYPOINT"
                if target_index == 0
                else "CANONICAL_TRANSITION"
            )

        target = chain[target_index]
        if status == "STORY_CURRENTLY_COMPLETE":
            previous = target
            transition = None
        else:
            previous = chain[target_index - 1] if target_index > 0 else None
            transition = (
                catalog.transition_after(previous.question_ref)
                if previous is not None
                else None
            )
        if transition is not None and (
            transition.to_question_ref != target.question_ref
        ):
            raise DreamStateError("dream_grove_chapter_transition_mismatch")
        preceding_world_event_ref = (
            completed_by_source[previous.question_ref].outcome_world_event_ref
            if status == "AVAILABLE" and previous is not None
            else (
                completed_by_source[target.question_ref].outcome_world_event_ref
                if status == "STORY_CURRENTLY_COMPLETE"
                else None
            )
        )
        route = DreamGroveChapterRoute.issue(
            status=status,
            basis=basis,
            candidate=candidate,
            previous=previous,
            target=target,
            transition=transition,
            chapter_label=self._chapter_label(
                status=status,
                target_index=target_index,
                transition=transition,
            ),
        )
        return DreamGroveChapterResolution(
            route=route,
            target_episode=target,
            preceding_world_event_ref=preceding_world_event_ref,
        )

    @staticmethod
    def _chapter_label(
        *,
        status: Literal["AVAILABLE", "STORY_CURRENTLY_COMPLETE"],
        target_index: int,
        transition: EpisodeTransitionContract | None,
    ) -> str:
        if status == "STORY_CURRENTLY_COMPLETE":
            return "这一段暂告一段落 · 等待新章"
        if target_index == 0:
            return "第一章"
        if transition is None:
            raise DreamStateError("dream_grove_chapter_transition_missing")
        return transition.label

    @staticmethod
    def _completed_chapters(
        connection: Any,
        *,
        account_ref: str,
        candidate: GroveCandidateDefinition,
        catalog: ActiveEpisodeCatalog,
    ) -> tuple[_CompletedChapter, ...]:
        rows = (
            connection.execute(
                text(
                    """
                    SELECT encounter.encounter_ref,
                           question.world_event_ref
                               AS outcome_world_event_ref,
                           COALESCE(
                               event.event_json ->> 'source_question_ref',
                               question.question_ref
                           ) AS source_question_ref,
                           event.event_json
                               ->> 'source_candidate_ref'
                               AS source_candidate_ref,
                           event.event_json
                    FROM dream.encounters AS encounter
                    JOIN story.question_instances AS question
                      ON question.question_ref = encounter.question_ref
                    JOIN world.events AS event
                      ON event.world_event_ref = question.world_event_ref
                    JOIN dream.reveals AS reveal
                      ON reveal.encounter_ref = encounter.encounter_ref
                     AND reveal.world_event_ref = question.world_event_ref
                    WHERE encounter.viewer_account_ref = :account_ref
                      AND encounter.actor_ref = :actor_ref
                      AND encounter.tree_ref = :tree_ref
                      AND encounter.status = 'COMPLETED'
                      AND event.status = 'SETTLED'
                      AND encounter.state_json @>
                          '{"reconciled": true,
                            "departed_to_grove": true}'::jsonb
                    ORDER BY encounter.updated_at DESC,
                             encounter.encounter_ref DESC
                    """
                ),
                {
                    "account_ref": account_ref,
                    "actor_ref": candidate.actor_ref,
                    "tree_ref": candidate.tree_ref,
                },
            )
            .mappings()
            .all()
        )
        completed: dict[str, _CompletedChapter] = {}
        for row in rows:
            source_candidate_ref = row["source_candidate_ref"]
            if (
                source_candidate_ref is not None
                and source_candidate_ref != candidate.candidate_ref
            ):
                raise DreamStateError(
                    "dream_grove_chapter_history_candidate_mismatch"
                )
            source_question_ref = str(row["source_question_ref"])
            if not candidate_source_lineage_is_valid(
                catalog=catalog,
                candidate=candidate,
                source_question_ref=source_question_ref,
                event_payload=dict(row["event_json"]),
            ):
                raise DreamStateError(
                    "dream_grove_chapter_history_lineage_invalid"
                )
            completed.setdefault(
                source_question_ref,
                _CompletedChapter(
                    source_question_ref=source_question_ref,
                    outcome_world_event_ref=str(
                        row["outcome_world_event_ref"]
                    ),
                ),
            )
        return tuple(completed.values())
