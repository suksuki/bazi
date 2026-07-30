from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from abu_v60.db import engine
from abu_v60.dream.errors import DreamConflictError, DreamStateError
from abu_v60.dream.grove import DreamGroveRepository
from abu_v60.dream.persistence import DreamRepository
from abu_v60.dream.personal_journey import DreamPersonalJourneyService
from abu_v60.dream.personal_journey_contracts import (
    DreamPersonalCheckInRequest,
    DreamPersonalObservationRequest,
    DreamPrivateInquiryRecord,
    DreamPrivateInquiryRequest,
)
from abu_v60.dream.personal_journey_store import DreamPersonalJourneyStore
from abu_v60.identity import lock_account_transaction
from abu_v60.observability.personal_journey_integrity import (
    DreamPersonalJourneyIntegrityInspector,
)
from abu_v60.provenance import canonical_json, content_hash
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

ACCOUNT_REF = "v60-account-personal-journey-qa"
OTHER_ACCOUNT_REF = "v60-account-personal-journey-other-qa"
ACCOUNT_REFS = (ACCOUNT_REF, OTHER_ACCOUNT_REF)


class _TemplateSelector:
    def __init__(self, candidate: Any) -> None:
        self.candidate = candidate
        self.calls = 0

    def select(
        self,
        connection: Any,
        *,
        account_ref: str,
        candidate_ref: str,
    ) -> SimpleNamespace:
        self.calls += 1
        assert candidate_ref == self.candidate.candidate_ref
        return SimpleNamespace(
            question_ref=self.candidate.question_ref,
            actor_ref=self.candidate.actor_ref,
            tree_ref=self.candidate.tree_ref,
            causation_id=f"qa-personal-journey:{account_ref}",
        )


