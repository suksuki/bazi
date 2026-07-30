from __future__ import annotations

import re
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor

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
from abu_v60.dream.grove import GroveCandidateDefinition
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
    assert first_grove["grove"]["grove_version"] == "v60.dream-grove.003"

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
