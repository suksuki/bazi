from __future__ import annotations

from typing import Any

from pydantic import ValidationError
from sqlalchemy import text

from abu_v60.dream.errors import DreamStateError
from abu_v60.dream.personal_journey_contracts import (
    DreamPersonalCheckInRecord,
    DreamPersonalObservationTask,
    DreamPrivateInquiryRecord,
)
from abu_v60.identity import lock_account_transaction
from abu_v60.provenance import canonical_json


class DreamPersonalJourneyStore:
    """Persist and validate the account-private personal journey ledger."""

    @staticmethod
    def lock_account(connection: Any, *, account_ref: str) -> None:
        lock_account_transaction(
            connection,
            account_ref=account_ref,
        )
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
            raise DreamStateError("dream_personal_journey_account_not_found")

    @staticmethod
    def owner_context(
        connection: Any,
        *,
        account_ref: str,
    ) -> dict[str, str]:
        rows = (
            connection.execute(
                text(
                    """
                    SELECT active_case.case_ref,
                           revision.life_case_revision_ref,
                           reading.reading_ref,
                           reading.reading_hash
                    FROM mingli.cases AS active_case
                    JOIN LATERAL (
                        SELECT life_case_revision_ref
                        FROM mingli.life_case_revisions
                        WHERE case_ref = active_case.case_ref
                        ORDER BY revision DESC, created_at DESC
                        LIMIT 1
                    ) AS revision ON true
                    JOIN LATERAL (
                        SELECT reading_ref, reading_hash
                        FROM mingli.readings
                        WHERE case_ref = active_case.case_ref
                          AND life_case_revision_ref =
                              revision.life_case_revision_ref
                        ORDER BY created_at DESC, reading_ref DESC
                        LIMIT 1
                    ) AS reading ON true
                    WHERE active_case.owner_account_ref = :account_ref
                      AND active_case.subject_kind = 'HUMAN_OWNER'
                      AND active_case.status = 'ACTIVE'
                    ORDER BY active_case.case_ref
                    """
                ),
                {"account_ref": account_ref},
            )
            .mappings()
            .all()
        )
        if len(rows) != 1:
            raise DreamStateError("dream_private_inquiry_requires_one_active_owner_case")
        return dict(rows[0])

    @staticmethod
    def owner_timezone(
        connection: Any,
        *,
        account_ref: str,
        inquiry: DreamPrivateInquiryRecord,
    ) -> str:
        timezone = connection.execute(
            text(
                """
                SELECT profile.timezone
                FROM mingli.cases AS owner_case
                JOIN identity.profiles AS profile
                  ON profile.profile_ref = owner_case.profile_ref
                WHERE owner_case.case_ref = :case_ref
                  AND owner_case.owner_account_ref = :account_ref
                  AND owner_case.subject_kind = 'HUMAN_OWNER'
                """
            ),
            {
                "account_ref": account_ref,
                "case_ref": inquiry.case_ref,
            },
        ).scalar_one_or_none()
        if timezone is None:
            raise DreamStateError("dream_private_inquiry_owner_timezone_missing")
        return str(timezone)

    @staticmethod
    def validate_inquiry(row: Any) -> DreamPrivateInquiryRecord:
        try:
            record = DreamPrivateInquiryRecord.model_validate(row["inquiry_json"])
        except (ValidationError, ValueError) as exc:
            raise DreamStateError("dream_private_inquiry_record_invalid") from exc
        if (
            record.inquiry_ref != row["inquiry_ref"]
            or record.inquiry_hash != row["inquiry_hash"]
            or record.viewer_account_ref != row["viewer_account_ref"]
            or record.case_ref != row["case_ref"]
            or record.life_case_revision_ref != row["life_case_revision_ref"]
            or record.reading_ref != row["reading_ref"]
            or record.candidate_ref != row["candidate_ref"]
            or record.encounter_ref != row["encounter_ref"]
            or record.domain != row["domain"]
            or record.idempotency_key != row["idempotency_key"]
        ):
            raise DreamStateError("dream_private_inquiry_column_mismatch")
        return record

    @staticmethod
    def validate_task(row: Any) -> DreamPersonalObservationTask:
        try:
            record = DreamPersonalObservationTask.model_validate(row["task_json"])
        except (ValidationError, ValueError) as exc:
            raise DreamStateError("dream_personal_observation_record_invalid") from exc
        if (
            record.task_ref != row["task_ref"]
            or record.task_hash != row["task_hash"]
            or record.viewer_account_ref != row["viewer_account_ref"]
            or record.inquiry_ref != row["inquiry_ref"]
            or record.encounter_ref != row["encounter_ref"]
            or record.option.option_ref != row["option_ref"]
            or record.checkpoint_on != row["checkpoint_on"]
            or record.idempotency_key != row["idempotency_key"]
        ):
            raise DreamStateError("dream_personal_observation_column_mismatch")
        return record

    @staticmethod
    def validate_checkin(row: Any) -> DreamPersonalCheckInRecord:
        try:
            record = DreamPersonalCheckInRecord.model_validate(row["checkin_json"])
        except (ValidationError, ValueError) as exc:
            raise DreamStateError("dream_personal_checkin_record_invalid") from exc
        if (
            record.checkin_ref != row["checkin_ref"]
            or record.checkin_hash != row["checkin_hash"]
            or record.viewer_account_ref != row["viewer_account_ref"]
            or record.inquiry_ref != row["inquiry_ref"]
            or record.task_ref != row["task_ref"]
            or record.status != row["status"]
            or record.checked_in_on != row["checked_in_on"]
            or record.idempotency_key != row["idempotency_key"]
        ):
            raise DreamStateError("dream_personal_checkin_column_mismatch")
        return record

    def latest_inquiry(
        self,
        connection: Any,
        *,
        account_ref: str,
    ) -> DreamPrivateInquiryRecord | None:
        row = (
            connection.execute(
                text(
                    """
                    SELECT inquiry_ref, inquiry_hash, viewer_account_ref,
                           case_ref, life_case_revision_ref, reading_ref,
                           candidate_ref, encounter_ref, domain,
                           idempotency_key, inquiry_json
                    FROM dream.private_inquiries AS inquiry
                    WHERE inquiry.viewer_account_ref = :account_ref
                      AND NOT EXISTS (
                          SELECT 1
                          FROM dream.private_inquiries AS successor
                          WHERE successor.viewer_account_ref =
                                inquiry.viewer_account_ref
                            AND successor.inquiry_json
                                  ->> 'supersedes_inquiry_ref' =
                                inquiry.inquiry_ref
                      )
                    """
                ),
                {"account_ref": account_ref},
            )
            .mappings()
            .one_or_none()
        )
        return self.validate_inquiry(row) if row is not None else None

    def inquiry(
        self,
        connection: Any,
        *,
        account_ref: str,
        inquiry_ref: str,
        for_update: bool,
    ) -> DreamPrivateInquiryRecord:
        lock_clause = "FOR UPDATE" if for_update else ""
        row = (
            connection.execute(
                text(
                    f"""
                    SELECT inquiry_ref, inquiry_hash, viewer_account_ref,
                           case_ref, life_case_revision_ref, reading_ref,
                           candidate_ref, encounter_ref, domain,
                           idempotency_key, inquiry_json
                    FROM dream.private_inquiries
                    WHERE viewer_account_ref = :account_ref
                      AND inquiry_ref = :inquiry_ref
                    {lock_clause}
                    """
                ),
                {
                    "account_ref": account_ref,
                    "inquiry_ref": inquiry_ref,
                },
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise DreamStateError("dream_private_inquiry_not_found")
        return self.validate_inquiry(row)

    def inquiry_for_encounter(
        self,
        connection: Any,
        *,
        account_ref: str,
        encounter_ref: str,
    ) -> DreamPrivateInquiryRecord | None:
        row = (
            connection.execute(
                text(
                    """
                    SELECT inquiry_ref, inquiry_hash, viewer_account_ref,
                           case_ref, life_case_revision_ref, reading_ref,
                           candidate_ref, encounter_ref, domain,
                           idempotency_key, inquiry_json
                    FROM dream.private_inquiries
                    WHERE viewer_account_ref = :account_ref
                      AND encounter_ref = :encounter_ref
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
        return self.validate_inquiry(row) if row is not None else None

    def inquiry_for_idempotency(
        self,
        connection: Any,
        *,
        account_ref: str,
        idempotency_key: str,
    ) -> DreamPrivateInquiryRecord | None:
        row = (
            connection.execute(
                text(
                    """
                    SELECT inquiry_ref, inquiry_hash, viewer_account_ref,
                           case_ref, life_case_revision_ref, reading_ref,
                           candidate_ref, encounter_ref, domain,
                           idempotency_key, inquiry_json
                    FROM dream.private_inquiries
                    WHERE viewer_account_ref = :account_ref
                      AND idempotency_key = :idempotency_key
                    """
                ),
                {
                    "account_ref": account_ref,
                    "idempotency_key": idempotency_key,
                },
            )
            .mappings()
            .one_or_none()
        )
        return self.validate_inquiry(row) if row is not None else None

    @staticmethod
    def encounter_for_inquiry(
        connection: Any,
        *,
        account_ref: str,
        inquiry: DreamPrivateInquiryRecord,
    ) -> dict[str, Any]:
        row = (
            connection.execute(
                text(
                    """
                    SELECT encounter_ref, viewer_account_ref, actor_ref,
                           tree_ref, question_ref, status, state_json
                    FROM dream.encounters
                    WHERE viewer_account_ref = :account_ref
                      AND encounter_ref = :encounter_ref
                    """
                ),
                {
                    "account_ref": account_ref,
                    "encounter_ref": inquiry.encounter_ref,
                },
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise DreamStateError("dream_private_inquiry_encounter_missing")
        if (
            row["actor_ref"] != inquiry.actor_ref
            or row["tree_ref"] != inquiry.tree_ref
            or row["question_ref"] != inquiry.episode_question_ref
        ):
            raise DreamStateError("dream_private_inquiry_encounter_lineage_mismatch")
        return dict(row)

    def task_for_inquiry(
        self,
        connection: Any,
        *,
        account_ref: str,
        inquiry_ref: str,
        for_update: bool,
    ) -> DreamPersonalObservationTask | None:
        lock_clause = "FOR UPDATE" if for_update else ""
        row = (
            connection.execute(
                text(
                    f"""
                    SELECT task_ref, task_hash, viewer_account_ref,
                           inquiry_ref, encounter_ref, option_ref,
                           checkpoint_on, idempotency_key, task_json
                    FROM dream.personal_observation_tasks
                    WHERE viewer_account_ref = :account_ref
                      AND inquiry_ref = :inquiry_ref
                    {lock_clause}
                    """
                ),
                {
                    "account_ref": account_ref,
                    "inquiry_ref": inquiry_ref,
                },
            )
            .mappings()
            .one_or_none()
        )
        return self.validate_task(row) if row is not None else None

    def task(
        self,
        connection: Any,
        *,
        account_ref: str,
        task_ref: str,
        for_update: bool,
    ) -> DreamPersonalObservationTask:
        lock_clause = "FOR UPDATE" if for_update else ""
        row = (
            connection.execute(
                text(
                    f"""
                    SELECT task_ref, task_hash, viewer_account_ref,
                           inquiry_ref, encounter_ref, option_ref,
                           checkpoint_on, idempotency_key, task_json
                    FROM dream.personal_observation_tasks
                    WHERE viewer_account_ref = :account_ref
                      AND task_ref = :task_ref
                    {lock_clause}
                    """
                ),
                {
                    "account_ref": account_ref,
                    "task_ref": task_ref,
                },
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise DreamStateError("dream_personal_observation_not_found")
        return self.validate_task(row)

    def task_for_idempotency(
        self,
        connection: Any,
        *,
        account_ref: str,
        idempotency_key: str,
    ) -> DreamPersonalObservationTask | None:
        row = (
            connection.execute(
                text(
                    """
                    SELECT task_ref, task_hash, viewer_account_ref,
                           inquiry_ref, encounter_ref, option_ref,
                           checkpoint_on, idempotency_key, task_json
                    FROM dream.personal_observation_tasks
                    WHERE viewer_account_ref = :account_ref
                      AND idempotency_key = :idempotency_key
                    """
                ),
                {
                    "account_ref": account_ref,
                    "idempotency_key": idempotency_key,
                },
            )
            .mappings()
            .one_or_none()
        )
        return self.validate_task(row) if row is not None else None

    def checkin_for_idempotency(
        self,
        connection: Any,
        *,
        account_ref: str,
        idempotency_key: str,
    ) -> DreamPersonalCheckInRecord | None:
        row = (
            connection.execute(
                text(
                    """
                    SELECT checkin_ref, checkin_hash, viewer_account_ref,
                           inquiry_ref, task_ref, status, checked_in_on,
                           idempotency_key, checkin_json
                    FROM dream.personal_observation_checkins
                    WHERE viewer_account_ref = :account_ref
                      AND idempotency_key = :idempotency_key
                    """
                ),
                {
                    "account_ref": account_ref,
                    "idempotency_key": idempotency_key,
                },
            )
            .mappings()
            .one_or_none()
        )
        return self.validate_checkin(row) if row is not None else None

    def checkins(
        self,
        connection: Any,
        *,
        account_ref: str,
        task_ref: str,
    ) -> tuple[DreamPersonalCheckInRecord, ...]:
        rows = (
            connection.execute(
                text(
                    """
                    SELECT checkin_ref, checkin_hash, viewer_account_ref,
                           inquiry_ref, task_ref, status, checked_in_on,
                           idempotency_key, checkin_json
                    FROM dream.personal_observation_checkins
                    WHERE viewer_account_ref = :account_ref
                      AND task_ref = :task_ref
                    """
                ),
                {
                    "account_ref": account_ref,
                    "task_ref": task_ref,
                },
            )
            .mappings()
            .all()
        )
        records = {
            record.checkin_ref: record for record in (self.validate_checkin(row) for row in rows)
        }
        if not records:
            return ()
        roots = [record for record in records.values() if record.previous_checkin_ref is None]
        successors: dict[str, DreamPersonalCheckInRecord] = {}
        for record in records.values():
            if record.previous_checkin_ref is None:
                continue
            parent = records.get(record.previous_checkin_ref)
            if (
                parent is None
                or parent.checkin_hash != record.previous_checkin_hash
                or record.previous_checkin_ref in successors
            ):
                raise DreamStateError("dream_personal_checkin_chain_invalid")
            successors[record.previous_checkin_ref] = record
        if len(roots) != 1:
            raise DreamStateError("dream_personal_checkin_chain_invalid")
        ordered: list[DreamPersonalCheckInRecord] = []
        seen: set[str] = set()
        current: DreamPersonalCheckInRecord | None = roots[0]
        while current is not None and current.checkin_ref not in seen:
            ordered.append(current)
            seen.add(current.checkin_ref)
            current = successors.get(current.checkin_ref)
        if len(ordered) != len(records):
            raise DreamStateError("dream_personal_checkin_chain_invalid")
        return tuple(ordered)

    @staticmethod
    def insert_inquiry(
        connection: Any,
        *,
        inquiry: DreamPrivateInquiryRecord,
    ) -> None:
        connection.execute(
            text(
                """
                INSERT INTO dream.private_inquiries
                    (inquiry_ref, viewer_account_ref, case_ref,
                     life_case_revision_ref, reading_ref, candidate_ref,
                     encounter_ref, domain, idempotency_key,
                     inquiry_json, inquiry_hash)
                VALUES
                    (:inquiry_ref, :viewer_account_ref, :case_ref,
                     :life_case_revision_ref, :reading_ref, :candidate_ref,
                     :encounter_ref, :domain, :idempotency_key,
                     CAST(:inquiry_json AS jsonb), :inquiry_hash)
                """
            ),
            {
                **inquiry.model_dump(
                    mode="python",
                    include={
                        "inquiry_ref",
                        "viewer_account_ref",
                        "case_ref",
                        "life_case_revision_ref",
                        "reading_ref",
                        "candidate_ref",
                        "encounter_ref",
                        "domain",
                        "idempotency_key",
                        "inquiry_hash",
                    },
                ),
                "inquiry_json": canonical_json(inquiry.model_dump(mode="json")),
            },
        )

    @staticmethod
    def insert_task(
        connection: Any,
        *,
        task: DreamPersonalObservationTask,
    ) -> None:
        connection.execute(
            text(
                """
                INSERT INTO dream.personal_observation_tasks
                    (task_ref, viewer_account_ref, inquiry_ref,
                     encounter_ref, option_ref, checkpoint_on,
                     idempotency_key, task_json, task_hash)
                VALUES
                    (:task_ref, :viewer_account_ref, :inquiry_ref,
                     :encounter_ref, :option_ref, :checkpoint_on,
                     :idempotency_key, CAST(:task_json AS jsonb),
                     :task_hash)
                """
            ),
            {
                **task.model_dump(
                    mode="python",
                    include={
                        "task_ref",
                        "viewer_account_ref",
                        "inquiry_ref",
                        "encounter_ref",
                        "checkpoint_on",
                        "idempotency_key",
                        "task_hash",
                    },
                ),
                "option_ref": task.option.option_ref,
                "task_json": canonical_json(task.model_dump(mode="json")),
            },
        )

    @staticmethod
    def insert_checkin(
        connection: Any,
        *,
        checkin: DreamPersonalCheckInRecord,
    ) -> None:
        connection.execute(
            text(
                """
                INSERT INTO dream.personal_observation_checkins
                    (checkin_ref, viewer_account_ref, inquiry_ref,
                     task_ref, status, checked_in_on, idempotency_key,
                     checkin_json, checkin_hash)
                VALUES
                    (:checkin_ref, :viewer_account_ref, :inquiry_ref,
                     :task_ref, :status, :checked_in_on, :idempotency_key,
                     CAST(:checkin_json AS jsonb), :checkin_hash)
                """
            ),
            {
                **checkin.model_dump(
                    mode="python",
                    include={
                        "checkin_ref",
                        "viewer_account_ref",
                        "inquiry_ref",
                        "task_ref",
                        "status",
                        "checked_in_on",
                        "idempotency_key",
                        "checkin_hash",
                    },
                ),
                "checkin_json": canonical_json(checkin.model_dump(mode="json")),
            },
        )
