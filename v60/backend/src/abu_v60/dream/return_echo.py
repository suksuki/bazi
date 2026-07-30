from __future__ import annotations

from typing import Any

from pydantic import ValidationError
from sqlalchemy import text

from abu_v60.dream.errors import DreamStateError
from abu_v60.dream.grove import GroveCandidateDefinition
from abu_v60.dream.return_echo_contracts import (
    DreamReturnEcho,
    DreamReturnEchoAbuRecap,
    DreamReturnEchoJudgment,
    DreamReturnEchoLineage,
    DreamReturnEchoOpenObservation,
    DreamReturnEchoWorldResponse,
)
from abu_v60.game import (
    DreamEpisodeContract,
    DreamGameplayDirector,
    DreamPhase,
)
from abu_v60.provenance import content_hash, stable_ref
from abu_v60.story.admission import validate_persisted_episode_admission
from abu_v60.world.actor_admission import (
    validate_persisted_world_actor_admission,
)
from abu_v60.world.admission import (
    WorldEventAdmissionError,
    validate_persisted_world_event_admission,
)

_STILL_TO_OBSERVE = (
    "下一次遇到相似分岔，仍可先记下支持判断的当下证据，"
    "再与后来发生的事分开核对。"
)
_BOUNDARY = (
    "它不能说明主人的命理关系、机制或人生结果，"
    "也不会成为主人的命理证据。"
)
_NEXT_ATTENTION = (
    "回到林中后，继续观察下一段梦中生命如何留下自己的判断与世界证据。"
)
_RESULT_MEANINGS = {
    "SUPPORTED": "这次只说明，后来提交的梦中事实支持了当时的判断。",
    "PARTIAL": "这次只说明，后来提交的梦中事实部分支持了当时的判断。",
    "NOT_SUPPORTED": "这次只说明，后来提交的梦中事实没有支持当时的判断。",
}


