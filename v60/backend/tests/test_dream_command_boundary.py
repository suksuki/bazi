from __future__ import annotations

from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest
from abu_v60.db import engine
from abu_v60.dream.errors import DreamConflictError
from abu_v60.dream.first_slice import SEALED_FUTURE_OUTCOME
from abu_v60.dream.grove import DreamGroveRepository
from abu_v60.dream.return_slice import RETURN_SEALED_FUTURE_OUTCOME
from abu_v60.dream.seed import SEED_BATCH_REF
from abu_v60.dream.service import DreamService
from abu_v60.game import DreamCommand, DreamCommandEnvelope
from abu_v60.provenance import canonical_json
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


def test_completed_encounter_returns_to_grove_and_starts_a_new_tree(
    qa_account: str,
) -> None:
    service = DreamService(engine)
    entry = service.entry(account_ref=qa_account)
    assert entry["kind"] == "GROVE"
    candidates = entry["grove"]["candidates"]
    first_candidate = candidates[0]
    next_candidate = candidates[1]
    snapshot = service.start_grove_encounter(
        account_ref=qa_account,
        candidate_ref=first_candidate["candidate_ref"],
    )
    first_encounter_ref = snapshot["encounter"]["encounter_ref"]
    first_question_ref = snapshot["lineage"]["question_ref"]

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
    assert service.execute_command(
        account_ref=qa_account,
        envelope=return_command,
    )["kind"] == "GROVE"
    assert service.entry(account_ref=qa_account)["kind"] == "GROVE"

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
