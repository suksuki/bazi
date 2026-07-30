from __future__ import annotations

from typing import Any

from pydantic import ValidationError
from sqlalchemy import text

from abu_v60.dream.attention_follow_through_contracts import (
    DreamAttentionFollowThrough,
    DreamAttentionFollowThroughStatus,
    DreamAttentionProgress,
    DreamAttentionWorldResponse,
    DreamPendingAttention,
)
from abu_v60.dream.errors import DreamStateError
from abu_v60.dream.grove import GroveCandidateDefinition
from abu_v60.dream.return_attention import DreamReturnAttentionCoordinator
from abu_v60.dream.return_attention_contracts import (
    DreamReturnAttentionApplication,
    DreamReturnAttentionRecord,
)
from abu_v60.dream.return_echo import DreamReturnEchoProjector
from abu_v60.dream.return_echo_contracts import DreamReturnEcho
from abu_v60.provenance import content_hash, stable_ref

_REQUIRED_ORGAN_KEYS = (
    "evidence_leaf_world",
    "evidence_leaf_structure",
    "structure_branch",
)
_REQUIRED_ORGAN_ROLES = {
    "evidence_leaf_world": "EVIDENCE_LEAF",
    "evidence_leaf_structure": "EVIDENCE_LEAF",
    "structure_branch": "STRUCTURE_BRANCH",
}
_RESPONSE_VISIBLE_STATUSES = {
    "WORLD_RESPONSE_AVAILABLE",
    "RECONCILED_NOT_EVALUATED",
    "RETURNED_NOT_EVALUATED",
}