class DreamReturnEchoProjector:
    """Rebuild one Grove echo only from committed Dream-owned records."""

    def __init__(
        self,
        *,
        director: DreamGameplayDirector | None = None,
    ) -> None:
        self._director = director or DreamGameplayDirector()

    def project(
        self,
        connection: Any,
        *,
        account_ref: str,
    ) -> DreamReturnEcho | None:
        encounter = self._latest_departed_encounter(
            connection,
            account_ref=account_ref,
        )
        if encounter is None:
            return None
        try:
            return self._project_validated(
                connection,
                account_ref=account_ref,
                encounter=encounter,
            )
        except DreamStateError:
            raise
        except (KeyError, TypeError, ValidationError, ValueError) as exc:
            raise DreamStateError("dream_return_echo_lineage_invalid") from exc

    def project_for_encounter(
        self,
        connection: Any,
        *,
        account_ref: str,
        encounter_ref: str,
    ) -> DreamReturnEcho | None:
        """Rebuild one exact departed Echo instead of trusting a stored ref."""

        encounter = self._departed_encounter(
            connection,
            account_ref=account_ref,
            encounter_ref=encounter_ref,
        )
        if encounter is None:
            return None
        try:
            return self._project_validated(
                connection,
                account_ref=account_ref,
                encounter=encounter,
            )
        except DreamStateError:
            raise
        except (KeyError, TypeError, ValidationError, ValueError) as exc:
            raise DreamStateError(
                "dream_return_echo_lineage_invalid"
            ) from exc

    @staticmethod
    def _latest_departed_encounter(
        connection: Any,
        *,
        account_ref: str,
    ) -> dict[str, Any] | None:
        row = (
            connection.execute(
                text(
                    """
                    SELECT encounter_ref, viewer_account_ref, actor_ref,
                           tree_ref, question_ref, status, state_json,
                           state_hash, updated_at
                    FROM dream.encounters
                    WHERE viewer_account_ref = :account_ref
                      AND status = 'COMPLETED'
                      AND state_json @> '{"departed_to_grove": true}'::jsonb
                    ORDER BY updated_at DESC, encounter_ref DESC
                    LIMIT 1
                    """
                ),
                {"account_ref": account_ref},
            )
            .mappings()
            .one_or_none()
        )
        return dict(row) if row is not None else None

    @staticmethod
    def _departed_encounter(
        connection: Any,
        *,
        account_ref: str,
        encounter_ref: str,
    ) -> dict[str, Any] | None:
        row = (
            connection.execute(
                text(
                    """
                    SELECT encounter_ref, viewer_account_ref, actor_ref,
                           tree_ref, question_ref, status, version,
                           state_json, state_hash, updated_at
                    FROM dream.encounters
                    WHERE viewer_account_ref = :account_ref
                      AND encounter_ref = :encounter_ref
                      AND status = 'COMPLETED'
                      AND state_json
                            @> '{"departed_to_grove": true}'::jsonb
                    """
                ),
                {
                    "account_ref": account_ref,
                    "encounter_ref": encounter_ref,
                },
            )
            .mappings()
            .one_or_none()
        )
        return dict(row) if row is not None else None

    def _project_validated(
        self,
        connection: Any,
        *,
        account_ref: str,
        encounter: dict[str, Any],
    ) -> DreamReturnEcho:
        self._validate_encounter(encounter, account_ref=account_ref)
        sources = self._load_sources(
            connection,
            account_ref=account_ref,
            encounter=encounter,
        )
        episode = self._director.load_episode(
            payload=sources["episode_contract_json"],
            expected_hash=str(sources["episode_contract_hash"]),
            question_ref=str(encounter["question_ref"]),
        )
        if (
            episode.episode_ref != sources["episode_ref"]
            or episode.episode_version != int(sources["episode_version"])
            or episode.world_event_ref != sources["world_event_ref"]
            or episode.actor_ref != encounter["actor_ref"]
            or sources["question_actor_ref"] != encounter["actor_ref"]
            or episode.tree_ref != encounter["tree_ref"]
            or episode.cutoff_tick != int(sources["question_cutoff_tick"])
            or episode.due_tick != int(sources["question_due_tick"])
        ):
            raise DreamStateError("dream_return_echo_episode_identity_mismatch")
        self._validate_episode_admission(
            episode=episode,
            sources=sources,
        )

        public_alias = self._validated_public_alias(
            encounter=encounter,
            sources=sources,
        )

        seals = self._answer_seals(
            connection,
            encounter_ref=str(encounter["encounter_ref"]),
        )
        seals_by_role = self._validate_answer_seals(
            seals=seals,
            account_ref=account_ref,
            encounter=encounter,
            sources=sources,
        )

        reveal_payload = dict(sources["reveal_json"])
        if (
            content_hash(reveal_payload) != sources["reveal_hash"]
            or stable_ref("v60-reveal", sources["reveal_hash"])
            != sources["reveal_ref"]
            or reveal_payload["result"] != sources["result"]
        ):
            raise DreamStateError("dream_return_echo_reveal_invalid")
        self._validate_reveal_and_world(
            encounter=encounter,
            sources=sources,
            reveal_payload=reveal_payload,
            seals_by_role=seals_by_role,
        )

        evidence = self._committed_outcome_evidence(
            connection,
            world_event_ref=str(sources["world_event_ref"]),
        )
        self._validate_evidence(
            evidence=evidence,
            reveal_payload=reveal_payload,
            world_event_ref=str(sources["world_event_ref"]),
            cutoff_tick=int(sources["cutoff_tick"]),
            settled_at_tick=int(sources["settled_at_tick"]),
        )

        evidence_refs = tuple(str(item["evidence_ref"]) for item in evidence)
        evidence_hashes = tuple(str(item["evidence_hash"]) for item in evidence)
        evidence_summaries = tuple(
            str(item["evidence_json"]["summary"]) for item in evidence
        )
        result = str(sources["result"])
        completed_narrative = episode.narrative.for_phase(DreamPhase.COMPLETED)
        choice_label = str(reveal_payload["human_answer"]["label"])
        return DreamReturnEcho.issue(
            encounter_ref=str(encounter["encounter_ref"]),
            public_alias=public_alias,
            episode_title=completed_narrative.title,
            judgment=DreamReturnEchoJudgment(
                choice_label=choice_label,
                summary=f"你当时把「{choice_label}」作为那一刻的判断。",
            ),
            world_response=DreamReturnEchoWorldResponse(
                summary=str(reveal_payload["actual_event"]),
                evidence_summaries=evidence_summaries,
            ),
            still_to_observe=DreamReturnEchoOpenObservation(
                summary=_STILL_TO_OBSERVE,
            ),
            abu_recap=DreamReturnEchoAbuRecap(
                meaning=_RESULT_MEANINGS[result],
                boundary=_BOUNDARY,
                next_attention=_NEXT_ATTENTION,
            ),
            lineage=DreamReturnEchoLineage(
                question_ref=str(encounter["question_ref"]),
                episode_ref=episode.episode_ref,
                episode_version=episode.episode_version,
                answer_seal_ref=str(sources["answer_seal_ref"]),
                answer_seal_hash=str(sources["seal_hash"]),
                reveal_ref=str(sources["reveal_ref"]),
                reveal_hash=str(sources["reveal_hash"]),
                world_event_ref=str(sources["world_event_ref"]),
                reconciliation_result=result,
                committed_evidence_refs=evidence_refs,
                committed_evidence_hashes=evidence_hashes,
            ),
        )

    @staticmethod
    def _validate_encounter(
        encounter: dict[str, Any],
        *,
        account_ref: str,
    ) -> None:
        state = dict(encounter["state_json"])
        if (
            encounter["viewer_account_ref"] != account_ref
            or encounter["status"] != "COMPLETED"
            or not state.get("answer_sealed")
            or not state.get("world_settled")
            or not state.get("revealed")
            or not state.get("reconciled")
            or not state.get("departed_to_grove")
            or content_hash(state) != encounter["state_hash"]
        ):
            raise DreamStateError("dream_return_echo_encounter_invalid")

    @staticmethod
    def _validated_public_alias(
        *,
        encounter: dict[str, Any],
        sources: dict[str, Any],
    ) -> str:
        actor = validate_persisted_world_actor_admission(
            {
                "actor_ref": sources["world_actor_ref"],
                "world_ref": sources["actor_world_ref"],
                "case_ref": sources["actor_case_ref"],
                "actor_kind": sources["actor_kind"],
                "display_name": sources["actor_display_name"],
                "branch": sources["actor_branch"],
                "admission_manifest_json": sources[
                    "actor_admission_manifest_json"
                ],
                "admission_manifest_hash": sources[
                    "actor_admission_manifest_hash"
                ],
            }
        )
        if (
            actor.actor_ref != encounter["actor_ref"]
            or actor.case_ref != sources["life_case_case_ref"]
        ):
            raise DreamStateError("dream_return_echo_actor_identity_mismatch")

        candidate_payload = sources["candidate_json"]
        if candidate_payload is None:
            if sources["source_question_ref"] != encounter["question_ref"]:
                raise DreamStateError(
                    "dream_return_echo_source_candidate_missing"
                )
            return actor.display_name

        candidate = GroveCandidateDefinition.model_validate(
            {
                **candidate_payload,
                "candidate_hash": sources["candidate_hash"],
            }
        )
        if (
            candidate.question_ref != sources["source_question_ref"]
            or candidate.actor_ref != encounter["actor_ref"]
            or candidate.tree_ref != encounter["tree_ref"]
        ):
            raise DreamStateError(
                "dream_return_echo_candidate_identity_mismatch"
            )
        return candidate.public_alias

    @staticmethod
    def _load_sources(
        connection: Any,
        *,
        account_ref: str,
        encounter: dict[str, Any],
    ) -> dict[str, Any]:
        row = (
            connection.execute(
                text(
                    """
                    SELECT seal.answer_seal_ref, seal.encounter_ref,
                           seal.question_ref, seal.actor_role, seal.actor_ref,
                           seal.choice_id, seal.sealed_at_tick,
                           seal.cutoff_tick, seal.idempotency_key,
                           seal.seal_hash,
                           reveal.reveal_ref, reveal.world_event_ref,
                           reveal.result, reveal.reveal_json,
                           reveal.reveal_hash,
                           fruit.status AS fruit_status,
                           fruit.question_ref AS fruit_question_ref,
                           fruit.fruit_hash,
                           question.actor_ref AS question_actor_ref,
                           question.life_case_revision_ref,
                           revision.case_ref AS life_case_case_ref,
                           revision.revision_hash
                               AS life_case_revision_hash,
                           question.question_version, question.prompt,
                           question.options_json,
                           question.evidence_refs_json,
                           question.cutoff_tick AS question_cutoff_tick,
                           question.due_tick AS question_due_tick,
                           question.resolution_rule_json,
                           question.question_hash,
                           question.organ_set_json,
                           question.organ_set_hash,
                           question.episode_ref, question.episode_version,
                           question.world_event_ref
                               AS question_world_event_ref,
                           question.episode_contract_json,
                           question.episode_contract_hash,
                           question.admission_manifest_json,
                           question.admission_manifest_hash,
                           event.status AS event_status,
                           COALESCE(
                               event.event_json ->> 'source_question_ref',
                               question.question_ref
                           ) AS source_question_ref,
                           event.sealed_outcome_json, event.outcome_hash,
                           event.world_ref AS event_world_ref,
                           event.actor_ref AS event_actor_ref,
                           event.event_type,
                           event.event_json,
                           event.due_tick AS event_due_tick,
                           event.settled_at_tick, event.settlement_hash,
                           event.definition_hash AS event_definition_hash,
                           event.admission_manifest_json
                               AS event_admission_manifest_json,
                           event.admission_manifest_hash
                               AS event_admission_manifest_hash,
                           actor.actor_ref AS world_actor_ref,
                           actor.world_ref AS actor_world_ref,
                           actor.case_ref AS actor_case_ref,
                           actor.actor_kind,
                           actor.display_name AS actor_display_name,
                           actor.branch AS actor_branch,
                           actor.admission_manifest_json
                               AS actor_admission_manifest_json,
                           actor.admission_manifest_hash
                               AS actor_admission_manifest_hash,
                           candidate.candidate_json,
                           candidate.candidate_hash
                    FROM dream.answer_seals AS seal
                    JOIN dream.reveals AS reveal
                      ON reveal.encounter_ref = seal.encounter_ref
                    JOIN dream.story_fruits AS fruit
                      ON fruit.encounter_ref = seal.encounter_ref
                    JOIN story.question_instances AS question
                      ON question.question_ref = seal.question_ref
                    JOIN mingli.life_case_revisions AS revision
                      ON revision.life_case_revision_ref =
                         question.life_case_revision_ref
                    JOIN world.events AS event
                      ON event.world_event_ref = reveal.world_event_ref
                    JOIN world.actors AS actor
                      ON actor.actor_ref = question.actor_ref
                    LEFT JOIN dream.grove_candidates AS candidate
                      ON candidate.question_ref = COALESCE(
                          event.event_json ->> 'source_question_ref',
                          question.question_ref
                      )
                    WHERE seal.encounter_ref = :encounter_ref
                      AND seal.actor_role = 'HUMAN'
                      AND seal.actor_ref = :account_ref
                    """
                ),
                {
                    "encounter_ref": encounter["encounter_ref"],
                    "account_ref": account_ref,
                },
            )
            .mappings()
            .all()
        )
        if len(row) != 1:
            raise DreamStateError("dream_return_echo_source_lineage_missing")
        return dict(row[0])

    @staticmethod
    def _answer_seals(
        connection: Any,
        *,
        encounter_ref: str,
    ) -> tuple[dict[str, Any], ...]:
        rows = (
            connection.execute(
                text(
                    """
                    SELECT answer_seal_ref, encounter_ref, question_ref,
                           actor_role, actor_ref, choice_id, sealed_at_tick,
                           cutoff_tick, idempotency_key, seal_hash
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
        return tuple(dict(row) for row in rows)

    @staticmethod
    def _validate_answer_seals(
        *,
        seals: tuple[dict[str, Any], ...],
        account_ref: str,
        encounter: dict[str, Any],
        sources: dict[str, Any],
    ) -> dict[str, dict[str, Any]]:
        if tuple(item["actor_role"] for item in seals) != ("HUMAN", "NPC"):
            raise DreamStateError("dream_return_echo_answer_seal_set_invalid")
        options = {
            str(item["choice_id"]): dict(item)
            for item in sources["options_json"]
        }
        by_role = {str(item["actor_role"]): item for item in seals}
        for seal in seals:
            seal_payload = {
                key: seal[key]
                for key in (
                    "encounter_ref",
                    "question_ref",
                    "actor_role",
                    "actor_ref",
                    "choice_id",
                    "sealed_at_tick",
                    "cutoff_tick",
                    "idempotency_key",
                )
            }
            if (
                seal["encounter_ref"] != encounter["encounter_ref"]
                or seal["question_ref"] != encounter["question_ref"]
                or int(seal["cutoff_tick"])
                != int(sources["question_cutoff_tick"])
                or seal["choice_id"] not in options
                or content_hash(seal_payload) != seal["seal_hash"]
                or stable_ref("v60-answer-seal", seal_payload)
                != seal["answer_seal_ref"]
            ):
                raise DreamStateError("dream_return_echo_answer_seal_invalid")
        if (
            by_role["HUMAN"]["actor_ref"] != account_ref
            or by_role["NPC"]["actor_ref"] != encounter["actor_ref"]
            or by_role["HUMAN"]["answer_seal_ref"]
            != sources["answer_seal_ref"]
            or by_role["HUMAN"]["seal_hash"] != sources["seal_hash"]
        ):
            raise DreamStateError("dream_return_echo_answer_seal_owner_mismatch")
        return by_role

    @staticmethod
    def _validate_episode_admission(
        *,
        episode: DreamEpisodeContract,
        sources: dict[str, Any],
    ) -> None:
        question_payload = {
            "question_ref": sources["question_ref"],
            "actor_ref": sources["question_actor_ref"],
            "life_case_revision_ref": sources["life_case_revision_ref"],
            "world_event_ref": sources["question_world_event_ref"],
            "question_version": sources["question_version"],
            "prompt": sources["prompt"],
            "options": sources["options_json"],
            "evidence_refs": sources["evidence_refs_json"],
            "cutoff_tick": sources["question_cutoff_tick"],
            "due_tick": sources["question_due_tick"],
        }
        if (
            content_hash(
                {
                    **question_payload,
                    "resolution_rule": sources["resolution_rule_json"],
                }
            )
            != sources["question_hash"]
            or content_hash(sources["organ_set_json"])
            != sources["organ_set_hash"]
        ):
            raise DreamStateError("dream_return_echo_question_hash_invalid")
        validate_persisted_episode_admission(
            manifest_payload=sources["admission_manifest_json"],
            manifest_hash=sources["admission_manifest_hash"],
            episode=episode,
            persisted={
                **sources,
                "question_ref": sources["question_ref"],
                "life_case_revision_ref": sources[
                    "life_case_revision_ref"
                ],
                "life_case_revision_hash": sources[
                    "life_case_revision_hash"
                ],
                "evidence_refs_json": sources["evidence_refs_json"],
            },
        )

    @staticmethod
    def _validate_reveal_and_world(
        *,
        encounter: dict[str, Any],
        sources: dict[str, Any],
        reveal_payload: dict[str, Any],
        seals_by_role: dict[str, dict[str, Any]],
    ) -> None:
        human_answer = dict(reveal_payload["human_answer"])
        npc_answer = dict(reveal_payload["npc_answer"])
        options = {
            str(item["choice_id"]): dict(item)
            for item in sources["options_json"]
        }
        world_outcome = dict(sources["sealed_outcome_json"])
        try:
            validate_persisted_world_event_admission(
                {
                    "world_event_ref": sources["world_event_ref"],
                    "world_ref": sources["event_world_ref"],
                    "actor_ref": sources["event_actor_ref"],
                    "actor_case_ref": sources["actor_case_ref"],
                    "actor_kind": sources["actor_kind"],
                    "actor_branch": sources["actor_branch"],
                    "event_type": sources["event_type"],
                    "due_tick": sources["event_due_tick"],
                    "event_json": sources["event_json"],
                    "sealed_outcome_json": world_outcome,
                    "outcome_hash": sources["outcome_hash"],
                    "definition_hash": sources["event_definition_hash"],
                    "admission_manifest_json": sources[
                        "event_admission_manifest_json"
                    ],
                    "admission_manifest_hash": sources[
                        "event_admission_manifest_hash"
                    ],
                }
            )
        except WorldEventAdmissionError as exc:
            raise DreamStateError(
                "dream_return_echo_world_event_admission_invalid"
            ) from exc
        expected_settlement_hash = content_hash(
            {
                "world_event_ref": sources["world_event_ref"],
                "settled_at_tick": sources["settled_at_tick"],
                "outcome_hash": sources["outcome_hash"],
            }
        )
        if (
            sources["event_status"] != "SETTLED"
            or sources["settled_at_tick"] is None
            or int(sources["settled_at_tick"])
            != int(sources["event_due_tick"])
            or int(sources["settled_at_tick"])
            != int(sources["question_due_tick"])
            or sources["settlement_hash"] != expected_settlement_hash
            or content_hash(world_outcome) != sources["outcome_hash"]
            or sources["fruit_status"] != "RECONCILED"
            or sources["fruit_question_ref"] != encounter["question_ref"]
            or sources["fruit_hash"]
            != content_hash(
                {
                    "encounter_ref": encounter["encounter_ref"],
                    "status": "RECONCILED",
                }
            )
            or sources["world_event_ref"]
            != sources["question_world_event_ref"]
            or sources["event_actor_ref"] != encounter["actor_ref"]
            or sources["event_actor_ref"] != sources["question_actor_ref"]
            or sources["event_actor_ref"] != sources["world_actor_ref"]
            or sources["event_world_ref"] != sources["actor_world_ref"]
        ):
            raise DreamStateError("dream_return_echo_committed_world_invalid")
        if (
            human_answer.get("answer_seal_ref") != sources["answer_seal_ref"]
            or human_answer.get("choice_id") != sources["choice_id"]
            or human_answer.get("label")
            != options[sources["choice_id"]]["label"]
            or npc_answer.get("answer_seal_ref")
            != seals_by_role["NPC"]["answer_seal_ref"]
            or npc_answer.get("choice_id")
            != seals_by_role["NPC"]["choice_id"]
            or npc_answer.get("label")
            != options[seals_by_role["NPC"]["choice_id"]]["label"]
            or reveal_payload.get("settlement_hash")
            != sources["settlement_hash"]
            or reveal_payload.get("actual_event")
            != world_outcome.get("actual_event")
            or reveal_payload.get("actual_evidence")
            != world_outcome.get("evidence")
        ):
            raise DreamStateError("dream_return_echo_reveal_world_mismatch")

    @staticmethod
    def _committed_outcome_evidence(
        connection: Any,
        *,
        world_event_ref: str,
    ) -> tuple[dict[str, Any], ...]:
        rows = (
            connection.execute(
                text(
                    """
                    SELECT evidence_ref, world_event_ref, committed_at_tick,
                           evidence_json, evidence_hash
                    FROM world.event_evidence
                    WHERE world_event_ref = :world_event_ref
                    ORDER BY evidence_ref
                    """
                ),
                {"world_event_ref": world_event_ref},
            )
            .mappings()
            .all()
        )
        return tuple(dict(row) for row in rows)

    @staticmethod
    def _validate_evidence(
        *,
        evidence: tuple[dict[str, Any], ...],
        reveal_payload: dict[str, Any],
        world_event_ref: str,
        cutoff_tick: int,
        settled_at_tick: int,
    ) -> None:
        if not evidence:
            raise DreamStateError("dream_return_echo_committed_evidence_missing")
        reveal_evidence = {
            str(item["evidence_ref"]): dict(item)
            for item in reveal_payload["actual_evidence"]
        }
        if len(reveal_evidence) != len(reveal_payload["actual_evidence"]):
            raise DreamStateError("dream_return_echo_reveal_evidence_duplicate")
        evidence_refs = tuple(str(item["evidence_ref"]) for item in evidence)
        if evidence_refs != tuple(sorted(set(reveal_evidence))):
            raise DreamStateError("dream_return_echo_evidence_scope_mismatch")
        for item in evidence:
            ref = str(item["evidence_ref"])
            payload = dict(item["evidence_json"])
            if (
                item["world_event_ref"] != world_event_ref
                or payload != reveal_evidence[ref]
                or content_hash(payload) != item["evidence_hash"]
                or int(item["committed_at_tick"]) <= cutoff_tick
                or int(item["committed_at_tick"]) > settled_at_tick
            ):
                raise DreamStateError("dream_return_echo_committed_evidence_invalid")
