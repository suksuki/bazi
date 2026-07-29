from __future__ import annotations

from typing import Any

from sqlalchemy import text

from abu_v60.decision import (
    CognitiveDecisionLedger,
    DecisionAuthority,
    DecisionKind,
    DecisionRequest,
    DecisionRouteStatus,
    EvidenceReconciliationEngine,
)
from abu_v60.dream.catalog import DreamEpisodeCatalog, EpisodeCatalogError
from abu_v60.dream.errors import DreamStateError
from abu_v60.dream.persistence import DreamRepository
from abu_v60.provenance import content_hash, stable_ref


class DreamOutcomeCoordinator:
    """Settles fruits and derives reveal payloads from committed evidence."""

    def __init__(
        self,
        *,
        episodes: DreamEpisodeCatalog,
        decisions: CognitiveDecisionLedger,
        reconciliation: EvidenceReconciliationEngine,
        repository: DreamRepository,
    ) -> None:
        self._episodes = episodes
        self._decisions = decisions
        self._reconciliation = reconciliation
        self._repository = repository

    def apply_world_settlement(
        self,
        *,
        connection: Any,
        encounter: dict[str, Any],
        event_ref: str,
    ) -> None:
        state = dict(encounter["state_json"])
        if state["world_settled"]:
            return
        event = (
            connection.execute(
                text(
                    """
                    SELECT status, event_json
                    FROM world.events
                    WHERE world_event_ref = :event_ref
                    """
                ),
                {"event_ref": event_ref},
            )
            .mappings()
            .one()
        )
        if event["status"] != "SETTLED":
            raise DreamStateError("world_event_not_settled")
        try:
            catalog = self._episodes.load(connection)
        except EpisodeCatalogError as exc:
            raise DreamStateError(str(exc)) from exc
        episode = catalog.for_question(encounter["question_ref"])
        if episode.world_event_ref != event_ref:
            raise DreamStateError("encounter_world_event_contract_mismatch")

        state["world_settled"] = True
        self._mature_fruit(
            connection=connection,
            encounter=encounter,
            event_ref=event_ref,
        )
        if event["event_json"].get("tree_projection_scope") != "ENCOUNTER":
            self._repository.write_tree_state(
                connection=connection,
                tree_ref=encounter["tree_ref"],
                state=episode.tree_state_after_settlement,
                target_version=catalog.tree_settlement_version(episode.question_ref),
            )
        self._repository.write_encounter_state(
            connection=connection,
            encounter=encounter,
            status="REVEAL_READY",
            state=state,
        )

    def build_reveal(
        self,
        *,
        connection: Any,
        encounter: dict[str, Any],
    ) -> tuple[dict[str, Any], str]:
        encounter_ref = str(encounter["encounter_ref"])
        question_ref = str(encounter["question_ref"])
        question = (
            connection.execute(
                text(
                    """
                    SELECT options_json, resolution_rule_json, world_event_ref
                    FROM story.question_instances
                    WHERE question_ref = :question_ref
                    """
                ),
                {"question_ref": question_ref},
            )
            .mappings()
            .one()
        )
        event = (
            connection.execute(
                text(
                    """
                    SELECT sealed_outcome_json, settlement_hash
                    FROM world.events
                    WHERE world_event_ref = :event_ref
                      AND status = 'SETTLED'
                    """
                ),
                {"event_ref": question["world_event_ref"]},
            )
            .mappings()
            .one()
        )
        seals = (
            connection.execute(
                text(
                    """
                    SELECT actor_role, actor_ref, choice_id, answer_seal_ref
                    FROM dream.answer_seals
                    WHERE encounter_ref = :encounter_ref
                    ORDER BY actor_role
                    """
                ),
                {"encounter_ref": encounter_ref},
            )
            .mappings()
            .all()
        )
        seal_by_role = {seal["actor_role"]: dict(seal) for seal in seals}
        human_choice = seal_by_role["HUMAN"]["choice_id"]
        option_by_id = {item["choice_id"]: item for item in question["options_json"]}
        reconciliation = self._reconciliation.reconcile(
            predicted_atoms=option_by_id[human_choice]["proposition"],
            actual_atoms=event["sealed_outcome_json"]["resolved_proposition"],
            compare_atoms=question["resolution_rule_json"]["compare_atoms"],
        )
        result = reconciliation.result.value
        decision = self._decisions.route_and_record(
            connection=connection,
            request=DecisionRequest(
                request_id=stable_ref(
                    "v60-decision-request",
                    {
                        "kind": "RECONCILIATION",
                        "encounter_ref": encounter_ref,
                        "human_seal_ref": seal_by_role["HUMAN"]["answer_seal_ref"],
                        "settlement_hash": event["settlement_hash"],
                    },
                ),
                decision_kind=DecisionKind.DOMAIN_INFERENCE,
                subject_ref=encounter_ref,
                evidence_refs=tuple(
                    str(item["evidence_ref"]) for item in event["sealed_outcome_json"]["evidence"]
                ),
                deterministic_result={
                    "result": result,
                    "baseline_credit": reconciliation.baseline_credit,
                    "atom_reconciliation": reconciliation.atom_reconciliation,
                },
                llm_allowed=False,
                correlation_id=str(encounter["correlation_id"]),
                causation_id=str(question["world_event_ref"]),
            ),
        )
        if (
            decision.route.status is not DecisionRouteStatus.RESOLVED
            or decision.route.authority is not DecisionAuthority.SYSTEM
        ):
            raise DreamStateError("reconciliation_not_system_resolved")
        return (
            {
                "result": result,
                "decision_ref": decision.decision_id,
                "actual_event": event["sealed_outcome_json"]["actual_event"],
                "actual_evidence": event["sealed_outcome_json"]["evidence"],
                "baseline_credit": reconciliation.baseline_credit,
                "atom_reconciliation": reconciliation.atom_reconciliation,
                "human_answer": {
                    "answer_seal_ref": seal_by_role["HUMAN"]["answer_seal_ref"],
                    "choice_id": human_choice,
                    "label": option_by_id[human_choice]["label"],
                },
                "npc_answer": {
                    "answer_seal_ref": seal_by_role["NPC"]["answer_seal_ref"],
                    "choice_id": seal_by_role["NPC"]["choice_id"],
                    "label": option_by_id[seal_by_role["NPC"]["choice_id"]]["label"],
                },
                "settlement_hash": event["settlement_hash"],
            },
            result,
        )

    @staticmethod
    def _mature_fruit(
        *,
        connection: Any,
        encounter: dict[str, Any],
        event_ref: str,
    ) -> None:
        connection.execute(
            text(
                """
                UPDATE dream.story_fruits
                SET status = 'MATURED',
                    fruit_version = CASE WHEN status = 'SEALED'
                        THEN fruit_version + 1 ELSE fruit_version END,
                    fruit_json = fruit_json || '{"matured": true}'::jsonb,
                    fruit_hash = :fruit_hash,
                    updated_at = now()
                WHERE encounter_ref = :encounter_ref
                  AND status IN ('SEALED', 'MATURED')
                """
            ),
            {
                "encounter_ref": encounter["encounter_ref"],
                "fruit_hash": content_hash(
                    {
                        "encounter_ref": encounter["encounter_ref"],
                        "status": "MATURED",
                        "event_ref": event_ref,
                    }
                ),
            },
        )
