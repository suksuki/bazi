from __future__ import annotations

import re
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from abu_v60.db import engine
from abu_v60.dream.attention_follow_through import (
    DreamAttentionFollowThroughProjector,
)
from abu_v60.dream.attention_follow_through_contracts import (
    DreamAttentionFollowThrough,
    DreamPendingAttention,
)
from abu_v60.dream.errors import DreamConflictError, DreamStateError
from abu_v60.dream.grove import (
    DreamGroveAdmissionService,
    GroveCandidateDefinition,
)
from abu_v60.dream.opportunity import OPPORTUNITY_WINDOW_TICKS
from abu_v60.dream.return_attention import DreamReturnAttentionCoordinator
from abu_v60.dream.return_attention_contracts import (
    DREAM_OPENING_ATTENTION_VERSION,
    DREAM_RETURN_ATTENTION_VERSION,
    DreamOpeningAttention,
    DreamReturnAttentionApplication,
    DreamReturnAttentionPrompt,
    DreamReturnAttentionRecord,
)
from abu_v60.dream.return_echo_contracts import (
    DreamReturnEcho,
    DreamReturnEchoAbuRecap,
    DreamReturnEchoJudgment,
    DreamReturnEchoLineage,
    DreamReturnEchoOpenObservation,
    DreamReturnEchoWorldResponse,
)
from abu_v60.dream.seed import SEED_BATCH_REF
from abu_v60.dream.service import DreamService
from abu_v60.game import DreamCommand, DreamCommandEnvelope
from abu_v60.knowledge import KnowledgeAuthority
from abu_v60.provenance import content_hash, stable_ref
from abu_v60.world import WorldContinuityEngine
from pydantic import ValidationError
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError

ATTENTION_ACCOUNT_REF = "v60-account-return-attention-qa"
ATTENTION_OTHER_ACCOUNT_REF = "v60-account-return-attention-other-qa"
ATTENTION_ACCOUNT_REFS = (
    ATTENTION_ACCOUNT_REF,
    ATTENTION_OTHER_ACCOUNT_REF,
)


def _issue_echo() -> DreamReturnEcho:
    return DreamReturnEcho.issue(
        encounter_ref="v60-encounter-return-attention-contract",
        public_alias="馆页树",
        episode_title="共同修复，共同署名",
        judgment=DreamReturnEchoJudgment(
            choice_label="保留试案",
            summary="你当时把「保留试案」作为那一刻的判断。",
        ),
        world_response=DreamReturnEchoWorldResponse(
            summary="后来共同小组完成了修复。",
            evidence_summaries=(
                "馆方把修复安排交给共同小组。",
                "完成记录同时留下两个人的名字。",
            ),
        ),
        still_to_observe=DreamReturnEchoOpenObservation(
            summary="下一次仍把当下证据和后来结果分开核对。",
        ),
        abu_recap=DreamReturnEchoAbuRecap(
            meaning="这次只说明后来事实支持了当时判断。",
            boundary="它不能说明主人的命理关系。",
            next_attention="继续观察下一段梦中生命自己的证据。",
        ),
        lineage=DreamReturnEchoLineage(
            question_ref="v60-question-return-attention-contract",
            episode_ref="v60-episode-return-attention-contract",
            episode_version=1,
            answer_seal_ref="v60-answer-seal-return-attention-contract",
            answer_seal_hash="1" * 64,
            reveal_ref="v60-reveal-return-attention-contract",
            reveal_hash="2" * 64,
            world_event_ref="v60-world-event-return-attention-contract",
            reconciliation_result="SUPPORTED",
            committed_evidence_refs=(
                "v60-evidence-return-attention-a",
                "v60-evidence-return-attention-b",
            ),
            committed_evidence_hashes=("3" * 64, "4" * 64),
        ),
    )


def _candidate() -> GroveCandidateDefinition:
    return GroveCandidateDefinition.issue(
        pool_ref="v60.dream-grove.three-life-qualification.001",
        question_ref="v60-question-return-attention-source",
        actor_ref="v60-actor-return-attention-source",
        tree_ref="v60-tree-return-attention-source",
        domain="career",
        public_alias="馆页树",
        premise="一段仍可继续观察的梦中生命。",
        display_order=1,
    )


