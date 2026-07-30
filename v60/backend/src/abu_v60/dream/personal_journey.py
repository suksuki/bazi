from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.engine import Engine

from abu_v60.dream.errors import DreamConflictError, DreamStateError
from abu_v60.dream.grove import DreamGroveRepository
from abu_v60.dream.persistence import DreamRepository
from abu_v60.dream.personal_journey_contracts import (
    DreamLifeDomain,
    DreamPersonalCheckInRecord,
    DreamPersonalCheckInRequest,
    DreamPersonalCheckInView,
    DreamPersonalJourneyProjection,
    DreamPersonalObservationOption,
    DreamPersonalObservationRequest,
    DreamPersonalObservationTask,
    DreamPersonalObservationView,
    DreamPrivateInquiryRecord,
    DreamPrivateInquiryRequest,
    DreamPrivateInquiryView,
)
from abu_v60.dream.personal_journey_store import (
    DreamPersonalJourneyStore,
)

_OBSERVATION_COPY: dict[
    DreamLifeDomain,
    tuple[tuple[str, str], ...],
] = {
    "career": (
        (
            "职责有没有写进安排",
            "未来七天，留意谁被明确交付下一步，以及有没有留下可核验的职责记录。",
        ),
        (
            "投入有没有换来位置变化",
            "只记录实际权限、署名或责任是否变化，不把口头认可提前算作结果。",
        ),
        (
            "承诺有没有落成行动",
            "挑一项已经说出口的工作承诺，观察它是否进入排期、交付或复盘。",
        ),
    ),
    "wealth": (
        (
            "交换有没有真实回流",
            "未来七天，记录一次投入之后有没有出现可核验的付款、回款或资源回流。",
        ),
        (
            "一次成交能不能重复",
            "区分偶然的一次结果与第二次可重复的往来，只记已经发生的事实。",
        ),
        (
            "成本与承诺能不能对上",
            "观察时间、费用与交付条件是否被双方说清，并在实际记录里一致。",
        ),
    ),
    "relationship": (
        (
            "边界有没有被双方说清",
            "未来七天，记录一次双方明确说出能做、不能做或需要协商之处的时刻。",
        ),
        (
            "协作有没有持续发生",
            "不要只看一次回应；观察同一件事是否出现第二次可见的共同投入。",
        ),
        (
            "关心有没有落成行动",
            "把表达与行动分开，记录一个已经发生、可以复核的照顾或支持行为。",
        ),
    ),
}


