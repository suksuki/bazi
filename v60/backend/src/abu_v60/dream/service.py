from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

from abu_v60.decision import (
    CognitiveDecisionLedger,
    EvidenceReconciliationEngine,
)
from abu_v60.dream.catalog import (
    ActiveEpisodeCatalog,
    DreamEpisodeCatalog,
    EpisodeCatalogError,
)
from abu_v60.dream.command_guard import DreamCommandGuard
from abu_v60.dream.errors import DreamStateError
from abu_v60.dream.grove import (
    DREAM_GROVE_VERSION,
    DreamGroveError,
    DreamGroveRepository,
)
from abu_v60.dream.grove_selection import DreamGroveEncounterSelector
from abu_v60.dream.opportunity import DreamOpportunityMaterializer
from abu_v60.dream.outcomes import DreamOutcomeCoordinator
from abu_v60.dream.persistence import DreamRepository
from abu_v60.dream.projection import DreamSnapshotProjector
from abu_v60.dream.return_echo import DreamReturnEchoProjector
from abu_v60.experience import EpisodePublicProjection, ExperienceProjectionComposer
from abu_v60.game import (
    DreamCommand,
    DreamCommandEnvelope,
    DreamGameEngine,
    DreamGameplayDirector,
    GameRuleError,
)
from abu_v60.provenance import canonical_json, content_hash, stable_ref
from abu_v60.world.service import WorldContinuityEngine