def test_return_attention_contracts_lock_identity_and_same_tree_application() -> None:
    echo = _issue_echo()
    candidate = _candidate()
    options = DreamReturnAttentionCoordinator._options(echo)
    assert len(options) == 3
    assert [option.kind for option in options] == [
        "WORLD_RESPONSE",
        "OUTCOME_EVIDENCE",
        "OUTCOME_EVIDENCE",
    ]

    record = DreamReturnAttentionRecord.issue(
        viewer_account_ref=ATTENTION_ACCOUNT_REF,
        source_encounter_ref=echo.encounter_ref,
        source_encounter_version=8,
        source_echo_ref=echo.echo_ref,
        source_echo_hash=echo.echo_hash,
        source_candidate_ref=candidate.candidate_ref,
        source_candidate_hash=candidate.candidate_hash,
        tree_ref=candidate.tree_ref,
        observation=options[0],
        idempotency_key="qa:return-attention:contract",
    )
    prompt = DreamReturnAttentionPrompt(
        source_encounter_ref=echo.encounter_ref,
        source_encounter_version=8,
        source_echo_ref=echo.echo_ref,
        source_echo_hash=echo.echo_hash,
        source_candidate_ref=candidate.candidate_ref,
        source_candidate_hash=candidate.candidate_hash,
        tree_ref=candidate.tree_ref,
        status="SELECTED",
        options=options,
        selection=record.public_selection(),
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
    application = DreamReturnAttentionApplication.issue(
        viewer_account_ref=ATTENTION_ACCOUNT_REF,
        attention_ref=record.attention_ref,
        attention_hash=record.attention_hash,
        encounter_ref="v60-encounter-return-attention-target",
        tree_ref=candidate.tree_ref,
    )
    opening = DreamOpeningAttention.issue(
        record=record,
        application=application,
    )

    assert prompt.contract_version == DREAM_RETURN_ATTENTION_VERSION
    assert prompt.evidence_role == "NOT_EVIDENCE"
    assert opening.contract_version == DREAM_OPENING_ATTENTION_VERSION
    assert opening.source_tree_ref == opening.target_tree_ref
    assert opening.target_encounter_ref == application.encounter_ref
    assert opening.mingli_write_allowed is False
    assert opening.decision_write_allowed is False
    assert opening.knowledge_write_allowed is False

    payload = record.model_dump(mode="python")
    with pytest.raises(
        ValidationError,
        match="dream_return_attention_option_ref_mismatch",
    ):
        DreamReturnAttentionRecord.model_validate(
            {
                **payload,
                "observation": {
                    **payload["observation"],
                    "summary": "漂移后的观察目标",
                },
            }
        )
    with pytest.raises(
        ValueError,
        match="dream_opening_attention_lineage_mismatch",
    ):
        DreamOpeningAttention.issue(
            record=record,
            application=application.model_copy(
                update={"tree_ref": "v60-tree-wrong-target"}
            ),
        )

    reveal_payload = {
        "actual_event": "共同修复完成。",
        "actual_evidence": [
            {
                "evidence_ref": "v60-evidence-attention-event-binding",
                "summary": "完成记录保留共同署名。",
            }
        ],
    }
    reveal_hash = content_hash(reveal_payload)
    with pytest.raises(
        DreamStateError,
        match="dream_attention_reveal_invalid",
    ):
        DreamAttentionFollowThroughProjector._active_world_response(
            encounter={
                "encounter_ref": application.encounter_ref,
            },
            world_event_ref="v60-world-event-expected",
            status="WORLD_RESPONSE_AVAILABLE",
            reveal={
                "encounter_ref": application.encounter_ref,
                "world_event_ref": "v60-world-event-wrong",
                "reveal_ref": stable_ref("v60-reveal", reveal_hash),
                "reveal_hash": reveal_hash,
                "reveal_json": reveal_payload,
            },
            revealed_evidence=(
                {
                    "evidence_ref": (
                        "v60-evidence-attention-event-binding"
                    ),
                    "world_event_ref": "v60-world-event-wrong",
                    "evidence_hash": content_hash(
                        reveal_payload["actual_evidence"][0]
                    ),
                    "evidence_json": reveal_payload[
                        "actual_evidence"
                    ][0],
                },
            ),
        )


def test_candidate_less_legacy_echo_has_no_attention_prompt() -> None:
    coordinator = DreamReturnAttentionCoordinator.__new__(
        DreamReturnAttentionCoordinator
    )
    coordinator._source_context = lambda *args, **kwargs: None

    assert coordinator.project_prompt(
        object(),
        account_ref=ATTENTION_ACCOUNT_REF,
        echo=_issue_echo(),
    ) is None


def _cleanup_accounts(account_refs: tuple[str, ...]) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                ALTER TABLE dream.return_attention_applications
                DISABLE TRIGGER
                    trg_dream_return_attention_application_append_only
                """
            )
        )
        connection.execute(
            text(
                """
                ALTER TABLE dream.return_attention_selections
                DISABLE TRIGGER
                    trg_dream_return_attention_selection_append_only
                """
            )
        )
        connection.execute(
            text(
                """
                DELETE FROM dream.return_attention_applications
                WHERE viewer_account_ref = ANY(:account_refs)
                """
            ),
            {"account_refs": list(account_refs)},
        )
        connection.execute(
            text(
                """
                DELETE FROM dream.return_attention_selections
                WHERE viewer_account_ref = ANY(:account_refs)
                """
            ),
            {"account_refs": list(account_refs)},
        )
        connection.execute(
            text(
                """
                ALTER TABLE dream.return_attention_applications
                ENABLE TRIGGER
                    trg_dream_return_attention_application_append_only
                """
            )
        )
        connection.execute(
            text(
                """
                ALTER TABLE dream.return_attention_selections
                ENABLE TRIGGER
                    trg_dream_return_attention_selection_append_only
                """
            )
        )
    with engine.begin() as connection:
        encounter_refs = list(
            connection.execute(
                text(
                    """
                    SELECT encounter_ref
                    FROM dream.encounters
                    WHERE viewer_account_ref = ANY(:account_refs)
                    """
                ),
                {"account_refs": list(account_refs)},
            ).scalars()
        )
        connection.execute(
            text(
                """
                DELETE FROM dream.command_receipts
                WHERE viewer_account_ref = ANY(:account_refs)
                """
            ),
            {"account_refs": list(account_refs)},
        )
        if encounter_refs:
            connection.execute(
                text(
                    """
                    DELETE FROM cognition.decision_records
                    WHERE subject_ref = ANY(:encounter_refs)
                    """
                ),
                {"encounter_refs": encounter_refs},
            )
            for table_name in ("reveals", "story_fruits", "answer_seals"):
                connection.execute(
                    text(
                        f"""
                        DELETE FROM dream.{table_name}
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
                DELETE FROM identity.sessions
                WHERE account_ref = ANY(:account_refs)
                """
            ),
            {"account_refs": list(account_refs)},
        )
        connection.execute(
            text(
                """
                DELETE FROM identity.accounts
                WHERE account_ref = ANY(:account_refs)
                """
            ),
            {"account_refs": list(account_refs)},
        )


@pytest.fixture
def attention_accounts() -> Iterator[tuple[str, str]]:
    _cleanup_accounts(ATTENTION_ACCOUNT_REFS)
    with engine.begin() as connection:
        for index, account_ref in enumerate(ATTENTION_ACCOUNT_REFS, start=1):
            connection.execute(
                text(
                    """
                    INSERT INTO identity.accounts
                        (account_ref, email, display_name, account_role, active,
                         password_scheme, password_hash, password_salt,
                         source_ref, source_hash, source_batch_ref)
                    VALUES
                        (:account_ref, :email, :display_name, 'test_operator',
                         true, 'pbkdf2_sha256_310k', :password_hash,
                         :password_salt, :source_ref, :source_hash,
                         :batch_ref)
                    """
                ),
                {
                    "account_ref": account_ref,
                    "email": f"v60-return-attention-{index}@example.invalid",
                    "display_name": f"Dream Return Attention QA {index}",
                    "password_hash": "0" * 64,
                    "password_salt": "0" * 32,
                    "source_ref": f"v60:test:return-attention:{index}",
                    "source_hash": str(index) * 64,
                    "batch_ref": SEED_BATCH_REF,
                },
            )
    try:
        yield ATTENTION_ACCOUNT_REFS
    finally:
        _cleanup_accounts(ATTENTION_ACCOUNT_REFS)


def _command(
    snapshot: dict[str, object],
    command: DreamCommand,
    *,
    target_ref: str | None = None,
    choice_id: str | None = None,
) -> DreamCommandEnvelope:
    encounter = snapshot["encounter"]
    assert isinstance(encounter, dict)
    identity = target_ref or choice_id or "none"
    return DreamCommandEnvelope(
        command=command,
        encounter_ref=str(encounter["encounter_ref"]),
        expected_version=int(encounter["version"]),
        idempotency_key=(
            f"qa:return-attention:{encounter['encounter_ref']}:"
            f"{encounter['version']}:{command.value}:{identity}"
        ),
        target_ref=target_ref,
        choice_id=choice_id,
    )


def _organ(snapshot: dict[str, object], key: str) -> dict[str, object]:
    tree = snapshot["tree"]
    assert isinstance(tree, dict)
    organs = tree["organs"]
    assert isinstance(organs, list)
    return next(organ for organ in organs if organ["key"] == key)


def _complete_and_return(
    service: DreamService,
    *,
    account_ref: str,
    snapshot: dict[str, object],
) -> dict[str, object]:
    for key, command in (
        ("evidence_leaf_world", DreamCommand.OBSERVE_EVIDENCE),
        ("evidence_leaf_structure", DreamCommand.OBSERVE_EVIDENCE),
        ("structure_branch", DreamCommand.OBSERVE_STRUCTURE),
        ("question_flower", DreamCommand.OPEN_QUESTION),
    ):
        snapshot = service.execute_command(
            account_ref=account_ref,
            envelope=_command(
                snapshot,
                command,
                target_ref=str(_organ(snapshot, key)["organ_ref"]),
            ),
        )
    question = snapshot["question"]
    assert isinstance(question, dict)
    options = question["options"]
    assert isinstance(options, list)
    snapshot = service.execute_command(
        account_ref=account_ref,
        envelope=_command(
            snapshot,
            DreamCommand.SEAL_ANSWER,
            choice_id=str(options[0]["choice_id"]),
        ),
    )
    lineage = snapshot["lineage"]
    assert isinstance(lineage, dict)
    with engine.connect() as connection:
        event_ref = str(
            connection.execute(
                text(
                    """
                    SELECT world_event_ref
                    FROM story.question_instances
                    WHERE question_ref = :question_ref
                    """
                ),
                {"question_ref": lineage["question_ref"]},
            ).scalar_one()
        )
    with engine.begin() as connection:
        WorldContinuityEngine().advance_and_settle(
            connection=connection,
            event_ref=event_ref,
        )
    assert service.synchronize_settled_world_events(
        event_refs=[event_ref]
    ) == 1
    snapshot = service.snapshot(account_ref=account_ref)
    for command in (DreamCommand.REVEAL, DreamCommand.RECONCILE):
        snapshot = service.execute_command(
            account_ref=account_ref,
            envelope=_command(snapshot, command),
        )
    return service.execute_command(
        account_ref=account_ref,
        envelope=_command(snapshot, DreamCommand.RETURN_TO_GROVE),
    )


def test_expired_second_chapter_is_archived_and_rematerialized(
    attention_accounts: tuple[str, str],
) -> None:
    account_ref, _ = attention_accounts
    service = DreamService(engine)
    entry = service.entry(account_ref=account_ref)
    first_candidate = entry["grove"]["candidates"][0]
    first_snapshot = service.start_grove_encounter(
        account_ref=account_ref,
        candidate_ref=first_candidate["candidate_ref"],
    )
    second_chapter_grove = _complete_and_return(
        service,
        account_ref=account_ref,
        snapshot=first_snapshot,
    )
    second_route = next(
        candidate["chapter_route"]
        for candidate in second_chapter_grove["grove"]["candidates"]
        if candidate["candidate_ref"] == first_candidate["candidate_ref"]
    )
    assert second_route["basis"] == "CANONICAL_TRANSITION"
    assert second_route["target_chapter"] == "RETURN_VISIT"

    snapshot = service.start_grove_encounter(
        account_ref=account_ref,
        candidate_ref=first_candidate["candidate_ref"],
    )
    assert snapshot["encounter"]["chapter"] == "RETURN_VISIT"
    expired_encounter_ref = snapshot["encounter"]["encounter_ref"]
    expired_question_ref = snapshot["lineage"]["question_ref"]
    expired_world_event_ref = snapshot["lineage"]["world_event_ref"]
    for key, command in (
        ("evidence_leaf_world", DreamCommand.OBSERVE_EVIDENCE),
        ("evidence_leaf_structure", DreamCommand.OBSERVE_EVIDENCE),
        ("structure_branch", DreamCommand.OBSERVE_STRUCTURE),
        ("question_flower", DreamCommand.OPEN_QUESTION),
    ):
        snapshot = service.execute_command(
            account_ref=account_ref,
            envelope=_command(
                snapshot,
                command,
                target_ref=str(_organ(snapshot, key)["organ_ref"]),
            ),
        )
    assert snapshot["question"]["answer_window_status"] == "OPEN"

    with engine.begin() as connection:
        WorldContinuityEngine().advance_and_settle(
            connection=connection,
            event_ref=expired_world_event_ref,
        )
    expired_snapshot = service.snapshot(account_ref=account_ref)
    assert expired_snapshot["encounter"]["status"] == "QUESTION_OPEN"
    assert expired_snapshot["question"]["answer_window_status"] == (
        "CLOSED_UNSEALED"
    )
    assert expired_snapshot["game"]["available_commands"] == [
        "RETURN_TO_GROVE"
    ]
    with pytest.raises(
        DreamStateError,
        match="dream_question_window_closed",
    ):
        service.execute_command(
            account_ref=account_ref,
            envelope=_command(
                expired_snapshot,
                DreamCommand.SEAL_ANSWER,
                choice_id=str(
                    expired_snapshot["question"]["options"][0]["choice_id"]
                ),
            ),
        )

    recovery_command = _command(
        expired_snapshot,
        DreamCommand.RETURN_TO_GROVE,
    )
    returned = service.execute_command(
        account_ref=account_ref,
        envelope=recovery_command,
    )
    assert returned["kind"] == "GROVE"
    retry_route = next(
        candidate["chapter_route"]
        for candidate in returned["grove"]["candidates"]
        if candidate["candidate_ref"] == first_candidate["candidate_ref"]
    )
    assert retry_route["basis"] == "CANONICAL_TRANSITION"
    assert retry_route["target_source_question_ref"] == second_route[
        "target_source_question_ref"
    ]
    with engine.connect() as connection:
        archived = (
            connection.execute(
                text(
                    """
                    SELECT status, version, state_json, state_hash
                    FROM dream.encounters
                    WHERE encounter_ref = :encounter_ref
                    """
                ),
                {"encounter_ref": expired_encounter_ref},
            )
            .mappings()
            .one()
        )
        assert archived["status"] == "QUESTION_OPEN"
        assert archived["state_json"]["departed_to_grove"] is True
        assert archived["state_json"]["expired_unsealed"] is True
        assert archived["state_json"]["expiration_reason"] == (
            "QUESTION_WINDOW_CLOSED"
        )
        assert content_hash(archived["state_json"]) == archived["state_hash"]
        receipt = (
            connection.execute(
                text(
                    """
                    SELECT result_status, result_version,
                           result_state_hash
                    FROM dream.command_receipts
                    WHERE viewer_account_ref = :account_ref
                      AND idempotency_key = :idempotency_key
                    """
                ),
                {
                    "account_ref": account_ref,
                    "idempotency_key": recovery_command.idempotency_key,
                },
            )
            .mappings()
            .one()
        )
        assert receipt["result_status"] == "QUESTION_OPEN"
        assert receipt["result_version"] == archived["version"]
        assert receipt["result_state_hash"] == archived["state_hash"]
        assert (
            connection.execute(
                text(
                    """
                    SELECT count(*)
                    FROM dream.answer_seals
                    WHERE encounter_ref = :encounter_ref
                      AND actor_role = 'HUMAN'
                    """
                ),
                {"encounter_ref": expired_encounter_ref},
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
                      AND status = 'COMPLETED'
                    """
                ),
                {"account_ref": account_ref},
            ).scalar_one()
            == 1
        )

    retried = service.start_grove_encounter(
        account_ref=account_ref,
        candidate_ref=first_candidate["candidate_ref"],
    )
    assert retried["encounter"]["chapter"] == "RETURN_VISIT"
    assert retried["encounter"]["encounter_ref"] != expired_encounter_ref
    assert retried["lineage"]["question_ref"] != expired_question_ref
    assert retried["lineage"]["world_event_ref"] != expired_world_event_ref
    assert retried["continuation"]["completed_encounter_count"] == 1
    with engine.connect() as connection:
        retry_window = (
            connection.execute(
                text(
                    """
                    SELECT cutoff_tick, due_tick
                    FROM story.question_instances
                    WHERE question_ref = :question_ref
                    """
                ),
                {"question_ref": retried["lineage"]["question_ref"]},
            )
            .mappings()
            .one()
        )
        assert (
            int(retry_window["due_tick"])
            - int(retry_window["cutoff_tick"])
            == OPPORTUNITY_WINDOW_TICKS
        )
        assert OPPORTUNITY_WINDOW_TICKS == 5
        assert (
            connection.execute(
                text(
                    """
                    SELECT count(*)
                    FROM dream.encounters
                    WHERE viewer_account_ref = :account_ref
                      AND COALESCE(
                          state_json ->> 'departed_to_grove',
                          'false'
                      ) <> 'true'
                    """
                ),
                {"account_ref": account_ref},
            ).scalar_one()
            == 1
        )
    for key, command in (
        ("evidence_leaf_world", DreamCommand.OBSERVE_EVIDENCE),
        ("evidence_leaf_structure", DreamCommand.OBSERVE_EVIDENCE),
        ("structure_branch", DreamCommand.OBSERVE_STRUCTURE),
        ("question_flower", DreamCommand.OPEN_QUESTION),
    ):
        retried = service.execute_command(
            account_ref=account_ref,
            envelope=_command(
                retried,
                command,
                target_ref=str(_organ(retried, key)["organ_ref"]),
            ),
        )
    retried = service.execute_command(
        account_ref=account_ref,
        envelope=_command(
            retried,
            DreamCommand.SEAL_ANSWER,
            choice_id=str(retried["question"]["options"][0]["choice_id"]),
        ),
    )
    with engine.begin() as connection:
        WorldContinuityEngine().advance_and_settle(
            connection=connection,
            event_ref=str(retried["lineage"]["world_event_ref"]),
        )
    assert (
        service.synchronize_settled_world_events(
            event_refs=[str(retried["lineage"]["world_event_ref"])]
        )
        == 1
    )
    retried = service.snapshot(account_ref=account_ref)
    for command in (DreamCommand.REVEAL, DreamCommand.RECONCILE):
        retried = service.execute_command(
            account_ref=account_ref,
            envelope=_command(retried, command),
        )
    assert retried["encounter"]["encounter_ref"] != expired_encounter_ref
    assert retried["encounter"]["status"] == "COMPLETED"
    assert retried["encounter"]["state"]["reconciled"] is True


