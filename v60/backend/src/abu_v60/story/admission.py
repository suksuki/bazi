from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import text

from abu_v60.game import (
    DreamEpisodeContract,
    DreamEpisodeDefinition,
    resolution_rule_for_persistence,
    runtime_metadata_from_resolution_rule,
)
from abu_v60.provenance import canonical_json, content_hash
from abu_v60.story.contracts import EpisodeTransitionContract


class EpisodeAdmissionError(ValueError):
    pass


class EpisodeAuthoritySnapshot(BaseModel):
    """Hashes and identities resolved from canonical owners at admission time."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    life_case_revision_ref: str = Field(min_length=1)
    life_case_revision_hash: str = Field(min_length=64, max_length=64)
    world_event_ref: str = Field(min_length=1)
    outcome_hash: str = Field(min_length=64, max_length=64)


class EpisodeAdmissionManifest(BaseModel):
    """Immutable receipt binding one playable Episode to canonical sources."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    admission_version: Literal["v60.episode-admission.001"]
    question_ref: str = Field(min_length=1)
    episode_ref: str = Field(min_length=1)
    episode_version: int = Field(ge=1)
    actor_ref: str = Field(min_length=1)
    tree_ref: str = Field(min_length=1)
    life_case_revision_ref: str = Field(min_length=1)
    life_case_revision_hash: str = Field(min_length=64, max_length=64)
    world_event_ref: str = Field(min_length=1)
    outcome_hash: str = Field(min_length=64, max_length=64)
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    question_hash: str = Field(min_length=64, max_length=64)
    organ_set_hash: str = Field(min_length=64, max_length=64)
    resolution_rule_hash: str = Field(min_length=64, max_length=64)
    episode_contract_hash: str = Field(min_length=64, max_length=64)


def validate_persisted_episode_admission(
    *,
    manifest_payload: dict[str, Any],
    manifest_hash: str,
    episode: DreamEpisodeContract,
    persisted: dict[str, Any],
) -> EpisodeAdmissionManifest:
    try:
        manifest = EpisodeAdmissionManifest.model_validate(manifest_payload)
    except ValueError as exc:
        raise EpisodeAdmissionError(str(exc)) from exc
    if content_hash(manifest.model_dump(mode="json")) != manifest_hash:
        raise EpisodeAdmissionError("episode_admission_manifest_hash_mismatch")
    expected = {
        "question_ref": persisted["question_ref"],
        "episode_ref": episode.episode_ref,
        "episode_version": episode.episode_version,
        "actor_ref": episode.actor_ref,
        "tree_ref": episode.tree_ref,
        "life_case_revision_ref": persisted["life_case_revision_ref"],
        "life_case_revision_hash": persisted["life_case_revision_hash"],
        "world_event_ref": episode.world_event_ref,
        "outcome_hash": persisted["outcome_hash"],
        "evidence_refs": tuple(persisted["evidence_refs_json"]),
        "question_hash": persisted["question_hash"],
        "organ_set_hash": persisted["organ_set_hash"],
        "resolution_rule_hash": episode.resolution_rule_hash,
        "episode_contract_hash": persisted["episode_contract_hash"],
    }
    for field_name, expected_value in expected.items():
        if getattr(manifest, field_name) != expected_value:
            raise EpisodeAdmissionError(f"episode_admission_{field_name}_binding_mismatch")
    return manifest