class DreamService:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._game = DreamGameEngine()
        self._director = DreamGameplayDirector(self._game)
        self._episodes = DreamEpisodeCatalog(self._director)
        self._command_guard = DreamCommandGuard(
            game=self._game,
            catalog_loader=self._catalog,
        )
        self._decisions = CognitiveDecisionLedger()
        self._world = WorldContinuityEngine(self._decisions)
        self._repository = DreamRepository()
        self._grove = DreamGroveRepository()
        self._grove_selector = DreamGroveEncounterSelector(
            repository=self._repository,
            grove=self._grove,
            catalog_loader=self._catalog,
            opportunities=DreamOpportunityMaterializer(world=self._world),
        )
        self._return_echo = DreamReturnEchoProjector(
            director=self._director,
        )
        self._experience = ExperienceProjectionComposer()
        self._public_projection = EpisodePublicProjection()
        self._outcomes = DreamOutcomeCoordinator(
            episodes=self._episodes,
            decisions=self._decisions,
            reconciliation=EvidenceReconciliationEngine(),
            repository=self._repository,
        )
        self._snapshot_projector = DreamSnapshotProjector(
            engine=engine,
            director=self._director,
            episodes=self._episodes,
            experience=self._experience,
            public_projection=self._public_projection,
            repository=self._repository,
        )

    def ensure_encounter(self, *, account_ref: str) -> dict[str, Any]:
        with self._engine.begin() as connection:
            existing = self._repository.current_encounter(
                connection,
                account_ref=account_ref,
                for_update=False,
            )
            if existing is None:
                if self._grove.active_candidates(connection):
                    raise DreamStateError("dream_tree_selection_required")
                entry = self._catalog(connection).entry
                self._create_encounter(
                    connection=connection,
                    account_ref=account_ref,
                    question_ref=entry.question_ref,
                    actor_ref=entry.actor_ref,
                    tree_ref=entry.tree_ref,
                    causation_id=entry.baseline_event_ref,
                )
        return self.snapshot(account_ref=account_ref)

    def entry(self, *, account_ref: str) -> dict[str, Any]:
        with self._engine.connect() as connection:
            encounter = self._repository.current_encounter(
                connection,
                account_ref=account_ref,
                for_update=False,
            )
            if encounter is None:
                candidates = self._grove.active_candidates(connection)
                if candidates:
                    if len(candidates) != 3:
                        raise DreamStateError("dream_grove_requires_exactly_three_trees")
                    return_echo = self._return_echo.project(
                        connection,
                        account_ref=account_ref,
                    )
                    return {
                        "kind": "GROVE",
                        "grove": {
                            "grove_version": DREAM_GROVE_VERSION,
                            "selection_status": "AWAITING_TREE_SELECTION",
                            "candidates": candidates,
                            "return_echo": (
                                return_echo.model_dump(mode="json")
                                if return_echo is not None
                                else None
                            ),
                            "hidden_outcome_included": False,
                            "hidden_npc_choice_included": False,
                        },
                    }
        return {
            "kind": "ENCOUNTER",
            "snapshot": self.snapshot(account_ref=account_ref),
        }

    def start_grove_encounter(
        self,
        *,
        account_ref: str,
        candidate_ref: str,
    ) -> dict[str, Any]:
        with self._engine.begin() as connection:
            intent = self._grove_selector.select(
                connection,
                account_ref=account_ref,
                candidate_ref=candidate_ref,
            )
            if intent is not None:
                self._create_encounter(
                    connection=connection,
                    account_ref=account_ref,
                    question_ref=intent.question_ref,
                    actor_ref=intent.actor_ref,
                    tree_ref=intent.tree_ref,
                    causation_id=intent.causation_id,
                )
        return self.snapshot(account_ref=account_ref)

    def execute_command(
        self,
        *,
        account_ref: str,
        envelope: DreamCommandEnvelope,
    ) -> dict[str, Any]:
        if envelope.command in {
            DreamCommand.OBSERVE_EVIDENCE,
            DreamCommand.OBSERVE_STRUCTURE,
            DreamCommand.OPEN_QUESTION,
        }:
            return self._observe_organ(account_ref=account_ref, envelope=envelope)
        if envelope.command is DreamCommand.SEAL_ANSWER:
            return self._seal_answer(account_ref=account_ref, envelope=envelope)
        if envelope.command is DreamCommand.REVEAL:
            return self._reveal(account_ref=account_ref, envelope=envelope)
        if envelope.command is DreamCommand.RECONCILE:
            return self._reconcile(account_ref=account_ref, envelope=envelope)
        if envelope.command is DreamCommand.CONTINUE_ENCOUNTER:
            return self._continue_encounter(account_ref=account_ref, envelope=envelope)
        if envelope.command is DreamCommand.RETURN_TO_GROVE:
            return self._return_to_grove(account_ref=account_ref, envelope=envelope)
        raise DreamStateError("unsupported_dream_command")

    def _return_to_grove(
        self,
        *,
        account_ref: str,
        envelope: DreamCommandEnvelope,
    ) -> dict[str, Any]:
        with self._engine.begin() as connection:
            if not self._repository.command_replayed(
                connection=connection,
                account_ref=account_ref,
                envelope=envelope,
            ):
                encounter = self._repository.locked_encounter(
                    connection,
                    account_ref=account_ref,
                )
                self._command_guard.assert_identity(
                    encounter=encounter,
                    envelope=envelope,
                )
                self._command_guard.assert_version(
                    encounter=encounter,
                    envelope=envelope,
                )
                if encounter["status"] != "COMPLETED":
                    raise DreamStateError("return_to_grove_requires_completed_encounter")
                self._command_guard.assert_available(
                    connection=connection,
                    encounter=encounter,
                    envelope=envelope,
                    organ_key=None,
                )
                progress = self._game.progress(encounter["state_json"]).model_copy(
                    update={"departed_to_grove": True}
                )
                self._repository.write_encounter_state(
                    connection=connection,
                    encounter=encounter,
                    status="COMPLETED",
                    state=progress.as_state_json(),
                )
                self._repository.record_command_receipt(
                    connection=connection,
                    account_ref=account_ref,
                    envelope=envelope,
                    result_encounter_ref=encounter["encounter_ref"],
                )
        return self.entry(account_ref=account_ref)

    def _continue_encounter(
        self,
        *,
        account_ref: str,
        envelope: DreamCommandEnvelope,
    ) -> dict[str, Any]:
        with self._engine.begin() as connection:
            encounter = self._repository.locked_encounter(
                connection,
                account_ref=account_ref,
            )
            if self._repository.command_replayed(
                connection=connection,
                account_ref=account_ref,
                envelope=envelope,
            ):
                return self.snapshot(account_ref=account_ref)
            self._command_guard.assert_identity(
                encounter=encounter,
                envelope=envelope,
            )
            self._command_guard.assert_version(
                encounter=encounter,
                envelope=envelope,
            )
            if encounter["status"] != "COMPLETED":
                raise DreamStateError("current_encounter_not_completed")
            catalog = self._catalog(connection)
            continuation = catalog.next_episode(encounter["question_ref"])
            if continuation is None:
                raise DreamStateError("no_further_encounter_available")
            next_episode, _continuation_label = continuation
            next_question_ref = next_episode.question_ref
            self._command_guard.assert_available(
                connection=connection,
                encounter=encounter,
                envelope=envelope,
                organ_key=None,
                catalog=catalog,
            )

            existing = connection.execute(
                text(
                    """
                    SELECT encounter_ref
                    FROM dream.encounters
                    WHERE viewer_account_ref = :account_ref
                      AND question_ref = :question_ref
                    """
                ),
                {"account_ref": account_ref, "question_ref": next_question_ref},
            ).scalar_one_or_none()
            result_encounter_ref = str(existing) if existing is not None else None
            if existing is None:
                entry_event = next_episode.entry_world_event
                if entry_event is None or next_episode.tree_state_on_entry is None:
                    raise DreamStateError("continuation_episode_entry_contract_missing")
                self._world.commit_historical_event(
                    connection=connection,
                    event_ref=entry_event.event_ref,
                    actor_ref=next_episode.actor_ref,
                    event_type=entry_event.event_type,
                    summary=entry_event.summary,
                    caused_by_event_ref=entry_event.caused_by_event_ref,
                    evidence=entry_event.evidence,
                    actor_state_delta=entry_event.actor_state_delta,
                )
                self._repository.write_tree_state(
                    connection=connection,
                    tree_ref=next_episode.tree_ref,
                    state=next_episode.tree_state_on_entry,
                    target_version=catalog.tree_entry_version(next_episode.question_ref),
                )
                result_encounter_ref = self._create_encounter(
                    connection=connection,
                    account_ref=account_ref,
                    question_ref=next_episode.question_ref,
                    actor_ref=next_episode.actor_ref,
                    tree_ref=next_episode.tree_ref,
                    causation_id=next_episode.baseline_event_ref,
                )
            assert result_encounter_ref is not None
            self._repository.record_command_receipt(
                connection=connection,
                account_ref=account_ref,
                envelope=envelope,
                result_encounter_ref=result_encounter_ref,
            )
        return self.snapshot(account_ref=account_ref)

    def _observe_organ(
        self,
        *,
        account_ref: str,
        envelope: DreamCommandEnvelope,
    ) -> dict[str, Any]:
        assert envelope.target_ref is not None
        with self._engine.begin() as connection:
            encounter = self._repository.locked_encounter(
                connection,
                account_ref=account_ref,
            )
            if self._repository.command_replayed(
                connection=connection,
                account_ref=account_ref,
                envelope=envelope,
            ):
                return self.snapshot(account_ref=account_ref)
            self._command_guard.assert_identity(
                encounter=encounter,
                envelope=envelope,
            )
            self._command_guard.assert_version(
                encounter=encounter,
                envelope=envelope,
            )
            question = (
                connection.execute(
                    text(
                        """
                    SELECT organ_set_json
                    FROM story.question_instances
                    WHERE question_ref = :question_ref
                    """
                    ),
                    {"question_ref": encounter["question_ref"]},
                )
                .mappings()
                .one()
            )
            organs = question["organ_set_json"]
            organ_key = next(
                (key for key, value in organs.items() if value["organ_ref"] == envelope.target_ref),
                None,
            )
            if organ_key is None:
                raise DreamStateError("unknown_tree_organ")
            self._command_guard.assert_available(
                connection=connection,
                encounter=encounter,
                envelope=envelope,
                organ_key=organ_key,
                organs=organs,
            )
            try:
                mutation = self._game.observe(
                    state=encounter["state_json"],
                    organ_key=organ_key,
                    organs=organs,
                )
            except GameRuleError as exc:
                raise DreamStateError(str(exc)) from exc
            state = mutation.progress.as_state_json()
            self._repository.write_encounter_state(
                connection=connection,
                encounter=encounter,
                status=mutation.phase.value,
                state=state,
            )
            self._repository.record_command_receipt(
                connection=connection,
                account_ref=account_ref,
                envelope=envelope,
                result_encounter_ref=encounter["encounter_ref"],
            )
        return self.snapshot(account_ref=account_ref)

    def _seal_answer(
        self,
        *,
        account_ref: str,
        envelope: DreamCommandEnvelope,
    ) -> dict[str, Any]:
        assert envelope.choice_id is not None
        with self._engine.begin() as connection:
            encounter = self._repository.locked_encounter(
                connection,
                account_ref=account_ref,
            )
            if self._repository.command_replayed(
                connection=connection,
                account_ref=account_ref,
                envelope=envelope,
            ):
                return self.snapshot(account_ref=account_ref)
            self._command_guard.assert_identity(
                encounter=encounter,
                envelope=envelope,
            )
            self._command_guard.assert_version(
                encounter=encounter,
                envelope=envelope,
            )
            state = dict(encounter["state_json"])
            if not state["question_visible"]:
                raise DreamStateError("question_not_open")
            question = (
                connection.execute(
                    text(
                        """
                    SELECT question.options_json, question.cutoff_tick,
                           question.due_tick, question.world_event_ref,
                           event.event_json
                    FROM story.question_instances AS question
                    JOIN world.events AS event
                      ON event.world_event_ref = question.world_event_ref
                    WHERE question.question_ref = :question_ref
                    """
                    ),
                    {"question_ref": encounter["question_ref"]},
                )
                .mappings()
                .one()
            )
            valid_choices = {item["choice_id"] for item in question["options_json"]}
            if envelope.choice_id not in valid_choices:
                raise DreamStateError("invalid_choice")
            self._command_guard.assert_available(
                connection=connection,
                encounter=encounter,
                envelope=envelope,
                organ_key=None,
            )
            current_tick = self._world.current_tick(connection)
            if (
                question["event_json"].get("opportunity_cycle_ref")
                and current_tick >= int(question["due_tick"])
            ):
                raise DreamStateError("dream_question_window_closed")
            seal_payload = {
                "encounter_ref": encounter["encounter_ref"],
                "question_ref": encounter["question_ref"],
                "actor_role": "HUMAN",
                "actor_ref": account_ref,
                "choice_id": envelope.choice_id,
                "sealed_at_tick": current_tick,
                "cutoff_tick": question["cutoff_tick"],
                "idempotency_key": envelope.idempotency_key,
            }
            connection.execute(
                text(
                    """
                    INSERT INTO dream.answer_seals
                        (answer_seal_ref, encounter_ref, question_ref, actor_role,
                         actor_ref, choice_id, sealed_at_tick, cutoff_tick,
                         idempotency_key, seal_hash)
                    VALUES
                        (:seal_ref, :encounter_ref, :question_ref, 'HUMAN',
                         :actor_ref, :choice_id, :sealed_at_tick, :cutoff_tick,
                         :idempotency_key, :seal_hash)
                    """
                ),
                {
                    **seal_payload,
                    "seal_ref": stable_ref("v60-answer-seal", seal_payload),
                    "seal_hash": content_hash(seal_payload),
                },
            )
            episode = self._catalog(connection).for_question(encounter["question_ref"])
            runtime_metadata = self._experience.question_metadata(
                question_ref=encounter["question_ref"],
                runtime_metadata=episode.runtime_metadata.model_dump(mode="json"),
            )
            fruit_payload = {
                "name": runtime_metadata["fruit_name"],
                "question_ref": encounter["question_ref"],
                "world_event_ref": question["world_event_ref"],
                "answer_count": 2,
                "result_visible": False,
            }
            connection.execute(
                text(
                    """
                    INSERT INTO dream.story_fruits
                        (fruit_ref, encounter_ref, question_ref, status,
                         fruit_version, fruit_json, fruit_hash)
                    VALUES
                        (:fruit_ref, :encounter_ref, :question_ref, 'SEALED',
                         1, CAST(:fruit_json AS jsonb), :fruit_hash)
                    """
                ),
                {
                    "fruit_ref": stable_ref("v60-story-fruit", encounter["encounter_ref"]),
                    "encounter_ref": encounter["encounter_ref"],
                    "question_ref": encounter["question_ref"],
                    "fruit_json": canonical_json(fruit_payload),
                    "fruit_hash": content_hash(
                        {"encounter_ref": encounter["encounter_ref"], **fruit_payload}
                    ),
                },
            )
            state["answer_sealed"] = True
            self._repository.write_encounter_state(
                connection=connection,
                encounter=encounter,
                status="WAITING_FOR_WORLD",
                state=state,
            )
            self._repository.record_command_receipt(
                connection=connection,
                account_ref=account_ref,
                envelope=envelope,
                result_encounter_ref=encounter["encounter_ref"],
            )
        return self.snapshot(account_ref=account_ref)

    def synchronize_settled_world_events(
        self,
        *,
        event_refs: Sequence[str] = (),
    ) -> int:
        """Apply committed World outcomes to waiting Dream projections."""

        event_filter = ""
        parameters: dict[str, Any] = {}
        if event_refs:
            event_filter = "AND question.world_event_ref = ANY(:event_refs)"
            parameters["event_refs"] = list(event_refs)
        synchronized = 0
        with self._engine.begin() as connection:
            encounters = (
                connection.execute(
                    text(
                        f"""
                    SELECT encounter.*
                    FROM dream.encounters AS encounter
                    JOIN story.question_instances AS question
                      ON question.question_ref = encounter.question_ref
                    JOIN world.events AS event
                      ON event.world_event_ref = question.world_event_ref
                    WHERE event.status = 'SETTLED'
                      AND encounter.state_json @> '{{"answer_sealed": true}}'::jsonb
                      AND NOT (
                          encounter.state_json @> '{{"world_settled": true}}'::jsonb
                      )
                      {event_filter}
                    ORDER BY encounter.updated_at, encounter.encounter_ref
                    FOR UPDATE OF encounter SKIP LOCKED
                    """
                    ),
                    parameters,
                )
                .mappings()
                .all()
            )
            for row in encounters:
                encounter = dict(row)
                event_ref = connection.execute(
                    text(
                        """
                        SELECT world_event_ref
                        FROM story.question_instances
                        WHERE question_ref = :question_ref
                        """
                    ),
                    {"question_ref": encounter["question_ref"]},
                ).scalar_one()
                self._outcomes.apply_world_settlement(
                    connection=connection,
                    encounter=encounter,
                    event_ref=str(event_ref),
                )
                synchronized += 1
        return synchronized

    def _reveal(
        self,
        *,
        account_ref: str,
        envelope: DreamCommandEnvelope,
    ) -> dict[str, Any]:
        with self._engine.begin() as connection:
            encounter = self._repository.locked_encounter(
                connection,
                account_ref=account_ref,
            )
            if self._repository.command_replayed(
                connection=connection,
                account_ref=account_ref,
                envelope=envelope,
            ):
                return self.snapshot(account_ref=account_ref)
            self._command_guard.assert_identity(
                encounter=encounter,
                envelope=envelope,
            )
            self._command_guard.assert_version(
                encounter=encounter,
                envelope=envelope,
            )
            state = dict(encounter["state_json"])
            if not state["world_settled"]:
                raise DreamStateError("world_event_not_settled")
            self._command_guard.assert_available(
                connection=connection,
                encounter=encounter,
                envelope=envelope,
                organ_key=None,
            )
            event_ref = connection.execute(
                text(
                    """
                    SELECT world_event_ref
                    FROM story.question_instances
                    WHERE question_ref = :question_ref
                    """
                ),
                {"question_ref": encounter["question_ref"]},
            ).scalar_one()
            existing = connection.execute(
                text("SELECT reveal_ref FROM dream.reveals WHERE encounter_ref = :encounter_ref"),
                {"encounter_ref": encounter["encounter_ref"]},
            ).scalar_one_or_none()
            if existing is None:
                reveal_payload, result = self._outcomes.build_reveal(
                    connection=connection,
                    encounter=encounter,
                )
                reveal_hash = content_hash(reveal_payload)
                connection.execute(
                    text(
                        """
                        INSERT INTO dream.reveals
                            (reveal_ref, encounter_ref, world_event_ref,
                             result, reveal_json, reveal_hash)
                        VALUES
                            (:reveal_ref, :encounter_ref, :event_ref,
                             :result, CAST(:reveal_json AS jsonb), :reveal_hash)
                        """
                    ),
                    {
                        "reveal_ref": stable_ref("v60-reveal", reveal_hash),
                        "encounter_ref": encounter["encounter_ref"],
                        "event_ref": event_ref,
                        "result": result,
                        "reveal_json": canonical_json(reveal_payload),
                        "reveal_hash": reveal_hash,
                    },
                )
                connection.execute(
                    text(
                        """
                        UPDATE dream.story_fruits
                        SET status = 'REVEALED',
                            fruit_version = fruit_version + 1,
                            fruit_json = fruit_json || CAST(:reveal_summary AS jsonb),
                            fruit_hash = :fruit_hash,
                            updated_at = now()
                        WHERE encounter_ref = :encounter_ref
                        """
                    ),
                    {
                        "encounter_ref": encounter["encounter_ref"],
                        "reveal_summary": canonical_json(
                            {"result": result, "result_visible": True}
                        ),
                        "fruit_hash": content_hash(
                            {
                                "encounter_ref": encounter["encounter_ref"],
                                "status": "REVEALED",
                                "result": result,
                            }
                        ),
                    },
                )
            state["revealed"] = True
            self._repository.write_encounter_state(
                connection=connection,
                encounter=encounter,
                status="REVEALED",
                state=state,
            )
            self._repository.record_command_receipt(
                connection=connection,
                account_ref=account_ref,
                envelope=envelope,
                result_encounter_ref=encounter["encounter_ref"],
            )
        return self.snapshot(account_ref=account_ref)

    def _reconcile(
        self,
        *,
        account_ref: str,
        envelope: DreamCommandEnvelope,
    ) -> dict[str, Any]:
        with self._engine.begin() as connection:
            encounter = self._repository.locked_encounter(
                connection,
                account_ref=account_ref,
            )
            if self._repository.command_replayed(
                connection=connection,
                account_ref=account_ref,
                envelope=envelope,
            ):
                return self.snapshot(account_ref=account_ref)
            self._command_guard.assert_identity(
                encounter=encounter,
                envelope=envelope,
            )
            self._command_guard.assert_version(
                encounter=encounter,
                envelope=envelope,
            )
            state = dict(encounter["state_json"])
            if not state["revealed"]:
                raise DreamStateError("reveal_required")
            self._command_guard.assert_available(
                connection=connection,
                encounter=encounter,
                envelope=envelope,
                organ_key=None,
            )
            if not state["reconciled"]:
                connection.execute(
                    text(
                        """
                        UPDATE dream.story_fruits
                        SET status = 'RECONCILED',
                            fruit_version = fruit_version + 1,
                            fruit_json = fruit_json || '{"reconciled": true}'::jsonb,
                            fruit_hash = :fruit_hash,
                            updated_at = now()
                        WHERE encounter_ref = :encounter_ref
                        """
                    ),
                    {
                        "encounter_ref": encounter["encounter_ref"],
                        "fruit_hash": content_hash(
                            {
                                "encounter_ref": encounter["encounter_ref"],
                                "status": "RECONCILED",
                            }
                        ),
                    },
                )
                state["reconciled"] = True
                self._repository.write_encounter_state(
                    connection=connection,
                    encounter=encounter,
                    status="COMPLETED",
                    state=state,
                )
            self._repository.record_command_receipt(
                connection=connection,
                account_ref=account_ref,
                envelope=envelope,
                result_encounter_ref=encounter["encounter_ref"],
            )
        return self.snapshot(account_ref=account_ref)

    def snapshot(self, *, account_ref: str) -> dict[str, Any]:
        return self._snapshot_projector.snapshot(account_ref=account_ref)

    def _create_encounter(
        self,
        *,
        connection: Any,
        account_ref: str,
        question_ref: str,
        actor_ref: str,
        tree_ref: str,
        causation_id: str,
    ) -> str:
        question = (
            connection.execute(
                text(
                    """
                SELECT cutoff_tick
                FROM story.question_instances
                WHERE question_ref = :question_ref
                """
                ),
                {"question_ref": question_ref},
            )
            .mappings()
            .one()
        )
        episode = self._catalog(connection).for_question(question_ref)
        runtime_metadata = self._experience.question_metadata(
            question_ref=question_ref,
            runtime_metadata=episode.runtime_metadata.model_dump(mode="json"),
        )
        return self._repository.create_encounter(
            connection=connection,
            account_ref=account_ref,
            question_ref=question_ref,
            actor_ref=actor_ref,
            tree_ref=tree_ref,
            causation_id=causation_id,
            cutoff_tick=int(question["cutoff_tick"]),
            npc_choice_id=str(runtime_metadata["npc_choice_id"]),
        )

    def _catalog(self, connection: Any) -> ActiveEpisodeCatalog:
        try:
            return self._episodes.load(connection)
        except (DreamGroveError, EpisodeCatalogError) as exc:
            raise DreamStateError(str(exc)) from exc
