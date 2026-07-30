from __future__ import annotations

from typing import Any

from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.engine import Engine

from abu_v60.dream.catalog import DreamEpisodeCatalog
from abu_v60.dream.errors import DreamConflictError, DreamStateError
from abu_v60.dream.grove import GroveCandidateDefinition
from abu_v60.dream.grove_candidate_lineage import (
    candidate_source_lineage_is_valid,
)
from abu_v60.dream.persistence import DreamRepository
from abu_v60.dream.return_attention_contracts import (
    DreamOpeningAttention,
    DreamReturnAttentionApplication,
    DreamReturnAttentionOption,
    DreamReturnAttentionPrompt,
    DreamReturnAttentionRecord,
)
from abu_v60.dream.return_echo import DreamReturnEchoProjector
from abu_v60.dream.return_echo_contracts import DreamReturnEcho
from abu_v60.game import DreamCommand, DreamCommandEnvelope
from abu_v60.provenance import canonical_json, stable_ref


class DreamReturnAttentionCoordinator:
    """Own one Dream-only attention from Grove choice through same-tree opening."""

    def __init__(
        self,
        *,
        repository: DreamRepository,
        return_echo: DreamReturnEchoProjector,
    ) -> None:
        self._repository = repository
        self._return_echo = return_echo
        self._episodes = DreamEpisodeCatalog()

    def project_prompt(
        self,
        connection: Any,
        *,
        account_ref: str,
        echo: DreamReturnEcho,
    ) -> DreamReturnAttentionPrompt | None:
        source = self._source_context(
            connection,
            account_ref=account_ref,
            encounter_ref=echo.encounter_ref,
            for_update=False,
            allow_missing_candidate=True,
        )
        if source is None:
            return None
        record = self._selection_for_source(
            connection,
            account_ref=account_ref,
            source_encounter_ref=echo.encounter_ref,
        )
        return self._issue_prompt(
            echo=echo,
            source=source,
            record=record,
        )

    def execute_selection(
        self,
        engine: Engine,
        *,
        account_ref: str,
        envelope: DreamCommandEnvelope,
    ) -> None:
        if envelope.command is not DreamCommand.SELECT_NEXT_ATTENTION:
            raise DreamStateError("dream_return_attention_command_invalid")
        with engine.begin() as connection:
            self._lock_account(
                connection,
                account_ref=account_ref,
            )
            if self._repository.command_replayed(
                connection=connection,
                account_ref=account_ref,
                envelope=envelope,
            ):
                return
            if (
                self._repository.current_encounter(
                    connection,
                    account_ref=account_ref,
                    for_update=False,
                )
                is not None
            ):
                raise DreamConflictError(
                    "dream_return_attention_requires_grove"
                )
            source = self._source_context(
                connection,
                account_ref=account_ref,
                encounter_ref=envelope.encounter_ref,
                for_update=True,
                allow_missing_candidate=False,
            )
            if source is None:
                raise DreamStateError(
                    "dream_return_attention_source_candidate_invalid"
                )
            if int(source["version"]) != envelope.expected_version:
                raise DreamConflictError("dream_command_version_conflict")
            echo = self._return_echo.project(
                connection,
                account_ref=account_ref,
            )
            if echo is None or echo.encounter_ref != envelope.encounter_ref:
                raise DreamConflictError(
                    "dream_return_attention_requires_latest_echo"
                )
            existing = self._selection_for_source(
                connection,
                account_ref=account_ref,
                source_encounter_ref=envelope.encounter_ref,
            )
            if existing is not None:
                raise DreamConflictError(
                    "dream_return_attention_already_selected"
                )
            prompt = self._issue_prompt(
                echo=echo,
                source=source,
                record=None,
            )
            selected = next(
                (
                    option
                    for option in prompt.options
                    if option.observation_ref == envelope.target_ref
                ),
                None,
            )
            if selected is None:
                raise DreamStateError(
                    "dream_return_attention_option_not_admitted"
                )
            record = DreamReturnAttentionRecord.issue(
                viewer_account_ref=account_ref,
                source_encounter_ref=envelope.encounter_ref,
                source_encounter_version=envelope.expected_version,
                source_echo_ref=echo.echo_ref,
                source_echo_hash=echo.echo_hash,
                source_candidate_ref=source["candidate"].candidate_ref,
                source_candidate_hash=source["candidate"].candidate_hash,
                tree_ref=source["tree_ref"],
                observation=selected,
                idempotency_key=envelope.idempotency_key,
            )
            self._insert_selection(connection, record=record)
            self._repository.record_command_receipt(
                connection=connection,
                account_ref=account_ref,
                envelope=envelope,
                result_encounter_ref=envelope.encounter_ref,
            )

    @staticmethod
    def _lock_account(connection: Any, *, account_ref: str) -> None:
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
            raise DreamStateError("dream_return_attention_account_not_found")

    def apply_pending(
        self,
        connection: Any,
        *,
        account_ref: str,
        encounter_ref: str,
        tree_ref: str,
    ) -> None:
        target = (
            connection.execute(
                text(
                    """
                    SELECT viewer_account_ref, tree_ref
                    FROM dream.encounters
                    WHERE encounter_ref = :encounter_ref
                    """
                ),
                {"encounter_ref": encounter_ref},
            )
            .mappings()
            .one()
        )
        if (
            target["viewer_account_ref"] != account_ref
            or target["tree_ref"] != tree_ref
        ):
            raise DreamStateError(
                "dream_opening_attention_target_identity_mismatch"
            )
        row = (
            connection.execute(
                text(
                    """
                    SELECT selection.attention_ref,
                           selection.viewer_account_ref,
                           selection.source_encounter_ref,
                           selection.source_encounter_version,
                           selection.source_echo_ref,
                           selection.source_echo_hash,
                           selection.source_candidate_ref,
                           selection.source_candidate_hash,
                           selection.tree_ref,
                           selection.observation_ref,
                           selection.idempotency_key,
                           selection.record_json, selection.record_hash
                    FROM dream.return_attention_selections AS selection
                    LEFT JOIN dream.return_attention_applications AS application
                      ON application.attention_ref = selection.attention_ref
                    WHERE selection.viewer_account_ref = :account_ref
                      AND selection.tree_ref = :tree_ref
                      AND application.attention_ref IS NULL
                    ORDER BY selection.created_at, selection.attention_ref
                    LIMIT 1
                    FOR UPDATE OF selection
                    """
                ),
                {
                    "account_ref": account_ref,
                    "tree_ref": tree_ref,
                },
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return
        record = self._validate_record(row)
        application = DreamReturnAttentionApplication.issue(
            viewer_account_ref=account_ref,
            attention_ref=record.attention_ref,
            attention_hash=record.attention_hash,
            encounter_ref=encounter_ref,
            tree_ref=tree_ref,
        )
        self._insert_application(
            connection,
            application=application,
        )

    def opening_projection(
        self,
        connection: Any,
        *,
        account_ref: str,
        encounter_ref: str,
    ) -> DreamOpeningAttention | None:
        binding = self.applied_binding(
            connection,
            account_ref=account_ref,
            encounter_ref=encounter_ref,
        )
        if binding is None:
            return None
        record, application = binding
        try:
            return DreamOpeningAttention.issue(
                record=record,
                application=application,
            )
        except ValueError as exc:
            raise DreamStateError(
                "dream_opening_attention_lineage_invalid"
            ) from exc

    def oldest_pending_record(
        self,
        connection: Any,
        *,
        account_ref: str,
    ) -> DreamReturnAttentionRecord | None:
        row = (
            connection.execute(
                text(
                    """
                    SELECT selection.attention_ref,
                           selection.viewer_account_ref,
                           selection.source_encounter_ref,
                           selection.source_encounter_version,
                           selection.source_echo_ref,
                           selection.source_echo_hash,
                           selection.source_candidate_ref,
                           selection.source_candidate_hash,
                           selection.tree_ref,
                           selection.observation_ref,
                           selection.idempotency_key,
                           selection.record_json,
                           selection.record_hash
                    FROM dream.return_attention_selections AS selection
                    LEFT JOIN dream.return_attention_applications AS application
                      ON application.attention_ref = selection.attention_ref
                    WHERE selection.viewer_account_ref = :account_ref
                      AND application.attention_ref IS NULL
                    ORDER BY selection.created_at, selection.attention_ref
                    LIMIT 1
                    """
                ),
                {"account_ref": account_ref},
            )
            .mappings()
            .one_or_none()
        )
        return self._validate_record(row) if row is not None else None

    def applied_binding(
        self,
        connection: Any,
        *,
        account_ref: str,
        encounter_ref: str,
    ) -> tuple[
        DreamReturnAttentionRecord,
        DreamReturnAttentionApplication,
    ] | None:
        row = (
            connection.execute(
                text(
                    """
                    SELECT selection.attention_ref,
                           selection.viewer_account_ref,
                           selection.source_encounter_ref,
                           selection.source_encounter_version,
                           selection.source_echo_ref,
                           selection.source_echo_hash,
                           selection.source_candidate_ref,
                           selection.source_candidate_hash,
                           selection.tree_ref,
                           selection.observation_ref,
                           selection.idempotency_key,
                           selection.record_json, selection.record_hash,
                           application.application_ref,
                           application.viewer_account_ref
                               AS application_viewer_account_ref,
                           application.attention_ref
                               AS application_attention_ref,
                           application.encounter_ref
                               AS application_encounter_ref,
                           application.tree_ref AS application_tree_ref,
                           application.application_json,
                           application.application_hash,
                           target.viewer_account_ref
                               AS target_viewer_account_ref,
                           target.tree_ref AS target_tree_ref
                    FROM dream.return_attention_applications AS application
                    JOIN dream.return_attention_selections AS selection
                      ON selection.attention_ref = application.attention_ref
                    JOIN dream.encounters AS target
                      ON target.encounter_ref = application.encounter_ref
                    WHERE application.viewer_account_ref = :account_ref
                      AND application.encounter_ref = :encounter_ref
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
        if row is None:
            return None
        record = self._validate_record(row)
        application = self._validate_application(row)
        if (
            application.viewer_account_ref != account_ref
            or application.encounter_ref != encounter_ref
            or row["target_viewer_account_ref"] != account_ref
            or row["target_tree_ref"] != application.tree_ref
            or record.viewer_account_ref != account_ref
            or record.tree_ref != application.tree_ref
        ):
            raise DreamStateError(
                "dream_opening_attention_target_identity_mismatch"
            )
        return record, application

    @staticmethod
    def _issue_prompt(
        *,
        echo: DreamReturnEcho,
        source: dict[str, Any],
        record: DreamReturnAttentionRecord | None,
    ) -> DreamReturnAttentionPrompt:
        options = DreamReturnAttentionCoordinator._options(echo)
        if record is not None:
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
                record.viewer_account_ref != source["viewer_account_ref"]
                or record.source_encounter_ref != echo.encounter_ref
                or record.source_encounter_version != int(source["version"])
                or record.source_echo_ref != echo.echo_ref
                or record.source_echo_hash != echo.echo_hash
                or record.source_candidate_ref
                != source["candidate"].candidate_ref
                or record.source_candidate_hash
                != source["candidate"].candidate_hash
                or record.tree_ref != source["tree_ref"]
                or selected is None
                or selected != record.observation
            ):
                raise DreamStateError(
                    "dream_return_attention_projection_lineage_mismatch"
                )
        return DreamReturnAttentionPrompt(
            source_encounter_ref=echo.encounter_ref,
            source_encounter_version=int(source["version"]),
            source_echo_ref=echo.echo_ref,
            source_echo_hash=echo.echo_hash,
            source_candidate_ref=source["candidate"].candidate_ref,
            source_candidate_hash=source["candidate"].candidate_hash,
            tree_ref=source["tree_ref"],
            status=(
                "SELECTED"
                if record is not None
                else "AWAITING_SELECTION"
            ),
            options=options,
            selection=(
                record.public_selection()
                if record is not None
                else None
            ),
            semantics="DREAM_RETURN_ATTENTION_ONLY",
            evidence_role="NOT_EVIDENCE",
            tree_candidate_set_or_order_changed=False,
            question_changed=False,
            answer_changed=False,
            npc_choice_changed=False,
            outcome_changed=False,
            mingli_write_allowed=False,
            decision_write_allowed=False,
            knowledge_write_allowed=False,
        )

    @staticmethod
    def _options(
        echo: DreamReturnEcho,
    ) -> tuple[DreamReturnAttentionOption, ...]:
        candidates: list[tuple[str, str, str]] = [
            (
                "WORLD_RESPONSE",
                "再看结果如何落地",
                echo.world_response.summary,
            )
        ]
        candidates.extend(
            (
                "OUTCOME_EVIDENCE",
                f"再核对第{index}条事实",
                summary,
            )
            for index, summary in enumerate(
                echo.world_response.evidence_summaries[:2],
                start=1,
            )
        )
        if len(candidates) < 3:
            candidates.append(
                (
                    "OPEN_OBSERVATION",
                    "再留意尚未说明的部分",
                    echo.still_to_observe.summary,
                )
            )
        return tuple(
            DreamReturnAttentionOption(
                observation_ref=stable_ref(
                    "v60-dream-return-observation",
                    {
                        "source_echo_ref": echo.echo_ref,
                        "kind": kind,
                        "label": label,
                        "summary": summary,
                    },
                ),
                kind=kind,
                label=label,
                summary=summary,
            )
            for kind, label, summary in candidates
        )

    def _source_context(
        self,
        connection: Any,
        *,
        account_ref: str,
        encounter_ref: str,
        for_update: bool,
        allow_missing_candidate: bool,
    ) -> dict[str, Any] | None:
        lock_clause = "FOR UPDATE OF encounter" if for_update else ""
        rows = (
            connection.execute(
                text(
                    f"""
                    SELECT encounter.encounter_ref,
                           encounter.viewer_account_ref,
                           encounter.actor_ref, encounter.question_ref,
                           encounter.version, encounter.tree_ref,
                           encounter.status,
                           encounter.state_json, candidate.candidate_json,
                           candidate.candidate_hash,
                           COALESCE(
                               event.event_json ->> 'source_question_ref',
                               encounter.question_ref
                           ) AS source_question_ref,
                           event.event_json
                    FROM dream.encounters AS encounter
                    JOIN story.question_instances AS question
                      ON question.question_ref = encounter.question_ref
                    JOIN world.events AS event
                      ON event.world_event_ref = question.world_event_ref
                    LEFT JOIN dream.grove_candidates AS candidate
                      ON (
                            candidate.candidate_ref = event.event_json
                                ->> 'source_candidate_ref'
                            OR (
                                event.event_json
                                    ->> 'source_candidate_ref' IS NULL
                                AND candidate.question_ref = COALESCE(
                                    event.event_json
                                        ->> 'source_question_ref',
                                    encounter.question_ref
                                )
                            )
                         )
                     AND candidate.tree_ref = encounter.tree_ref
                     AND candidate.actor_ref = encounter.actor_ref
                     AND candidate.runtime_status = 'ACTIVE'
                    WHERE encounter.encounter_ref = :encounter_ref
                      AND encounter.viewer_account_ref = :account_ref
                    ORDER BY candidate.candidate_ref
                    {lock_clause}
                    """
                ),
                {
                    "account_ref": account_ref,
                    "encounter_ref": encounter_ref,
                },
            )
            .mappings()
            .all()
        )
        if len(rows) != 1:
            raise DreamStateError(
                "dream_return_attention_source_candidate_invalid"
            )
        row = dict(rows[0])
        if (
            row["status"] != "COMPLETED"
            or row["state_json"].get("departed_to_grove") is not True
        ):
            raise DreamStateError(
                "dream_return_attention_requires_departed_encounter"
            )
        if row["candidate_json"] is None:
            if allow_missing_candidate:
                return None
            raise DreamStateError(
                "dream_return_attention_source_candidate_invalid"
            )
        try:
            row["candidate"] = GroveCandidateDefinition.model_validate(
                {
                    **row["candidate_json"],
                    "candidate_hash": row["candidate_hash"],
                }
            )
        except (ValidationError, ValueError) as exc:
            raise DreamStateError(
                "dream_return_attention_source_candidate_invalid"
            ) from exc
        if (
            row["candidate"].tree_ref != row["tree_ref"]
            or row["candidate"].actor_ref != row["actor_ref"]
            or row["candidate"].runtime_status != "ACTIVE"
            or not candidate_source_lineage_is_valid(
                catalog=self._episodes.load(connection),
                candidate=row["candidate"],
                source_question_ref=str(row["source_question_ref"]),
                event_payload=dict(row["event_json"]),
            )
        ):
            if allow_missing_candidate:
                return None
            raise DreamStateError(
                "dream_return_attention_source_candidate_invalid"
            )
        return row

    @staticmethod
    def _selection_for_source(
        connection: Any,
        *,
        account_ref: str,
        source_encounter_ref: str,
    ) -> DreamReturnAttentionRecord | None:
        row = (
            connection.execute(
                text(
                    """
                    SELECT attention_ref, viewer_account_ref,
                           source_encounter_ref, source_encounter_version,
                           source_echo_ref, source_echo_hash,
                           source_candidate_ref, source_candidate_hash,
                           tree_ref, observation_ref,
                           idempotency_key, record_json, record_hash
                    FROM dream.return_attention_selections
                    WHERE viewer_account_ref = :account_ref
                      AND source_encounter_ref = :source_encounter_ref
                    """
                ),
                {
                    "account_ref": account_ref,
                    "source_encounter_ref": source_encounter_ref,
                },
            )
            .mappings()
            .one_or_none()
        )
        return (
            DreamReturnAttentionCoordinator._validate_record(row)
            if row is not None
            else None
        )

    @staticmethod
    def _validate_record(row: Any) -> DreamReturnAttentionRecord:
        try:
            record = DreamReturnAttentionRecord.model_validate(
                row["record_json"]
            )
        except (ValidationError, ValueError) as exc:
            raise DreamStateError(
                "dream_return_attention_record_invalid"
            ) from exc
        if record.attention_hash != row["record_hash"]:
            raise DreamStateError(
                "dream_return_attention_record_hash_mismatch"
            )
        expected_columns = {
            "attention_ref": record.attention_ref,
            "viewer_account_ref": record.viewer_account_ref,
            "source_encounter_ref": record.source_encounter_ref,
            "source_encounter_version": record.source_encounter_version,
            "source_echo_ref": record.source_echo_ref,
            "source_echo_hash": record.source_echo_hash,
            "source_candidate_ref": record.source_candidate_ref,
            "source_candidate_hash": record.source_candidate_hash,
            "tree_ref": record.tree_ref,
            "observation_ref": record.observation.observation_ref,
            "idempotency_key": record.idempotency_key,
        }
        if any(
            key in row and row[key] != value
            for key, value in expected_columns.items()
        ):
            raise DreamStateError(
                "dream_return_attention_record_column_mismatch"
            )
        return record

    @staticmethod
    def _validate_application(
        row: Any,
    ) -> DreamReturnAttentionApplication:
        try:
            application = DreamReturnAttentionApplication.model_validate(
                row["application_json"]
            )
        except (ValidationError, ValueError) as exc:
            raise DreamStateError(
                "dream_opening_attention_application_invalid"
            ) from exc
        if application.application_hash != row["application_hash"]:
            raise DreamStateError(
                "dream_opening_attention_application_hash_mismatch"
            )
        expected_columns = {
            "application_ref": application.application_ref,
            "application_viewer_account_ref": (
                application.viewer_account_ref
            ),
            "application_attention_ref": application.attention_ref,
            "application_encounter_ref": application.encounter_ref,
            "application_tree_ref": application.tree_ref,
        }
        if any(
            key in row and row[key] != value
            for key, value in expected_columns.items()
        ):
            raise DreamStateError(
                "dream_opening_attention_application_column_mismatch"
            )
        return application

    @staticmethod
    def _insert_selection(
        connection: Any,
        *,
        record: DreamReturnAttentionRecord,
    ) -> None:
        inserted = connection.execute(
            text(
                """
                INSERT INTO dream.return_attention_selections
                    (attention_ref, viewer_account_ref,
                     source_encounter_ref, source_encounter_version,
                     source_echo_ref,
                     source_echo_hash, source_candidate_ref,
                     source_candidate_hash, tree_ref,
                     observation_ref, idempotency_key,
                     record_json, record_hash)
                VALUES
                    (:attention_ref, :viewer_account_ref,
                     :source_encounter_ref, :source_encounter_version,
                     :source_echo_ref,
                     :source_echo_hash, :source_candidate_ref,
                     :source_candidate_hash, :tree_ref,
                     :observation_ref, :idempotency_key,
                     CAST(:record_json AS jsonb), :record_hash)
                ON CONFLICT DO NOTHING
                RETURNING attention_ref
                """
            ),
            {
                "attention_ref": record.attention_ref,
                "viewer_account_ref": record.viewer_account_ref,
                "source_encounter_ref": record.source_encounter_ref,
                "source_encounter_version": (
                    record.source_encounter_version
                ),
                "source_echo_ref": record.source_echo_ref,
                "source_echo_hash": record.source_echo_hash,
                "source_candidate_ref": record.source_candidate_ref,
                "source_candidate_hash": record.source_candidate_hash,
                "tree_ref": record.tree_ref,
                "observation_ref": record.observation.observation_ref,
                "idempotency_key": record.idempotency_key,
                "record_json": canonical_json(
                    record.model_dump(mode="json")
                ),
                "record_hash": record.attention_hash,
            },
        ).scalar_one_or_none()
        if inserted is None:
            raise DreamConflictError(
                "dream_return_attention_selection_conflict"
            )

    @staticmethod
    def _insert_application(
        connection: Any,
        *,
        application: DreamReturnAttentionApplication,
    ) -> None:
        inserted = connection.execute(
            text(
                """
                INSERT INTO dream.return_attention_applications
                    (application_ref, viewer_account_ref, attention_ref,
                     encounter_ref, tree_ref, application_json,
                     application_hash)
                VALUES
                    (:application_ref, :viewer_account_ref, :attention_ref,
                     :encounter_ref, :tree_ref, CAST(:application_json AS jsonb),
                     :application_hash)
                ON CONFLICT DO NOTHING
                RETURNING application_ref
                """
            ),
            {
                **application.model_dump(
                    mode="python",
                    include={
                        "application_ref",
                        "viewer_account_ref",
                        "attention_ref",
                        "encounter_ref",
                        "tree_ref",
                        "application_hash",
                    },
                ),
                "application_json": canonical_json(
                    application.model_dump(mode="json")
                ),
            },
        ).scalar_one_or_none()
        if inserted is None:
            raise DreamConflictError(
                "dream_opening_attention_application_conflict"
            )
