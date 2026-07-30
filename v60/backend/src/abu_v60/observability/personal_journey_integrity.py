from __future__ import annotations

from typing import Any

from sqlalchemy import text

from abu_v60.dream.personal_journey import DreamPersonalJourneyService
from abu_v60.dream.personal_journey_store import (
    DreamPersonalJourneyStore,
)


def _chain_is_valid(
    records: list[Any],
    *,
    ref_field: str,
    hash_field: str,
    previous_ref_field: str,
    previous_hash_field: str,
) -> bool:
    if not records:
        return True
    by_ref = {
        getattr(record, ref_field): record for record in records
    }
    roots: list[Any] = []
    successor_by_ref: dict[str, Any] = {}
    for record in records:
        previous_ref = getattr(record, previous_ref_field)
        if previous_ref is None:
            roots.append(record)
            continue
        parent = by_ref.get(previous_ref)
        if (
            parent is None
            or getattr(parent, hash_field)
            != getattr(record, previous_hash_field)
            or previous_ref in successor_by_ref
        ):
            return False
        successor_by_ref[previous_ref] = record
    if len(roots) != 1:
        return False
    seen: set[str] = set()
    current: Any | None = roots[0]
    while current is not None:
        current_ref = getattr(current, ref_field)
        if current_ref in seen:
            return False
        seen.add(current_ref)
        current = successor_by_ref.get(current_ref)
    return len(seen) == len(records)