class CompiledEpisodeAdmission(BaseModel):
    """Canonical row payload produced by the only Episode admission compiler."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    question_ref: str
    actor_ref: str
    life_case_revision_ref: str
    world_event_ref: str
    question_version: int
    prompt: str
    options: tuple[dict[str, Any], ...]
    evidence_refs: tuple[str, ...]
    cutoff_tick: int
    due_tick: int
    resolution_rule: dict[str, Any]
    question_hash: str = Field(min_length=64, max_length=64)
    organ_set: dict[str, dict[str, Any]]
    organ_set_hash: str = Field(min_length=64, max_length=64)
    episode_ref: str
    episode_version: int
    episode_contract: dict[str, Any]
    episode_contract_hash: str = Field(min_length=64, max_length=64)
    admission_manifest: EpisodeAdmissionManifest
    admission_manifest_hash: str = Field(min_length=64, max_length=64)

    @model_validator(mode="after")
    def validate_hashes(self) -> CompiledEpisodeAdmission:
        if content_hash(self.organ_set) != self.organ_set_hash:
            raise ValueError("episode_admission_organ_hash_mismatch")
        if content_hash(self.episode_contract) != self.episode_contract_hash:
            raise ValueError("episode_admission_contract_hash_mismatch")
        if content_hash(self.admission_manifest.model_dump(mode="json")) != (
            self.admission_manifest_hash
        ):
            raise ValueError("episode_admission_manifest_hash_mismatch")
        if self.admission_manifest.question_hash != self.question_hash:
            raise ValueError("episode_admission_question_hash_mismatch")
        return self

    def sql_parameters(self) -> dict[str, Any]:
        return {
            "question_ref": self.question_ref,
            "actor_ref": self.actor_ref,
            "life_case_ref": self.life_case_revision_ref,
            "event_ref": self.world_event_ref,
            "question_version": self.question_version,
            "prompt": self.prompt,
            "options": canonical_json(self.options),
            "evidence_refs": canonical_json(self.evidence_refs),
            "cutoff_tick": self.cutoff_tick,
            "due_tick": self.due_tick,
            "resolution_rule": canonical_json(self.resolution_rule),
            "question_hash": self.question_hash,
            "organ_set": canonical_json(self.organ_set),
            "organ_set_hash": self.organ_set_hash,
            "episode_ref": self.episode_ref,
            "episode_version": self.episode_version,
            "episode_contract": canonical_json(self.episode_contract),
            "episode_contract_hash": self.episode_contract_hash,
            "admission_manifest": canonical_json(self.admission_manifest.model_dump(mode="json")),
            "admission_manifest_hash": self.admission_manifest_hash,
        }


class EpisodeAdmissionCompiler:
    """Compile one validated authoring package into its immutable persisted form."""

    def compile(
        self,
        *,
        definition: DreamEpisodeDefinition,
        authority: EpisodeAuthoritySnapshot,
    ) -> CompiledEpisodeAdmission:
        definition = DreamEpisodeDefinition.model_validate(definition.model_dump(mode="json"))
        episode = definition.runtime
        if episode.world_event_ref != authority.world_event_ref:
            raise EpisodeAdmissionError("episode_admission_world_event_mismatch")
        if content_hash(definition.sealed_outcome.model_dump(mode="json")) != (
            authority.outcome_hash
        ):
            raise EpisodeAdmissionError("episode_admission_outcome_hash_mismatch")

        authored_resolution_rule = definition.resolution_rule.model_dump(mode="json")
        resolution_rule = resolution_rule_for_persistence(definition.resolution_rule)
        resolution_rule_hash = content_hash(resolution_rule)
        if resolution_rule_hash != episode.resolution_rule_hash:
            raise EpisodeAdmissionError("episode_admission_resolution_rule_hash_mismatch")
        if runtime_metadata_from_resolution_rule(authored_resolution_rule) != (
            episode.runtime_metadata
        ):
            raise EpisodeAdmissionError("episode_admission_runtime_metadata_mismatch")

        baseline_refs = tuple(
            str(item["evidence_ref"])
            for item in definition.baseline_evidence
            if item.get("evidence_ref")
        )
        leaf_world_refs = definition.organ_set["evidence_leaf_world"].source_refs
        if not set(leaf_world_refs).issubset(baseline_refs):
            raise EpisodeAdmissionError("episode_admission_world_leaf_not_in_baseline")
        evidence_refs = tuple(
            dict.fromkeys(
                (
                    *baseline_refs,
                    *definition.organ_set["evidence_leaf_structure"].source_refs,
                )
            )
        )
        options = tuple(option.model_dump(mode="json") for option in definition.options)
        organ_set = {
            key: organ.model_dump(mode="json") for key, organ in definition.organ_set.items()
        }
        episode_contract = episode.model_dump(mode="json")
        question_payload = {
            "question_ref": episode.question_ref,
            "actor_ref": episode.actor_ref,
            "life_case_revision_ref": authority.life_case_revision_ref,
            "world_event_ref": episode.world_event_ref,
            "question_version": definition.question_version,
            "prompt": definition.prompt,
            "options": options,
            "evidence_refs": evidence_refs,
            "cutoff_tick": episode.cutoff_tick,
            "due_tick": episode.due_tick,
        }
        question_hash = content_hash({**question_payload, "resolution_rule": resolution_rule})
        organ_set_hash = content_hash(organ_set)
        episode_contract_hash = content_hash(episode_contract)
        manifest = EpisodeAdmissionManifest(
            admission_version="v60.episode-admission.001",
            question_ref=episode.question_ref,
            episode_ref=episode.episode_ref,
            episode_version=episode.episode_version,
            actor_ref=episode.actor_ref,
            tree_ref=episode.tree_ref,
            life_case_revision_ref=authority.life_case_revision_ref,
            life_case_revision_hash=authority.life_case_revision_hash,
            world_event_ref=episode.world_event_ref,
            outcome_hash=authority.outcome_hash,
            evidence_refs=evidence_refs,
            question_hash=question_hash,
            organ_set_hash=organ_set_hash,
            resolution_rule_hash=resolution_rule_hash,
            episode_contract_hash=episode_contract_hash,
        )
        manifest_payload = manifest.model_dump(mode="json")
        return CompiledEpisodeAdmission(
            **question_payload,
            resolution_rule=resolution_rule,
            question_hash=question_hash,
            organ_set=organ_set,
            organ_set_hash=organ_set_hash,
            episode_ref=episode.episode_ref,
            episode_version=episode.episode_version,
            episode_contract=episode_contract,
            episode_contract_hash=episode_contract_hash,
            admission_manifest=manifest,
            admission_manifest_hash=content_hash(manifest_payload),
        )


class StoryEpisodeAdmissionService:
    """The Story schema's single idempotent Episode admission write path."""

    def __init__(self, compiler: EpisodeAdmissionCompiler | None = None) -> None:
        self._compiler = compiler or EpisodeAdmissionCompiler()

    def admit(
        self,
        connection: Any,
        *,
        life_case_revision_ref: str,
        definition: DreamEpisodeDefinition,
    ) -> CompiledEpisodeAdmission:
        authority = self._authority_snapshot(
            connection,
            life_case_revision_ref=life_case_revision_ref,
            definition=definition,
        )
        admission = self._compiler.compile(
            definition=definition,
            authority=authority,
        )
        connection.execute(
            text(
                """
                INSERT INTO story.question_instances
                    (question_ref, actor_ref, life_case_revision_ref, world_event_ref,
                     question_version, prompt, options_json, evidence_refs_json,
                     cutoff_tick, due_tick, resolution_rule_json, question_hash,
                     organ_set_json, organ_set_hash, episode_ref, episode_version,
                     episode_contract_json, episode_contract_hash,
                     admission_manifest_json, admission_manifest_hash)
                VALUES
                    (:question_ref, :actor_ref, :life_case_ref, :event_ref,
                     :question_version, :prompt, CAST(:options AS jsonb),
                     CAST(:evidence_refs AS jsonb), :cutoff_tick, :due_tick,
                     CAST(:resolution_rule AS jsonb), :question_hash,
                     CAST(:organ_set AS jsonb), :organ_set_hash, :episode_ref,
                     :episode_version, CAST(:episode_contract AS jsonb),
                     :episode_contract_hash, CAST(:admission_manifest AS jsonb),
                     :admission_manifest_hash)
                ON CONFLICT (question_ref) DO NOTHING
                """
            ),
            admission.sql_parameters(),
        )
        persisted = (
            connection.execute(
                text(
                    """
                SELECT question_hash, organ_set_hash, episode_contract_hash,
                       admission_manifest_hash
                FROM story.question_instances
                WHERE question_ref = :question_ref
                """
                ),
                {"question_ref": admission.question_ref},
            )
            .mappings()
            .one()
        )
        expected = {
            "question_hash": admission.question_hash,
            "organ_set_hash": admission.organ_set_hash,
            "episode_contract_hash": admission.episode_contract_hash,
            "admission_manifest_hash": admission.admission_manifest_hash,
        }
        if dict(persisted) != expected:
            raise EpisodeAdmissionError("episode_admission_conflict")
        return admission

    def _authority_snapshot(
        self,
        connection: Any,
        *,
        life_case_revision_ref: str,
        definition: DreamEpisodeDefinition,
    ) -> EpisodeAuthoritySnapshot:
        episode = definition.runtime
        row = (
            connection.execute(
                text(
                    """
                SELECT actor.case_ref AS actor_case_ref,
                       tree.actor_ref AS tree_actor_ref,
                       life_case.case_ref AS life_case_case_ref,
                       life_case.chart_version_ref,
                       life_case.revision_hash,
                       event.actor_ref AS event_actor_ref,
                       event.event_type,
                       event.due_tick,
                       event.event_json,
                       event.sealed_outcome_json,
                       event.outcome_hash
                FROM world.actors AS actor
                JOIN dream.life_trees AS tree
                  ON tree.tree_ref = :tree_ref
                JOIN mingli.life_case_revisions AS life_case
                  ON life_case.life_case_revision_ref = :life_case_ref
                JOIN world.events AS event
                  ON event.world_event_ref = :event_ref
                WHERE actor.actor_ref = :actor_ref
                """
                ),
                {
                    "actor_ref": episode.actor_ref,
                    "tree_ref": episode.tree_ref,
                    "life_case_ref": life_case_revision_ref,
                    "event_ref": episode.world_event_ref,
                },
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise EpisodeAdmissionError("episode_admission_authority_missing")
        if not (
            row["actor_case_ref"] == row["life_case_case_ref"]
            and row["tree_actor_ref"] == episode.actor_ref
            and row["event_actor_ref"] == episode.actor_ref
        ):
            raise EpisodeAdmissionError("episode_admission_authority_lineage_mismatch")
        if row["event_type"] != definition.world_event_type:
            raise EpisodeAdmissionError("episode_admission_world_event_type_mismatch")
        if row["due_tick"] != episode.due_tick:
            raise EpisodeAdmissionError("episode_admission_world_event_due_tick_mismatch")
        if row["event_json"].get("summary") != definition.world_event_summary:
            raise EpisodeAdmissionError("episode_admission_world_event_summary_mismatch")
        if content_hash(row["sealed_outcome_json"]) != row["outcome_hash"]:
            raise EpisodeAdmissionError("episode_admission_persisted_outcome_hash_mismatch")

        self._validate_structure_sources(
            connection,
            definition=definition,
            case_ref=row["life_case_case_ref"],
            chart_version_ref=row["chart_version_ref"],
        )
        self._validate_baseline_sources(connection, definition=definition)
        return EpisodeAuthoritySnapshot(
            life_case_revision_ref=life_case_revision_ref,
            life_case_revision_hash=row["revision_hash"],
            world_event_ref=episode.world_event_ref,
            outcome_hash=row["outcome_hash"],
        )

    @staticmethod
    def _validate_structure_sources(
        connection: Any,
        *,
        definition: DreamEpisodeDefinition,
        case_ref: str,
        chart_version_ref: str,
    ) -> None:
        for source_ref in definition.organ_set["evidence_leaf_structure"].source_refs:
            fact_row = (
                connection.execute(
                    text(
                        """
                    SELECT case_ref, chart_version_ref
                    FROM mingli.facts
                    WHERE fact_ref = :fact_ref
                    """
                    ),
                    {"fact_ref": source_ref},
                )
                .mappings()
                .one_or_none()
            )
            if fact_row is not None:
                if (
                    fact_row["case_ref"] != case_ref
                    or fact_row["chart_version_ref"] != chart_version_ref
                ):
                    raise EpisodeAdmissionError(
                        "episode_admission_structure_fact_lineage_mismatch"
                    )
                continue
            timing_row = (
                connection.execute(
                    text(
                        """
                    SELECT case_ref, chart_version_ref
                    FROM mingli.timing_evidence_vectors
                    WHERE vector_ref = :vector_ref
                    """
                    ),
                    {"vector_ref": source_ref},
                )
                .mappings()
                .one_or_none()
            )
            if timing_row is not None:
                if (
                    timing_row["case_ref"] != case_ref
                    or timing_row["chart_version_ref"] != chart_version_ref
                ):
                    raise EpisodeAdmissionError(
                        "episode_admission_structure_fact_lineage_mismatch"
                    )
                continue
            domain_row = (
                connection.execute(
                    text(
                        """
                    SELECT case_ref, chart_version_ref
                    FROM mingli.life_domain_evidence_vectors
                    WHERE vector_ref = :vector_ref
                    """
                    ),
                    {"vector_ref": source_ref},
                )
                .mappings()
                .one_or_none()
            )
            if domain_row is None:
                raise EpisodeAdmissionError("episode_admission_structure_source_missing")
            if (
                domain_row["case_ref"] != case_ref
                or domain_row["chart_version_ref"] != chart_version_ref
            ):
                raise EpisodeAdmissionError(
                    "episode_admission_structure_fact_lineage_mismatch"
                )

    @staticmethod
    def _validate_baseline_sources(
        connection: Any,
        *,
        definition: DreamEpisodeDefinition,
    ) -> None:
        episode = definition.runtime
        expected = {str(item["evidence_ref"]): item for item in definition.baseline_evidence}
        if episode.entry_world_event is not None:
            authored = {
                str(item["evidence_ref"]): item for item in episode.entry_world_event.evidence
            }
            if authored != expected:
                raise EpisodeAdmissionError("episode_admission_entry_evidence_mismatch")
            return

        for evidence_ref, evidence in expected.items():
            row = (
                connection.execute(
                    text(
                        """
                    SELECT world_event_ref, committed_at_tick,
                           evidence_json, evidence_hash
                    FROM world.event_evidence
                    WHERE evidence_ref = :evidence_ref
                    """
                    ),
                    {"evidence_ref": evidence_ref},
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                raise EpisodeAdmissionError("episode_admission_baseline_evidence_missing")
            if (
                row["world_event_ref"] != episode.baseline_event_ref
                or row["committed_at_tick"] > episode.cutoff_tick
                or row["evidence_json"] != evidence
                or row["evidence_hash"] != content_hash(evidence)
            ):
                raise EpisodeAdmissionError("episode_admission_baseline_evidence_mismatch")


class StoryEpisodeTransitionAdmissionService:
    """Story-owned append-only writer for Episode graph edges."""

    def admit(
        self,
        connection: Any,
        *,
        definition: EpisodeTransitionContract,
    ) -> str:
        transition = EpisodeTransitionContract.model_validate(definition.model_dump(mode="json"))
        payload = transition.model_dump(mode="json")
        transition_hash = content_hash(payload)
        persisted = self._persisted_transition(
            connection,
            transition_ref=transition.transition_ref,
        )
        if persisted is not None:
            self._verify_persisted(
                persisted=persisted,
                transition=transition,
                payload=payload,
                transition_hash=transition_hash,
            )
            return transition_hash

        self._validate_endpoints(connection, transition=transition)
        connection.execute(
            text(
                """
                INSERT INTO story.episode_transitions
                    (transition_ref, transition_version, from_question_ref,
                     to_question_ref, label, runtime_status,
                     transition_json, transition_hash)
                VALUES
                    (:transition_ref, :transition_version, :from_question_ref,
                     :to_question_ref, :label, :runtime_status,
                     CAST(:transition_json AS jsonb), :transition_hash)
                ON CONFLICT (transition_ref) DO NOTHING
                """
            ),
            {
                **payload,
                "transition_json": canonical_json(payload),
                "transition_hash": transition_hash,
            },
        )
        persisted = self._persisted_transition(
            connection,
            transition_ref=transition.transition_ref,
        )
        if persisted is None:
            raise EpisodeAdmissionError("episode_transition_admission_missing")
        self._verify_persisted(
            persisted=persisted,
            transition=transition,
            payload=payload,
            transition_hash=transition_hash,
        )
        return transition_hash

    @staticmethod
    def _persisted_transition(
        connection: Any,
        *,
        transition_ref: str,
    ) -> Any | None:
        return (
            connection.execute(
                text(
                    """
                    SELECT transition_version, from_question_ref, to_question_ref,
                           label, runtime_status, transition_json, transition_hash
                    FROM story.episode_transitions
                    WHERE transition_ref = :transition_ref
                    """
                ),
                {"transition_ref": transition_ref},
            )
            .mappings()
            .one_or_none()
        )

    @staticmethod
    def _verify_persisted(
        *,
        persisted: Any,
        transition: EpisodeTransitionContract,
        payload: dict[str, Any],
        transition_hash: str,
    ) -> None:
        expected = {
            "transition_version": transition.transition_version,
            "from_question_ref": transition.from_question_ref,
            "to_question_ref": transition.to_question_ref,
            "label": transition.label,
            "runtime_status": transition.runtime_status,
            "transition_json": payload,
            "transition_hash": transition_hash,
        }
        if dict(persisted) != expected:
            raise EpisodeAdmissionError("episode_transition_admission_conflict")

    @staticmethod
    def _validate_endpoints(
        connection: Any,
        *,
        transition: EpisodeTransitionContract,
    ) -> None:
        rows = (
            connection.execute(
                text(
                    """
                    SELECT question_ref, due_tick, cutoff_tick,
                           episode_contract_json
                    FROM story.question_instances
                    WHERE question_ref = ANY(:question_refs)
                    """
                ),
                {
                    "question_refs": [
                        transition.from_question_ref,
                        transition.to_question_ref,
                    ]
                },
            )
            .mappings()
            .all()
        )
        by_ref = {str(row["question_ref"]): row for row in rows}
        if set(by_ref) != {
            transition.from_question_ref,
            transition.to_question_ref,
        }:
            raise EpisodeAdmissionError("episode_transition_endpoint_missing")
        source = by_ref[transition.from_question_ref]
        target = by_ref[transition.to_question_ref]
        source_episode = DreamEpisodeContract.model_validate(source["episode_contract_json"])
        target_episode = DreamEpisodeContract.model_validate(target["episode_contract_json"])
        if (
            source_episode.actor_ref != target_episode.actor_ref
            or source_episode.tree_ref != target_episode.tree_ref
        ):
            raise EpisodeAdmissionError("episode_transition_identity_mismatch")
        if target_episode.entrypoint:
            raise EpisodeAdmissionError("episode_transition_target_is_entrypoint")
        if int(target["cutoff_tick"]) < int(source["due_tick"]):
            raise EpisodeAdmissionError("episode_transition_time_overlap")
        if source_episode.continuation_question_ref not in (
            None,
            transition.to_question_ref,
        ):
            raise EpisodeAdmissionError("episode_transition_legacy_target_mismatch")
        if source_episode.continuation_label not in (None, transition.label):
            raise EpisodeAdmissionError("episode_transition_legacy_label_mismatch")