class _TemplateEncounterCreator:
    def __init__(self) -> None:
        self.repository = DreamRepository()

    def create(
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
                    SELECT cutoff_tick, options_json
                    FROM story.question_instances
                    WHERE question_ref = :question_ref
                    """
                ),
                {"question_ref": question_ref},
            )
            .mappings()
            .one()
        )
        return self.repository.create_encounter(
            connection=connection,
            account_ref=account_ref,
            question_ref=question_ref,
            actor_ref=actor_ref,
            tree_ref=tree_ref,
            causation_id=causation_id,
            cutoff_tick=int(question["cutoff_tick"]),
            npc_choice_id=str(question["options_json"][0]["choice_id"]),
        )


class _NoReturnAttention:
    @staticmethod
    def apply_pending(*_: Any, **__: Any) -> None:
        return None


def _insert_owner_context(account_ref: str) -> None:
    suffix = content_hash(account_ref)[:12]
    profile_ref = f"v60-profile-personal-journey-{suffix}"
    case_ref = f"v60-case-personal-journey-{suffix}"
    chart_ref = f"v60-chart-personal-journey-{suffix}"
    revision_ref = f"v60-lifecase-personal-journey-{suffix}"
    reading_ref = f"v60-reading-personal-journey-{suffix}"
    chart_payload = {"account_ref": account_ref, "kind": "qa-chart"}
    revision_payload = {"account_ref": account_ref, "kind": "qa-revision"}
    reading_payload = {"account_ref": account_ref, "kind": "qa-reading"}
    with engine.begin() as connection:
        batch_ref = connection.execute(
            text(
                """
                SELECT batch_ref
                FROM platform.migration_batches
                ORDER BY created_at, batch_ref
                LIMIT 1
                """
            )
        ).scalar_one()
        connection.execute(
            text(
                """
                INSERT INTO identity.accounts
                    (account_ref, email, display_name, account_role,
                     active, password_scheme, password_hash, password_salt,
                     source_ref, source_hash, source_batch_ref)
                VALUES
                    (:account_ref, :email, 'Personal Journey QA',
                     'HUMAN_OWNER', true, 'qa', :password_hash,
                     :password_salt, :source_ref, :source_hash, :batch_ref)
                """
            ),
            {
                "account_ref": account_ref,
                "email": f"{suffix}@personal-journey.qa",
                "password_hash": content_hash({"account_ref": account_ref, "kind": "password"}),
                "password_salt": content_hash({"account_ref": account_ref, "kind": "salt"}),
                "source_ref": f"qa:{account_ref}",
                "source_hash": content_hash({"account_ref": account_ref, "kind": "account"}),
                "batch_ref": batch_ref,
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO identity.profiles
                    (profile_ref, account_ref, display_name, gender,
                     calendar_type, birth_date, birth_time, birth_location,
                     timezone, source_ref, source_hash, input_json, active)
                VALUES
                    (:profile_ref, :account_ref, 'Personal Journey QA',
                     'UNSPECIFIED', 'SOLAR', DATE '1990-01-01',
                     TIME '12:00:00', 'QA', 'Asia/Seoul',
                     :source_ref, :source_hash, '{}'::jsonb, true)
                """
            ),
            {
                "profile_ref": profile_ref,
                "account_ref": account_ref,
                "source_ref": f"qa-profile:{account_ref}",
                "source_hash": content_hash({"account_ref": account_ref, "kind": "profile"}),
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO mingli.cases
                    (case_ref, owner_account_ref, profile_ref,
                     subject_kind, status, case_version)
                VALUES
                    (:case_ref, :account_ref, :profile_ref,
                     'HUMAN_OWNER', 'ACTIVE', 1)
                """
            ),
            {
                "case_ref": case_ref,
                "account_ref": account_ref,
                "profile_ref": profile_ref,
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO mingli.chart_versions
                    (chart_version_ref, case_ref, version, birth_input_hash,
                     pillars_json, algorithm_version, source_manifest_json,
                     chart_hash)
                VALUES
                    (:chart_ref, :case_ref, 1, :birth_hash,
                     '{}'::jsonb, 'qa', '{}'::jsonb, :chart_hash)
                """
            ),
            {
                "chart_ref": chart_ref,
                "case_ref": case_ref,
                "birth_hash": content_hash({"account_ref": account_ref, "kind": "birth"}),
                "chart_hash": content_hash(chart_payload),
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO mingli.life_case_revisions
                    (life_case_revision_ref, case_ref, chart_version_ref,
                     revision, status, payload_json,
                     evidence_manifest_json, revision_hash)
                VALUES
                    (:revision_ref, :case_ref, :chart_ref, 1,
                     'BOUNDED_BASELINE', CAST(:payload AS jsonb),
                     '{}'::jsonb, :revision_hash)
                """
            ),
            {
                "revision_ref": revision_ref,
                "case_ref": case_ref,
                "chart_ref": chart_ref,
                "payload": canonical_json(revision_payload),
                "revision_hash": content_hash(revision_payload),
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO mingli.readings
                    (reading_ref, reading_version, case_ref,
                     chart_version_ref, life_case_revision_ref,
                     foundation_profile_ref, foundation_profile_hash,
                     candidate_rule_profile_ref,
                     candidate_rule_profile_hash,
                     reading_json, reading_hash)
                VALUES
                    (:reading_ref, 'v60.mingli-reading.qa',
                     :case_ref, :chart_ref, :revision_ref,
                     'qa-foundation', :foundation_hash,
                     'qa-candidate-rules', :candidate_hash,
                     CAST(:reading_json AS jsonb), :reading_hash)
                """
            ),
            {
                "reading_ref": reading_ref,
                "case_ref": case_ref,
                "chart_ref": chart_ref,
                "revision_ref": revision_ref,
                "foundation_hash": content_hash({"account_ref": account_ref, "kind": "foundation"}),
                "candidate_hash": content_hash({"account_ref": account_ref, "kind": "candidate"}),
                "reading_json": canonical_json(reading_payload),
                "reading_hash": content_hash(reading_payload),
            },
        )


