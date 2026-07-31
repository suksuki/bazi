from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from sqlalchemy import text

from abu_v60.game import DreamEpisodeContract
from abu_v60.provenance import content_hash
from abu_v60.story.admission import (
    EpisodeAdmissionError,
    validate_persisted_episode_admission,
)


def persisted_seed_episode_bindings(
    connection: Any,
    *,
    sources: Sequence[Any],
    bindings: Mapping[str, str],
) -> dict[str, str]:
    """Recover immutable source bindings only from fully verified seed receipts."""

    proposed = dict(bindings)
    persisted_sources: list[tuple[Any, tuple[str, ...]]] = []
    overrides: dict[str, str] = {}
    for source in sources:
        question_ref = source.definition.runtime.question_ref
        row = _persisted_seed_episode_row(
            connection,
            question_ref=question_ref,
        )
        if row is None:
            continue
        _validate_persisted_seed_episode(row)
        current_refs = tuple(
            source.definition.organ_set["evidence_leaf_structure"].source_refs
        )
        persisted_refs = tuple(
            str(item)
            for item in row["organ_set_json"]["evidence_leaf_structure"][
                "source_refs"
            ]
        )
        if len(current_refs) != len(persisted_refs):
            raise EpisodeAdmissionError(
                "episode_seed_replay_structure_shape_mismatch"
            )
        persisted_sources.append((source, persisted_refs))
        for current_ref, persisted_ref in zip(
            current_refs,
            persisted_refs,
            strict=True,
        ):
            if current_ref == persisted_ref:
                continue
            matching_keys = [
                key for key, value in proposed.items() if value == current_ref
            ]
            if len(matching_keys) != 1:
                raise EpisodeAdmissionError(
                    "episode_seed_replay_unbound_structure_drift"
                )
            key = matching_keys[0]
            previous = overrides.get(key)
            if previous is not None and previous != persisted_ref:
                raise EpisodeAdmissionError(
                    "episode_seed_replay_binding_conflict"
                )
            overrides[key] = persisted_ref

    replay = {**proposed, **overrides}
    replacement_by_ref = {
        proposed[key]: persisted_ref
        for key, persisted_ref in overrides.items()
    }
    for source, persisted_refs in persisted_sources:
        current_refs = tuple(
            source.definition.organ_set["evidence_leaf_structure"].source_refs
        )
        replayed_refs = tuple(
            replacement_by_ref.get(source_ref, source_ref)
            for source_ref in current_refs
        )
        if replayed_refs != persisted_refs:
            raise EpisodeAdmissionError("episode_seed_replay_binding_conflict")
    return replay


def _persisted_seed_episode_row(
    connection: Any,
    *,
    question_ref: str,
) -> dict[str, Any] | None:
    row = (
        connection.execute(
            text(
                """
                SELECT question.question_ref, question.actor_ref,
                       question.life_case_revision_ref,
                       question.world_event_ref, question.question_version,
                       question.prompt, question.options_json,
                       question.evidence_refs_json, question.cutoff_tick,
                       question.due_tick, question.resolution_rule_json,
                       question.question_hash, question.organ_set_json,
                       question.organ_set_hash, question.episode_ref,
                       question.episode_version,
                       question.episode_contract_json,
                       question.episode_contract_hash,
                       question.admission_manifest_json,
                       question.admission_manifest_hash,
                       life_case.revision_hash AS life_case_revision_hash,
                       event.outcome_hash
                FROM story.question_instances AS question
                JOIN mingli.life_case_revisions AS life_case
                  ON life_case.life_case_revision_ref =
                     question.life_case_revision_ref
                JOIN world.events AS event
                  ON event.world_event_ref = question.world_event_ref
                WHERE question.question_ref = :question_ref
                """
            ),
            {"question_ref": question_ref},
        )
        .mappings()
        .one_or_none()
    )
    return dict(row) if row is not None else None


def _validate_persisted_seed_episode(row: dict[str, Any]) -> None:
    try:
        episode = DreamEpisodeContract.model_validate(
            row["episode_contract_json"]
        )
    except ValueError as exc:
        raise EpisodeAdmissionError(str(exc)) from exc
    if content_hash(episode.model_dump(mode="json")) != row[
        "episode_contract_hash"
    ]:
        raise EpisodeAdmissionError(
            "episode_seed_replay_contract_hash_mismatch"
        )
    exact_columns = {
        "question_ref": row["question_ref"],
        "episode_ref": row["episode_ref"],
        "episode_version": row["episode_version"],
        "actor_ref": row["actor_ref"],
        "world_event_ref": row["world_event_ref"],
        "cutoff_tick": row["cutoff_tick"],
        "due_tick": row["due_tick"],
    }
    if any(
        getattr(episode, field_name) != value
        for field_name, value in exact_columns.items()
    ):
        raise EpisodeAdmissionError(
            "episode_seed_replay_contract_column_mismatch"
        )
    question_payload = {
        "question_ref": row["question_ref"],
        "actor_ref": row["actor_ref"],
        "life_case_revision_ref": row["life_case_revision_ref"],
        "world_event_ref": row["world_event_ref"],
        "question_version": row["question_version"],
        "prompt": row["prompt"],
        "options": tuple(row["options_json"]),
        "evidence_refs": tuple(row["evidence_refs_json"]),
        "cutoff_tick": row["cutoff_tick"],
        "due_tick": row["due_tick"],
    }
    if (
        content_hash(
            {
                **question_payload,
                "resolution_rule": row["resolution_rule_json"],
            }
        )
        != row["question_hash"]
    ):
        raise EpisodeAdmissionError(
            "episode_seed_replay_question_hash_mismatch"
        )
    if content_hash(row["organ_set_json"]) != row["organ_set_hash"]:
        raise EpisodeAdmissionError(
            "episode_seed_replay_organ_hash_mismatch"
        )
    if content_hash(row["resolution_rule_json"]) != episode.resolution_rule_hash:
        raise EpisodeAdmissionError(
            "episode_seed_replay_resolution_rule_hash_mismatch"
        )
    validate_persisted_episode_admission(
        manifest_payload=row["admission_manifest_json"],
        manifest_hash=row["admission_manifest_hash"],
        episode=episode,
        persisted=row,
    )