class DreamPersonalJourneyIntegrityInspector:
    """Rebuild private journey records and verify their persisted parents."""

    def __init__(self) -> None:
        self._store = DreamPersonalJourneyStore()

    def inspect(self, connection: Any) -> dict[str, int]:
        inquiry_rows = (
            connection.execute(
                text(
                    """
                    SELECT inquiry.*,
                           owner_case.owner_account_ref,
                           owner_case.subject_kind,
                           revision.case_ref AS revision_case_ref,
                           reading.life_case_revision_ref
                               AS reading_revision_ref,
                           reading.reading_hash
                               AS persisted_reading_hash,
                           candidate.candidate_hash
                               AS persisted_candidate_hash,
                           candidate.domain AS persisted_candidate_domain,
                           candidate.actor_ref AS candidate_actor_ref,
                           candidate.tree_ref AS candidate_tree_ref,
                           candidate.public_alias
                               AS candidate_public_alias,
                           encounter.viewer_account_ref
                               AS encounter_account_ref,
                           encounter.actor_ref AS encounter_actor_ref,
                           encounter.tree_ref AS encounter_tree_ref,
                           encounter.question_ref
                               AS encounter_question_ref
                    FROM dream.private_inquiries AS inquiry
                    LEFT JOIN mingli.cases AS owner_case
                      ON owner_case.case_ref = inquiry.case_ref
                    LEFT JOIN mingli.life_case_revisions AS revision
                      ON revision.life_case_revision_ref =
                         inquiry.life_case_revision_ref
                    LEFT JOIN mingli.readings AS reading
                      ON reading.reading_ref = inquiry.reading_ref
                    LEFT JOIN dream.grove_candidates AS candidate
                      ON candidate.candidate_ref = inquiry.candidate_ref
                    LEFT JOIN dream.encounters AS encounter
                      ON encounter.encounter_ref = inquiry.encounter_ref
                    ORDER BY inquiry.viewer_account_ref,
                             inquiry.created_at,
                             inquiry.inquiry_ref
                    """
                )
            )
            .mappings()
            .all()
        )
        inquiries: dict[str, Any] = {}
        invalid_inquiries = 0
        inquiry_groups: dict[str, list[Any]] = {}
        for row in inquiry_rows:
            try:
                inquiry = self._store.validate_inquiry(row)
                if (
                    row["owner_account_ref"]
                    != inquiry.viewer_account_ref
                    or row["subject_kind"] != "HUMAN_OWNER"
                    or row["revision_case_ref"] != inquiry.case_ref
                    or row["reading_revision_ref"]
                    != inquiry.life_case_revision_ref
                    or row["persisted_reading_hash"]
                    != inquiry.reading_hash
                    or row["persisted_candidate_hash"]
                    != inquiry.candidate_hash
                    or row["persisted_candidate_domain"]
                    != inquiry.domain
                    or row["candidate_actor_ref"] != inquiry.actor_ref
                    or row["candidate_tree_ref"] != inquiry.tree_ref
                    or row["candidate_public_alias"]
                    != inquiry.public_alias
                    or row["encounter_account_ref"]
                    != inquiry.viewer_account_ref
                    or row["encounter_actor_ref"] != inquiry.actor_ref
                    or row["encounter_tree_ref"] != inquiry.tree_ref
                    or row["encounter_question_ref"]
                    != inquiry.episode_question_ref
                ):
                    raise ValueError("private_inquiry_parent_mismatch")
                inquiry_groups.setdefault(
                    inquiry.viewer_account_ref, []
                ).append(inquiry)
            except (TypeError, ValueError):
                invalid_inquiries += 1
        for records in inquiry_groups.values():
            if not _chain_is_valid(
                records,
                ref_field="inquiry_ref",
                hash_field="inquiry_hash",
                previous_ref_field="supersedes_inquiry_ref",
                previous_hash_field="supersedes_inquiry_hash",
            ):
                invalid_inquiries += len(records)
                continue
            inquiries.update(
                (inquiry.inquiry_ref, inquiry)
                for inquiry in records
            )

        task_rows = (
            connection.execute(
                text(
                    """
                    SELECT task.*, inquiry.inquiry_hash
                               AS persisted_inquiry_hash,
                           inquiry.viewer_account_ref
                               AS inquiry_account_ref,
                           inquiry.encounter_ref
                               AS inquiry_encounter_ref
                    FROM dream.personal_observation_tasks AS task
                    LEFT JOIN dream.private_inquiries AS inquiry
                      ON inquiry.inquiry_ref = task.inquiry_ref
                    """
                )
            )
            .mappings()
            .all()
        )
        tasks: dict[str, Any] = {}
        invalid_tasks = 0
        for row in task_rows:
            try:
                task = self._store.validate_task(row)
                inquiry = inquiries.get(task.inquiry_ref)
                if (
                    inquiry is None
                    or row["persisted_inquiry_hash"]
                    != task.inquiry_hash
                    or row["inquiry_account_ref"]
                    != task.viewer_account_ref
                    or row["inquiry_encounter_ref"]
                    != task.encounter_ref
                    or task.option not in (
                        DreamPersonalJourneyService._options(inquiry)
                    )
                ):
                    raise ValueError(
                        "personal_observation_parent_mismatch"
                    )
                tasks[task.task_ref] = task
            except (TypeError, ValueError):
                invalid_tasks += 1

        checkin_rows = (
            connection.execute(
                text(
                    """
                    SELECT checkin.*, task.task_hash
                               AS persisted_task_hash,
                           task.inquiry_ref AS task_inquiry_ref,
                           task.viewer_account_ref AS task_account_ref,
                           inquiry.inquiry_hash
                               AS persisted_inquiry_hash
                    FROM dream.personal_observation_checkins AS checkin
                    LEFT JOIN dream.personal_observation_tasks AS task
                      ON task.task_ref = checkin.task_ref
                    LEFT JOIN dream.private_inquiries AS inquiry
                      ON inquiry.inquiry_ref = checkin.inquiry_ref
                    ORDER BY checkin.viewer_account_ref,
                             checkin.task_ref,
                             checkin.created_at,
                             checkin.checkin_ref
                    """
                )
            )
            .mappings()
            .all()
        )
        invalid_checkins = 0
        checkin_groups: dict[str, list[Any]] = {}
        for row in checkin_rows:
            try:
                checkin = self._store.validate_checkin(row)
                task = tasks.get(checkin.task_ref)
                if (
                    task is None
                    or row["persisted_task_hash"]
                    != checkin.task_hash
                    or row["task_inquiry_ref"]
                    != checkin.inquiry_ref
                    or row["task_account_ref"]
                    != checkin.viewer_account_ref
                    or row["persisted_inquiry_hash"]
                    != checkin.inquiry_hash
                ):
                    raise ValueError("personal_checkin_parent_mismatch")
                checkin_groups.setdefault(
                    checkin.task_ref, []
                ).append(checkin)
            except (TypeError, ValueError):
                invalid_checkins += 1
        for records in checkin_groups.values():
            if not _chain_is_valid(
                records,
                ref_field="checkin_ref",
                hash_field="checkin_hash",
                previous_ref_field="previous_checkin_ref",
                previous_hash_field="previous_checkin_hash",
            ):
                invalid_checkins += len(records)

        return {
            "invalid_dream_private_inquiries": invalid_inquiries,
            "invalid_dream_personal_observation_tasks": invalid_tasks,
            "invalid_dream_personal_observation_checkins": (
                invalid_checkins
            ),
        }