def _cleanup() -> None:
    with engine.begin() as connection:
        for table, trigger in (
            (
                "personal_observation_checkins",
                "trg_dream_personal_checkin_append_only",
            ),
            (
                "personal_observation_tasks",
                "trg_dream_personal_observation_append_only",
            ),
            (
                "private_inquiries",
                "trg_dream_private_inquiry_append_only",
            ),
        ):
            connection.execute(
                text(
                    f"""
                    ALTER TABLE dream.{table}
                    DISABLE TRIGGER {trigger}
                    """
                )
            )
            connection.execute(
                text(
                    f"""
                    DELETE FROM dream.{table}
                    WHERE viewer_account_ref = ANY(:account_refs)
                    """
                ),
                {"account_refs": list(ACCOUNT_REFS)},
            )
            connection.execute(
                text(
                    f"""
                    ALTER TABLE dream.{table}
                    ENABLE TRIGGER {trigger}
                    """
                )
            )
        encounter_refs = list(
            connection.execute(
                text(
                    """
                    SELECT encounter_ref
                    FROM dream.encounters
                    WHERE viewer_account_ref = ANY(:account_refs)
                    """
                ),
                {"account_refs": list(ACCOUNT_REFS)},
            ).scalars()
        )
        if encounter_refs:
            connection.execute(
                text(
                    """
                    DELETE FROM dream.answer_seals
                    WHERE encounter_ref = ANY(:encounter_refs)
                    """
                ),
                {"encounter_refs": encounter_refs},
            )
            connection.execute(
                text(
                    """
                    DELETE FROM dream.encounters
                    WHERE encounter_ref = ANY(:encounter_refs)
                    """
                ),
                {"encounter_refs": encounter_refs},
            )
        connection.execute(
            text(
                """
                ALTER TABLE mingli.readings
                DISABLE TRIGGER trg_mingli_readings_append_only
                """
            )
        )
        connection.execute(
            text(
                """
                DELETE FROM mingli.readings
                WHERE case_ref LIKE 'v60-case-personal-journey-%'
                """
            )
        )
        connection.execute(
            text(
                """
                ALTER TABLE mingli.readings
                ENABLE TRIGGER trg_mingli_readings_append_only
                """
            )
        )
        connection.execute(
            text(
                """
                DELETE FROM mingli.life_case_revisions
                WHERE case_ref LIKE 'v60-case-personal-journey-%'
                """
            )
        )
        connection.execute(
            text(
                """
                DELETE FROM mingli.chart_versions
                WHERE case_ref LIKE 'v60-case-personal-journey-%'
                """
            )
        )
        connection.execute(
            text(
                """
                DELETE FROM mingli.cases
                WHERE owner_account_ref = ANY(:account_refs)
                """
            ),
            {"account_refs": list(ACCOUNT_REFS)},
        )
        connection.execute(
            text(
                """
                DELETE FROM identity.profiles
                WHERE account_ref = ANY(:account_refs)
                """
            ),
            {"account_refs": list(ACCOUNT_REFS)},
        )
        connection.execute(
            text(
                """
                DELETE FROM identity.accounts
                WHERE account_ref = ANY(:account_refs)
                """
            ),
            {"account_refs": list(ACCOUNT_REFS)},
        )


@pytest.fixture()
def personal_accounts() -> None:
    _cleanup()
    for account_ref in ACCOUNT_REFS:
        _insert_owner_context(account_ref)
    try:
        yield
    finally:
        _cleanup()


def _relationship_candidate() -> Any:
    with engine.connect() as connection:
        candidate = next(
            item
            for item in DreamGroveRepository().active_candidates(connection)
            if item["domain"] == "relationship"
        )
        return DreamGroveRepository().candidate_definition(
            connection,
            candidate_ref=candidate["candidate_ref"],
            for_update=False,
        )