def test_historical_echo_binds_persisted_candidate_when_same_tree_candidates_coexist(
    attention_accounts: tuple[str, str],
) -> None:
    account_ref, _ = attention_accounts
    service = DreamService(engine)
    entry = service.entry(account_ref=account_ref)
    first_candidate = entry["grove"]["candidates"][0]
    first_snapshot = service.start_grove_encounter(
        account_ref=account_ref,
        candidate_ref=first_candidate["candidate_ref"],
    )
    returned = _complete_and_return(
        service,
        account_ref=account_ref,
        snapshot=first_snapshot,
    )
    source_encounter_ref = returned["grove"]["return_echo"][
        "encounter_ref"
    ]

    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            actor_ref = str(
                connection.execute(
                    text(
                        """
                        SELECT actor_ref
                        FROM dream.grove_candidates
                        WHERE candidate_ref = :candidate_ref
                        """
                    ),
                    {"candidate_ref": first_candidate["candidate_ref"]},
                ).scalar_one()
            )
            competing_candidate = GroveCandidateDefinition.issue(
                pool_ref="v60.dream-grove.same-tree-regression.001",
                question_ref="v60-question-wenxi-index-convention-v1",
                actor_ref=actor_ref,
                tree_ref=str(first_snapshot["tree"]["tree_ref"]),
                domain="career",
                public_alias="未来馆页树",
                premise="同一生命树未来可能出现的另一条候选记录。",
                display_order=1,
            )
            DreamGroveAdmissionService().admit(
                connection,
                definition=competing_candidate,
            )
            echo = service._return_echo.project_for_encounter(
                connection,
                account_ref=account_ref,
                encounter_ref=source_encounter_ref,
            )
            source = service._return_attention._source_context(
                connection,
                account_ref=account_ref,
                encounter_ref=source_encounter_ref,
                for_update=False,
                allow_missing_candidate=False,
            )
            assert echo is not None
            assert source is not None
            assert source["candidate"].candidate_ref == first_candidate[
                "candidate_ref"
            ]
            assert echo.public_alias == first_candidate["public_alias"]
        finally:
            transaction.rollback()