class DreamPersonalJourneyService:
    """Own the account-private question, observation and follow-up ledger."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._grove = DreamGroveRepository()
        self._repository = DreamRepository()
        self._store = DreamPersonalJourneyStore()

    def start_encounter(
        self,
        *,
        account_ref: str,
        candidate_ref: str,
        request: DreamPrivateInquiryRequest,
        grove_selector: Any,
        encounter_creator: Any,
        return_attention: Any,
    ) -> str:
        with self._engine.begin() as connection:
            self._store.lock_account(connection, account_ref=account_ref)
            replay = self._store.inquiry_for_idempotency(
                connection,
                account_ref=account_ref,
                idempotency_key=request.idempotency_key,
            )
            if replay is not None:
                if (
                    replay.candidate_ref != candidate_ref
                    or replay.domain != request.domain
                    or replay.question != request.question
                ):
                    raise DreamConflictError("dream_private_inquiry_idempotency_conflict")
                current = self._repository.current_encounter(
                    connection,
                    account_ref=account_ref,
                    for_update=False,
                )
                if current is None or current["encounter_ref"] != replay.encounter_ref:
                    raise DreamConflictError("dream_private_inquiry_replay_not_current")
                return replay.encounter_ref

            candidate = self._grove.candidate_definition(
                connection,
                candidate_ref=candidate_ref,
                for_update=True,
            )
            if candidate is None:
                raise DreamStateError("dream_private_inquiry_candidate_not_found")
            if candidate.domain != request.domain:
                raise DreamStateError("dream_private_inquiry_domain_candidate_mismatch")
            owner_context = self._store.owner_context(
                connection,
                account_ref=account_ref,
            )
            previous = self._store.latest_inquiry(
                connection,
                account_ref=account_ref,
            )
            self._assert_previous_journey_closed(
                connection,
                account_ref=account_ref,
                inquiry=previous,
            )
            intent = grove_selector.select(
                connection,
                account_ref=account_ref,
                candidate_ref=candidate_ref,
            )
            if intent is None:
                raise DreamConflictError("dream_private_inquiry_encounter_already_committed")
            encounter_ref = encounter_creator.create(
                connection=connection,
                account_ref=account_ref,
                question_ref=intent.question_ref,
                actor_ref=intent.actor_ref,
                tree_ref=intent.tree_ref,
                causation_id=intent.causation_id,
            )
            inquiry = DreamPrivateInquiryRecord.issue(
                viewer_account_ref=account_ref,
                **owner_context,
                domain=request.domain,
                question=request.question,
                candidate_ref=candidate.candidate_ref,
                candidate_hash=candidate.candidate_hash,
                public_alias=candidate.public_alias,
                actor_ref=intent.actor_ref,
                tree_ref=intent.tree_ref,
                encounter_ref=encounter_ref,
                episode_question_ref=intent.question_ref,
                supersedes_inquiry_ref=(previous.inquiry_ref if previous is not None else None),
                supersedes_inquiry_hash=(previous.inquiry_hash if previous is not None else None),
                idempotency_key=request.idempotency_key,
            )
            self._store.insert_inquiry(
                connection,
                inquiry=inquiry,
            )
            return_attention.apply_pending(
                connection,
                account_ref=account_ref,
                encounter_ref=encounter_ref,
                tree_ref=intent.tree_ref,
            )
            return encounter_ref

    def select_observation(
        self,
        *,
        account_ref: str,
        request: DreamPersonalObservationRequest,
    ) -> DreamPersonalObservationTask:
        with self._engine.begin() as connection:
            self._store.lock_account(connection, account_ref=account_ref)
            replay = self._store.task_for_idempotency(
                connection,
                account_ref=account_ref,
                idempotency_key=request.idempotency_key,
            )
            if replay is not None:
                if (
                    replay.inquiry_ref != request.inquiry_ref
                    or replay.inquiry_hash != request.inquiry_hash
                    or replay.option.option_ref != request.option_ref
                ):
                    raise DreamConflictError("dream_personal_observation_idempotency_conflict")
                return replay

            inquiry = self._store.inquiry(
                connection,
                account_ref=account_ref,
                inquiry_ref=request.inquiry_ref,
                for_update=True,
            )
            if inquiry.inquiry_hash != request.inquiry_hash:
                raise DreamStateError("dream_personal_observation_inquiry_hash_mismatch")
            self._assert_latest_inquiry(
                connection,
                account_ref=account_ref,
                inquiry=inquiry,
            )
            self._assert_completed_inquiry_encounter(
                connection,
                account_ref=account_ref,
                inquiry=inquiry,
            )
            existing = self._store.task_for_inquiry(
                connection,
                account_ref=account_ref,
                inquiry_ref=inquiry.inquiry_ref,
                for_update=True,
            )
            if existing is not None:
                raise DreamConflictError("dream_personal_observation_already_selected")
            option = next(
                (item for item in self._options(inquiry) if item.option_ref == request.option_ref),
                None,
            )
            if option is None:
                raise DreamStateError("dream_personal_observation_option_not_server_issued")
            task = DreamPersonalObservationTask.issue(
                viewer_account_ref=account_ref,
                inquiry_ref=inquiry.inquiry_ref,
                inquiry_hash=inquiry.inquiry_hash,
                encounter_ref=inquiry.encounter_ref,
                option=option,
                checkpoint_on=self._today(
                    self._store.owner_timezone(
                        connection,
                        account_ref=account_ref,
                        inquiry=inquiry,
                    )
                )
                + timedelta(days=7),
                idempotency_key=request.idempotency_key,
            )
            self._store.insert_task(
                connection,
                task=task,
            )
            return task

    def record_checkin(
        self,
        *,
        account_ref: str,
        request: DreamPersonalCheckInRequest,
    ) -> DreamPersonalCheckInRecord:
        with self._engine.begin() as connection:
            self._store.lock_account(connection, account_ref=account_ref)
            replay = self._store.checkin_for_idempotency(
                connection,
                account_ref=account_ref,
                idempotency_key=request.idempotency_key,
            )
            if replay is not None:
                if (
                    replay.task_ref != request.task_ref
                    or replay.task_hash != request.task_hash
                    or replay.status != request.status
                    or replay.note != request.note
                ):
                    raise DreamConflictError("dream_personal_checkin_idempotency_conflict")
                return replay

            task = self._store.task(
                connection,
                account_ref=account_ref,
                task_ref=request.task_ref,
                for_update=True,
            )
            if task.task_hash != request.task_hash:
                raise DreamStateError("dream_personal_checkin_task_hash_mismatch")
            inquiry = self._store.inquiry(
                connection,
                account_ref=account_ref,
                inquiry_ref=task.inquiry_ref,
                for_update=True,
            )
            self._assert_latest_inquiry(
                connection,
                account_ref=account_ref,
                inquiry=inquiry,
            )
            current = self._repository.current_encounter(
                connection,
                account_ref=account_ref,
                for_update=False,
            )
            if current is not None:
                raise DreamConflictError("dream_personal_checkin_requires_grove_return")
            checkins = self._store.checkins(
                connection,
                account_ref=account_ref,
                task_ref=task.task_ref,
            )
            previous = checkins[-1] if checkins else None
            checkin = DreamPersonalCheckInRecord.issue(
                viewer_account_ref=account_ref,
                inquiry_ref=inquiry.inquiry_ref,
                inquiry_hash=inquiry.inquiry_hash,
                task_ref=task.task_ref,
                task_hash=task.task_hash,
                previous_checkin_ref=(previous.checkin_ref if previous is not None else None),
                previous_checkin_hash=(previous.checkin_hash if previous is not None else None),
                status=request.status,
                note=request.note,
                checked_in_on=self._today(
                    self._store.owner_timezone(
                        connection,
                        account_ref=account_ref,
                        inquiry=inquiry,
                    )
                ),
                idempotency_key=request.idempotency_key,
            )
            self._store.insert_checkin(
                connection,
                checkin=checkin,
            )
            return checkin

    def project_encounter(
        self,
        connection: Any,
        *,
        account_ref: str,
        encounter_ref: str,
    ) -> DreamPersonalJourneyProjection | None:
        inquiry = self._store.inquiry_for_encounter(
            connection,
            account_ref=account_ref,
            encounter_ref=encounter_ref,
        )
        if inquiry is None:
            return None
        return self._project(
            connection,
            account_ref=account_ref,
            inquiry=inquiry,
        )

    def project_grove(
        self,
        connection: Any,
        *,
        account_ref: str,
    ) -> DreamPersonalJourneyProjection | None:
        inquiry = self._store.latest_inquiry(
            connection,
            account_ref=account_ref,
        )
        if inquiry is None:
            return None
        return self._project(
            connection,
            account_ref=account_ref,
            inquiry=inquiry,
        )

    def _project(
        self,
        connection: Any,
        *,
        account_ref: str,
        inquiry: DreamPrivateInquiryRecord,
    ) -> DreamPersonalJourneyProjection:
        encounter = self._store.encounter_for_inquiry(
            connection,
            account_ref=account_ref,
            inquiry=inquiry,
        )
        completed = (
            encounter["status"] == "COMPLETED" and encounter["state_json"].get("reconciled") is True
        )
        if not completed:
            status = (
                "DREAM_INTERRUPTED"
                if encounter["state_json"].get("departed_to_grove") is True
                else "IN_DREAM"
            )
            return DreamPersonalJourneyProjection.issue(
                status=status,
                inquiry=DreamPrivateInquiryView.from_record(inquiry),
                observation_options=(),
                observation=None,
                latest_checkin=None,
                checkin_count=0,
            )

        options = self._options(inquiry)
        task = self._store.task_for_inquiry(
            connection,
            account_ref=account_ref,
            inquiry_ref=inquiry.inquiry_ref,
            for_update=False,
        )
        if task is None:
            return DreamPersonalJourneyProjection.issue(
                status="AWAITING_OBSERVATION",
                inquiry=DreamPrivateInquiryView.from_record(inquiry),
                observation_options=options,
                observation=None,
                latest_checkin=None,
                checkin_count=0,
            )
        if task.option not in options:
            raise DreamStateError("dream_personal_observation_option_lineage_invalid")
        checkins = self._store.checkins(
            connection,
            account_ref=account_ref,
            task_ref=task.task_ref,
        )
        latest = checkins[-1] if checkins else None
        return DreamPersonalJourneyProjection.issue(
            status="FOLLOWED_UP" if latest is not None else "OBSERVING",
            inquiry=DreamPrivateInquiryView.from_record(inquiry),
            observation_options=options,
            observation=DreamPersonalObservationView.from_record(task),
            latest_checkin=(
                DreamPersonalCheckInView.from_record(latest) if latest is not None else None
            ),
            checkin_count=len(checkins),
        )

    @staticmethod
    def _options(
        inquiry: DreamPrivateInquiryRecord,
    ) -> tuple[DreamPersonalObservationOption, ...]:
        return tuple(
            DreamPersonalObservationOption.issue(
                inquiry_ref=inquiry.inquiry_ref,
                domain=inquiry.domain,
                label=label,
                summary=summary,
            )
            for label, summary in _OBSERVATION_COPY[inquiry.domain]
        )

    def _assert_latest_inquiry(
        self,
        connection: Any,
        *,
        account_ref: str,
        inquiry: DreamPrivateInquiryRecord,
    ) -> None:
        latest = self._store.latest_inquiry(
            connection,
            account_ref=account_ref,
        )
        if (
            latest is None
            or latest.inquiry_ref != inquiry.inquiry_ref
            or latest.inquiry_hash != inquiry.inquiry_hash
        ):
            raise DreamConflictError("dream_private_inquiry_superseded")

    def _assert_completed_inquiry_encounter(
        self,
        connection: Any,
        *,
        account_ref: str,
        inquiry: DreamPrivateInquiryRecord,
    ) -> None:
        encounter = self._store.encounter_for_inquiry(
            connection,
            account_ref=account_ref,
            inquiry=inquiry,
        )
        if (
            encounter["status"] != "COMPLETED"
            or encounter["state_json"].get("reconciled") is not True
        ):
            raise DreamConflictError("dream_personal_observation_requires_completed_encounter")

    def _assert_previous_journey_closed(
        self,
        connection: Any,
        *,
        account_ref: str,
        inquiry: DreamPrivateInquiryRecord | None,
    ) -> None:
        if inquiry is None:
            return
        task = self._store.task_for_inquiry(
            connection,
            account_ref=account_ref,
            inquiry_ref=inquiry.inquiry_ref,
            for_update=True,
        )
        if task is None:
            return
        checkins = self._store.checkins(
            connection,
            account_ref=account_ref,
            task_ref=task.task_ref,
        )
        if not checkins or checkins[-1].status == "STILL_OBSERVING":
            raise DreamConflictError("dream_personal_observation_still_active")

    @staticmethod
    def _today(timezone: str) -> date:
        try:
            return datetime.now(ZoneInfo(timezone)).date()
        except ZoneInfoNotFoundError as exc:
            raise DreamStateError("dream_private_inquiry_owner_timezone_invalid") from exc