def _complete_encounter(encounter_ref: str, *, departed: bool) -> None:
    state = {
        "observed_organs": [
            "evidence_leaf_world",
            "evidence_leaf_structure",
            "structure_branch",
        ],
        "question_visible": True,
        "answer_sealed": True,
        "world_settled": True,
        "revealed": True,
        "reconciled": True,
        **({"departed_to_grove": True} if departed else {}),
    }
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                UPDATE dream.encounters
                SET status = 'COMPLETED',
                    state_json = CAST(:state_json AS jsonb),
                    state_hash = :state_hash,
                    version = version + 1,
                    updated_at = now()
                WHERE encounter_ref = :encounter_ref
                """
            ),
            {
                "encounter_ref": encounter_ref,
                "state_json": canonical_json(state),
                "state_hash": content_hash(state),
            },
        )


def _depart_newer_timeline_tip(
    *,
    account_ref: str,
    source_encounter_ref: str,
) -> str:
    with engine.begin() as connection:
        source = (
            connection.execute(
                text(
                    """
                    SELECT actor_ref, tree_ref, question_ref
                    FROM dream.encounters
                    WHERE encounter_ref = :encounter_ref
                    """
                ),
                {"encounter_ref": source_encounter_ref},
            )
            .mappings()
            .one()
        )
        question = (
            connection.execute(
                text(
                    """
                    SELECT question_ref, cutoff_tick, options_json
                    FROM story.question_instances AS question
                    WHERE question.question_ref <> :source_question_ref
                      AND jsonb_array_length(question.options_json) > 0
                      AND NOT EXISTS (
                          SELECT 1
                          FROM dream.encounters AS encounter
                          WHERE encounter.viewer_account_ref = :account_ref
                            AND encounter.question_ref =
                                question.question_ref
                      )
                    ORDER BY question.question_ref
                    LIMIT 1
                    """
                ),
                {
                    "account_ref": account_ref,
                    "source_question_ref": source["question_ref"],
                },
            )
            .mappings()
            .one()
        )
        newer_ref = DreamRepository.create_encounter(
            connection=connection,
            account_ref=account_ref,
            question_ref=str(question["question_ref"]),
            actor_ref=str(source["actor_ref"]),
            tree_ref=str(source["tree_ref"]),
            causation_id=f"qa-personal-journey-continuation:{account_ref}",
            cutoff_tick=int(question["cutoff_tick"]),
            npc_choice_id=str(question["options_json"][0]["choice_id"]),
        )
    _complete_encounter(newer_ref, departed=True)
    return newer_ref


def test_personal_journey_contract_rejects_content_drift() -> None:
    inquiry = DreamPrivateInquiryRecord.issue(
        viewer_account_ref=ACCOUNT_REF,
        case_ref="case",
        life_case_revision_ref="revision",
        reading_ref="reading",
        reading_hash="1" * 64,
        domain="relationship",
        question="我想观察边界是否会被双方说清。",
        candidate_ref="candidate",
        candidate_hash="2" * 64,
        public_alias="灯册树",
        actor_ref="actor",
        tree_ref="tree",
        encounter_ref="encounter",
        episode_question_ref="episode-question",
        supersedes_inquiry_ref=None,
        supersedes_inquiry_hash=None,
        idempotency_key="qa:contract",
    )

    assert inquiry.mingli_evidence_role == "NOT_MINGLI_EVIDENCE"
    assert inquiry.dream_answers_owner_question is False
    assert inquiry.reading_used_to_select_candidate is False
    assert inquiry.world_outcome_changed is False
    assert inquiry.mingli_write_allowed is False
    payload = inquiry.model_dump(mode="python")
    with pytest.raises(
        ValidationError,
        match="dream_private_inquiry_hash_mismatch",
    ):
        DreamPrivateInquiryRecord.model_validate({**payload, "question": "被改写的问题"})
    with pytest.raises(ValidationError):
        DreamPrivateInquiryRequest.model_validate(
            {
                "domain": "relationship",
                "question": "问题",
                "idempotency_key": "qa:short",
                "unexpected": True,
            }
        )


def test_personal_journey_shares_the_account_current_lock(
    personal_accounts: None,
) -> None:
    first = engine.connect()
    first_transaction = first.begin()
    try:
        DreamPersonalJourneyStore().lock_account(
            first,
            account_ref=ACCOUNT_REF,
        )
        second = engine.connect()
        second_transaction = second.begin()
        try:
            second.execute(text("SET LOCAL statement_timeout = '120ms'"))
            with pytest.raises(DBAPIError):
                lock_account_transaction(
                    second,
                    account_ref=ACCOUNT_REF,
                )
        finally:
            second_transaction.rollback()
            second.close()
    finally:
        first_transaction.rollback()
        first.close()


def test_private_question_observation_and_followup_persist(
    personal_accounts: None,
) -> None:
    candidate = _relationship_candidate()
    assert candidate is not None
    selector = _TemplateSelector(candidate)
    creator = _TemplateEncounterCreator()
    service = DreamPersonalJourneyService(engine)
    request = DreamPrivateInquiryRequest(
        domain="relationship",
        question="一次边界说清之后，协作是否会继续留下行动？",
        idempotency_key="qa:personal-inquiry:one",
    )
    unchanged_before = _unchanged_counts()

    encounter_ref = service.start_encounter(
        account_ref=ACCOUNT_REF,
        candidate_ref=candidate.candidate_ref,
        request=request,
        grove_selector=selector,
        encounter_creator=creator,
        return_attention=_NoReturnAttention(),
    )
    replay_ref = service.start_encounter(
        account_ref=ACCOUNT_REF,
        candidate_ref=candidate.candidate_ref,
        request=request,
        grove_selector=selector,
        encounter_creator=creator,
        return_attention=_NoReturnAttention(),
    )
    assert replay_ref == encounter_ref
    assert selector.calls == 1
    with pytest.raises(
        DreamConflictError,
        match="dream_private_inquiry_idempotency_conflict",
    ):
        service.start_encounter(
            account_ref=ACCOUNT_REF,
            candidate_ref=candidate.candidate_ref,
            request=request.model_copy(update={"question": "同一幂等键不能换成另一个问题。"}),
            grove_selector=selector,
            encounter_creator=creator,
            return_attention=_NoReturnAttention(),
        )
    with engine.connect() as connection:
        opening = service.project_encounter(
            connection,
            account_ref=ACCOUNT_REF,
            encounter_ref=encounter_ref,
        )
    assert opening is not None
    assert opening.status == "IN_DREAM"
    assert opening.inquiry.question == request.question
    assert opening.inquiry.candidate_ref == candidate.candidate_ref
    assert opening.observation_options == ()

    _complete_encounter(encounter_ref, departed=False)
    with engine.connect() as connection:
        completed = service.project_encounter(
            connection,
            account_ref=ACCOUNT_REF,
            encounter_ref=encounter_ref,
        )
    assert completed is not None
    assert completed.status == "AWAITING_OBSERVATION"
    assert len(completed.observation_options) == 3
    selected_option = completed.observation_options[0]
    task = service.select_observation(
        account_ref=ACCOUNT_REF,
        request=DreamPersonalObservationRequest(
            inquiry_ref=completed.inquiry.inquiry_ref,
            inquiry_hash=completed.inquiry.inquiry_hash,
            option_ref=selected_option.option_ref,
            idempotency_key="qa:personal-observation:one",
        ),
    )
    assert task.option == selected_option
    assert task.checkpoint_on == (datetime.now(ZoneInfo("Asia/Seoul")).date() + timedelta(days=7))
    assert task.mingli_evidence_role == "NOT_MINGLI_EVIDENCE"
    assert task.dream_result_validates_owner_question is False
    with pytest.raises(
        DreamStateError,
        match="dream_personal_observation_not_found",
    ):
        service.record_checkin(
            account_ref=OTHER_ACCOUNT_REF,
            request=DreamPersonalCheckInRequest(
                task_ref=task.task_ref,
                task_hash=task.task_hash,
                status="OBSERVED",
                note=None,
                idempotency_key="qa:other-account-checkin",
            ),
        )
    with pytest.raises(
        DreamConflictError,
        match="dream_personal_checkin_requires_grove_return",
    ):
        service.record_checkin(
            account_ref=ACCOUNT_REF,
            request=DreamPersonalCheckInRequest(
                task_ref=task.task_ref,
                task_hash=task.task_hash,
                status="STILL_OBSERVING",
                note=None,
                idempotency_key="qa:early-checkin",
            ),
        )

    newer_encounter_ref = _depart_newer_timeline_tip(
        account_ref=ACCOUNT_REF,
        source_encounter_ref=encounter_ref,
    )
    assert newer_encounter_ref != encounter_ref
    first_checkin = service.record_checkin(
        account_ref=ACCOUNT_REF,
        request=DreamPersonalCheckInRequest(
            task_ref=task.task_ref,
            task_hash=task.task_hash,
            status="STILL_OBSERVING",
            note="双方已经说清分工，继续观察是否重复发生。",
            idempotency_key="qa:checkin:one",
        ),
    )
    assert first_checkin.checked_in_on == datetime.now(ZoneInfo("Asia/Seoul")).date()
    restarted = DreamPersonalJourneyService(engine)
    with engine.connect() as connection:
        restored = restarted.project_grove(
            connection,
            account_ref=ACCOUNT_REF,
        )
    assert restored is not None
    assert restored.status == "FOLLOWED_UP"
    assert restored.observation is not None
    assert restored.observation.task_ref == task.task_ref
    assert restored.latest_checkin is not None
    assert restored.latest_checkin.checkin_ref == first_checkin.checkin_ref
    assert restored.checkin_count == 1
    assert restored.mingli_evidence_role == "NOT_MINGLI_EVIDENCE"

    with pytest.raises(
        DreamConflictError,
        match="dream_personal_observation_still_active",
    ):
        restarted.start_encounter(
            account_ref=ACCOUNT_REF,
            candidate_ref=candidate.candidate_ref,
            request=request.model_copy(
                update={
                    "question": "尚未结束的观察不能被一个新问题藏起来。",
                    "idempotency_key": "qa:personal-inquiry:blocked",
                }
            ),
            grove_selector=selector,
            encounter_creator=creator,
            return_attention=_NoReturnAttention(),
        )

    second = restarted.record_checkin(
        account_ref=ACCOUNT_REF,
        request=DreamPersonalCheckInRequest(
            task_ref=task.task_ref,
            task_hash=task.task_hash,
            status="OBSERVED",
            note="第二次协作也按同一边界执行。",
            idempotency_key="qa:checkin:two",
        ),
    )
    assert second.previous_checkin_ref == first_checkin.checkin_ref
    with engine.connect() as connection:
        latest = restarted.project_grove(
            connection,
            account_ref=ACCOUNT_REF,
        )
    assert latest is not None
    assert latest.checkin_count == 2
    assert latest.latest_checkin is not None
    assert latest.latest_checkin.checkin_ref == second.checkin_ref
    assert _unchanged_counts() == unchanged_before

    tamper_cases = (
        (
            """
            ALTER TABLE dream.private_inquiries
            DISABLE TRIGGER trg_dream_private_inquiry_append_only
            """,
            """
            UPDATE dream.private_inquiries
            SET domain = 'career'
            WHERE inquiry_ref = :record_ref
            """,
            completed.inquiry.inquiry_ref,
            "invalid_dream_private_inquiries",
        ),
        (
            """
            ALTER TABLE dream.personal_observation_tasks
            DISABLE TRIGGER trg_dream_personal_observation_append_only
            """,
            """
            UPDATE dream.personal_observation_tasks
            SET checkpoint_on = checkpoint_on + 1
            WHERE task_ref = :record_ref
            """,
            task.task_ref,
            "invalid_dream_personal_observation_tasks",
        ),
        (
            """
            ALTER TABLE dream.personal_observation_checkins
            DISABLE TRIGGER trg_dream_personal_checkin_append_only
            """,
            """
            UPDATE dream.personal_observation_checkins
            SET status = 'NOT_OBSERVED'
            WHERE checkin_ref = :record_ref
            """,
            second.checkin_ref,
            "invalid_dream_personal_observation_checkins",
        ),
    )
    for disable_sql, update_sql, record_ref, integrity_key in tamper_cases:
        connection = engine.connect()
        transaction = connection.begin()
        try:
            connection.execute(text(disable_sql))
            connection.execute(
                text(update_sql),
                {"record_ref": record_ref},
            )
            integrity = DreamPersonalJourneyIntegrityInspector().inspect(connection)
            assert integrity[integrity_key] >= 1
        finally:
            transaction.rollback()
            connection.close()

    with (
        pytest.raises(
            DBAPIError,
            match="dream_personal_journey_is_append_only",
        ),
        engine.begin() as connection,
    ):
        connection.execute(
            text(
                """
                    UPDATE dream.private_inquiries
                    SET domain = 'career'
                    WHERE inquiry_ref = :inquiry_ref
                    """
            ),
            {"inquiry_ref": completed.inquiry.inquiry_ref},
        )


def test_domain_mismatch_fails_before_encounter_or_question_write(
    personal_accounts: None,
) -> None:
    candidate = _relationship_candidate()
    assert candidate is not None
    selector = _TemplateSelector(candidate)
    service = DreamPersonalJourneyService(engine)
    with pytest.raises(
        DreamStateError,
        match="dream_private_inquiry_domain_candidate_mismatch",
    ):
        service.start_encounter(
            account_ref=ACCOUNT_REF,
            candidate_ref=candidate.candidate_ref,
            request=DreamPrivateInquiryRequest(
                domain="career",
                question="这条问题不能被偷偷送到关系人生。",
                idempotency_key="qa:wrong-domain",
            ),
            grove_selector=selector,
            encounter_creator=_TemplateEncounterCreator(),
            return_attention=_NoReturnAttention(),
        )
    assert selector.calls == 0
    with engine.connect() as connection:
        assert (
            connection.execute(
                text(
                    """
                    SELECT count(*)
                    FROM dream.private_inquiries
                    WHERE viewer_account_ref = :account_ref
                    """
                ),
                {"account_ref": ACCOUNT_REF},
            ).scalar_one()
            == 0
        )
        assert (
            connection.execute(
                text(
                    """
                    SELECT count(*)
                    FROM dream.encounters
                    WHERE viewer_account_ref = :account_ref
                    """
                ),
                {"account_ref": ACCOUNT_REF},
            ).scalar_one()
            == 0
        )


def _unchanged_counts() -> tuple[int, int, int, int]:
    with engine.connect() as connection:
        return tuple(
            int(value)
            for value in connection.execute(
                text(
                    """
                    SELECT
                        (SELECT count(*) FROM mingli.readings),
                        (SELECT count(*) FROM cognition.decision_records),
                        (SELECT count(*) FROM world.events),
                        (SELECT count(*) FROM story.question_instances)
                    """
                )
            ).one()
        )
