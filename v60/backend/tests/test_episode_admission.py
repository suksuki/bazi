from __future__ import annotations

import pytest
from abu_v60.db.engine import engine
from abu_v60.dream.first_slice import first_episode_definition
from abu_v60.game import DreamEpisodeDefinition
from abu_v60.provenance import content_hash
from abu_v60.story import (
    EpisodeAdmissionCompiler,
    EpisodeAdmissionError,
    EpisodeAuthoritySnapshot,
    StoryEpisodeAdmissionService,
    StoryEpisodeTransitionAdmissionService,
    episode_transition,
)
from sqlalchemy import text


def _authority(definition: DreamEpisodeDefinition) -> EpisodeAuthoritySnapshot:
    return EpisodeAuthoritySnapshot(
        life_case_revision_ref="v60-life-case-revision-test",
        life_case_revision_hash="a" * 64,
        world_event_ref=definition.runtime.world_event_ref,
        outcome_hash=content_hash(definition.sealed_outcome.model_dump(mode="json")),
    )


def test_episode_admission_is_deterministic_and_binds_all_persisted_hashes() -> None:
    definition = first_episode_definition("v60-fact-structure-test")
    compiler = EpisodeAdmissionCompiler()

    first = compiler.compile(definition=definition, authority=_authority(definition))
    replay = compiler.compile(definition=definition, authority=_authority(definition))

    assert first == replay
    assert first.admission_manifest.question_hash == first.question_hash
    assert first.admission_manifest.organ_set_hash == first.organ_set_hash
    assert first.admission_manifest.episode_contract_hash == first.episode_contract_hash
    assert first.admission_manifest.resolution_rule_hash == (
        definition.runtime.resolution_rule_hash
    )
    assert first.admission_manifest_hash == content_hash(
        first.admission_manifest.model_dump(mode="json")
    )


def test_episode_admission_rejects_outcome_authority_drift() -> None:
    definition = first_episode_definition("v60-fact-structure-test")
    authority = _authority(definition).model_copy(update={"outcome_hash": "0" * 64})

    with pytest.raises(EpisodeAdmissionError, match="outcome_hash_mismatch"):
        EpisodeAdmissionCompiler().compile(
            definition=definition,
            authority=authority,
        )


def test_episode_admission_rejects_world_leaf_outside_baseline() -> None:
    payload = first_episode_definition("v60-fact-structure-test").model_dump(mode="json")
    payload["organ_set"]["evidence_leaf_world"]["source_refs"] = ["v60-evidence-not-in-baseline"]
    payload["organ_set"]["structure_branch"]["source_refs"] = [
        "v60-evidence-not-in-baseline",
        "v60-fact-structure-test",
    ]
    definition = DreamEpisodeDefinition.model_validate(payload)

    with pytest.raises(EpisodeAdmissionError, match="world_leaf_not_in_baseline"):
        EpisodeAdmissionCompiler().compile(
            definition=definition,
            authority=_authority(definition),
        )


def test_story_admission_is_idempotent_and_rejects_changed_content() -> None:
    with engine.begin() as connection:
        row = (
            connection.execute(
                text(
                    """
                SELECT question.life_case_revision_ref,
                       question.evidence_refs_json
                FROM story.question_instances AS question
                WHERE question.question_ref =
                    'v60-question-yanzhou-old-channel-v1'
                """
                )
            )
            .mappings()
            .one()
        )
        definition = first_episode_definition(row["evidence_refs_json"][-1])
        service = StoryEpisodeAdmissionService()

        admission = service.admit(
            connection,
            life_case_revision_ref=row["life_case_revision_ref"],
            definition=definition,
        )
        assert admission.question_ref == definition.runtime.question_ref

        changed = DreamEpisodeDefinition.model_validate(
            {
                **definition.model_dump(mode="json"),
                "prompt": f"{definition.prompt}（内容漂移）",
            }
        )
        with pytest.raises(EpisodeAdmissionError, match="admission_conflict"):
            service.admit(
                connection,
                life_case_revision_ref=row["life_case_revision_ref"],
                definition=changed,
            )


def test_episode_transition_admission_is_append_only_and_idempotent() -> None:
    service = StoryEpisodeTransitionAdmissionService()
    transition = episode_transition(
        from_question_ref="v60-question-yanzhou-old-channel-v1",
        to_question_ref="v60-question-yanzhou-wet-bank-v1",
        label="过一段时间，再回到这棵树",
    )
    with engine.begin() as connection:
        first_hash = service.admit(connection, definition=transition)
        replay_hash = service.admit(connection, definition=transition)
        count = connection.execute(
            text(
                """
                SELECT count(*)
                FROM story.episode_transitions
                WHERE transition_ref = :transition_ref
                """
            ),
            {"transition_ref": transition.transition_ref},
        ).scalar_one()

        assert first_hash == replay_hash
        assert count == 1

        with pytest.raises(EpisodeAdmissionError, match="transition_admission_conflict"):
            service.admit(
                connection,
                definition=transition.model_copy(
                    update={"label": "试图改写已经入库的章节连接"}
                ),
            )