def test_stale_attention_is_rejected_after_start_while_exact_replay_survives(
    attention_accounts: tuple[str, str],
) -> None:
    account_ref, stale_account_ref = attention_accounts
    service = DreamService(engine)

    def prepare(
        owner_ref: str,
        *,
        idempotency_key: str,
    ) -> tuple[dict[str, object], DreamCommandEnvelope]:
        entry = service.entry(account_ref=owner_ref)
        candidate = entry["grove"]["candidates"][0]
        snapshot = service.start_grove_encounter(
            account_ref=owner_ref,
            candidate_ref=candidate["candidate_ref"],
        )
        returned = _complete_and_return(
            service,
            account_ref=owner_ref,
            snapshot=snapshot,
        )
        prompt = DreamReturnAttentionPrompt.model_validate(
            returned["grove"]["next_attention"]
        )
        return candidate, DreamCommandEnvelope(
            command=DreamCommand.SELECT_NEXT_ATTENTION,
            encounter_ref=prompt.source_encounter_ref,
            expected_version=prompt.source_encounter_version,
            idempotency_key=idempotency_key,
            target_ref=prompt.options[0].observation_ref,
        )

    candidate, replay_envelope = prepare(
        account_ref,
        idempotency_key="qa:return-attention:replay-after-start",
    )
    service.execute_command(
        account_ref=account_ref,
        envelope=replay_envelope,
    )
    started = service.start_grove_encounter(
        account_ref=account_ref,
        candidate_ref=str(candidate["candidate_ref"]),
    )
    replayed = service.execute_command(
        account_ref=account_ref,
        envelope=replay_envelope,
    )
    assert replayed["kind"] == "ENCOUNTER"
    assert replayed["snapshot"]["encounter"]["encounter_ref"] == (
        started["encounter"]["encounter_ref"]
    )

    stale_candidate, stale_envelope = prepare(
        stale_account_ref,
        idempotency_key="qa:return-attention:stale-after-start",
    )
    service.start_grove_encounter(
        account_ref=stale_account_ref,
        candidate_ref=str(stale_candidate["candidate_ref"]),
    )
    with pytest.raises(
        DreamConflictError,
        match="dream_return_attention_requires_grove",
    ):
        service.execute_command(
            account_ref=stale_account_ref,
            envelope=stale_envelope,
        )
    with engine.connect() as connection:
        assert (
            connection.execute(
                text(
                    """
                    SELECT count(*)
                    FROM dream.return_attention_selections
                    WHERE viewer_account_ref = :account_ref
                    """
                ),
                {"account_ref": stale_account_ref},
            ).scalar_one()
            == 0
        )


