from __future__ import annotations

from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest
from abu_v60.db import engine
from abu_v60.dream.errors import DreamConflictError, DreamStateError
from abu_v60.dream.first_slice import SEALED_FUTURE_OUTCOME
from abu_v60.dream.grove import DreamGroveRepository
from abu_v60.dream.return_slice import RETURN_SEALED_FUTURE_OUTCOME
from abu_v60.dream.seed import SEED_BATCH_REF
from abu_v60.dream.service import DreamService
from abu_v60.game import DreamCommand, DreamCommandEnvelope
from abu_v60.provenance import canonical_json, content_hash
from abu_v60.world import WorldContinuityEngine
from sqlalchemy import text

QA_ACCOUNT_REF = "v60-account-command-boundary-qa"
QA_EMAIL = "v60-command-boundary@example.invalid"


@pytest.fixture
def qa_account() -> Iterator[str]:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO identity.accounts
                    (account_ref, email, display_name, account_role, active,
                     password_scheme, password_hash, password_salt,
                     source_ref, source_hash, source_batch_ref)
                VALUES
                    (:account_ref, :email, 'Dream Command QA', 'test_operator', true,
                     'pbkdf2_sha256_310k', :password_hash, :password_salt,
                     'v60:test:dream-command-boundary', :source_hash, :batch_ref)
                ON CONFLICT (account_ref) DO NOTHING
                """
            ),
            {
                "account_ref": QA_ACCOUNT_REF,
                "email": QA_EMAIL,
                "password_hash": "0" * 64,
                "password_salt": "0" * 32,
                "source_hash": "1" * 64,
                "batch_ref": SEED_BATCH_REF,
            },
        )
    try:
        yield QA_ACCOUNT_REF
    finally:
        with engine.begin() as connection:
            encounter_refs = list(
                connection.execute(
                    text(
                        """
                        SELECT encounter_ref
                        FROM dream.encounters
                        WHERE viewer_account_ref = :account_ref
                        """
                    ),
                    {"account_ref": QA_ACCOUNT_REF},
                ).scalars()
            )
            if encounter_refs:
                connection.execute(
                    text(
                        """
                        DELETE FROM dream.command_receipts
                        WHERE viewer_account_ref = :account_ref
                        """
                    ),
                    {"account_ref": QA_ACCOUNT_REF},
                )
                connection.execute(
                    text(
                        """
                        DELETE FROM cognition.decision_records
                        WHERE subject_ref = ANY(:encounter_refs)
                        """
                    ),
                    {"encounter_refs": encounter_refs},
                )
                for table in ("reveals", "story_fruits", "answer_seals"):
                    connection.execute(
                        text(
                            f"""
                            DELETE FROM dream.{table}
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
                    WHERE account_ref = :account_ref
                    """
                ),
                {"account_ref": QA_ACCOUNT_REF},
            )
            connection.execute(
                text(
                    """
                    DELETE FROM identity.accounts
                    WHERE account_ref = :account_ref
                    """
                ),
                {"account_ref": QA_ACCOUNT_REF},
            )


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
            f"qa:{encounter['encounter_ref']}:{encounter['version']}:{command.value}:{identity}"
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


def _ensure_legacy_yanzhou_encounter(
    service: DreamService,
    *,
    account_ref: str,
) -> dict[str, object]:
    with patch.object(DreamGroveRepository, "active_candidates", return_value=[]):
        return service.ensure_encounter(account_ref=account_ref)


def test_single_command_boundary_is_versioned_and_semantically_idempotent(
    qa_account: str,
) -> None:
    service = DreamService(engine)
    snapshot = _ensure_legacy_yanzhou_encounter(service, account_ref=qa_account)
    serialized = canonical_json(snapshot)
    assert SEALED_FUTURE_OUTCOME["actual_event"] not in serialized
    assert RETURN_SEALED_FUTURE_OUTCOME["actual_event"] not in serialized
    assert snapshot["actor"]["projection_as_of_tick"] == 0
    assert snapshot["actor"]["state"] is None
    assert snapshot["actor"]["state_visibility"] == (
        "WITHHELD_OUTSIDE_EPISODE_HORIZON"
    )
    assert [
        event["world_event_ref"]
        for event in snapshot["actor"]["public_timeline"]["events"]
    ] == ["v60-world-event-yanzhou-channel-return-v1"]
    assert snapshot["tree"]["state"] == "DORMANT_QUESTION"
    assert snapshot["tree"]["projection_version"] == 1

    first_leaf = _command(
        snapshot,
        DreamCommand.OBSERVE_EVIDENCE,
        target_ref=str(_organ(snapshot, "evidence_leaf_world")["organ_ref"]),
    )
    after_first_leaf = service.execute_command(
        account_ref=qa_account,
        envelope=first_leaf,
    )
    assert after_first_leaf["encounter"]["version"] == 2

    replayed_first_leaf = service.execute_command(
        account_ref=qa_account,
        envelope=first_leaf,
    )
    assert replayed_first_leaf["encounter"]["version"] == 2

    with pytest.raises(DreamConflictError, match="dream_command_idempotency_conflict"):
        service.execute_command(
            account_ref=qa_account,
            envelope=first_leaf.model_copy(
                update={
                    "target_ref": _organ(
                        after_first_leaf,
                        "evidence_leaf_structure",
                    )["organ_ref"],
                }
            ),
        )

    with pytest.raises(DreamConflictError, match="dream_command_version_conflict"):
        service.execute_command(
            account_ref=qa_account,
            envelope=first_leaf.model_copy(
                update={"idempotency_key": "qa:fresh-stale-first-leaf"},
            ),
        )

    stale_second_leaf = first_leaf.model_copy(
        update={
            "target_ref": _organ(
                after_first_leaf,
                "evidence_leaf_structure",
            )["organ_ref"],
            "idempotency_key": "qa:stale-second-leaf",
        }
    )
    with pytest.raises(DreamConflictError, match="dream_command_version_conflict"):
        service.execute_command(
            account_ref=qa_account,
            envelope=stale_second_leaf,
        )

    for key, command in (
        ("evidence_leaf_structure", DreamCommand.OBSERVE_EVIDENCE),
        ("structure_branch", DreamCommand.OBSERVE_STRUCTURE),
        ("question_flower", DreamCommand.OPEN_QUESTION),
    ):
        snapshot = service.execute_command(
            account_ref=qa_account,
            envelope=_command(
                snapshot=after_first_leaf,
                command=command,
                target_ref=str(_organ(after_first_leaf, key)["organ_ref"]),
            ),
        )
        after_first_leaf = snapshot

    question = snapshot["question"]
    assert isinstance(question, dict)
    choice_id = str(question["options"][1]["choice_id"])
    seal = _command(
        snapshot,
        DreamCommand.SEAL_ANSWER,
        choice_id=choice_id,
    )
    snapshot = service.execute_command(account_ref=qa_account, envelope=seal)
    assert snapshot["encounter"]["status"] == "WAITING_FOR_WORLD"
    assert service.execute_command(
        account_ref=qa_account,
        envelope=seal,
    )["encounter"]["version"] == snapshot["encounter"]["version"]

    with engine.connect() as connection:
        event_ref = connection.execute(
            text(
                """
                SELECT world_event_ref
                FROM story.question_instances
                WHERE question_ref = :question_ref
                """
            ),
            {"question_ref": snapshot["lineage"]["question_ref"]},
        ).scalar_one()
    with engine.begin() as connection:
        WorldContinuityEngine().advance_and_settle(
            connection=connection,
            event_ref=str(event_ref),
        )
    assert service.synchronize_settled_world_events(event_refs=[event_ref]) == 1
    snapshot = service.snapshot(account_ref=qa_account)
    assert snapshot["encounter"]["status"] == "REVEAL_READY"
    assert snapshot["tree"]["state"] == "FIRST_FRUIT_MATURED"
    assert snapshot["tree"]["projection_version"] == 2
    assert SEALED_FUTURE_OUTCOME["actual_event"] not in canonical_json(snapshot)

    for command, expected_status in (
        (DreamCommand.REVEAL, "REVEALED"),
        (DreamCommand.RECONCILE, "COMPLETED"),
    ):
        envelope = _command(snapshot, command)
        snapshot = service.execute_command(
            account_ref=qa_account,
            envelope=envelope,
        )
        assert snapshot["encounter"]["status"] == expected_status
        replay = service.execute_command(
            account_ref=qa_account,
            envelope=envelope,
        )
        assert replay["encounter"]["version"] == snapshot["encounter"]["version"]

    assert SEALED_FUTURE_OUTCOME["actual_event"] in canonical_json(snapshot)
    assert RETURN_SEALED_FUTURE_OUTCOME["actual_event"] not in canonical_json(snapshot)
    revealed_evidence_refs = {
        item["evidence_ref"] for item in SEALED_FUTURE_OUTCOME["evidence"]
    }
    assert {
        item["evidence_ref"]
        for item in snapshot["public_evidence"]
        if item["epistemic_role"] == "OUTCOME_EVIDENCE"
    } == revealed_evidence_refs
    assert set(snapshot["projections"]["theater"]["evidence_refs"]) == (
        revealed_evidence_refs
    )
    assert set(snapshot["lineage"]["revealed_evidence_refs"]) == (
        revealed_evidence_refs
    )
    visible_event_refs = {
        event["world_event_ref"]
        for event in snapshot["actor"]["public_timeline"]["events"]
    }
    assert "v60-world-event-yanzhou-channel-return-v1" in visible_event_refs
    assert visible_event_refs <= {
        "v60-world-event-yanzhou-channel-return-v1",
        "v60-world-event-yanzhou-channel-outcome-v1",
    }

    continuation = _command(snapshot, DreamCommand.CONTINUE_ENCOUNTER)
    next_snapshot = service.execute_command(
        account_ref=qa_account,
        envelope=continuation,
    )
    assert next_snapshot["encounter"]["chapter"] == "RETURN_VISIT"
    assert next_snapshot["tree"]["state"] == "RETURN_BASELINE_COMMITTED"
    assert next_snapshot["tree"]["projection_version"] == 1
    assert RETURN_SEALED_FUTURE_OUTCOME["actual_event"] not in canonical_json(
        next_snapshot
    )
    replayed_continuation = service.execute_command(
        account_ref=qa_account,
        envelope=continuation,
    )
    assert (
        replayed_continuation["encounter"]["encounter_ref"]
        == next_snapshot["encounter"]["encounter_ref"]
    )
    with engine.connect() as connection:
        receipts = connection.execute(
            text(
                """
                SELECT command, envelope_hash, receipt_hash
                FROM dream.command_receipts
                WHERE viewer_account_ref = :account_ref
                ORDER BY created_at, command_receipt_ref
                """
            ),
            {"account_ref": qa_account},
        ).mappings().all()
    assert len(receipts) == 8
    assert all(len(row["envelope_hash"]) == 64 for row in receipts)
    assert all(len(row["receipt_hash"]) == 64 for row in receipts)


def test_concurrent_exact_command_replay_commits_once(qa_account: str) -> None:
    service = DreamService(engine)
    snapshot = _ensure_legacy_yanzhou_encounter(service, account_ref=qa_account)
    envelope = _command(
        snapshot,
        DreamCommand.OBSERVE_EVIDENCE,
        target_ref=str(_organ(snapshot, "evidence_leaf_world")["organ_ref"]),
    )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(
            executor.map(
                lambda _: service.execute_command(
                    account_ref=qa_account,
                    envelope=envelope,
                ),
                range(2),
            )
        )

    assert {result["encounter"]["version"] for result in results} == {2}
    with engine.connect() as connection:
        receipt_count = connection.execute(
            text(
                """
                SELECT count(*)
                FROM dream.command_receipts
                WHERE viewer_account_ref = :account_ref
                """
            ),
            {"account_ref": qa_account},
        ).scalar_one()
    assert receipt_count == 1


def test_concurrent_grove_selection_creates_one_current_encounter(
    qa_account: str,
) -> None:
    service = DreamService(engine)
    entry = service.entry(account_ref=qa_account)
    candidate_ref = entry["grove"]["candidates"][0]["candidate_ref"]

    with ThreadPoolExecutor(max_workers=2) as executor:
        snapshots = list(
            executor.map(
                lambda _: service.start_grove_encounter(
                    account_ref=qa_account,
                    candidate_ref=candidate_ref,
                ),
                range(2),
            )
        )

    encounter_refs = {
        snapshot["encounter"]["encounter_ref"] for snapshot in snapshots
    }
    assert len(encounter_refs) == 1
    with engine.connect() as connection:
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
                {"account_ref": qa_account},
            ).scalar_one()
            == 1
        )


def test_completed_encounter_returns_to_grove_and_starts_a_new_tree(
    qa_account: str,
) -> None:
    service = DreamService(engine)
    entry = service.entry(account_ref=qa_account)
    assert entry["kind"] == "GROVE"
    assert entry["grove"]["grove_version"] == "v60.dream-grove.004"
    assert entry["grove"]["return_echo"] is None
    candidates = entry["grove"]["candidates"]
    candidate_order = [
        candidate["candidate_ref"] for candidate in candidates
    ]
    first_candidate = candidates[0]
    next_candidate = candidates[1]
    snapshot = service.start_grove_encounter(
        account_ref=qa_account,
        candidate_ref=first_candidate["candidate_ref"],
    )
    first_encounter_ref = snapshot["encounter"]["encounter_ref"]
    first_question_ref = snapshot["lineage"]["question_ref"]
    legacy_state = {
        "observed_organs": [],
        "question_visible": True,
        "answer_sealed": True,
        "world_settled": True,
        "revealed": True,
        "reconciled": True,
        "departed_to_grove": False,
    }
    with engine.begin() as connection:
        legacy_source = (
            connection.execute(
                text(
                    """
                    SELECT question_ref, actor_ref, tree_ref
                    FROM dream.grove_candidates
                    WHERE candidate_ref = :candidate_ref
                    """
                ),
                {"candidate_ref": candidates[2]["candidate_ref"]},
            )
            .mappings()
            .one()
        )
        connection.execute(
            text(
                """
                INSERT INTO dream.encounters
                    (encounter_ref, viewer_account_ref, actor_ref, tree_ref,
                     question_ref, status, version, correlation_id,
                     causation_id, state_json, state_hash, updated_at)
                VALUES
                    (:encounter_ref, :account_ref, :actor_ref, :tree_ref,
                     :question_ref, 'COMPLETED', 1, :correlation_id,
                     :causation_id, CAST(:state_json AS jsonb), :state_hash,
                     now() - interval '7 days')
                """
            ),
            {
                "encounter_ref": "v60-encounter-legacy-completed-history",
                "account_ref": qa_account,
                "actor_ref": legacy_source["actor_ref"],
                "tree_ref": legacy_source["tree_ref"],
                "question_ref": legacy_source["question_ref"],
                "correlation_id": "v60-correlation-legacy-completed-history",
                "causation_id": "v60-causation-legacy-completed-history",
                "state_json": canonical_json(legacy_state),
                "state_hash": content_hash(legacy_state),
            },
        )

    for key, command in (
        ("evidence_leaf_world", DreamCommand.OBSERVE_EVIDENCE),
        ("evidence_leaf_structure", DreamCommand.OBSERVE_EVIDENCE),
        ("structure_branch", DreamCommand.OBSERVE_STRUCTURE),
        ("question_flower", DreamCommand.OPEN_QUESTION),
    ):
        snapshot = service.execute_command(
            account_ref=qa_account,
            envelope=_command(
                snapshot,
                command,
                target_ref=str(_organ(snapshot, key)["organ_ref"]),
            ),
        )
    snapshot = service.execute_command(
        account_ref=qa_account,
        envelope=_command(
            snapshot,
            DreamCommand.SEAL_ANSWER,
            choice_id=str(snapshot["question"]["options"][0]["choice_id"]),
        ),
    )
    with engine.connect() as connection:
        event_ref = connection.execute(
            text(
                """
                SELECT world_event_ref
                FROM story.question_instances
                WHERE question_ref = :question_ref
                """
            ),
            {"question_ref": first_question_ref},
        ).scalar_one()
    with engine.begin() as connection:
        WorldContinuityEngine().advance_and_settle(
            connection=connection,
            event_ref=str(event_ref),
        )
    assert service.synchronize_settled_world_events(event_refs=[event_ref]) == 1
    snapshot = service.snapshot(account_ref=qa_account)
    for command in (DreamCommand.REVEAL, DreamCommand.RECONCILE):
        snapshot = service.execute_command(
            account_ref=qa_account,
            envelope=_command(snapshot, command),
        )
    assert "RETURN_TO_GROVE" in snapshot["game"]["available_commands"]

    return_command = _command(snapshot, DreamCommand.RETURN_TO_GROVE)
    grove_entry = service.execute_command(
        account_ref=qa_account,
        envelope=return_command,
    )
    assert grove_entry["kind"] == "GROVE"
    assert [
        candidate["candidate_ref"]
        for candidate in grove_entry["grove"]["candidates"]
    ] == candidate_order
    echo = grove_entry["grove"]["return_echo"]
    assert echo["contract_version"] == "v60.dream-return-echo.001"
    assert echo["encounter_ref"] == first_encounter_ref
    assert echo["public_alias"] == first_candidate["public_alias"]
    assert echo["episode_title"]
    assert echo["judgment"]["choice_label"]
    assert echo["judgment"]["summary"]
    assert echo["world_response"]["summary"]
    assert echo["world_response"]["evidence_summaries"]
    assert echo["still_to_observe"]["summary"]
    assert set(echo["abu_recap"]) == {
        "meaning",
        "boundary",
        "next_attention",
    }
    assert echo["semantics"] == "DREAM_LIFE_RETURN_ECHO_ONLY"
    assert echo["owner_mingli_evidence_allowed"] is False
    assert echo["dream_outcome_admitted_as_owner_evidence"] is False
    assert echo["tree_candidate_set_or_order_changed"] is False
    assert echo["mingli_write_allowed"] is False
    assert echo["decision_write_allowed"] is False
    assert echo["knowledge_write_allowed"] is False
    assert echo["canonical_write_allowed"] is False
    assert echo["read_only"] is True
    echo_json = canonical_json(echo)
    for forbidden in (
        "decision_ref",
        "chart_version_ref",
        "mingli_reading",
        "knowledge_profile",
        "probability",
    ):
        assert forbidden not in echo_json

    with engine.connect() as connection:
        decision_count_before_reads = connection.execute(
            text(
                """
                SELECT count(*)
                FROM cognition.decision_records
                WHERE subject_ref = :encounter_ref
                """
            ),
            {"encounter_ref": first_encounter_ref},
        ).scalar_one()
        source_rows = connection.execute(
            text(
                """
                SELECT seal.answer_seal_ref, seal.seal_hash,
                       reveal.reveal_ref, reveal.reveal_hash,
                       reveal.world_event_ref,
                       event.actor_ref AS event_actor_ref
                FROM dream.answer_seals AS seal
                JOIN dream.reveals AS reveal
                  ON reveal.encounter_ref = seal.encounter_ref
                JOIN world.events AS event
                  ON event.world_event_ref = reveal.world_event_ref
                WHERE seal.encounter_ref = :encounter_ref
                  AND seal.actor_role = 'HUMAN'
                """
            ),
            {"encounter_ref": first_encounter_ref},
        ).mappings().one()
        evidence_rows = connection.execute(
            text(
                """
                SELECT evidence_ref, evidence_hash,
                       evidence_json ->> 'summary' AS summary
                FROM world.event_evidence
                WHERE world_event_ref = :world_event_ref
                ORDER BY evidence_ref
                """
            ),
            {"world_event_ref": source_rows["world_event_ref"]},
        ).mappings().all()
        alternate_actor_ref = connection.execute(
            text(
                """
                SELECT actor_ref
                FROM world.actors
                WHERE actor_ref <> :actor_ref
                ORDER BY actor_ref
                LIMIT 1
                """
            ),
            {"actor_ref": source_rows["event_actor_ref"]},
        ).scalar_one()
    assert echo["lineage"]["answer_seal_ref"] == source_rows[
        "answer_seal_ref"
    ]
    assert echo["lineage"]["answer_seal_hash"] == source_rows["seal_hash"]
    assert echo["lineage"]["reveal_ref"] == source_rows["reveal_ref"]
    assert echo["lineage"]["reveal_hash"] == source_rows["reveal_hash"]
    assert echo["lineage"]["committed_evidence_refs"] == [
        row["evidence_ref"] for row in evidence_rows
    ]
    assert echo["lineage"]["committed_evidence_hashes"] == [
        row["evidence_hash"] for row in evidence_rows
    ]
    assert echo["world_response"]["evidence_summaries"] == [
        row["summary"] for row in evidence_rows
    ]

    replayed_grove = service.execute_command(
        account_ref=qa_account,
        envelope=return_command,
    )
    refreshed_grove = service.entry(account_ref=qa_account)
    restarted_grove = DreamService(engine).entry(account_ref=qa_account)
    assert replayed_grove["grove"]["return_echo"] == echo
    assert refreshed_grove["grove"]["return_echo"] == echo
    assert restarted_grove["grove"]["return_echo"] == echo
    other_account_entry = DreamService(engine).entry(
        account_ref="v60-account-return-echo-isolation-check"
    )
    assert other_account_entry["kind"] == "GROVE"
    assert other_account_entry["grove"]["return_echo"] is None
    with engine.connect() as connection:
        assert (
            connection.execute(
                text(
                    """
                    SELECT count(*)
                    FROM cognition.decision_records
                    WHERE subject_ref = :encounter_ref
                    """
                ),
                {"encounter_ref": first_encounter_ref},
            ).scalar_one()
            == decision_count_before_reads
        )
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE dream.reveals
                    SET reveal_hash = :invalid_hash
                    WHERE reveal_ref = :reveal_ref
                    """
                ),
                {
                    "invalid_hash": "0" * 64,
                    "reveal_ref": source_rows["reveal_ref"],
                },
            )
        with pytest.raises(
            DreamStateError,
            match="dream_return_echo_reveal_invalid",
        ):
            DreamService(engine).entry(account_ref=qa_account)
    finally:
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE dream.reveals
                    SET reveal_hash = :reveal_hash
                    WHERE reveal_ref = :reveal_ref
                    """
                ),
                {
                    "reveal_hash": source_rows["reveal_hash"],
                    "reveal_ref": source_rows["reveal_ref"],
                },
            )
    assert DreamService(engine).entry(account_ref=qa_account)[
        "grove"
    ]["return_echo"] == echo
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE world.events
                    SET actor_ref = :actor_ref
                    WHERE world_event_ref = :world_event_ref
                    """
                ),
                {
                    "actor_ref": alternate_actor_ref,
                    "world_event_ref": source_rows["world_event_ref"],
                },
            )
        with pytest.raises(
            DreamStateError,
            match="dream_return_echo_world_event_admission_invalid",
        ):
            DreamService(engine).entry(account_ref=qa_account)
    finally:
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE world.events
                    SET actor_ref = :actor_ref
                    WHERE world_event_ref = :world_event_ref
                    """
                ),
                {
                    "actor_ref": source_rows["event_actor_ref"],
                    "world_event_ref": source_rows["world_event_ref"],
                },
            )
    assert DreamService(engine).entry(account_ref=qa_account)[
        "grove"
    ]["return_echo"] == echo

    next_snapshot = service.start_grove_encounter(
        account_ref=qa_account,
        candidate_ref=next_candidate["candidate_ref"],
    )
    assert next_snapshot["encounter"]["encounter_ref"] != first_encounter_ref
    assert next_snapshot["lineage"]["question_ref"] != first_question_ref
    with engine.connect() as connection:
        archived = connection.execute(
            text(
                """
                SELECT status, state_json
                FROM dream.encounters
                WHERE encounter_ref = :encounter_ref
                """
            ),
            {"encounter_ref": first_encounter_ref},
        ).mappings().one()
    assert archived["status"] == "COMPLETED"
    assert archived["state_json"]["departed_to_grove"] is True