class DreamAttentionFollowThroughProjector:
    """Derive pending, active and returned attention without new writes."""

    def __init__(
        self,
        *,
        coordinator: DreamReturnAttentionCoordinator,
        return_echo: DreamReturnEchoProjector,
    ) -> None:
        self._coordinator = coordinator
        self._return_echo = return_echo

    def pending_projection(
        self,
        connection: Any,
        *,
        account_ref: str,
    ) -> DreamPendingAttention | None:
        record = self._coordinator.oldest_pending_record(
            connection,
            account_ref=account_ref,
        )
        if record is None:
            return None
        self._validate_source(
            connection,
            account_ref=account_ref,
            record=record,
        )
        return DreamPendingAttention.issue(record=record)

    def grove_projections(
        self,
        connection: Any,
        *,
        account_ref: str,
        echo: DreamReturnEcho | None,
    ) -> dict[str, Any]:
        pending = self.pending_projection(
            connection,
            account_ref=account_ref,
        )
        returned = (
            self.returned_projection(
                connection,
                account_ref=account_ref,
                echo=echo,
            )
            if echo is not None
            else None
        )
        return {
            "pending_attention": (
                pending.model_dump(mode="json")
                if pending is not None
                else None
            ),
            "attention_follow_through": (
                returned.model_dump(mode="json")
                if returned is not None
                else None
            ),
        }

    def active_projection(
        self,
        connection: Any,
        *,
        account_ref: str,
        encounter: dict[str, Any],
        organ_set: dict[str, Any],
        world_event_ref: str,
        reveal: dict[str, Any] | None,
        revealed_evidence: tuple[dict[str, Any], ...],
    ) -> DreamAttentionFollowThrough | None:
        binding = self._coordinator.applied_binding(
            connection,
            account_ref=account_ref,
            encounter_ref=str(encounter["encounter_ref"]),
        )
        if binding is None:
            return None
        record, application = binding
        self._validate_source(
            connection,
            account_ref=account_ref,
            record=record,
        )
        self._validate_target(
            account_ref=account_ref,
            encounter=encounter,
            application=application,
        )
        progress = self._progress(
            organ_set=organ_set,
            state=dict(encounter["state_json"]),
        )
        status = self._status(
            encounter=encounter,
            progress=progress,
        )
        response = self._active_world_response(
            encounter=encounter,
            world_event_ref=world_event_ref,
            status=status,
            reveal=reveal,
            revealed_evidence=revealed_evidence,
        )
        return self._issue(
            record=record,
            application=application,
            status=status,
            progress=progress,
            world_response=response,
        )

    def returned_projection(
        self,
        connection: Any,
        *,
        account_ref: str,
        echo: DreamReturnEcho,
    ) -> DreamAttentionFollowThrough | None:
        binding = self._coordinator.applied_binding(
            connection,
            account_ref=account_ref,
            encounter_ref=echo.encounter_ref,
        )
        if binding is None:
            return None
        record, application = binding
        self._validate_source(
            connection,
            account_ref=account_ref,
            record=record,
        )
        rebuilt_target_echo = self._return_echo.project_for_encounter(
            connection,
            account_ref=account_ref,
            encounter_ref=application.encounter_ref,
        )
        if (
            rebuilt_target_echo is None
            or rebuilt_target_echo.echo_ref != echo.echo_ref
            or rebuilt_target_echo.echo_hash != echo.echo_hash
        ):
            raise DreamStateError(
                "dream_attention_returned_echo_mismatch"
            )
        target = (
            connection.execute(
                text(
                    """
                    SELECT encounter.*, question.organ_set_json
                    FROM dream.encounters AS encounter
                    JOIN story.question_instances AS question
                      ON question.question_ref = encounter.question_ref
                    WHERE encounter.encounter_ref = :encounter_ref
                      AND encounter.viewer_account_ref = :account_ref
                    """
                ),
                {
                    "encounter_ref": application.encounter_ref,
                    "account_ref": account_ref,
                },
            )
            .mappings()
            .one()
        )
        encounter = dict(target)
        self._validate_target(
            account_ref=account_ref,
            encounter=encounter,
            application=application,
        )
        progress = self._progress(
            organ_set=dict(target["organ_set_json"]),
            state=dict(encounter["state_json"]),
        )
        if (
            encounter["status"] != "COMPLETED"
            or not encounter["state_json"].get("reconciled")
            or not encounter["state_json"].get("departed_to_grove")
        ):
            raise DreamStateError(
                "dream_attention_returned_target_incomplete"
            )
        response = DreamAttentionWorldResponse(
            actual_event=echo.world_response.summary,
            evidence_refs=echo.lineage.committed_evidence_refs,
            evidence_summaries=echo.world_response.evidence_summaries,
            material_count=len(echo.lineage.committed_evidence_refs),
        )
        return self._issue(
            record=record,
            application=application,
            status="RETURNED_NOT_EVALUATED",
            progress=progress,
            world_response=response,
        )

    def _validate_source(
        self,
        connection: Any,
        *,
        account_ref: str,
        record: DreamReturnAttentionRecord,
    ) -> None:
        echo = self._return_echo.project_for_encounter(
            connection,
            account_ref=account_ref,
            encounter_ref=record.source_encounter_ref,
        )
        if (
            echo is None
            or record.viewer_account_ref != account_ref
            or echo.encounter_ref != record.source_encounter_ref
            or echo.echo_ref != record.source_echo_ref
            or echo.echo_hash != record.source_echo_hash
        ):
            raise DreamStateError(
                "dream_attention_source_echo_mismatch"
            )
        source = (
            connection.execute(
                text(
                    """
                    SELECT encounter.version, encounter.tree_ref,
                           encounter.actor_ref,
                           encounter.viewer_account_ref,
                           COALESCE(
                               event.event_json ->> 'source_question_ref',
                               question.question_ref
                           ) AS source_question_ref,
                           candidate.candidate_json,
                           candidate.candidate_hash
                    FROM dream.encounters AS encounter
                    JOIN story.question_instances AS question
                      ON question.question_ref = encounter.question_ref
                    JOIN world.events AS event
                      ON event.world_event_ref = question.world_event_ref
                    JOIN dream.grove_candidates AS candidate
                      ON candidate.candidate_ref = :candidate_ref
                     AND candidate.tree_ref = encounter.tree_ref
                     AND candidate.runtime_status = 'ACTIVE'
                    WHERE encounter.encounter_ref = :encounter_ref
                      AND encounter.viewer_account_ref = :account_ref
                    """
                ),
                {
                    "candidate_ref": record.source_candidate_ref,
                    "encounter_ref": record.source_encounter_ref,
                    "account_ref": account_ref,
                },
            )
            .mappings()
            .one_or_none()
        )
        if source is None:
            raise DreamStateError(
                "dream_attention_source_candidate_missing"
            )
        try:
            candidate = GroveCandidateDefinition.model_validate(
                {
                    **source["candidate_json"],
                    "candidate_hash": source["candidate_hash"],
                }
            )
        except (ValidationError, ValueError) as exc:
            raise DreamStateError(
                "dream_attention_source_candidate_invalid"
            ) from exc
        options = DreamReturnAttentionCoordinator._options(echo)
        selected = next(
            (
                option
                for option in options
                if option.observation_ref
                == record.observation.observation_ref
            ),
            None,
        )
        if (
            int(source["version"]) != record.source_encounter_version
            or source["tree_ref"] != record.tree_ref
            or source["viewer_account_ref"] != account_ref
            or candidate.candidate_ref != record.source_candidate_ref
            or candidate.candidate_hash != record.source_candidate_hash
            or candidate.tree_ref != record.tree_ref
            or candidate.actor_ref != source["actor_ref"]
            or candidate.question_ref != source["source_question_ref"]
            or selected is None
            or selected != record.observation
        ):
            raise DreamStateError(
                "dream_attention_source_lineage_mismatch"
            )

    @staticmethod
    def _validate_target(
        *,
        account_ref: str,
        encounter: dict[str, Any],
        application: DreamReturnAttentionApplication,
    ) -> None:
        state = dict(encounter["state_json"])
        if (
            encounter["viewer_account_ref"] != account_ref
            or application.viewer_account_ref != account_ref
            or encounter["encounter_ref"] != application.encounter_ref
            or encounter["tree_ref"] != application.tree_ref
            or content_hash(state) != encounter["state_hash"]
        ):
            raise DreamStateError(
                "dream_attention_target_lineage_mismatch"
            )

    @staticmethod
    def _progress(
        *,
        organ_set: dict[str, Any],
        state: dict[str, Any],
    ) -> DreamAttentionProgress:
        for key in _REQUIRED_ORGAN_KEYS:
            organ = organ_set.get(key)
            if (
                not isinstance(organ, dict)
                or organ.get("role") != _REQUIRED_ORGAN_ROLES[key]
                or not organ.get("organ_ref")
            ):
                raise DreamStateError(
                    "dream_attention_required_organ_invalid"
                )
        required_refs = [
            str(organ["organ_ref"])
            for key, organ in organ_set.items()
            if key in _REQUIRED_ORGAN_ROLES
        ]
        if len(set(required_refs)) != 3:
            raise DreamStateError(
                "dream_attention_required_organs_not_unique"
            )
        observed = tuple(str(ref) for ref in state["observed_organs"])
        if len(observed) != len(set(observed)) or not set(observed).issubset(
            required_refs
        ):
            raise DreamStateError(
                "dream_attention_observed_organs_invalid"
            )
        ordered_observed = tuple(
            ref for ref in required_refs if ref in set(observed)
        )
        return DreamAttentionProgress(
            required_count=3,
            observed_count=len(ordered_observed),
            required_organ_refs=tuple(required_refs),
            observed_organ_refs=ordered_observed,
        )

    @staticmethod
    def _status(
        *,
        encounter: dict[str, Any],
        progress: DreamAttentionProgress,
    ) -> DreamAttentionFollowThroughStatus:
        status = str(encounter["status"])
        if status == "OBSERVING":
            return (
                "OBSERVATIONS_COMPLETE"
                if progress.observed_count == 3
                else "OBSERVING"
            )
        mapping: dict[str, DreamAttentionFollowThroughStatus] = {
            "QUESTION_OPEN": "OBSERVATIONS_COMPLETE",
            "WAITING_FOR_WORLD": "AWAITING_WORLD_RESPONSE",
            "REVEAL_READY": "WORLD_RESPONSE_READY_HIDDEN",
            "REVEALED": "WORLD_RESPONSE_AVAILABLE",
            "COMPLETED": "RECONCILED_NOT_EVALUATED",
        }
        try:
            return mapping[status]
        except KeyError as exc:
            raise DreamStateError(
                "dream_attention_target_status_invalid"
            ) from exc

    @staticmethod
    def _active_world_response(
        *,
        encounter: dict[str, Any],
        world_event_ref: str,
        status: DreamAttentionFollowThroughStatus,
        reveal: dict[str, Any] | None,
        revealed_evidence: tuple[dict[str, Any], ...],
    ) -> DreamAttentionWorldResponse | None:
        if status not in _RESPONSE_VISIBLE_STATUSES:
            if reveal is not None or revealed_evidence:
                raise DreamStateError(
                    "dream_attention_pre_reveal_response_leak"
                )
            return None
        if reveal is None or not revealed_evidence:
            raise DreamStateError(
                "dream_attention_world_response_missing"
            )
        reveal_payload = dict(reveal["reveal_json"])
        if (
            reveal.get("encounter_ref") != encounter["encounter_ref"]
            or reveal.get("world_event_ref") != world_event_ref
            or content_hash(reveal_payload) != reveal.get("reveal_hash")
            or stable_ref("v60-reveal", reveal["reveal_hash"])
            != reveal.get("reveal_ref")
        ):
            raise DreamStateError(
                "dream_attention_reveal_invalid"
            )
        by_ref = {
            str(item["evidence_ref"]): dict(item)
            for item in reveal_payload["actual_evidence"]
        }
        refs = tuple(
            str(item["evidence_ref"])
            for item in revealed_evidence
        )
        if refs != tuple(sorted(set(by_ref))):
            raise DreamStateError(
                "dream_attention_reveal_evidence_scope_mismatch"
            )
        summaries: list[str] = []
        for item in revealed_evidence:
            ref = str(item["evidence_ref"])
            payload = dict(item["evidence_json"])
            if (
                payload != by_ref[ref]
                or content_hash(payload) != item["evidence_hash"]
                or item["world_event_ref"] != reveal["world_event_ref"]
            ):
                raise DreamStateError(
                    "dream_attention_reveal_evidence_invalid"
                )
            summaries.append(str(payload["summary"]))
        return DreamAttentionWorldResponse(
            actual_event=str(reveal_payload["actual_event"]),
            evidence_refs=refs,
            evidence_summaries=tuple(summaries),
            material_count=len(refs),
        )

    @staticmethod
    def _issue(
        *,
        record: DreamReturnAttentionRecord,
        application: DreamReturnAttentionApplication,
        status: DreamAttentionFollowThroughStatus,
        progress: DreamAttentionProgress,
        world_response: DreamAttentionWorldResponse | None,
    ) -> DreamAttentionFollowThrough:
        try:
            return DreamAttentionFollowThrough.issue(
                record=record,
                application=application,
                status=status,
                progress=progress,
                world_response=world_response,
            )
        except ValueError as exc:
            raise DreamStateError(
                "dream_attention_follow_through_invalid"
            ) from exc