def test_concurrent_attention_and_chapter_start_never_leave_unapplied_selection(
    attention_accounts: tuple[str, str],
) -> None:
    account_ref, _ = attention_accounts
    service = DreamService(engine)
    entry = service.entry(account_ref=account_ref)
    candidate = entry["grove"]["candidates"][0]
    snapshot = service.start_grove_encounter(
        account_ref=account_ref,
        candidate_ref=candidate["candidate_ref"],
    )
    returned = _complete_and_return(
        service,
        account_ref=account_ref,
        snapshot=snapshot,
    )
    prompt = DreamReturnAttentionPrompt.model_validate(
        returned["grove"]["next_attention"]
    )
    envelope = DreamCommandEnvelope(
        command=DreamCommand.SELECT_NEXT_ATTENTION,
        encounter_ref=prompt.source_encounter_ref,
        expected_version=prompt.source_encounter_version,
        idempotency_key="qa:return-attention:concurrent-with-start",
        target_ref=prompt.options[0].observation_ref,
    )
    barrier = Barrier(2)

    def select_attention() -> str:
        barrier.wait()
        try:
            service.execute_command(
                account_ref=account_ref,
                envelope=envelope,
            )
        except DreamConflictError as exc:
            return str(exc)
        return "SELECTED"

    def start_chapter() -> dict[str, object]:
        barrier.wait()
        return service.start_grove_encounter(
            account_ref=account_ref,
            candidate_ref=str(candidate["candidate_ref"]),
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        selection_future = executor.submit(select_attention)
        chapter_future = executor.submit(start_chapter)
        selection_result = selection_future.result()
        chapter_snapshot = chapter_future.result()

    current_encounter_ref = chapter_snapshot["encounter"]["encounter_ref"]
    with engine.connect() as connection:
        binding = (
            connection.execute(
                text(
                    """
                    SELECT selection.attention_ref,
                           application.encounter_ref
                    FROM dream.return_attention_selections AS selection
                    LEFT JOIN dream.return_attention_applications AS application
                      ON application.attention_ref = selection.attention_ref
                    WHERE selection.viewer_account_ref = :account_ref
                    """
                ),
                {"account_ref": account_ref},
            )
            .mappings()
            .one_or_none()
        )
    if selection_result == "SELECTED":
        assert binding is not None
        assert binding["encounter_ref"] == current_encounter_ref
    else:
        assert selection_result == "dream_return_attention_requires_grove"
        assert binding is None


def _schema_digest(schema_name: str) -> tuple[tuple[str, int, str], ...]:
    table_names = inspect(engine).get_table_names(schema=schema_name)
    assert all(re.fullmatch(r"[a-z_][a-z0-9_]*", name) for name in table_names)
    digest: list[tuple[str, int, str]] = []
    with engine.connect() as connection:
        for table_name in sorted(table_names):
            row = (
                connection.execute(
                    text(
                        f"""
                        SELECT count(*) AS row_count,
                               md5(COALESCE(
                                   string_agg(row_hash, '' ORDER BY row_hash),
                                   ''
                               )) AS content_digest
                        FROM (
                            SELECT md5(row_to_json(source_row)::text)
                                       AS row_hash
                            FROM "{schema_name}"."{table_name}" AS source_row
                        ) AS hashed_rows
                        """
                    )
                )
                .mappings()
                .one()
            )
            digest.append(
                (
                    table_name,
                    int(row["row_count"]),
                    str(row["content_digest"]),
                )
            )
    return tuple(digest)


def _knowledge_digest() -> str:
    authority = KnowledgeAuthority()
    return content_hash(
        {
            "public": authority.public_manifest(),
            "candidate": authority.candidate_rule_manifest(),
            "quant": authority.quant_foundation_manifest(),
            "source_review": authority.source_review_manifest(),
            "mechanism": authority.mechanism_evidence_manifest(),
            "timing": authority.timing_evidence_manifest(),
            "relation_effect": (
                authority.relation_effect_rule_admission_manifest()
            ),
            "selection": authority.selection_manifest(),
        }
    )


def test_return_attention_is_replay_safe_private_and_applies_only_same_tree(
    attention_accounts: tuple[str, str],
) -> None:
    account_ref, other_account_ref = attention_accounts
    service = DreamService(engine)
    entry = service.entry(account_ref=account_ref)
    assert entry["kind"] == "GROVE"
    candidates = entry["grove"]["candidates"]
    first_candidate = candidates[0]
    different_candidate = candidates[1]
    first_snapshot = service.start_grove_encounter(
        account_ref=account_ref,
        candidate_ref=first_candidate["candidate_ref"],
    )
    first_question_ref = first_snapshot["lineage"]["question_ref"]
    first_tree_ref = first_snapshot["tree"]["tree_ref"]
    first_grove = _complete_and_return(
        service,
        account_ref=account_ref,
        snapshot=first_snapshot,
    )
    prompt_payload = first_grove["grove"]["next_attention"]
    prompt = DreamReturnAttentionPrompt.model_validate(prompt_payload)
    assert prompt.status == "AWAITING_SELECTION"
    assert prompt.tree_ref == first_tree_ref
    assert first_grove["grove"]["grove_version"] == "v60.dream-grove.005"
    next_chapter_route = next(
        candidate["chapter_route"]
        for candidate in first_grove["grove"]["candidates"]
        if candidate["candidate_ref"] == first_candidate["candidate_ref"]
    )
    assert next_chapter_route["status"] == "AVAILABLE"
    assert next_chapter_route["basis"] == "CANONICAL_TRANSITION"
    assert next_chapter_route["target_chapter"] == "RETURN_VISIT"
    assert next_chapter_route["target_source_question_ref"] == (
        "v60-question-wenxi-index-convention-v1"
    )
    assert next_chapter_route["routing_authority"] == (
        "CANONICAL_EPISODE_GRAPH"
    )
    assert next_chapter_route["attention_routing_allowed"] is False
    assert next_chapter_route["attention_ref_used"] is False
    assert next_chapter_route["question_changed"] is False
    assert next_chapter_route["answer_changed"] is False
    assert next_chapter_route["npc_choice_changed"] is False
    assert next_chapter_route["outcome_changed"] is False
    other_account_route = DreamService(engine).entry(
        account_ref=other_account_ref
    )["grove"]["candidates"][0]["chapter_route"]
    assert other_account_route["basis"] == "ENTRYPOINT"
    assert other_account_route["target_chapter"] == "FIRST_VISIT"

    envelope = DreamCommandEnvelope(
        command=DreamCommand.SELECT_NEXT_ATTENTION,
        encounter_ref=prompt.source_encounter_ref,
        expected_version=prompt.source_encounter_version,
        idempotency_key="qa:return-attention:select:first",
        target_ref=prompt.options[0].observation_ref,
    )
    mingli_before = _schema_digest("mingli")
    cognition_before = _schema_digest("cognition")
    knowledge_before = _knowledge_digest()
    with ThreadPoolExecutor(max_workers=2) as executor:
        selected_entries = list(
            executor.map(
                lambda _: service.execute_command(
                    account_ref=account_ref,
                    envelope=envelope,
                ),
                range(2),
            )
        )
    selections = [
        DreamReturnAttentionPrompt.model_validate(
            item["grove"]["next_attention"]
        ).selection
        for item in selected_entries
    ]
    assert selections[0] is not None
    assert selections[0] == selections[1]
    assert service.execute_command(
        account_ref=account_ref,
        envelope=envelope,
    )["grove"]["next_attention"]["selection"] == (
        selections[0].model_dump(mode="json")
    )
    pending = DreamPendingAttention.model_validate(
        service.entry(account_ref=account_ref)["grove"][
            "pending_attention"
        ]
    )
    route_after_attention_selection = next(
        candidate["chapter_route"]
        for candidate in service.entry(account_ref=account_ref)["grove"][
            "candidates"
        ]
        if candidate["candidate_ref"] == first_candidate["candidate_ref"]
    )
    assert route_after_attention_selection == next_chapter_route
    assert pending.attention_ref == selections[0].attention_ref
    assert pending.source_candidate_ref == first_candidate["candidate_ref"]
    assert pending.tree_ref == first_tree_ref
    assert _schema_digest("mingli") == mingli_before
    assert _schema_digest("cognition") == cognition_before
    assert _knowledge_digest() == knowledge_before

    with engine.connect() as connection:
        assert (
            connection.execute(
                text(
                    """
                    SELECT count(*)
                    FROM dream.return_attention_selections
                    WHERE viewer_account_ref = :account_ref
                    """
                ),
                {"account_ref": account_ref},
            ).scalar_one()
            == 1
        )
    with pytest.raises(
        DreamConflictError,
        match="dream_command_idempotency_conflict",
    ):
        service.execute_command(
            account_ref=account_ref,
            envelope=envelope.model_copy(
                update={
                    "target_ref": prompt.options[1].observation_ref,
                }
            ),
        )
    with pytest.raises(
        DreamConflictError,
        match="dream_return_attention_already_selected",
    ):
        service.execute_command(
            account_ref=account_ref,
            envelope=envelope.model_copy(
                update={
                    "idempotency_key": (
                        "qa:return-attention:select:second-attempt"
                    ),
                    "target_ref": prompt.options[1].observation_ref,
                }
            ),
        )
    with pytest.raises(
        DreamStateError,
        match="dream_return_attention_source_candidate_invalid",
    ):
        service.execute_command(
            account_ref=other_account_ref,
            envelope=envelope,
        )

    different_snapshot = service.start_grove_encounter(
        account_ref=account_ref,
        candidate_ref=different_candidate["candidate_ref"],
    )
    different_tree_ref = different_snapshot["tree"]["tree_ref"]
    assert different_snapshot["opening_attention"] is None
    assert different_snapshot["attention_follow_through"] is None
    with engine.connect() as connection:
        assert (
            connection.execute(
                text(
                    """
                    SELECT count(*)
                    FROM dream.return_attention_applications
                    WHERE viewer_account_ref = :account_ref
                    """
                ),
                {"account_ref": account_ref},
            ).scalar_one()
            == 0
        )
    second_grove = _complete_and_return(
        service,
        account_ref=account_ref,
        snapshot=different_snapshot,
    )
    assert second_grove["grove"]["next_attention"]["tree_ref"] == (
        different_tree_ref
    )
    pending_after_other_tree = DreamPendingAttention.model_validate(
        second_grove["grove"]["pending_attention"]
    )
    assert pending_after_other_tree == pending
    assert second_grove["grove"]["attention_follow_through"] is None
    different_prompt = DreamReturnAttentionPrompt.model_validate(
        second_grove["grove"]["next_attention"]
    )
    assert different_prompt.status == "AWAITING_SELECTION"
    multiple_pending_entry = service.execute_command(
        account_ref=account_ref,
        envelope=DreamCommandEnvelope(
            command=DreamCommand.SELECT_NEXT_ATTENTION,
            encounter_ref=different_prompt.source_encounter_ref,
            expected_version=different_prompt.source_encounter_version,
            idempotency_key="qa:return-attention:select:different-tree",
            target_ref=different_prompt.options[0].observation_ref,
        ),
    )
    assert DreamPendingAttention.model_validate(
        multiple_pending_entry["grove"]["pending_attention"]
    ) == pending

    mingli_before_application = _schema_digest("mingli")
    cognition_before_application = _schema_digest("cognition")
    knowledge_before_application = _knowledge_digest()
    same_tree_snapshot = service.start_grove_encounter(
        account_ref=account_ref,
        candidate_ref=first_candidate["candidate_ref"],
    )
    assert same_tree_snapshot["encounter"]["chapter"] == "RETURN_VISIT"
    assert same_tree_snapshot["lineage"]["question_ref"] != first_question_ref
    with engine.connect() as connection:
        chapter_rows = (
            connection.execute(
                text(
                    """
                    SELECT question.question_ref, question.prompt,
                           question.options_json,
                           question.episode_contract_json,
                           event.world_event_ref, event.event_json,
                           event.sealed_outcome_json,
                           baseline.event_json AS baseline_event_json
                    FROM story.question_instances AS question
                    JOIN world.events AS event
                      ON event.world_event_ref = question.world_event_ref
                    LEFT JOIN world.events AS baseline
                      ON baseline.world_event_ref =
                         question.episode_contract_json
                             ->> 'baseline_event_ref'
                    WHERE question.question_ref = ANY(:question_refs)
                    """
                ),
                {
                    "question_refs": [
                        same_tree_snapshot["lineage"]["question_ref"],
                        next_chapter_route[
                            "target_source_question_ref"
                        ],
                        first_question_ref,
                    ]
                },
            )
            .mappings()
            .all()
        )
    by_question = {
        str(row["question_ref"]): dict(row) for row in chapter_rows
    }
    dynamic_second = by_question[
        str(same_tree_snapshot["lineage"]["question_ref"])
    ]
    static_second = by_question[
        str(next_chapter_route["target_source_question_ref"])
    ]
    dynamic_first = by_question[str(first_question_ref)]
    assert dynamic_second["prompt"] == static_second["prompt"]
    assert dynamic_second["options_json"] == static_second["options_json"]
    assert dynamic_second["episode_contract_json"]["entrypoint"] is True
    assert dynamic_second["episode_contract_json"]["chapter"] == (
        "RETURN_VISIT"
    )
    assert dynamic_second["event_json"]["source_question_ref"] == (
        next_chapter_route["target_source_question_ref"]
    )
    assert dynamic_second["event_json"]["source_candidate_ref"] == (
        first_candidate["candidate_ref"]
    )
    assert dynamic_second["event_json"]["source_transition_ref"] == (
        next_chapter_route["transition_ref"]
    )
    assert dynamic_second["event_json"]["attention_ref_used"] is False
    assert dynamic_second["event_json"]["attention_changed_route"] is False
    assert dynamic_second["sealed_outcome_json"][
        "resolved_proposition"
    ] == static_second["sealed_outcome_json"]["resolved_proposition"]
    assert dynamic_second["sealed_outcome_json"]["actual_event"] == (
        static_second["sealed_outcome_json"]["actual_event"]
    )
    assert dynamic_second["baseline_event_json"]["caused_by_event_ref"] == (
        dynamic_first["world_event_ref"]
    )
    opening = DreamOpeningAttention.model_validate(
        same_tree_snapshot["opening_attention"]
    )
    assert opening.attention_ref == selections[0].attention_ref
    assert opening.source_tree_ref == first_tree_ref
    assert opening.target_tree_ref == first_tree_ref
    assert opening.target_encounter_ref == (
        same_tree_snapshot["encounter"]["encounter_ref"]
    )
    follow_through = DreamAttentionFollowThrough.model_validate(
        same_tree_snapshot["attention_follow_through"]
    )
    assert follow_through.application_ref == opening.application_ref
    assert follow_through.status == "OBSERVING"
    assert follow_through.progress.observed_count == 0
    assert follow_through.world_response is None
    assert _schema_digest("mingli") == mingli_before_application
    assert _schema_digest("cognition") == cognition_before_application
    assert _knowledge_digest() == knowledge_before_application
    assert DreamService(engine).snapshot(account_ref=account_ref)[
        "opening_attention"
    ] == opening.model_dump(mode="json")
    assert DreamService(engine).snapshot(account_ref=account_ref)[
        "attention_follow_through"
    ] == follow_through.model_dump(mode="json")
    assert DreamService(engine).snapshot(account_ref=account_ref)[
        "opening_attention"
    ] == opening.model_dump(mode="json")
    with engine.connect() as connection:
        assert (
            connection.execute(
                text(
                    """
                    SELECT count(*)
                    FROM dream.return_attention_applications
                    WHERE viewer_account_ref = :account_ref
                    """
                ),
                {"account_ref": account_ref},
            ).scalar_one()
            == 1
        )

    snapshot = same_tree_snapshot
    for expected_count, (key, command) in enumerate(
        (
            ("evidence_leaf_world", DreamCommand.OBSERVE_EVIDENCE),
            (
                "evidence_leaf_structure",
                DreamCommand.OBSERVE_EVIDENCE,
            ),
            ("structure_branch", DreamCommand.OBSERVE_STRUCTURE),
        ),
        start=1,
    ):
        snapshot = service.execute_command(
            account_ref=account_ref,
            envelope=_command(
                snapshot,
                command,
                target_ref=str(_organ(snapshot, key)["organ_ref"]),
            ),
        )
        follow_through = DreamAttentionFollowThrough.model_validate(
            snapshot["attention_follow_through"]
        )
        assert follow_through.progress.observed_count == expected_count
        assert follow_through.status == (
            "OBSERVATIONS_COMPLETE"
            if expected_count == 3
            else "OBSERVING"
        )
        assert follow_through.world_response is None

    snapshot = service.execute_command(
        account_ref=account_ref,
        envelope=_command(
            snapshot,
            DreamCommand.OPEN_QUESTION,
            target_ref=str(
                _organ(snapshot, "question_flower")["organ_ref"]
            ),
        ),
    )
    assert snapshot["attention_follow_through"]["status"] == (
        "OBSERVATIONS_COMPLETE"
    )
    question = snapshot["question"]
    snapshot = service.execute_command(
        account_ref=account_ref,
        envelope=_command(
            snapshot,
            DreamCommand.SEAL_ANSWER,
            choice_id=str(question["options"][0]["choice_id"]),
        ),
    )
    assert snapshot["attention_follow_through"]["status"] == (
        "AWAITING_WORLD_RESPONSE"
    )
    lineage = snapshot["lineage"]
    with engine.connect() as connection:
        event_ref = str(
            connection.execute(
                text(
                    """
                    SELECT world_event_ref
                    FROM story.question_instances
                    WHERE question_ref = :question_ref
                    """
                ),
                {"question_ref": lineage["question_ref"]},
            ).scalar_one()
        )
    with engine.begin() as connection:
        WorldContinuityEngine().advance_and_settle(
            connection=connection,
            event_ref=event_ref,
        )
    assert service.synchronize_settled_world_events(
        event_refs=[event_ref]
    ) == 1
    snapshot = service.snapshot(account_ref=account_ref)
    hidden = DreamAttentionFollowThrough.model_validate(
        snapshot["attention_follow_through"]
    )
    assert hidden.status == "WORLD_RESPONSE_READY_HIDDEN"
    assert hidden.world_response is None
    snapshot = service.execute_command(
        account_ref=account_ref,
        envelope=_command(snapshot, DreamCommand.REVEAL),
    )
    visible = DreamAttentionFollowThrough.model_validate(
        snapshot["attention_follow_through"]
    )
    assert visible.status == "WORLD_RESPONSE_AVAILABLE"
    assert visible.world_response is not None
    assert visible.world_response.material_count == 2
    assert visible.semantic_match_status == (
        "SEMANTIC_MATCH_NOT_EVALUATED"
    )
    snapshot = service.execute_command(
        account_ref=account_ref,
        envelope=_command(snapshot, DreamCommand.RECONCILE),
    )
    assert snapshot["attention_follow_through"]["status"] == (
        "RECONCILED_NOT_EVALUATED"
    )
    returned = service.execute_command(
        account_ref=account_ref,
        envelope=_command(snapshot, DreamCommand.RETURN_TO_GROVE),
    )
    returned_follow_through = DreamAttentionFollowThrough.model_validate(
        returned["grove"]["attention_follow_through"]
    )
    assert returned_follow_through.status == "RETURNED_NOT_EVALUATED"
    assert returned_follow_through.world_response == visible.world_response
    remaining_pending = DreamPendingAttention.model_validate(
        returned["grove"]["pending_attention"]
    )
    assert remaining_pending.source_candidate_ref == (
        different_candidate["candidate_ref"]
    )
    assert remaining_pending.tree_ref == different_tree_ref
    terminal_route = next(
        candidate["chapter_route"]
        for candidate in returned["grove"]["candidates"]
        if candidate["candidate_ref"] == first_candidate["candidate_ref"]
    )
    assert terminal_route["status"] == "STORY_CURRENTLY_COMPLETE"
    assert terminal_route["basis"] == "TERMINAL_CHAPTER"
    assert terminal_route["previous_source_question_ref"] == (
        terminal_route["target_source_question_ref"]
    )
    assert terminal_route["transition_ref"] is None
    assert terminal_route["transition_hash"] is None
    with pytest.raises(
        DreamStateError,
        match="dream_grove_story_currently_complete",
    ):
        service.start_grove_encounter(
            account_ref=account_ref,
            candidate_ref=first_candidate["candidate_ref"],
        )

    assert DreamService(engine).entry(account_ref=other_account_ref)[
        "grove"
    ]["next_attention"] is None

    for statement in (
        """
        UPDATE dream.return_attention_selections
        SET observation_ref = 'v60-tampered-observation'
        WHERE attention_ref = :attention_ref
        """,
        """
        DELETE FROM dream.return_attention_applications
        WHERE attention_ref = :attention_ref
        """,
    ):
        with pytest.raises(
            DBAPIError,
            match="dream_return_attention_is_append_only",
        ), engine.begin() as connection:
            connection.execute(
                text(statement),
                {"attention_ref": opening.attention_ref},
            )
