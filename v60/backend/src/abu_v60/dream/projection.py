from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

from abu_v60.dream.attention_follow_through import (
    DreamAttentionFollowThroughProjector,
)
from abu_v60.dream.catalog import DreamEpisodeCatalog, EpisodeCatalogError
from abu_v60.dream.errors import DreamStateError
from abu_v60.dream.persistence import DreamRepository
from abu_v60.dream.personal_journey import DreamPersonalJourneyService
from abu_v60.dream.return_attention import DreamReturnAttentionCoordinator
from abu_v60.experience import EpisodePublicProjection, ExperienceProjectionComposer
from abu_v60.game import DreamCommand, DreamGameplayDirector
from abu_v60.system_manifest import DREAM_GAME_ENGINE_VERSION, PRIMARY_WORLD_ID


class DreamSnapshotProjector:
    """Builds the public Dream snapshot from committed domain state."""

    def __init__(
        self,
        *,
        engine: Engine,
        director: DreamGameplayDirector,
        episodes: DreamEpisodeCatalog,
        experience: ExperienceProjectionComposer,
        public_projection: EpisodePublicProjection,
        repository: DreamRepository,
        return_attention: DreamReturnAttentionCoordinator,
        attention_follow_through: DreamAttentionFollowThroughProjector,
        personal_journey: DreamPersonalJourneyService,
    ) -> None:
        self._engine = engine
        self._director = director
        self._episodes = episodes
        self._experience = experience
        self._public_projection = public_projection
        self._repository = repository
        self._return_attention = return_attention
        self._attention_follow_through = attention_follow_through
        self._personal_journey = personal_journey

    def snapshot(self, *, account_ref: str) -> dict[str, Any]:
        with self._engine.connect() as connection:
            encounter = self._repository.current_encounter(
                connection,
                account_ref=account_ref,
                for_update=False,
            )
            if encounter is None:
                raise DreamStateError("encounter_not_created")
            root = (
                connection.execute(
                    text(
                        """
                        SELECT a.actor_ref, a.display_name, a.actor_kind,
                               a.timeline_json, a.state_json AS actor_state,
                               t.tree_ref, t.organs_json,
                               q.question_ref, q.question_version, q.prompt,
                               q.options_json, q.evidence_refs_json,
                               q.cutoff_tick, q.due_tick,
                               q.world_event_ref, q.resolution_rule_json,
                               q.organ_set_json, q.organ_set_hash,
                               q.episode_ref, q.episode_version,
                               q.episode_contract_json, q.episode_contract_hash,
                               future.event_json AS future_event_json,
                               lc.case_ref, lc.life_case_revision_ref,
                               cv.chart_version_ref, cv.pillars_json,
                               cs.scene_ref, cs.scene_json,
                               w.current_tick
                        FROM world.actors AS a
                        JOIN dream.life_trees AS t ON t.actor_ref = a.actor_ref
                        JOIN story.question_instances AS q
                          ON q.actor_ref = a.actor_ref
                        JOIN world.events AS future
                          ON future.world_event_ref = q.world_event_ref
                        JOIN mingli.life_case_revisions AS lc
                          ON lc.life_case_revision_ref = q.life_case_revision_ref
                        JOIN mingli.chart_versions AS cv
                          ON cv.chart_version_ref = lc.chart_version_ref
                        JOIN mingli.canonical_scenes AS cs
                          ON cs.scene_ref = t.scene_ref
                        JOIN world.worlds AS w ON w.world_ref = a.world_ref
                        WHERE a.actor_ref = :actor_ref
                          AND t.tree_ref = :tree_ref
                          AND q.question_ref = :question_ref
                        """
                    ),
                    {
                        "actor_ref": encounter["actor_ref"],
                        "tree_ref": encounter["tree_ref"],
                        "question_ref": encounter["question_ref"],
                    },
                )
                .mappings()
                .one()
            )
            catalog = self._catalog(connection)
            episode = catalog.for_question(root["question_ref"])
            runtime_metadata = self._experience.question_metadata(
                question_ref=root["question_ref"],
                runtime_metadata=episode.runtime_metadata.model_dump(mode="json"),
            )
            historical_evidence = (
                connection.execute(
                    text(
                        """
                        SELECT evidence_ref, evidence_json
                        FROM world.event_evidence
                        WHERE world_event_ref = :event_ref
                        ORDER BY evidence_ref
                        """
                    ),
                    {"event_ref": runtime_metadata["baseline_event_ref"]},
                )
                .mappings()
                .all()
            )
            structure_facts = (
                connection.execute(
                    text(
                        """
                        SELECT fact_ref, fact_type, subject_ref, object_ref,
                               authority, fact_json, source_ref
                        FROM mingli.facts
                        WHERE chart_version_ref = :chart_ref
                          AND fact_ref = ANY(:fact_refs)
                        ORDER BY fact_ref
                        """
                    ),
                    {
                        "chart_ref": root["chart_version_ref"],
                        "fact_refs": root["evidence_refs_json"],
                    },
                )
                .mappings()
                .all()
            )
            timing_sources = (
                connection.execute(
                    text(
                        """
                        SELECT vector_ref, case_ref, timing_profile_ref, vector_json
                        FROM mingli.timing_evidence_vectors
                        WHERE chart_version_ref = :chart_ref
                          AND vector_ref = ANY(:source_refs)
                        ORDER BY vector_ref
                        """
                    ),
                    {
                        "chart_ref": root["chart_version_ref"],
                        "source_refs": root["evidence_refs_json"],
                    },
                )
                .mappings()
                .all()
            )
            life_domain_sources = (
                connection.execute(
                    text(
                        """
                        SELECT vector_ref, case_ref, policy_ref, vector_json
                        FROM mingli.life_domain_evidence_vectors
                        WHERE chart_version_ref = :chart_ref
                          AND vector_ref = ANY(:source_refs)
                        ORDER BY vector_ref
                        """
                    ),
                    {
                        "chart_ref": root["chart_version_ref"],
                        "source_refs": root["evidence_refs_json"],
                    },
                )
                .mappings()
                .all()
            )
            human_seal = (
                connection.execute(
                    text(
                        """
                        SELECT answer_seal_ref, choice_id, sealed_at_tick
                        FROM dream.answer_seals
                        WHERE encounter_ref = :encounter_ref
                          AND actor_role = 'HUMAN'
                        """
                    ),
                    {"encounter_ref": encounter["encounter_ref"]},
                )
                .mappings()
                .one_or_none()
            )
            fruit = (
                connection.execute(
                    text(
                        """
                        SELECT fruit_ref, status, fruit_version, fruit_json
                        FROM dream.story_fruits
                        WHERE encounter_ref = :encounter_ref
                        """
                    ),
                    {"encounter_ref": encounter["encounter_ref"]},
                )
                .mappings()
                .one_or_none()
            )
            reveal = (
                connection.execute(
                    text(
                        """
                        SELECT reveal_ref, encounter_ref, world_event_ref,
                               result, reveal_json, reveal_hash
                        FROM dream.reveals
                        WHERE encounter_ref = :encounter_ref
                        """
                    ),
                    {"encounter_ref": encounter["encounter_ref"]},
                )
                .mappings()
                .one_or_none()
            )
            revealed_evidence = (
                connection.execute(
                    text(
                        """
                        SELECT evidence_ref, world_event_ref,
                               committed_at_tick, evidence_json, evidence_hash
                        FROM world.event_evidence
                        WHERE world_event_ref = :event_ref
                        ORDER BY evidence_ref
                        """
                    ),
                    {"event_ref": root["world_event_ref"]},
                )
                .mappings()
                .all()
                if reveal is not None
                else ()
            )
            completed_encounter_count = self._repository.completed_encounter_count(
                connection,
                account_ref=account_ref,
            )
            opening_attention = self._return_attention.opening_projection(
                connection,
                account_ref=account_ref,
                encounter_ref=str(encounter["encounter_ref"]),
            )
            attention_follow_through = (
                self._attention_follow_through.active_projection(
                    connection,
                    account_ref=account_ref,
                    encounter=encounter,
                    organ_set=dict(root["organ_set_json"]),
                    world_event_ref=str(root["world_event_ref"]),
                    reveal=(
                        dict(reveal)
                        if reveal is not None
                        else None
                    ),
                    revealed_evidence=tuple(
                        dict(item) for item in revealed_evidence
                    ),
                )
            )
            personal_journey = self._personal_journey.project_encounter(
                connection,
                account_ref=account_ref,
                encounter_ref=str(encounter["encounter_ref"]),
            )

        state = encounter["state_json"]
        answer_window_status = self._answer_window_status(
            root=root,
            state=state,
            human_seal=human_seal,
        )
        scene = self._director.scene(
            episode=episode,
            state=state,
            organs=root["organ_set_json"],
            encounter_completed=encounter["status"] == "COMPLETED",
            continuation_label=(
                continuation[1]
                if (continuation := catalog.next_episode(root["question_ref"]))
                else None
            ),
        )
        question = self._question_projection(
            root=root,
            runtime_metadata=runtime_metadata,
            question_visible=state["question_visible"],
            answer_window_status=answer_window_status,
        )
        reveal_payload = dict(reveal) if reveal is not None else None
        decision_refs = (
            [str(reveal_payload["reveal_json"]["decision_ref"])]
            if reveal_payload and reveal_payload["reveal_json"].get("decision_ref")
            else []
        )
        narrative_moment = episode.narrative.for_phase(scene.phase)
        context = self._experience.build_context(
            actor_name=root["display_name"],
            cutoff_tick=root["cutoff_tick"],
            current_tick=root["current_tick"],
            lineage={
                "encounter_ref": encounter["encounter_ref"],
                "correlation_id": encounter["correlation_id"],
                "causation_id": encounter["causation_id"],
                "actor_ref": root["actor_ref"],
                "tree_ref": root["tree_ref"],
                "world_ref": PRIMARY_WORLD_ID,
                "case_ref": root["case_ref"],
                "life_case_revision_ref": root["life_case_revision_ref"],
                "chart_version_ref": root["chart_version_ref"],
                "scene_ref": root["scene_ref"],
                "question_ref": root["question_ref"],
                "world_event_ref": root["world_event_ref"],
            },
            progress={
                key: state[key]
                for key in (
                    "observed_organs",
                    "question_visible",
                    "answer_sealed",
                    "world_settled",
                    "revealed",
                    "reconciled",
                )
            },
            narrative_scene_ref=episode.narrative.scene_ref,
            narrative_moment=narrative_moment.model_dump(mode="json"),
            pillars=root["pillars_json"],
            facts=(
                *structure_facts,
                *(
                    {
                        "fact_ref": item["vector_ref"],
                        "fact_type": "timing_snapshot",
                        "subject_ref": item["case_ref"],
                        "object_ref": None,
                        "authority": "SYSTEM_DETERMINISTIC_BOUNDED",
                        "fact_json": {
                            "analysis_date": item["vector_json"]["analysis_date"],
                            "coordinates": item["vector_json"]["coordinates"],
                            "relation_evidence": item["vector_json"]["relation_evidence"],
                            "activation_status": item["vector_json"]["activation_status"],
                            "effect_status": item["vector_json"]["effect_status"],
                            "closed_world_validation": (
                                "DOES_NOT_PROVE_MINGLI_EFFECTIVENESS"
                            ),
                        },
                        "source_ref": item["timing_profile_ref"],
                    }
                    for item in timing_sources
                ),
                *(
                    {
                        "fact_ref": item["vector_ref"],
                        "fact_type": "life_domain_attention",
                        "subject_ref": item["case_ref"],
                        "object_ref": None,
                        "authority": "SYSTEM_DETERMINISTIC_BOUNDED",
                        "fact_json": {
                            "evidence_semantics": item["vector_json"][
                                "evidence_semantics"
                            ],
                            "observations": item["vector_json"]["observations"],
                            "outcome_status": item["vector_json"]["outcome_status"],
                            "probability_status": item["vector_json"][
                                "probability_status"
                            ],
                            "professional_verdict_allowed": item["vector_json"][
                                "professional_verdict_allowed"
                            ],
                        },
                        "source_ref": item["policy_ref"],
                    }
                    for item in life_domain_sources
                ),
            ),
            baseline_evidence=historical_evidence,
            revealed_evidence=[
                {
                    "evidence_ref": item["evidence_ref"],
                    "summary": item["evidence_json"]["summary"],
                    "committed_at_tick": item["committed_at_tick"],
                    "epistemic_role": "OUTCOME_EVIDENCE",
                }
                for item in revealed_evidence
            ],
            decision_refs=decision_refs,
        )
        projections = self._experience.compose(context=context)
        actor_projection = self._public_projection.actor(
            episode=episode,
            phase=scene.phase,
            timeline=root["timeline_json"],
            current_state=root["actor_state"],
        )
        tree_projection = self._public_projection.tree(
            episode=episode,
            phase=scene.phase,
            organ_projection_hash=root["organ_set_hash"],
            phenotype=root["scene_json"]["tree_phenotype"],
        )
        return {
            "encounter": {
                "encounter_ref": encounter["encounter_ref"],
                "status": encounter["status"],
                "version": encounter["version"],
                "correlation_id": encounter["correlation_id"],
                "causation_id": encounter["causation_id"],
                "chapter": scene.chapter.value,
                "state": state,
            },
            "world": {
                "world_ref": PRIMARY_WORLD_ID,
                "current_tick": root["current_tick"],
            },
            "game": {
                "engine_version": DREAM_GAME_ENGINE_VERSION,
                "gameplay_id": scene.gameplay_id,
                "scene_id": scene.scene_id,
                "scene_version": scene.scene_version,
                "layout_key": scene.layout_key,
                "episode_ref": scene.episode_ref,
                "episode_version": scene.episode_version,
                "content_key": scene.content_key,
                "phase": scene.phase.value,
                "available_commands": (
                    [DreamCommand.RETURN_TO_GROVE.value]
                    if answer_window_status == "CLOSED_UNSEALED"
                    else [
                        command.value
                        for command in scene.available_commands
                    ]
                ),
            },
            "actor": {
                "actor_ref": root["actor_ref"],
                "display_name": root["display_name"],
                "actor_kind": root["actor_kind"],
                **actor_projection,
            },
            "tree": {
                "tree_ref": root["tree_ref"],
                "organs": list(scene.organs),
                **tree_projection,
            },
            "question": question,
            "human_seal": dict(human_seal) if human_seal is not None else None,
            "fruit": dict(fruit) if fruit is not None else None,
            "reveal": reveal_payload,
            "public_evidence": [
                {
                    "evidence_ref": item["evidence_ref"],
                    **item["evidence_json"],
                }
                for item in historical_evidence
            ]
            + [
                {
                    "evidence_ref": item["evidence_ref"],
                    "summary": item["evidence_json"]["summary"],
                    "observed_at_tick": item["committed_at_tick"],
                    "epistemic_role": "OUTCOME_EVIDENCE",
                }
                for item in revealed_evidence
            ],
            "context": context.public_manifest(),
            "projections": projections,
            "lineage": {
                "life_case_revision_ref": root["life_case_revision_ref"],
                "chart_version_ref": root["chart_version_ref"],
                "scene_ref": root["scene_ref"],
                "question_ref": root["question_ref"],
                "world_event_ref": root["world_event_ref"],
                "evidence_refs": [item["evidence_ref"] for item in historical_evidence],
                "revealed_evidence_refs": [item["evidence_ref"] for item in revealed_evidence],
                "decision_refs": decision_refs,
            },
            "continuation": {
                "available": scene.continuation_available,
                "label": scene.continuation_label,
                "completed_encounter_count": completed_encounter_count,
            },
            "opening_attention": (
                opening_attention.model_dump(mode="json")
                if opening_attention is not None
                else None
            ),
            "attention_follow_through": (
                attention_follow_through.model_dump(mode="json")
                if attention_follow_through is not None
                else None
            ),
            "personal_journey": (
                personal_journey.model_dump(mode="json")
                if personal_journey is not None
                else None
            ),
        }

    def _catalog(self, connection: Any) -> Any:
        try:
            return self._episodes.load(connection)
        except EpisodeCatalogError as exc:
            raise DreamStateError(str(exc)) from exc

    @staticmethod
    def _question_projection(
        *,
        root: Any,
        runtime_metadata: dict[str, Any],
        question_visible: bool,
        answer_window_status: str,
    ) -> dict[str, Any] | None:
        if not question_visible:
            return None
        return {
            "question_ref": root["question_ref"],
            "question_version": root["question_version"],
            "prompt": root["prompt"],
            "options": [
                {"choice_id": item["choice_id"], "label": item["label"]}
                for item in root["options_json"]
            ],
            "cutoff_tick": root["cutoff_tick"],
            "due_tick": root["due_tick"],
            "flower_name": runtime_metadata["flower_name"],
            "answer_window_status": answer_window_status,
        }

    @staticmethod
    def _answer_window_status(
        *,
        root: Any,
        state: dict[str, Any],
        human_seal: Any,
    ) -> str:
        if human_seal is not None or state.get("answer_sealed") is True:
            return "SEALED"
        if (
            state.get("question_visible") is True
            and root["future_event_json"].get("opportunity_cycle_ref")
            is not None
            and int(root["current_tick"]) >= int(root["due_tick"])
        ):
            return "CLOSED_UNSEALED"
        return "OPEN"
