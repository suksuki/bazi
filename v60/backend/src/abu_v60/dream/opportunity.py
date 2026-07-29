from __future__ import annotations

from typing import Any

from sqlalchemy import text

from abu_v60.game import (
    DreamEpisodeContract,
    DreamEpisodeDefinition,
    QuestionChoiceDefinition,
    ResolutionRuleDefinition,
    SealedOutcomeDefinition,
    TreeOrganDefinition,
)
from abu_v60.provenance import stable_ref
from abu_v60.story import StoryEpisodeAdmissionService
from abu_v60.world import (
    WorldContinuityEngine,
    WorldEventAdmissionService,
    WorldEventDefinition,
    WorldEventStatus,
)

OPPORTUNITY_WINDOW_TICKS = 5
OPPORTUNITY_REUSE_MINIMUM_TICKS = 2


class DreamOpportunityError(ValueError):
    pass


class DreamOpportunityMaterializer:
    """Bind an approved Episode template to a fresh authoritative world window."""

    def __init__(
        self,
        *,
        world: WorldContinuityEngine,
        story_admission: StoryEpisodeAdmissionService | None = None,
        event_admission: WorldEventAdmissionService | None = None,
    ) -> None:
        self._world = world
        self._story_admission = story_admission or StoryEpisodeAdmissionService()
        self._event_admission = event_admission or WorldEventAdmissionService()

    def materialize(
        self,
        connection: Any,
        *,
        source_question_ref: str,
    ) -> DreamEpisodeContract:
        source = self._source(connection, source_question_ref=source_question_ref)
        source_episode = DreamEpisodeContract.model_validate(
            source["episode_contract_json"]
        )
        if source["event_json"].get("source_question_ref") is not None:
            raise DreamOpportunityError("dream_opportunity_source_must_be_template")
        current_tick = self._world.current_tick(connection)
        reusable = self._reusable(
            connection,
            source_question_ref=source_question_ref,
            current_tick=current_tick,
        )
        if reusable is not None:
            return reusable

        cutoff_tick = current_tick
        due_tick = cutoff_tick + OPPORTUNITY_WINDOW_TICKS
        cycle_ref = stable_ref(
            "v60-dream-opportunity-cycle",
            {
                "source_question_ref": source_question_ref,
                "cutoff_tick": cutoff_tick,
            },
        )
        baseline_event_ref = stable_ref(
            "v60-dream-opportunity-baseline",
            cycle_ref,
        )
        world_event_ref = stable_ref(
            "v60-dream-opportunity-outcome",
            cycle_ref,
        )
        question_ref = stable_ref("v60-dream-opportunity-question", cycle_ref)
        episode_ref = stable_ref("v60-dream-opportunity-episode", cycle_ref)

        baseline_evidence, baseline_ref_map = self._clone_baseline_evidence(
            connection,
            source_event_ref=source_episode.baseline_event_ref,
            cycle_ref=cycle_ref,
            cutoff_tick=cutoff_tick,
        )
        baseline_event = self._event(
            connection,
            event_ref=source_episode.baseline_event_ref,
        )
        self._world.commit_historical_event(
            connection=connection,
            event_ref=baseline_event_ref,
            actor_ref=source_episode.actor_ref,
            event_type=f"{baseline_event['event_type']}_OPPORTUNITY",
            summary=str(baseline_event["event_json"]["summary"]),
            caused_by_event_ref=cycle_ref,
            evidence=baseline_evidence,
            actor_state_delta={},
            world_ref=str(baseline_event["world_ref"]),
        )

        outcome_event = self._event(
            connection,
            event_ref=source_episode.world_event_ref,
        )
        sealed_outcome, future_ref_map = self._clone_sealed_outcome(
            source=outcome_event["sealed_outcome_json"],
            cycle_ref=cycle_ref,
        )
        event_payload = {
            **dict(outcome_event["event_json"]),
            "due_tick": due_tick,
            "source_question_ref": source_episode.question_ref,
            "source_world_event_ref": source_episode.world_event_ref,
            "opportunity_cycle_ref": cycle_ref,
            "caused_by_event_ref": baseline_event_ref,
            "baseline_evidence_lineage": {
                source_ref: cloned_ref
                for source_ref, cloned_ref in sorted(baseline_ref_map.items())
            },
            "tree_projection_scope": "ENCOUNTER",
        }
        self._event_admission.admit(
            connection,
            definition=WorldEventDefinition(
                world_event_ref=world_event_ref,
                world_ref=str(outcome_event["world_ref"]),
                actor_ref=source_episode.actor_ref,
                event_type=f"{outcome_event['event_type']}_OPPORTUNITY",
                due_tick=due_tick,
                initial_status=WorldEventStatus.SCHEDULED,
                event_payload=event_payload,
                sealed_outcome=sealed_outcome.model_dump(mode="json"),
            ),
        )

        definition = self._definition(
            source=source,
            source_episode=source_episode,
            cycle_ref=cycle_ref,
            baseline_event_ref=baseline_event_ref,
            world_event_ref=world_event_ref,
            question_ref=question_ref,
            episode_ref=episode_ref,
            cutoff_tick=cutoff_tick,
            due_tick=due_tick,
            baseline_evidence=baseline_evidence,
            baseline_ref_map=baseline_ref_map,
            future_ref_map=future_ref_map,
            sealed_outcome=sealed_outcome,
            event_type=f"{outcome_event['event_type']}_OPPORTUNITY",
            event_summary=str(outcome_event["event_json"]["summary"]),
        )
        self._story_admission.admit(
            connection,
            life_case_revision_ref=str(source["life_case_revision_ref"]),
            definition=definition,
        )
        return definition.runtime

    @staticmethod
    def source_question_ref(
        connection: Any,
        *,
        question_ref: str,
    ) -> str:
        return str(
            connection.execute(
                text(
                    """
                    SELECT COALESCE(
                        event.event_json ->> 'source_question_ref',
                        question.question_ref
                    )
                    FROM story.question_instances AS question
                    JOIN world.events AS event
                      ON event.world_event_ref = question.world_event_ref
                    WHERE question.question_ref = :question_ref
                    """
                ),
                {"question_ref": question_ref},
            ).scalar_one()
        )

    @staticmethod
    def _source(connection: Any, *, source_question_ref: str) -> dict[str, Any]:
        row = (
            connection.execute(
                text(
                    """
                    SELECT question.*, event.event_type, event.event_json,
                           event.sealed_outcome_json
                    FROM story.question_instances AS question
                    JOIN world.events AS event
                      ON event.world_event_ref = question.world_event_ref
                    WHERE question.question_ref = :question_ref
                    """
                ),
                {"question_ref": source_question_ref},
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise DreamOpportunityError("dream_opportunity_source_missing")
        return dict(row)

    @staticmethod
    def _event(connection: Any, *, event_ref: str) -> dict[str, Any]:
        row = (
            connection.execute(
                text(
                    """
                    SELECT world_event_ref, world_ref, actor_ref, event_type,
                           due_tick, status, event_json, sealed_outcome_json
                    FROM world.events
                    WHERE world_event_ref = :event_ref
                    """
                ),
                {"event_ref": event_ref},
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise DreamOpportunityError("dream_opportunity_event_missing")
        return dict(row)

    @staticmethod
    def _reusable(
        connection: Any,
        *,
        source_question_ref: str,
        current_tick: int,
    ) -> DreamEpisodeContract | None:
        row = (
            connection.execute(
                text(
                    """
                    SELECT question.episode_contract_json
                    FROM story.question_instances AS question
                    JOIN world.events AS event
                      ON event.world_event_ref = question.world_event_ref
                    WHERE event.event_json
                              ->> 'source_question_ref' = :source_question_ref
                      AND event.status = 'SCHEDULED'
                      AND question.due_tick >= :minimum_due_tick
                    ORDER BY question.cutoff_tick DESC, question.question_ref
                    LIMIT 1
                    """
                ),
                {
                    "source_question_ref": source_question_ref,
                    "minimum_due_tick": (
                        current_tick + OPPORTUNITY_REUSE_MINIMUM_TICKS
                    ),
                },
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        return DreamEpisodeContract.model_validate(row["episode_contract_json"])

    @staticmethod
    def _clone_baseline_evidence(
        connection: Any,
        *,
        source_event_ref: str,
        cycle_ref: str,
        cutoff_tick: int,
    ) -> tuple[tuple[dict[str, Any], ...], dict[str, str]]:
        rows = (
            connection.execute(
                text(
                    """
                    SELECT evidence_ref, evidence_json
                    FROM world.event_evidence
                    WHERE world_event_ref = :event_ref
                    ORDER BY evidence_ref
                    """
                ),
                {"event_ref": source_event_ref},
            )
            .mappings()
            .all()
        )
        if not rows:
            raise DreamOpportunityError("dream_opportunity_baseline_evidence_missing")
        evidence: list[dict[str, Any]] = []
        ref_map: dict[str, str] = {}
        for row in rows:
            source_ref = str(row["evidence_ref"])
            evidence_ref = stable_ref(
                "v60-dream-opportunity-baseline-evidence",
                {"cycle_ref": cycle_ref, "source_evidence_ref": source_ref},
            )
            ref_map[source_ref] = evidence_ref
            evidence.append(
                {
                    "evidence_ref": evidence_ref,
                    "summary": str(row["evidence_json"]["summary"]),
                    "observed_at_tick": cutoff_tick,
                    "epistemic_role": "DECISION_BASELINE_NO_CREDIT",
                }
            )
        return tuple(evidence), ref_map

    @staticmethod
    def _clone_sealed_outcome(
        *,
        source: dict[str, Any],
        cycle_ref: str,
    ) -> tuple[SealedOutcomeDefinition, dict[str, str]]:
        ref_map: dict[str, str] = {}
        evidence: list[dict[str, Any]] = []
        for item in source["evidence"]:
            source_ref = str(item["evidence_ref"])
            evidence_ref = stable_ref(
                "v60-dream-opportunity-outcome-evidence",
                {"cycle_ref": cycle_ref, "source_evidence_ref": source_ref},
            )
            ref_map[source_ref] = evidence_ref
            evidence.append({**dict(item), "evidence_ref": evidence_ref})
        sealed_outcome = SealedOutcomeDefinition.model_validate(
            {
                **source,
                "outcome_id": stable_ref(
                    "v60-dream-opportunity-outcome-id",
                    {"cycle_ref": cycle_ref, "source_outcome_id": source["outcome_id"]},
                ),
                "evidence": evidence,
            }
        )
        return sealed_outcome, ref_map

    @staticmethod
    def _definition(
        *,
        source: dict[str, Any],
        source_episode: DreamEpisodeContract,
        cycle_ref: str,
        baseline_event_ref: str,
        world_event_ref: str,
        question_ref: str,
        episode_ref: str,
        cutoff_tick: int,
        due_tick: int,
        baseline_evidence: tuple[dict[str, Any], ...],
        baseline_ref_map: dict[str, str],
        future_ref_map: dict[str, str],
        sealed_outcome: SealedOutcomeDefinition,
        event_type: str,
        event_summary: str,
    ) -> DreamEpisodeDefinition:
        runtime_metadata = source_episode.runtime_metadata.model_copy(
            update={"baseline_event_ref": baseline_event_ref}
        )
        narrative = source_episode.narrative.model_copy(
            update={
                "moments": tuple(
                    moment.model_copy(
                        update={
                            "content_key": (
                                f"{moment.content_key}.opportunity."
                                f"{cycle_ref.rsplit('-', 1)[-1]}"
                            )
                        }
                    )
                    for moment in source_episode.narrative.moments
                )
            }
        )
        episode = source_episode.model_copy(
            update={
                "episode_ref": episode_ref,
                "episode_version": 1,
                "content_key": f"{source_episode.content_key}.opportunity.{cycle_ref}",
                "question_ref": question_ref,
                "baseline_event_ref": baseline_event_ref,
                "world_event_ref": world_event_ref,
                "cutoff_tick": cutoff_tick,
                "due_tick": due_tick,
                "runtime_metadata": runtime_metadata,
                "narrative": narrative,
                "continuation_question_ref": None,
                "continuation_label": None,
                "entry_world_event": None,
                "tree_state_on_entry": None,
            }
        )
        source_organs = {
            key: TreeOrganDefinition.model_validate(value)
            for key, value in source["organ_set_json"].items()
        }
        source_map = {
            **baseline_ref_map,
            **future_ref_map,
            source_episode.question_ref: question_ref,
            source_episode.world_event_ref: world_event_ref,
        }
        organs = {
            key: organ.model_copy(
                update={
                    "organ_ref": stable_ref(
                        "v60-dream-opportunity-organ",
                        {"cycle_ref": cycle_ref, "source_organ_ref": organ.organ_ref},
                    ),
                    "source_refs": tuple(
                        source_map.get(source_ref, source_ref)
                        for source_ref in organ.source_refs
                    ),
                }
            )
            for key, organ in source_organs.items()
        }
        rule = ResolutionRuleDefinition(
            **dict(source["resolution_rule_json"]),
            baseline_event_ref=baseline_event_ref,
            npc_choice_id=runtime_metadata.npc_choice_id,
            flower_name=runtime_metadata.flower_name,
            fruit_name=runtime_metadata.fruit_name,
            return_label=runtime_metadata.return_label,
            theater_scene_ref=narrative.scene_ref,
            theater_beat=narrative.for_phase("QUESTION_OPEN").theater_beat,
        )
        return DreamEpisodeDefinition(
            runtime=episode,
            actor_ref=episode.actor_ref,
            tree_ref=episode.tree_ref,
            question_version=int(source["question_version"]) + 1,
            prompt=str(source["prompt"]),
            options=tuple(
                QuestionChoiceDefinition.model_validate(item)
                for item in source["options_json"]
            ),
            baseline_evidence=baseline_evidence,
            resolution_rule=rule,
            sealed_outcome=sealed_outcome,
            world_event_type=event_type,
            world_event_summary=event_summary,
            organ_set=organs,
        )
